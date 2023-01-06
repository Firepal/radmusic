import os
import shlex
import subprocess
import sys
import time
from . import fget, misc, conf
import re
import yaml

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

def get_percent_string(cur_len,orig_len,outfile):
    percent = 1-(cur_len/orig_len)

    full_string = str(round(percent*100,2))+"% "
    full_string += str(orig_len - cur_len)+"/"+str(orig_len)+" "+os.path.dirname(outfile)

    return misc.fit_in_one_line(full_string)

def get_file_string(outfile):
    return "Encoded " + outfile + "\n"

def convert_queue_parallel(target,enc_queue):
    orig_len = len(enc_queue)
    if ("preexisting_files" in target):
        orig_len += target["preexisting_files"]

    proc_queue = []
    while len(enc_queue) > 0 and len(proc_queue) >= 0:
        for (p, infile, outfile, proc_opts) in proc_queue:
            excode = p.poll()
            if excode == None: continue
            
            if excode > 0:
                print("------------")
                print(str(infile))
                print(str(outfile))
                print("One of your encodes did not succeed!")


                print(" ".join(get_command(infile,outfile,proc_opts)))
                if os.path.exists(outfile):
                    os.remove(outfile)
                print("------------")
                return
            sys.stdout.flush()
            
            progress_string = get_percent_string(len(enc_queue)-1, orig_len, outfile)
            # progress_string = get_file_string(outfile)
            print(end='\r'+misc.empty_column()+'\r')
            print(progress_string,end='',flush=True)

            proc_queue.remove((p, infile, outfile, proc_opts))
        
        if len(proc_queue) >= target["max_parallel_encodes"]:
            continue

        enc = enc_queue.pop()
        proc = convert_file_parallel(enc[0],enc[1],enc[2])
        proc_queue.append((proc,enc[0],enc[1],enc[2]))

def convert_queue_serial(target,enc_queue):
    while len(enc_queue) > 0:
        enc = enc_queue.pop()
        convert_file_serial(enc[0],enc[1],enc[2])

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
def get_overriden_files(all_files,config):
    conv = fget.filter_ext(all_files,[".umc_override"])
    
    overrides = []
    all_files_trim = all_files[:]

    for override_file in conv:
        files_overriden = []
        for file in all_files:
            if fget.path_is_parent(
                os.path.dirname(override_file),
                os.path.dirname(file),
                ):
                if not file in all_files_trim: continue
                all_files_trim.remove(file)
                if file == override_file: continue
                
                files_overriden.append(file)
        print(override_file)
        overrides.append((override_file,files_overriden))
    
    if len(overrides) == 0: return None

    return (all_files_trim,overrides)

def get_params_in_opts(opts):
    return re.findall('{.+?}',opts)

def apply_opts_params(target,uniforms):
    t_uniforms = get_params_in_opts(target["opts"])

    opts = target["opts"]
    for u_str in t_uniforms:
        opt_u = re.sub(r'[{}]', '', u_str)
        
        if opt_u in uniforms:
            opts = opts.replace(str(u_str),str(uniforms[opt_u]))
        else:
            print("Fatal error: \"" + opt_u + "\" in opts doesn't match any uniforms in config:\n")
            print("opts:", target["opts"])
            print("uniforms (parsed from opts):", t_uniforms)
            print("uniforms (defined in config):", uniforms)
            quit(1)
    return opts

def prepare_files(src_dir,target,config,tcrit,all_files,override):
    to_process = []
    files = all_files if override == None else override[0]
    
    if "uniforms" in config:
        init = (apply_opts_params(target,config["uniforms"]),files)
    elif override == None and len(get_params_in_opts(target["opts"])) > 0:
        print("Fatal error: no uniforms set")
        quit(1)
    else:
        init = (target["opts"],files)


    to_process.append(init)
    
    if override != None:
        for overrides in override[1]:
            ov_file = os.path.join(src_dir,overrides[0])

            ov_params = conf.get_dict_from_yaml(ov_file)

            if ov_params == None:
                print(ov_file, "didn't read properly, falling back to config uniforms...")
                ov_params = config["uniforms"]
            misc.extend_dict(ov_params,config["uniforms"])

            # print(ov_params)
            
            new_opts = apply_opts_params(target,ov_params)
            print("Applied override:", ov_file)

            to_process.append((
                new_opts,
                overrides[1]
            ))
    
    for i in range(len(to_process)):
        arr = to_process[i]
        yes = fget.filter_ext(arr[1],tcrit)

        to_process[i] = (arr[0],yes)
    
    return to_process

