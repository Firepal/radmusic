import os
import shlex
import subprocess
import sys
import time
from . import fget

ff = "ffmpeg"

def get_command(in_name, out_name, opts = ""):
    cmd = [ff, '-n', '-hide_banner', 
            '-i', in_name]
    cmd += shlex.split(opts)
    cmd.append(out_name)

    return cmd

def convert_file_parallel(in_name, out_name, opts = ""):
    command = get_command(in_name, out_name, opts)
    
    proc = subprocess.Popen(command, shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return proc

def convert_file_serial(in_name, out_name, opts = ""):
    command = get_command(in_name, out_name, opts)
    
    return subprocess.call(command, shell=False)

def convert_queue_parallel(target,enc_queue):
    orig_len = len(enc_queue)
    if ("preexisting_files" in target):
        orig_len += target["preexisting_files"]

    proc_queue = []
    while len(enc_queue) > 0:
        for (p, infile, outfile, opts) in proc_queue:
            excode = p.poll()
            if excode == None: continue
            
            if excode > 0:
                print("------------")
                print(str(infile))
                print(str(outfile))
                print("One of your encodes did not succeed!")
                print(get_command(infile,outfile,opts))
                os.remove(outfile)
                print("------------")
                return
            sys.stdout.flush()
            cur_len = len(enc_queue)-1
            percent = 1-(cur_len/orig_len)
            print(end='\r')

            full_string = str( round(percent*100,2) )+"% "
            full_string += str(orig_len - cur_len)+"/"+str(orig_len)+" "+os.path.dirname(outfile)

            columns, lines = os.get_terminal_size()
            print(full_string, end='')
            print(end=(' ' * int(columns-(len(full_string)+1))))
            
            # print("Encoded " + outfile)
            proc_queue.remove((p, infile, outfile, opts))
        
        if len(proc_queue) >= target["max_parallel_encodes"]:
            continue

        enc = enc_queue.pop()
        proc = convert_file_parallel(enc[0],enc[1],target["opts"])
        proc_queue.append((proc,enc[0],enc[1],target["opts"]))

def convert_queue_serial(target,enc_queue):
    while len(enc_queue) > 0:
        current = enc_queue.pop()
        convert_file_serial(current[0],current[1],target["opts"])

def get_max_parallel_encodes(config,target):
    iterator = [config,target]
    max_parallel_encodes = 1
    for conf in iterator:
        if "max_parallel_encodes" in conf:
            max_parallel_encodes = conf["max_parallel_encodes"]

    return min(max(max_parallel_encodes,1),12)

def get_key_or_none(a,b,key):
    iterator = [a,b]
    value = None
    for conf in iterator:
        if key in conf:
            value = conf[key]
            break

    return value


def process_targets(dir, all_files, config):
    copy_counter = [0,0]
    encode_counter = 0
    
    print()

    if config == None:
        print("Skipped target evaluation...")
        return 0

    if len(config["targets"].keys()) == 0:
        print("No targets defined. Wanna go through the configuration wizard now?")
        print("# TODO Implement.") # funny
        return 0
    
    quiet = False
    if ("quiet" in config):
        quiet = bool(config["quiet"])

    enc_queue = []
    for target_key in config["targets"].keys():
        target = config["targets"][target_key]
        print()
        print("Processing target \"" + target_key + "\"")
        
        if target["file_ext"][0] != ".":
            target["file_ext"] = "." + target["file_ext"]
        
        parallel_encs = get_key_or_none(target,config,"max_parallel_encodes")
        if parallel_encs == None: parallel_encs = 1
        parallel_encs = min(max(parallel_encs,1),12)
        target["max_parallel_encodes"] = parallel_encs

        t_dir = os.path.abspath(
            os.path.join( 
            os.path.join(dir, os.path.pardir), 
            target_key
            )
        )

        tcrit = get_key_or_none(target,config,"convert_exts")
        
        if tcrit == None:
            print("No file conversion filtering criteria (set \"convert_exts\" on config and/or target, e.g [\".wav\",\".flac\"])")
            return

        print("Filtering files for conversion according to target criteria: " + str(tcrit))
        
        conv = fget.filter_ext(all_files,tcrit,False)

        fget.copy_dirtree(dir,t_dir)

        if config["copy_aux_files"] == True:
            fget.copy_aux_files(all_files,tcrit,t_dir,copy_counter)
        

        for file in conv:
            out_name = os.path.splitext(
                os.path.join(t_dir,file)
            )[0] + target["file_ext"]

            in_name = os.path.join(dir,file)

            # This is slow and occurs on every target...
            # only way to ensure we aren't re-encoding uselessly though.
            if not os.path.exists(out_name):
                enc_queue.append((in_name,out_name))
                encode_counter += 1
            else:
                print(end='\r')
                print(os.path.basename(out_name) + " already exists", end='          ')
                if not ("preexisting_files" in target):
                    target["preexisting_files"] = 0
                target["preexisting_files"] += 1
        print()
        print("\n")
        
        if parallel_encs > 1:
            print("Encoding in parallel with", parallel_encs, "threads")
            convert_queue_parallel(target,enc_queue)
        else:
            if not quiet:
                print("****Encodes will occur serially (one-at-a-time).****")
                print("This is intended for weak computers or codecs that use many resources.")
                print("If you have more than 2 cores and the codec is sufficiently simple,")
                print("you can enable parallel encoding by setting \"max_parallel_encodes\" to a value greater than 1.")
                print("\n")
                print("You can disable this message by adding the following line to the beginning of your umc.yaml file: \"quiet\":true")
                print(end='\n')
                time.sleep(5)
            
            convert_queue_serial(target,enc_queue)

    
    print()
    print("Transcode/mirror successful. Phew!")
    print(str(copy_counter[0]) + " file(s) copied. " + str(copy_counter[1]) + " file(s) skipped.")
    print(str(encode_counter) + " file(s) transcoded.")