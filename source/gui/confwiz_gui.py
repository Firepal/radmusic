import sys
from tkinter import *
from tkinter import ttk
from .. import confwiz
from .. import conf

def main(cwd = "oh_fiddlesticks"):
    root = Tk()
    root.title("Configuration Wizard")
    root.resizable(False,False)

    lbl = Label(root,text="Welcome to the configuration wizard.\nPlease select a preset below.")
    lbl.grid(column=0, row=0, sticky=N)

    radioframe = Frame(root)
    radioframe.grid(column=0,row=1,padx=40)
    
    pick_id = IntVar(radioframe)
    pick_id.set(0)
    
    for i in range(len(confwiz.presets)):
        preset = confwiz.presets[i]
        if preset == None: 
            sp = ttk.Separator(radioframe,orient="horizontal")
            sp.grid(column=0,row=i,pady=10,sticky=S+W+E)
            continue

        preset_name = preset[0]
        
        r = Radiobutton(radioframe,text=preset_name,value=i,variable=pick_id)
        r.grid(column=0,row=i,sticky=W)
    
    btnframe = Frame(root)
    btnframe.grid(column=0, row=2)

    def close_this():
        root.destroy()
        return None

    def get_preset():
        pick_int = pick_id.get()+1
        root.destroy()

        p = confwiz.pick_preset(pick_int,cwd)
        
        if p == None: return None

        return p

    btn_ok = ttk.Button(btnframe,text="OK",command=get_preset)
    btn_ok.grid(column=1,row=0)
    btn_cancel = ttk.Button(btnframe,text="Cancel",command=close_this)
    btn_cancel.grid(column=0,row=0)

    for btn in btnframe.winfo_children():
        btn.grid_configure(padx=40,pady=10)

    root.mainloop()
