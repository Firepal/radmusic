import os
from . import conf

def opus_preset(name):
    return {
        "max_parallel_encodes": 6,
        "wav2flac": False,
        "copy_aux_files": True,

        "convert_exts": [".wav",".flac",".ogg",".mp3"],

        "targets": {
            name+"_opuslight": {
            "opts": "-ar 48000 -b:a 96k -application audio",
            "file_ext": "opus"
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
            "opts": "-ar 44100 -b:a 128k -map_metadata 0:s",
            "file_ext": "mp3",
            "convert_exts": [".wav",".flac",".ogg"]
            },
        }
    }

def av1_preset(name):
    return {
        "quiet": True,
        "max_parallel_encodes": 1,
        "copy_aux_files": True,
        "convert_exts": [".mkv",".mp4",".avi",".webm"],

        "targets": {
            name+"_AV1": {
            "opts": "-map 0 -c:v libsvtav1 -svtav1-params tune=0 -crf 25 -preset 8 -c:a libopus -ar 48000 -b:a 96k -ac 2 -application audio",
            "file_ext": "mkv"
            }
        }
    }

def n3ds_preset(name):
    return {
        "quiet": True,
        "max_parallel_encodes": 1,
        "copy_aux_files": False,
        "convert_exts": [".mkv",".mp4",".avi",".webm"],

        "targets": {
            name+"_3DS": {
            "opts": "-map 0 -c:v libx264 -pix_fmt yuv420p -crf 10 -c:a aac -b:a 128k -vf \"scale='trunc(min(1,min(400/iw,240/ih))*iw/2)*2':'trunc(min(1,min(400/iw,240/ih))*ih/2)*2':flags=bicubic\"",
            "file_ext": "mkv"
            }
        }
    }

def n3ds_2x_preset(name):
    return {
        "quiet": True,
        "max_parallel_encodes": 1,
        "copy_aux_files": False,
        "convert_exts": [".mkv",".mp4",".avi",".webm"],

        "targets": {
            name+"_3DS": {
            "opts": "-map 0 -c:v libx264 -pix_fmt yuv420p -crf 10 -c:a aac -b:a 128k -vf \"fps=30,scale='trunc(min(1,min(400/iw,240/ih))*iw/2)*4':'trunc(min(1,min(400/iw,240/ih))*ih/2)*2':flags=bicubic\"",
            "file_ext": "mkv"
            }
        }
    }

presets = [
    ("Convert music to Opus", opus_preset),
    ("Convert music to Opus and MP3", opusmp3_preset),
    ("Convert videos to AV1", av1_preset),
    ("Convert videos for 3DS", n3ds_preset),
    ("Convert videos for 3DS (Wide mode, 2x horizontal res)", n3ds_2x_preset),
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
    print("It is assumed you want to setup umc for this folder.")
    print("Here are presets to get you started.")
    print()
    
    picked = None
    while picked == None:
        show_presets()

        picked = pick_preset()
    
    picked_conf = picked[1](os.path.basename(cwd))
    
    conf.create_conf_file(picked_conf)

    print("Config created. Tweak the config in a text editor if you want, then restart umc.")
    
    return None
