from tkinter import *

root = Tk()
root.geometry("777x575")
root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=2)

root.rowconfigure(0, weight=1)

text = Text(root, width = 95 , height = 95)
text.insert("end","TESTTESTSTTESTTESTTESTTESTTESTTESTTESTSTTESTTESTTESTTESTTESTTESTTESTSTTESTTESTTESTTESTTESTTESTTESTSTTESTTESTTESTTESTTEST")
text.grid(column=0, row=0, ipadx=500, ipady=10, sticky="NSEW")

scrollbar = Scrollbar(text, orient=VERTICAL)
scrollbar.pack(fill=Y, side=RIGHT)

button = Button(root, text = "Sample Button")
button.grid(column=0, row=1, ipadx=500, ipady=10, sticky="NSEW")

mainloop()