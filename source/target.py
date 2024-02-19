import os
import shlex
import subprocess
import sys
import time
import math
from . import fget, misc, conf, specials
import re
import yaml
from pathlib import Path
import signal
from threading import Thread, Event

ff = "ffmpeg"

def smoothstep(edge0, edge1, x):
    # Scale, and clamp x to 0..1 range
    x = max(0.0, min((x - edge0) / (edge1 - edge0), 1.0))
    # Evaluate polynomial
    return x * x * (3 - 2 * x)

def lerp(a: float, b: float, t: float):
    return (1 - t) * a + t * b

class ProgressReport:
    def __init__(self,file: Path,encode_num: int,total_encodes: int):
        self.file = file
        self.encode_num = encode_num
        self.total_encodes = total_encodes

def get_percent_string(cur_len,orig_len,outfile):
    percent = 1-(cur_len/orig_len)

    full_string = str(round(percent*100,2))+"% "
    full_string += str(orig_len - cur_len)+"/"+str(orig_len)+" "+os.path.dirname(outfile)

    return misc.fit_in_one_line(full_string)

def get_file_string(outfile):
    return "Encoded " + outfile + "\n"

class Encode:
    def __init__(self,in_name: str, out_name: str, opts: str = "", preopts: str = ""):
        self.in_name = in_name
        self.out_name = out_name
        self.opts = opts
        if preopts == None: preopts = ""
        self.preopts = preopts

EncodeQueue = list[Encode]

class Converter:
    target: dict
    enc_queue: EncodeQueue
    event: Event
    def __init__(self, target, enc_queue, event = Event()):
        self.target = target
        self.enc_queue = enc_queue
        self.event = event
    
    def get_command(enc: Encode):
        cmd = [ff]
        cmd += ['-n']
        if len(enc.preopts) > 0:
            cmd += shlex.split(enc.preopts)
        cmd += ['-i', str(enc.in_name)]
        cmd += shlex.split(enc.opts)
        cmd += [str(enc.out_name)]

        return cmd
    
    def convert_file(self,enc, out=None):
        return subprocess.Popen(
            Converter.get_command(enc),
            stdout=out,
            stderr=out)
    
    def run(self): raise NotImplementedError

class ConverterParallel(Converter):
    proc_queue: list[tuple[subprocess.Popen,Encode]] = []
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        
        # sort by size to process smallest files first

        # this is a shim for the fact that 
        # the threaded performance starts sucking when umc processes bigger files with many threads

        # we need to find a way to only process 2 big files at once
        # to let more threads work on smaller files
        # print(self.enc_queue.sort(key=lambda x: os.path.getsize(x.in_name), reverse=True))
    
    def error(self, p: subprocess.Popen, enc: Encode):
        print("------------")
        print(str(enc.in_name))
        print(str(enc.out_name))
        print("One of your encodes did not succeed!")
        print(Converter.get_command(enc))
        print(" ".join(Converter.get_command(enc)))
        print(str(p.stdout.read()))
        print(str(p.stderr.read()))


        # if os.path.exists(enc.out_name):
        #     os.remove(enc.out_name)
        print("------------")

    def make_proc(self,enc: Encode):
        return self.convert_file(enc, subprocess.DEVNULL)

    def run(self):
        orig_len = 0
        if ("preexisting_files" in self.target):
            orig_len += self.target["preexisting_files"]
        
        max_total_par = self.target["max_parallel_encodes"]
        parallel_cap = 1
        
        proc_time_lerp = 3.0
        
        start = time.time()
        print("hello")
        while len(self.enc_queue) + len(self.proc_queue) > 0:
            for i, (p, enc, proc_start) in enumerate(self.proc_queue):
                code = p.poll()
                if code == None: continue
                if code > 0:
                    print(code)
                    self.error(p,enc)
                    return
                sys.stdout.flush()

                proc_time = time.time() - proc_start
                proc_time_lerp = lerp(proc_time_lerp, proc_time, 0.03)
                
                # we heuristically cap the number of simulateneous conversions based on speed
                # to make sure that I/O remains smooth and we don't destroy the CPU with a bunch of work
                
                sec = get_key_or_none("thread_speed",[self.target])
                if sec == None: sec = 6.0

                par = math.ceil(smoothstep(sec,0,proc_time) * max_total_par)
                
                old_pcap = parallel_cap
                parallel_cap = lerp(par,parallel_cap,0.9)
                parallel_cap = min(par,parallel_cap)
                parallel_cap = max(1,parallel_cap)
                
                this_encode_name = Path(enc.in_name).name
                self.proc_queue.remove((p, enc, proc_start))
                
                if round(old_pcap) != round(parallel_cap):
                    total_len = len(self.enc_queue) + len(self.proc_queue)
                    min_left = math.ceil((total_len * proc_time_lerp) / 60)
                    
                    threading_info = this_encode_name + " - "
                    threading_info += "{:.1f}s - ".format(proc_time)
                    threading_info += "Thread count now = {} - ".format(round(parallel_cap))
                    threading_info += "{} files left, ".format(total_len)
                    threading_info += "{} min left ".format(min_left)                  
                    print(threading_info)
                
            
            if self.event.is_set():
                print("Telling all the ffmpegs to shutdown gracefully...\nThis may take some time.")
                for p, enc, proc_start in self.proc_queue:
                    p.communicate("q")
                break
            
            if len(self.proc_queue) >= round(parallel_cap):
                continue

            if len(self.enc_queue) > 0:
                enc = self.enc_queue.pop()
                proc = self.make_proc(enc)
                proc_start = time.time()
                print(enc.in_name)
                self.proc_queue.append((proc,enc,proc_start))
        
        end = time.time()
        print("are we done? i think we're done")
        print(round(end - start), "seconds")
    

