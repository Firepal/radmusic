import os
import shlex
import subprocess
import sys
import time
from . import fget, misc, conf
import re
import yaml
from pathlib import Path
import signal
from threading import Thread, Event

ff = "ffmpeg"

def get_command(in_name, out_name, opts = ""):
    cmd = [ff, '-n', '-hide_banner', 
            '-i', in_name]
    cmd += shlex.split(opts)
    cmd.append(out_name)

    return cmd

def get_percent_string(cur_len,orig_len,outfile):
    percent = 1-(cur_len/orig_len)

    full_string = str(round(percent*100,2))+"% "
    full_string += str(orig_len - cur_len)+"/"+str(orig_len)+" "+os.path.dirname(outfile)

    return misc.fit_in_one_line(full_string)

def get_file_string(outfile):
    return "Encoded " + outfile + "\n"

class Encode:
    def __init__(self,in_name: str, out_name: str, opts: str):
        self.in_name = in_name
        self.out_name = out_name
        self.opts = opts

EncodeQueue = list[Encode]

class Converter:
    target: dict
    enc_queue: EncodeQueue
    event: Event
    def __init__(self, target, enc_queue, event):
        self.target = target
        self.enc_queue = enc_queue
        self.event = event
    
    def get_command(in_name, out_name, opts = ""):
        cmd = [ff, '-n', '-hide_banner', 
                '-i', in_name]
        cmd += shlex.split(opts)
        cmd.append(out_name)

        return cmd
    
    def convert_file(self,in_name: str, out_name: str, opts = "", out=subprocess.DEVNULL):
        return subprocess.Popen(
            Converter.get_command(in_name, out_name, opts),
            stdout=None,
            stderr=None
        )
    
    def run(self): raise NotImplementedError

class ConverterParallel(Converter):
    proc_queue: list[tuple[subprocess.Popen,Encode]] = []
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
    
    def error(self,enc: Encode):
        print("------------")
        print(str(enc.in_name))
        print(str(enc.out_name))
        print("One of your encodes did not succeed!")


        print(" ".join(Converter.get_command(enc.in_name,enc.out_name,enc.opts)))
        if os.path.exists(enc.out_name):
            os.remove(enc.out_name)
        print("------------")

    def make_proc(self,enc: Encode):
        return Converter.convert_file(enc.in_name, enc.out_name, enc.opts)

    def run(self):
        orig_len = 0
        if ("preexisting_files" in self.target):
            orig_len += self.target["preexisting_files"]

        while len(self.enc_queue) + len(self.proc_queue) > 0:
            for i, (p, enc) in enumerate(self.proc_queue):
                code = p.poll()
                if code == None: continue
                
                if code > 0:
                    self.error(enc)
                    return
                sys.stdout.flush()

                self.proc_queue.remove((p, enc))
            
            if self.event.is_set():
                proc.terminate()
                break

            if len(self.proc_queue) >= self.target["max_parallel_encodes"]:
                continue

            if len(self.enc_queue) > 0:
                enc = self.enc_queue.pop()
                proc = self.make_proc(enc)
                self.proc_queue.append((proc,enc))
    

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
            self.proc = self.convert_file(enc.in_name,enc.out_name,enc.opts)
        
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

def get_params_in_opts(opts: str):
    return re.findall('{.+?}',opts)

def strip_uniform_brackets(params):
    arr = []
    for p in params:
        arr.append(re.sub(r'[{}]', '', p))
    return arr

def apply_opts_params(target: dict,uniforms: dict):
    opts = target["opts"]
    t_uniforms = get_params_in_opts(opts)
    t_uniforms_ub = strip_uniform_brackets(t_uniforms)

    for u_str in t_uniforms:
        opt_u = re.sub(r'[{}]', '', u_str)
        
        if opt_u in uniforms:
            opts = opts.replace(str(u_str),str(uniforms[opt_u]))
        else:
            print("Fatal error: \"" + opt_u + "\" in opts doesn't match any uniform in config:\n")
            print("opts:", opts)
            print("uniforms (parsed from opts):", t_uniforms)
            print("uniforms (defined in config):", uniforms)
            return
    return opts

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
        

# creates target tuples and returns array
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
    
    if "uniforms" in config:
        init = Target(apply_opts_params(target,config["uniforms"]),files)
    elif override == None and len(get_params_in_opts(target["opts"])) > 0:
        print("Fatal error: no uniforms set")
        quit(1)
    else:
        init = Target(target["opts"],files)

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

            new_opts = apply_opts_params(target,ov_params)
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
            # out_name = os.path.splitext(
            #     os.path.join(target_dir,file)
            # )[0] + target["file_ext"]
            out_name = target_dir.joinpath(file).with_suffix(target["file_ext"])

            in_name = src_dir.joinpath(file)
            if os.path.exists(out_name):
                if not ("preexisting_files" in target):
                    target["preexisting_files"] = 0
                target["preexisting_files"] += 1
            else:
                enc_queue.append(Encode(in_name,out_name,opts))

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
    
    threads: list[Thread] = []
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

        tcrit = get_key_or_none("convert_exts",[target,config])
        
        if tcrit == None:
            print("No file conversion filtering criteria (set \"convert_exts\" on config and/or target, e.g [\".wav\",\".flac\"])")
            return

        print("Filtering files for conversion according to target criteria:", str(tcrit))
        
        prepare_files(src_dir,target_dir,target,config,tcrit,all_files,override,enc_queue)
        
        fget.copy_dirtree(src_dir,target_dir)

        if config["copy_aux_files"] == True:
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
        t.start()
        threads.append(t)
    
    while len(threads) > 0:
        for i, thread in enumerate(threads):
            if not thread.is_alive():
                threads.pop(i)
    
    print(enc_queue)
    
    print("Transcode/mirror successful. Phew!")
    print(str(copy_counter[0]), "file(s) copied.", str(copy_counter[1]), "file(s) skipped.")
    print(str(enc_count), "file(s) transcoded.")
    return (event,threads)