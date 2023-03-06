from tkinter import *
from tkinter.filedialog import *
from tkinter import ttk
import sys
from .. import cli
import argparse
import time
import typing
import os
from threading import Thread

from . import confwiz_gui

#TODO: refactor umc.program to use a dict
def get_fake_args():
    ns = argparse.Namespace()
    d = {"wizard":False,"quiet":False}
    for i in d.keys():
        setattr(ns,i,d[i])
    return ns

def umc_shim(cwd, btn: ttk.Button):
    btn["text"] = "Stop"
    has_config = cli.program(cwd,get_fake_args(),True)

    time.sleep(0.2)

    if not has_config:
        confwiz_gui.main(cwd)
    
    btn["text"] = "Run"

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

    txtbox = Text(root,insertwidth=0,width=80,font=("Courier", 9),bg="#111",fg="white")
    txtbox.bind("<Key>", lambda x: "break")
    txtbox.grid(column=1, row=0, sticky=E+W+N+S)
    
    button_run: ttk.Button = None
    thread: Thread = None
    def run():
        nonlocal thread
        nonlocal button_run
        nonlocal bx
        if bx["text"] == "Stop":
            print("trying to stop")
            return

        if thread != None:
            if thread.is_alive():
                print("thread was alive",file=sys.stderr)
                return
        

        if len(txtbox.get("1.0", END)) > 0:
            txtbox.delete("0.0",END)
            txtbox.update()
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
    
    class TxtboxStdout(typing.TextIO):
        def write(self,str):
            txtbox.insert("end", str)
            txtbox.see("end")

        def flush(self):
            super().flush()
            txtbox.update()
    
    sys.stdout = TxtboxStdout()
    print("Ready.")
    
    txtbox.grid_configure(padx=5, pady=5)
    for child in dirframe.winfo_children():
        if child == entry: pass
        child.grid_configure(padx=5, pady=5)
    

    entry.bind("<Return>", run)
    root.mainloop()