class ConverterSerial(Converter):
    already_stopping = False
    proc: subprocess.Popen = None
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
    
    def check_kill(self):
        time.sleep(1)
        if self.event.is_set():
            print("\nTelling ffmpeg to wrap up...")
            self.proc.terminate()
            self.already_stopping = True
        return self.event.is_set()
    
    def run(self):
        while len(self.enc_queue) > 0:
            if self.check_kill(): break
            if not (self.proc is None):
                if self.proc.poll() is None: continue
            
            enc = self.enc_queue.pop()
            print(Converter.get_command(enc))
            self.proc = self.convert_file(enc)
        
        while self.proc.poll() is None and not self.already_stopping:
            if self.check_kill(): break


def get_key_or_none(key, iterator):
    value = None
    for conf in iterator:
        if key in conf:
            value = conf[key]
            break

    return value

# returns 2-tuple, where:
# 0 = files affected by default config
# 1 = files affected by .umc_override files
def get_overriden_files(all_files,src_dir,config):
    conv = fget.filter_ext(all_files,[".umc_override"])
    
    overrides = []
    all_files_trim = all_files[:]

    for ov_file in conv:
        files_overriden = []
        
        ov_dict = conf.get_dict_from_yaml(
            os.path.join(src_dir,ov_file)
        )

        skip_dir = False
        if not ov_dict == None:
            skip_dir = get_key_or_none("skip_dir",[ov_dict])

        for file in all_files:
            if fget.path_is_parent(
                os.path.dirname(ov_file),
                os.path.dirname(file),
                ):
                if not file in all_files_trim: continue
                all_files_trim.remove(file)
                if file == ov_file or skip_dir: continue
                
                files_overriden.append(file)
        
        overrides.append((ov_file,files_overriden,ov_dict))
    
    if len(overrides) == 0: return None

    return (all_files_trim,overrides)


class Target:
    target_dict: dict
    files: list[str]
    def __init__(self, target_dict: dict, files: list[str]):
        self.target_dict = target_dict
        self.files = files
    
    def __getitem__(self, key):
        match key: 
            case 0: return self.target_dict
            case 1: return self.files
            case _: raise IndexError
    
    def __setitem__(self, key, val):
        match key: 
            case 0: self.target_dict = val
            case 1: self.files = val
            case _: raise IndexError
    
    def as_tuple(self):
        return (self.target_dict,self.files)
        

def prepare_files(
        src_dir: Path, 
        target_dir: Path, 
        target: dict,
        config: dict,
        tcrit: list[str],
        all_files: list,
        override,
        enc_queue: EncodeQueue):
    to_process: list[Target] = []
    files = all_files if override == None else override[0]
    macros = get_key_or_none("macros",[config])

    if "uniforms" in config:
        init = Target(specials.apply_opts_params(target["opts"],config["uniforms"],macros),files)
    elif override == None and len(specials.get_uniforms(target["opts"])) > 0:
        print("Fatal error: no uniforms set")
        quit(1)
    else:
        init = Target(target["opts"],files)
    print(init.target_dict)
    to_process.append(init)
    
    overrides_applied: list[Path] = []
    if override != None:
        for overrides in override[1]:
            ov_file = os.path.join(src_dir,overrides[0])

            ov_params = overrides[2]

            if ov_params == None:
                print(ov_file, "didn't read properly, falling back to config uniforms...")
                ov_params = config["uniforms"]
            misc.extend_dict(ov_params,config["uniforms"])

            new_opts = specials.apply_opts_params(target["opts"],ov_params,macros)
            print(new_opts)
            overrides_applied.append(Path(ov_file).relative_to(src_dir).parent)
            
            to_process.append(Target(
                new_opts,
                overrides[1]
            ))

    if len(overrides_applied) > 0:
        print(f"Applied overrides:\n{', '.join([str(i) for i in overrides_applied])}")
    
    # apply filter criteria
    for i in range(len(to_process)):
        to_process[i][1] = fget.filter_ext(to_process[i][1],tcrit)
    

    for opts, files in [target.as_tuple() for target in to_process]:
        for file in files:
            out_name = target_dir.joinpath(file).with_suffix(target["file_ext"])

            in_name = src_dir.joinpath(file)
            if os.path.exists(out_name):
                if not ("preexisting_files" in target):
                    target["preexisting_files"] = 0
                target["preexisting_files"] += 1
            else:
                enc_queue.append(Encode(in_name,out_name,opts,get_key_or_none("preopts",[target])))

