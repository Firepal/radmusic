import os
import yaml

conf_names = ["umc.yaml",".umc.yaml"]

def init_config(dir):
    cf = None
    for name in conf_names:
        file = os.path.join(dir,name)

        try:
            cf = open(file,"r")
        except OSError:
            pass
        else:
            break
    if cf == None:
        print("No known config file found.")
        print()
        return None
    
    try:
        config = yaml.load(cf.read(),yaml.Loader)
    except:
        print("Couldn't decode JSON in file " + file)
        quit(1)

    if config["targets"] == None:
        print("No targets.")
        quit(1)
    return config

conf_defaults = {
    "parallel": False,
    "wav2flac": False,
    "copy_aux_files": True,
}

def populate_with_defaults(config):
    for key in conf_defaults.keys():
        if not (key in config):
            config[key] = conf_defaults[key]

def create_conf_file(config):
    populate_with_defaults(config)

    fname = conf_names[0]
    file = open(fname,'w')
    print("Writing config to " + os.path.join(os.getcwd(),fname))
    yaml.dump(config,file,indent=4,sort_keys=False)
    file.close()