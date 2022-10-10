import os
import shutil
import subprocess
import json
import filecmp

def get_files_ext(dir,ext_array):
    out=[]
    for current_dir, dirs, files in os.walk( dir ):
        if len(files) == 0: continue

        for file in files:
            cur = os.path.splitext( file )
            
            for ext in ext_array:
                if cur[1].lower() == ext:
                    out.append(os.path.join( os.path.relpath(current_dir, dir), file ))
                    break
    return out

def get_files_not_ext(dir,ext_array):
    out=[]
    for current_dir, dirs, files in os.walk( dir ):
        if len(files) == 0: continue

        for file in files:
            cur = os.path.splitext( file )
            
            keep = True
            for ext in ext_array:
                if cur[1].lower() == ext:
                    keep = False
            
            if keep:
                out.append(os.path.join( os.path.relpath(current_dir, dir), file ))
    return out

def get_all_convertees(dir):
    return get_files_ext(dir,[".flac",".wav"])

def convert_file(in_name, out_name, opts = ""):
    command = "ffmpeg -n -i \"" + in_name + "\" " + opts + " \"" + out_name + "\""
    
    subprocess.run(command, shell=False)

def delete_all(files):
    for file in files:
        os.remove(file)

def silent_wav2flac(dir):
    files = get_files_ext(dir,[".wav"])
    for file in files:
        convert_file(file, os.path.splitext(file)[0] + ".flac")
    delete_all(files)

def check_for_wavs(dir):
    files = get_files_ext(dir,[".wav"])

    if len(files) > 0:
        conv_prompt = input("WAV file(s) detected. Would you like to convert them to FLAC to save space? ")

        if conv_prompt.lower()[0] == "y":
            for file in files:
                convert_file(file, os.path.splitext(file)[0] + ".flac")

            del_prompt = input("Would you like to *DELETE* the leftover WAV file(s)?")
            if del_prompt.lower()[0] == "y":
                for file in files:
                    print("Deleting " + file)
                    # os.remove(file)

def init_config(dir):
    file = os.path.join(dir,"radmusic_conf.json")

    
    try:
        cf = open(file,"r")
    except OSError:
        print("Couldn't load file")
        quit()
    
    try:
        config = json.loads(cf.read())
    except:
        print("Couldn't decode JSON in file " + file)
        quit()

    if config["targets"] == None:
        print("No targets.")
        quit(1)
    return config

def copy_aux_files(src,dst,count):
    files = get_files_not_ext(src,[".flac",".wav"])
    
    for file in files:
        d = os.path.join(
            dst,
            os.path.dirname(file)
        )
        
        df = os.path.join(dst,file)
        if os.path.exists(df):
            # compare files to prevent unnecessary copies
            if filecmp.cmp(file, df, shallow=True):
                count[1] += 1
                continue
        
        print("Copying " + df)
        shutil.copy(file,d)
        count[0] += 1

def copy_dirtree(src,dst):
    if not os.path.exists(dst):
        os.mkdir(dst)
    
    for current_dir, dirs, files in os.walk( src ):
        full = os.path.relpath(current_dir,src)
        for dir in dirs:
            leaf = os.path.join(full,dir)
            mirror = os.path.join(dst,leaf)
            
            os.makedirs( mirror, exist_ok=True )



def process_targets(dir, conv, config):
    copy_counter = [0,0]
    encode_counter = 0
    for target in config["targets"]:
        if target["file_ext"][0] != ".":
            target["file_ext"] = "." + target["file_ext"]


        t_dir = os.path.join( 
            os.path.join(dir, os.path.pardir), 
            target["name"]
        )

        copy_dirtree(dir,t_dir)

        if config["copy_aux_files"] == True:
            copy_aux_files(dir,t_dir,copy_counter)

        for file in conv:
            out_name = os.path.splitext(
                os.path.join(t_dir,file)
            )[0] + target["file_ext"]

            if not os.path.exists(out_name):
                convert_file(file,out_name,target["opts"])
                encode_counter += 1
            else:
                print(end='\r')
                print(os.path.basename(out_name) + " already exists", end='          ')
    
    print()
    print("Transcode/mirror successful. Phew!")
    print(str(copy_counter[0]) + " file(s) copied. " + str(copy_counter[1]) + " file(s) skipped.")
    print(str(encode_counter) + " file(s) transcoded.")


dir = os.getcwd()

config = init_config(dir)

if config["nuke_wavs_for_flac"]:
    silent_wav2flac(dir)
else:
    check_for_wavs(dir)

conv = get_all_convertees(dir)

process_targets(dir, conv, config)

input("Press Enter to quit...")