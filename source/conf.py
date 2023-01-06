import os
import yaml
from . import misc

conf_names = ["umc.yaml",".umc.yaml"]

def get_dict_from_yaml(file):
    try:
        cf = open(file,"r")
    except OSError:
        return None
    
    try:
        config = yaml.load(cf.read(),yaml.Loader)
    except:
        print("Couldn't decode " + file)
        return None
    
    return config

def init_config(dir):
    file = None
    for name in conf_names:
        ftest = os.path.join(dir,name)
        if os.path.exists(ftest): 
            file = ftest
            break
    
    if file == None:
        print("No config file found.")
        return None
    
    config = get_dict_from_yaml(file)
    print(config)

    if config["targets"] == None:
        print("No targets.")
        quit(1)
    return config

conf_defaults = {
    "copy_aux_files": True,
}

def create_conf_file(config, cwd = None):
    misc.extend_dict(config,conf_defaults)
    if cwd == None:
        cwd = os.getcwd()

    fname = os.path.abspath(os.path.join(cwd,conf_names[0]))
    file = open(fname,'w')
    print("Writing config to", fname)
    yaml.dump(config,file,indent=4,sort_keys=False)
    file.close()