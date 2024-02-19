import os
from . import conf

DEFAULT_PARALLEL_ENCODES = 8

def default_audio_exts(exclude: list[str]):
    exts = [
        ".wav",
        ".wv",
        ".flac",
        ".ogg",
        ".mp3",
        ".m4a",
        ".opus",
    ]
    
    if exclude == None:
        exclude = []

    return [ext for ext in exts if ext not in exclude]

# Presets

def wav2flac_preset(name):
    return {
        "max_parallel_encodes": DEFAULT_PARALLEL_ENCODES,

        "convert_exts": default_audio_exts([]),

        "targets": {
            name+"_flac": {
            "opts": "-ar 44100",
            "file_ext": "flac"
            },
        }
    }

def opus_preset(name):
    return {
        "max_parallel_encodes": DEFAULT_PARALLEL_ENCODES,

        "convert_exts": default_audio_exts([".opus"]),

        "uniforms": {
            "kbps": 96
        },

        "targets": {
            name+"_opus": {
            "opts": "-c:a libopus -b:a {kbps}k -ar 48000 -application audio",
            "file_ext": "ogg"
            },
        }
    }

def aac_preset(name):
    return {
        "max_parallel_encodes": DEFAULT_PARALLEL_ENCODES,

        "convert_exts": default_audio_exts([".m4a"]),

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
        
        "convert_exts": default_audio_exts([".mp3"]),

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
            "opts": "-ar 48000 -application audio -c:a libopus -b:a {kbps_opus}k",
            "file_ext": "ogg",
            "convert_exts": default_audio_exts([".opus"])
            },
            name+"_mp3": {
            "opts": "-ar 44100 -b:a {kbps_mp3}k -map_metadata 0:s",
            "file_ext": "mp3",
            "convert_exts": default_audio_exts([".mp3"])
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
            "convert_exts": default_audio_exts([".m4a"])
            },
            name+"_mp3": {
            "opts": "-ar 44100 -b:a {kbps_mp3}k -map_metadata 0:s",
            "file_ext": "mp3",
            "convert_exts": default_audio_exts([".mp3"])
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
            "convert_exts": default_audio_exts([".m4a"])
            },
            name+"_opus": {
            "opts": "-ar 48000 -b:a {kbps_opus}k -c:a libopus -application audio",
            "file_ext": "ogg",
            "convert_exts": default_audio_exts([".opus"])
            },
        }
    }

def av1_preset(name):
    return {
        "quiet": True,
        "max_parallel_encodes": 1, # serial
        "convert_exts": [".mkv",".mp4",".avi",".webm"],

        "uniforms": {
            "crf": 38,
            "preset": 8,
            "ssim0_psnr1": 1,
            "max_width": 1280,
            "max_height": 720,
            "w_anamorphic_scale": 1,
            "h_anamorphic_scale": 1,
            "audio_kbps": 96,
        },

        "targets": {
            name+"_AV1": {
            "opts":
"-map 0 -c:v libsvtav1 -svtav1-params tune={ssim0_psnr1} -crf {crf} -preset {preset} \
-movflags faststart \
-c:a libopus -b:a {audio_kbps}k -ac 2 -ar 48000 -application audio \
-vf \"scale=\
'ceil(min(1,min({max_width}/iw,{max_height}/ih))*iw/2)*{w_anamorphic_scale}*2':\
'ceil(min(1,min({max_width}/iw,{max_height}/ih))*ih/2)*{h_anamorphic_scale}*2':flags=bicubic\"",
            "file_ext": "mkv"
            }
        }
    }

def n3ds_preset_base(name,width_scale):
    scaler = "{scaler_default}"
    if width_scale > 1:
        scaler = "{scaler_hori_hd}"

    return {
        "quiet": True,
        "max_parallel_encodes": 1, # serial
        "copy_aux_files": False,
        "convert_exts": [".mkv",".mp4",".avi",".webm"],

        # TODO: implement recursive uniforms
        "uniforms": {
            "crf": 24,
            "audio_kbps": 48,
            "cropper_keepheight": "crop='max(400,min(iw,max(1,ih/240)*400))':ih",
            # "cropper_keepwidth": "crop=iw:'max(240,min(ih,max(1,iw/400)*240))'",
            "scaler_default": "scale='ceil(min(1,min(400/iw,240/ih))*iw/2)*1*2':'ceil(min(1,min(400/iw,240/ih))*ih/2)*1*2':flags=bicubic",
            "scaler_hori_hd": "scale='ceil(min(1,min(400/iw,240/ih))*iw/2)*2*2':'ceil(min(1,min(400/iw,240/ih))*ih/2)*1*2':flags=bicubic",
        },

        "targets": {
            name+"_3DS": {
            "opts":
"-map 0 -map -0:s -c:v libx264 -thread_type frame -pix_fmt yuv420p -crf {crf} \
-c:a libopus -b:a {audio_kbps}k -ac 2 -ar 48000 -vf \"{cropper_keepheight},"+ scaler +"\"",
            "file_ext": "mp4"
            }
        }
    }

def n3ds_preset(name):
    return n3ds_preset_base(name,1)

def n3ds_horihd_preset(name):
    return n3ds_preset_base(name,2)

presets = [
    ("Convert music to Opus", opus_preset),
    ("Convert music to AAC", aac_preset),
    ("Convert music to MP3", mp3_preset),
    ("Convert music to Opus and MP3", opusmp3_preset),
    ("Convert music to AAC and MP3", aacmp3_preset),
    ("Convert music to AAC and Opus", aacopus_preset),
    ("Convert music to FLAC", wav2flac_preset),
    None,
    ("Convert videos to AV1 (720p)", av1_preset),
    ("Convert videos for 3DS", n3ds_preset),
    ("Convert videos for 3DS (Hori-HD)", n3ds_horihd_preset),
]

def show_presets():
    for i in range(len(presets)):
        if presets[i] == None: print(); continue
        print(str(i+1) + ") " + presets[i][0])

def namify_preset(preset,cwd):
    return preset[1](os.path.basename(cwd))

def pick_preset(id,cwd):
    
    try:
        num = int(id)-1
    except ValueError:
        print()
        print(id+": not a number")
        return None
    
    try:
        p = presets[num]
        if num < 0: raise IndexError
    except IndexError:
        print()
        print(str(num+1)+": no such preset")
        return None

    p = namify_preset(p,cwd)

    conf.create_conf_file(p, cwd)

    print("Config created. Tweak the config in a text editor if you want, then rerun umc.")

    return p

def wizard(cwd):
    print("Welcome to the configuration wizard.")
    print("It is assumed you want to setup umc for this folder.")
    print("Here are presets to get you started.")
    print()
    
    picked = None
    while picked == None:
        show_presets()

        pick_id = input("Enter preset: ")
        picked = pick_preset(pick_id,cwd)
    
    return None