def create_queue(src_dir, t_dir, target: dict, to_process: list):
    enc_queue = []
    
    for opts, files in to_process:
        for file in files:
            out_name = os.path.splitext(
                os.path.join(t_dir,file)
            )[0] + target["file_ext"]

            in_name = os.path.join(src_dir,file)

            if os.path.exists(out_name):
                if not ("preexisting_files" in target):
                    target["preexisting_files"] = 0
                target["preexisting_files"] += 1
            else:
                enc_queue.append((in_name,out_name,opts))
    
    return enc_queue

def process_targets(src_dir, all_files, config):
    copy_counter = [0,0]
    
    print()

    if config == None:
        print("Skipped target evaluation...")
        return 0

    if len(config["targets"].keys()) == 0:
        print("No targets defined. Wanna go through the configuration wizard now?")
        print("# TODO Implement.") # funny
        return 0
    
    quiet = bool(get_key_or_none("quiet",[config]))
    config["quiet"] = quiet
    
    target_dir = os.path.join(src_dir, os.path.pardir)
    if ("target_dir" in config):
        target_dir = os.path.expanduser(config["target_dir"])
    
    override = get_overriden_files(all_files,config)
    
    if override != None:
        if not "uniforms" in config:
            print("Tried to use .umc_override where no uniforms exist on the default config!")
            quit(1)

    enc_queue = []
    for target_key in config["targets"].keys():
        target = config["targets"][target_key]
        print()
        print("Processing target \"" + target_key + "\"")
        
        # assert file ext has a dot prepended
        if target["file_ext"][0] != ".":
            target["file_ext"] = "." + target["file_ext"]
        
        parallel_encs = get_key_or_none("max_parallel_encodes",[target,config])
        if parallel_encs == None: parallel_encs = 1
        parallel_encs = min(max(parallel_encs,1),12) # TODO: get actual CPU count
        target["max_parallel_encodes"] = parallel_encs

        t_dir = os.path.abspath(
            os.path.join(target_dir,target_key)
        )

        tcrit = get_key_or_none("convert_exts",[target,config])
        
        if tcrit == None:
            print("No file conversion filtering criteria (set \"convert_exts\" on config and/or target, e.g [\".wav\",\".flac\"])")
            return

        print("Filtering files for conversion according to target criteria:", str(tcrit))
        
        to_process = prepare_files(src_dir,target,config,tcrit,all_files,override)

        fget.copy_dirtree(src_dir,t_dir)

        if config["copy_aux_files"] == True:
            fget.copy_aux_files(all_files,tcrit,src_dir,t_dir,copy_counter)
        
        enc_queue += create_queue(src_dir,t_dir,target,to_process)

        print()
        enc_count = len(enc_queue)
        if len(enc_queue) < 1:
            continue

        if parallel_encs > 1:
            if not quiet:
                print("Encoding in parallel with", parallel_encs, "threads")
            convert_queue_parallel(target,enc_queue)
        else:
            if not quiet:
                print("****Encodes will occur serially (one at a time)****")
                print("This is intended for weak computers or codecs that use many resources.")
                print("If you have RAM to spare, more than 2 CPU cores and the codec is simple,")
                print("try enabling parallel encodes by setting \"max_parallel_encodes\" to an integer greater than 1.")
                print("\n")
                print("You can disable this message with the -q option or by setting \"quiet\" to true.")
                print()
                time.sleep(5)
            
            convert_queue_serial(target,enc_queue)

    
    print()
    print("Transcode/mirror successful. Phew!")
    print(str(copy_counter[0]), "file(s) copied.", str(copy_counter[1]), "file(s) skipped.")
    print(str(enc_count), "file(s) transcoded.")