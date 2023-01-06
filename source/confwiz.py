import os
from . import conf

DEFAULT_PARALLEL_ENCODES = 4

def opus_preset(name):
    return {
        "max_parallel_encodes": DEFAULT_PARALLEL_ENCODES,

        "convert_exts": [".wav",".flac",".ogg",".mp3",".m4a"],

        "uniforms": {
            "kbps": 96
        },

        "targets": {
            name+"_opus": {
            "opts": "-ar 48000 -b:a {kbps}k -application audio",
            "file_ext": "opus"
            },
        }
    }

def aac_preset(name):
    return {
        "max_parallel_encodes": DEFAULT_PARALLEL_ENCODES,

        "convert_exts": [".wav",".flac",".ogg",".mp3",".m4a",".opus"],

        "uniforms": {
            "kbps": 96
        },

        "targets": {
            name+"_aac": {
            "opts": "-ar 44100 -b:a {kbps}k -map_metadata 0:s -c:a aac -movflags use_metadata_tags -vn",
            "file_ext": "m4a"
            },
        }
    }

def mp3_preset(name):
    return {
        "max_parallel_encodes": DEFAULT_PARALLEL_ENCODES,
        
        "convert_exts": [".wav",".flac",".ogg",".m4a",".opus"],

        "uniforms": {
            "kbps": 128
        },

        "targets": {
            name+"_mp3": {
            "opts": "-ar 44100 -b:a {kbps}k -map_metadata 0:s",
            "file_ext": "mp3"
            },
        }
    }

def opusmp3_preset(name):
    return {
        "max_parallel_encodes": DEFAULT_PARALLEL_ENCODES,

        "uniforms": {
            "kbps_opus": 96,
            "kbps_mp3": 128,
        },

        "targets": {
            name+"_opus": {
            "opts": "-ar 48000 -b:a {kbps_opus}k -application audio",
            "file_ext": "opus",
            "convert_exts": [".wav",".flac",".ogg",".m4a",".mp3"]
            },
            name+"_mp3": {
            "opts": "-ar 44100 -b:a {kbps_mp3}k -map_metadata 0:s",
            "file_ext": "mp3",
            "convert_exts": [".wav",".flac",".ogg",".m4a",".opus"]
            },
        }
    }

def aacmp3_preset(name):
    return {
        "max_parallel_encodes": DEFAULT_PARALLEL_ENCODES,

        "uniforms": {
            "kbps_aac": 96,
            "kbps_mp3": 128,
        },

        "targets": {
            name+"_aac": {
            "opts": "-ar 44100 -b:a {kbps_aac}k -c:a aac -vn -map_metadata 0:s -movflags use_metadata_tags",
            "file_ext": "m4a",
            "convert_exts": [".wav",".flac",".ogg",".m4a",".mp3"]
            },
            name+"_mp3": {
            "opts": "-ar 44100 -b:a {kbps_mp3}k -map_metadata 0:s",
            "file_ext": "mp3",
            "convert_exts": [".wav",".flac",".ogg",".m4a",".aac"]
            },
        }
    }

def aacopus_preset(name):
    return {
        "max_parallel_encodes": DEFAULT_PARALLEL_ENCODES,

        "uniforms": {
            "kbps_aac": 96,
            "kbps_opus": 96,
        },

        "targets": {
            name+"_aac": {
            "opts": "-ar 44100 -b:a {kbps_aac}k -c:a aac -vn -map_metadata 0:s -movflags use_metadata_tags",
            "file_ext": "m4a",
            "convert_exts": [".wav",".flac",".ogg",".m4a",".mp3"]
            },
            name+"_opus": {
            "opts": "-ar 48000 -b:a {kbps_opus}k -application audio",
            "file_ext": "opus",
            "convert_exts": [".wav",".flac",".ogg",".m4a",".mp3"]
            },
        }
    }

def av1_preset(name):
    return {
        "quiet": True,
        "max_parallel_encodes": 1, # serial
        "convert_exts": [".mkv",".mp4",".avi",".webm"],

        "uniforms": {
            "crf": 25,
            "preset": 9,
            "max_width": 1280,
            "max_height": 720,
            "audio_kbps": 96,
        },

        "targets": {
            name+"_AV1": {
            "opts": "-map 0 -c:v libsvtav1 -svtav1-params tune=0 -crf {crf} -preset {preset}\
                    -vf \"scale='min(1,min({max_width}/iw,{max_height}/ih))*iw':'min(1,min({max_width}/iw,{max_height}/ih))*ih'\"\
                    -c:a libopus -ar 48000 -b:a {audio_kbps}k -ac 2 -application audio",
            "file_ext": "mkv"
            }
        }
    }

def n3ds_preset(name):
    return {
        "quiet": True,
        "max_parallel_encodes": 1, # serial
        "copy_aux_files": False,
        "convert_exts": [".mkv",".mp4",".avi",".webm"],

        "targets": {
            name+"_3DS": {
            "opts": "-map 0 -c:v libx264 -pix_fmt yuv420p -crf 10 -c:a aac -b:a 128k\
                    -vf \"scale='trunc(min(1,min(400/iw,240/ih))*iw/2)*2':'trunc(min(1,min(400/iw,240/ih))*ih/2)*2':flags=bicubic\"",
            "file_ext": "mp4"
            }
        }
    }

def n3ds_2x_preset(name):
    return {
        "quiet": True,
        "max_parallel_encodes": 1, # serial
        "copy_aux_files": False,
        "convert_exts": [".mkv",".mp4",".avi",".webm"],

        "targets": {
            name+"_3DS": {
            "opts": "-map 0 -c:v libx264 -pix_fmt yuv420p -crf 10 -c:a aac -b:a 128k\
                    -vf \"fps=30,scale='trunc(min(1,min(400/iw,240/ih))*iw/2)*4':'trunc(min(1,min(400/iw,240/ih))*ih/2)*2':flags=bicubic\"",
            "file_ext": "mp4"
            }
        }
    }

presets = [
    ("Convert music to Opus", opus_preset),
    ("Convert music to AAC", aac_preset),
    ("Convert music to MP3", mp3_preset),
    ("Convert music to Opus and MP3", opusmp3_preset),
    ("Convert music to AAC and MP3", aacmp3_preset),
    ("Convert music to AAC and Opus", aacopus_preset),
    None,
    ("Convert videos to AV1", av1_preset),
    ("Convert videos for 3DS", n3ds_preset),
    ("Convert videos for 3DS (Wide mode, 2x horizontal res)", n3ds_2x_preset),
]

def show_presets():
    for i in range(len(presets)):
        if presets[i] == None: print(); continue
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
    
    conf.create_conf_file(picked_conf, cwd)

    print("Config created. Tweak the config in a text editor if you want, then restart umc.")
    
    return None
