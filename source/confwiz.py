import os
from . import conf

def opus_preset(name):
    return {
        "max_parallel_encodes": 6,
        "wav2flac": False,
        "copy_aux_files": True,

        "targets": {
            name+"_opuslight": {
            "opts": "-ar 48000 -b:a 96k -application audio",
            "file_ext": "opus",
            "convert_exts": [".wav",".flac",".ogg",".mp3"]
            },
        }
    }

def opusmp3_preset(name):
    return {
        "max_parallel_encodes": 6,
        "wav2flac": False,
        "copy_aux_files": True,

        "targets": {
            name+"_opus": {
            "opts": "-ar 48000 -b:a 96k -application audio",
            "file_ext": "opus",
            "convert_exts": [".wav",".flac",".ogg",".mp3"]
            },
            name+"_mp3": {
            "opts": "-ar 44100 -b:a 128k",
            "file_ext": "mp3",
            "convert_exts": [".wav",".flac",".ogg"]
            },
        }
    }

def av1_preset(name):
    return {
        "max_parallel_encodes": 6,
        "wav2flac": False,
        "copy_aux_files": True,
        "convert_exts": [".mkv",".mp4"],

        "targets": {
            name+"_AV1": {
            "opts": "-map 0 -c:v libsvtav1 -svtav1-params tune=0 -crf 25 -preset 8 -c:a libopus -ar 48000 -b:a 96k -ac 2 -application audio",
            "file_ext": "mkv"
            }
        }
    }

presets = [
    ("Convert music to Opus", opus_preset),
    ("Convert music to Opus and MP3", opusmp3_preset),
    ("Convert videos to AV1", av1_preset),
]

def show_presets():
    for i in range(len(presets)):
        print(str(i+1) + ") " + presets[i][0])

def pick_preset():
    picked = input("Enter preset: ")
    
    try:
        num = int(picked)-1
    except ValueError:
        print()
        print(picked+": not a number")
        return None
    
    try:
        p = presets[num]
        if num < 0: raise IndexError
    except IndexError:
        print()
        # print(str(num+1)+": no such preset")
        return None

    return p

def wizard(cwd):
    print("Welcome to the configuration wizard.")
    print("It is assumed you want to setup UMC for this folder.")
    print("Here are presets to get you started.")
    print()
    
    picked = None
    while picked == None:
        show_presets()

        picked = pick_preset()
    picked_conf = picked[1](os.path.basename(cwd))
    
    conf.create_conf_file(picked_conf)

    print("Config created. Tweak the config if you want, then restart umc.")
    
    return None
