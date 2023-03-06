import os

def convert_playlist_file(rel_path,src_dir,dst_dir):
    f = open(os.path.join(src_dir,rel_path),'r')
    fstr = f.read()
    
    eof = False
    last_nwline_idx = 0
    nwline_idx = 0
    while not nwline_idx == -1:
        last_nwline_idx = nwline_idx
        nwline_idx = fstr.find("\n",nwline_idx+1)
        if nwline_idx == -1: break
        if len(fstr) <= nwline_idx+1: break

        nxt_chr = fstr[nwline_idx+1]
        if nxt_chr == "#": continue

        file_start = nwline_idx
        file_end = fstr.find("\n",nwline_idx+1)
        file_listing = fstr[file_start:file_end]
        file_lastdotid = file_listing.rfind(".")
        file_listing_ext = file_listing[:file_lastdotid] + ".opus"
        print(nwline_idx, file_listing_ext)
    print("end")


    t_path = os.path.join(dst_dir,rel_path)