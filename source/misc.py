import os

def fit_in_one_line(text: str):
    columns, lines = os.get_terminal_size()

    ct = columns - len(text)
    if ct > 0:
        # text += ' ' * (ct-1)
        pass
    else: 
        text = text[0:ct-1]
    
    return text

def empty_column():
    columns, lines = os.get_terminal_size()
    return ' ' * (columns-1)

def extend_dict(AA : dict,BB : dict):
    for key in BB.keys():
        if not key in AA:
            AA[key] = BB[key]