import os
import filecmp
import shutil

def delete_files(files):
    for file in files:
        os.remove(file)

def get_all_files(dir):
    out=[]
    for current_dir, dirs, files in os.walk( dir ):
        if len(files) == 0: continue

        for file in files:
            out.append(os.path.join( os.path.relpath(current_dir, dir), file ))
    return out[::-1]

def filter_ext(all_files,ext_array,exclude = False):
    out=[]
    for file in all_files:
        cur = os.path.splitext( file )
        
        keep = True

        if exclude:
            for ext in ext_array:
                if (cur[1].lower() == ext):
                        keep = False
        else:
            keep = False
            for ext in ext_array:
                if (cur[1].lower() == ext):
                    out.append( file )
                    break
        
        if keep:
            out.append( file )
    return out

def copy_aux_files(all_files,exts,dst,count):
    files = filter_ext(all_files,exts,exclude=True)
    
    for file in files:
        d = os.path.join(
            dst,
            os.path.dirname(file)
        )
        df = os.path.join(dst,file)
        if os.path.exists(df):
            # compare files to prevent unnecessary copies
            if filecmp.cmp(file, df, shallow=True):
                count[1] += 1
                continue
        
        print(end='\n')
        print("Copying to " + os.path.basename(dst) + ": " + os.path.basename(file),end='')
        print(end='                      ')

        shutil.copy2(file,d)
        count[0] += 1

def copy_dirtree(src,dst):
    if not os.path.exists(dst):
        os.mkdir(dst)
    
    for current_dir, dirs, files in os.walk( src ):
        full = os.path.relpath(current_dir,src)
        for dir in dirs:
            leaf = os.path.join(full,dir)
            mirror = os.path.join(dst,leaf)
            
            os.makedirs( mirror, exist_ok=True )