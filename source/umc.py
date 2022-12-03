import os
import time
from threading import Thread
try:
    from Queue import Queue
except ImportError:
    from queue import Queue

from . import conf, confwiz, fget, target

def wav2flac(files):
    for file in files:
        target.convert_file(file, os.path.splitext(file)[0] + ".flac")
    fget.delete_all(files)

def check_for_wavs_silent(all_files):
    files = fget.filter_ext(all_files,[".wav"])
    wav2flac(files)

def check_for_wavs(all_files):
    files = fget.filter_ext(all_files,[".wav"])

    if len(files) < 1:
        return
    
    print(files)
    conv_prompt = input("WAV file(s) detected. Would you like to convert them to FLAC to save space? ")

    if conv_prompt.lower()[0] != "y":
        return
    
    for file in files:
        fname = os.path.splitext(file)[0] + ".flac"
        print("Encoding " + fname)
        target.convert_file(file, fname)

    del_prompt = input("Would you like to *DELETE* the leftover WAV file(s)?")
    if del_prompt.lower()[0] == "y":
        fget.delete_files(files)

def program(cwd,config):
    print("Doing one-time file discovery...")
    all_files = fget.get_all_files(cwd)
    print(str(len(all_files)) + " file(s)")

    if config["wav2flac"]:
        print("would destroy")
        # silent_wav2flac(cwd)
    else:
        check_for_wavs(cwd)

    c_start = time.time()
    target.process_targets(cwd, all_files, config)
    c_end = time.time()

    print("Time elapsed: " + str(round(c_end-c_start)) + " seconds")

def main():
    cwd = os.getcwd()

    config = conf.init_config(cwd)
    
    if config == None:
        config = confwiz.wizard(cwd)

    if config != None:
        program(cwd,config)

    input("Press Enter to quit...")
