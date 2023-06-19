from tkinter import *
from tkinter.filedialog import *
from tkinter import ttk
import sys
from source import cli
import argparse
import time
import typing
import os
from pathlib import Path
from threading import Thread, Event

from . import confwiz_gui

evt = Event()

#TODO: refactor umc.program to use a dict
def get_fake_args():
    ns = argparse.Namespace()
    d = {"wizard":False,"quiet":False}
    for i in d.keys():
        setattr(ns,i,d[i])
    return ns

def umc_shim(cwd, btn: ttk.Button):
    global cli_out
    btn["text"] = "Stop"
    cli_out = cli.converter(Path(cwd),get_fake_args(),True)

    time.sleep(0.2)

    def threads_alive():
        global cli_out
        for t in cli_out[1]:
            t: tuple[Thread,str] = t
            if t[0].is_alive(): return True
        return False

    if not cli_out: # No config
        cwg = confwiz_gui.ConfwizGUI(cwd)
        cwg.mainloop()
        if cwg.preset == None: return
    else:
        while threads_alive():
            if evt.is_set():
                cli_out[0].set() # inform umc thread we want to stop
            # time.sleep(0.1)
    
        if cli_out[0].is_set():
            print("Termination successful")
    
    btn["text"] = "Run"
    evt.clear()

def create_umc_thread(cwd, btn: ttk.Button):
    return Thread(target=umc_shim,args=(cwd,btn))

recent_file = os.path.expanduser("~/.umc_recent.conf")
def save_recent(lstbox: Listbox):
    recent = lstbox.get('@1,0', END)

    f = open(recent_file,'w')
    f.write("\n".join(recent))
    f.close()

def get_recent_file():
    if not os.path.exists(recent_file):
        return tuple()
    f = open(recent_file,'r')
    lines = f.readlines()

    # remove newlines
    for i in range(len(lines)):
        if i == len(lines)-1: continue
        lines[i] = lines[i][:-1]
    
    return tuple(lines)

def main():
    stdout = sys.stdout

    root = Tk()
    root.title("umc")
    window_width = 500
    window_height = 500
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    x = int((screen_width/2) - (window_width/2))
    y = int((screen_height/2) - (window_height/2))
    root.geometry(f"+{x}+{y}")

    bx: Listbox = None

    def exit_tk():
        nonlocal root
        nonlocal bx
        sys.stdout = stdout
        save_recent(bx)
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", exit_tk)

    root.columnconfigure(1,weight=1)
    root.rowconfigure(0,weight=1)

    dirframe = ttk.Frame(root)
    dirframe.grid(column=0, row=0, sticky=N+S)
    dirframe.columnconfigure(0,weight=1)
    dirframe.rowconfigure(1,weight=1)

    entry = ttk.Entry(dirframe,width=55)
    entry.grid(column=0, row=0)

    def pick(*args):
        dir = askdirectory(mustexist=True)
        entry.delete(0,len(entry.get()))
        entry.insert(0,dir)
    ttk.Button(dirframe, text="Pick...", command=pick).grid(column=0, row=0, sticky=W)

    
    button_run: ttk.Button = None
    thread: Thread = None
    def run():
        nonlocal thread
        nonlocal button_run
        nonlocal bx

        if thread != None:
            if thread.is_alive():
                evt.set()
                return
        
        d = entry.get()
        
        if len(d) == 0: return
        
        bxlist: tuple = bx.get('@1,0', END)
        if not d in bxlist:
            bx.insert(0,d)
        else:
            bxidx = bxlist.index(d)
            if not bxidx == len(bxlist):
                bx.delete(bxidx)
                bx.insert(0,d)

        
        thread = create_umc_thread(d, button_run)
        thread.start()

    
    button_run = ttk.Button(dirframe, text="Run", command=run)
    button_run.grid(column=0, row=0, sticky=E)
    
    lablframe = ttk.LabelFrame(dirframe, text="Recent")
    lablframe.grid(column=0, row=1, sticky=N+S)
    lablframe.columnconfigure(0,weight=1)
    lablframe.rowconfigure(0,weight=1)

    recent_list = get_recent_file()

    bx = Listbox(lablframe,width=80,height=19,exportselection=0,listvariable=Variable(value=recent_list))
    bx.grid(column=0, row=0, padx=10, pady=5, sticky=N+S)

    def clear_recent():
        nonlocal bx
        bx.delete(0,END)

    clr_btn = ttk.Button(lablframe, text="Clear Recent", command=clear_recent)
    clr_btn.grid(column=0, row=1, padx=10, pady=10,sticky=W+N)

    def onselect(*args):
        entry.delete(0,len(entry.get()))
        entry.insert(0,bx.get(bx.curselection()))
    
    bx.bind('<<ListboxSelect>>', onselect)
    
    print("Ready.")
    
    for child in dirframe.winfo_children():
        if child == entry: pass
        child.grid_configure(padx=5, pady=5)
    

    entry.bind("<Return>", run)
    root.mainloop()