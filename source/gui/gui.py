from tkinter import *
from tkinter.filedialog import *
from tkinter import ttk
import sys
from .. import umc
import argparse
from threading import Thread


def get_fake_args():
    ns = argparse.Namespace()
    d = {"wizard":False,"quiet":False}
    for i in d.keys():
        setattr(ns,i,d[i])
    return ns

def create_umc_thread(cwd):
    return Thread(target=umc.program,args=(cwd,get_fake_args(),True))

def main():
    root = Tk()
    root.title("umc")

    pane = PanedWindow(root)

    dirframe = ttk.Frame(root)
    dirframe.grid(column=0, row=0, sticky=N+S)
    dirframe.columnconfigure(0,weight=1)
    dirframe.rowconfigure(1,weight=1)

    entry = ttk.Entry(dirframe,width=50)
    entry.grid(column=0, row=0)

    def pick(*args):
        dir = askdirectory(mustexist=True)
        entry.delete(0,len(entry.get()))
        entry.insert(0,dir)
    ttk.Button(dirframe, text="Pick...", command=pick).grid(column=0, row=0, sticky=W)

    txtbox = Text(root,font=("Courier", 9))
    txtbox.grid(column=1, row=0, sticky=E+W+N+S)
    
    thread = None
    def run(*args):
        nonlocal thread
        if len(txtbox.get("1.0", END))<0:
            txtbox.delete(1,END)
        d = entry.get()
        if len(d) == 0: return
        if thread != None:
            if thread.is_alive(): return
                
        thread = create_umc_thread(d)

        thread.start()
    
    ttk.Button(dirframe, text="Run", command=run).grid(column=0, row=0, sticky=E)
    
    lablframe = ttk.LabelFrame(dirframe, text="Recent")
    lablframe.grid(column=0, row=1, sticky=N+S)
    lablframe.columnconfigure(0,weight=1)
    lablframe.rowconfigure(0,weight=1)
    bx = Listbox(lablframe,width=80,height=19,exportselection=0)
    bx.grid(column=0, row=0, padx=10, pady=5, sticky=N+S)
    bx.insert(0,"F:\\Ultimate Music Colec")
    bx.insert(0,"F:\\Ultimate Podcast Colec")
    bx.insert(0,"C:\\Users\\Brad\\Music\\Firepal\\New folder (2)\\New folder")

    def onselect(*args):
        entry.delete(0,len(entry.get()))
        entry.insert(0,bx.get(bx.curselection()))
    
    bx.bind('<<ListboxSelect>>', onselect)
    
    def faux_write(str):
        txtbox.insert("end", str)
        txtbox.see("end")

    def flush(self): pass
    sys.stdout.write = faux_write
    
    txtbox.grid_configure(padx=5, pady=5)
    for child in dirframe.winfo_children():
        child.grid_configure(padx=5, pady=5)
    
    entry.bind("<Return>", run)
    root.mainloop()