def get_target_dir(src_dir,config,target):
    target_dir = get_key_or_none("target_dir",[target,config])
    if target_dir != None:
        return Path(target_dir)
    else: # use parent dir as default
        return Path(src_dir).parent

def process_targets(src_dir: Path, all_files: list, config: dict):
    copy_counter = [0,0]

    if config == None:
        print("Skipped target evaluation...")
        return

    if len(config["targets"].keys()) == 0:
        print("No targets defined. Wanna go through the configuration wizard now?")
        print("# TODO Implement.") # funny
        return
    
    quiet = bool(get_key_or_none("quiet",[config]))
    config["quiet"] = quiet
    
    override = get_overriden_files(all_files,src_dir,config)
    
    if override != None:
        if "uniforms" in override and not "uniforms" in config:
            print("Tried to use .umc_override where no default uniforms exist in the config!")
            return
    
    threads: list[tuple[Thread,str]] = []
    event = Event()
    enc_queue = EncodeQueue()
    
    for target_key in config["targets"].keys():
        target = config["targets"][target_key]
        target["name"] = str(target_key)
        
        print("Processing target \"" + target_key + "\"")

        target_dir = get_target_dir(src_dir,config,target).joinpath(target_key).resolve()
        
        # assert file ext has a dot prepended
        if target["file_ext"][0] != ".":
            target["file_ext"] = "." + target["file_ext"]
        
        parallel_encs = get_key_or_none("max_parallel_encodes",[target,config])
        if parallel_encs == None: parallel_encs = 1
        parallel_encs = min(max(parallel_encs,1),12) # TODO: get actual CPU count
        target["max_parallel_encodes"] = parallel_encs
        target["thread_speed"] = get_key_or_none("thread_speed",[config])

        tcrit = get_key_or_none("convert_exts",[target,config])
        
        if tcrit == None:
            print("No file conversion filtering criteria (set \"convert_exts\" on config and/or target, e.g [\".wav\",\".flac\"])")
            return

        print("Filtering files for conversion according to target criteria:", str(tcrit))
        
        prepare_files(src_dir,target_dir,target,config,tcrit,all_files,override,enc_queue)
        
        fget.copy_dirtree(src_dir,target_dir)

        if get_key_or_none("copy_aux_files",[target,config]) == True:
            fget.copy_aux_files(all_files,tcrit,src_dir,target_dir,copy_counter)
        
        enc_count = len(enc_queue)
        if len(enc_queue) < 1: continue
        
        converter = None
        
        conv_args = (target, enc_queue, event)
        if parallel_encs > 1:
            if not quiet:
                print("Encoding in parallel with", parallel_encs, "threads")
            converter = ConverterParallel(*conv_args)
        else:
            if not quiet:
                print("****Encodes will occur serially (one at a time)****")
                print("This is intended for weak computers or codecs that use many resources.")
                print("If you have RAM to spare, more than 2 CPU cores and the codec is simple,")
                print("try enabling parallel encodes by setting \"max_parallel_encodes\" to an integer greater than 1.")
                print("\n")
                print("You can disable this message with the -q option or by setting \"quiet\" to true.")
                
                time.sleep(5)
            
            converter = ConverterSerial(*conv_args)
        
        t = Thread(target=converter.run)
        threads.append((t,target_key))
    
    # Run target threads sequentially
    def worker():
        t = None
        for th in threads:
            if t == None:
                new_thread = th
                print(f"Running thread for {new_thread[1]}")
                t = new_thread[0]
                t.start()
                continue
            
            if not t.is_alive():
                t = None
        print("All targets done.")
    
    worker_thread = Thread(target=worker)
    worker_thread.start()
    
    return (event,threads)