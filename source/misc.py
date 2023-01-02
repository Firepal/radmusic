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

def extend_dict(A,B):
    for key in B.keys():
        if not key in A:
            A[key] = B[key]