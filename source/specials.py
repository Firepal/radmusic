import re


# Specials are basically preprocessor macros for umc config files.
# There are two classes of specials.
# Uniforms: Works like #define values
# Macros: Works like #define macros

macro_re = r'([^(,)]+)(?!.*\()'

def get_macro_args(macro_instance: str):
    return re.findall(macro_re, macro_instance)

def get_macro_name(macro_instance: str):
    return re.search(r'(.*?)\s*\(', macro_instance).group(1)

def is_macro(uniform: str):
    return re.search(r'^\w+\(.*\)$', uniform) != None

def process_macros(s: str, macros: dict[str,str]):
    global_macro_names = [get_macro_name(m) for m in macros]
    global_macro_args = [get_macro_args(m) for m in macros]
    global_macro_def = [macros[m] for m in macros]

    for macro in get_macros(s):
        print(f"{macro} is macro")

        # check if macro exists
        macro_name = get_macro_name(macro)
        print(f"name: {macro_name}")

        if not (macro_name in global_macro_names):
            print("macro doesn't exist!")
            s = s.replace(f"{{{macro}}}",'')
            continue
        macro_index = global_macro_names.index(macro_name)

        original_args = global_macro_args[macro_index]
        set_args = get_macro_args(macro)

        
        if macro in set_args:
            print("No args")
            s = s.replace(f"{{{macro}}}",'')
            continue

        if len(original_args) != len(set_args):
            print(f"macro {macro_name} has {len(original_args)} args, but was called with {len(set_args)}")
            s = s.replace(f"{{{macro}}}",'')
            continue
        
        macro_def = global_macro_def[macro_index]
        for spec in get_specials(macro_def):
            if not (spec in original_args): continue
            spec_index = original_args.index(spec)

            set_arg = set_args[spec_index]
            print(f"replacing {spec} with {set_arg}")
            macro_def = macro_def.replace(f"{{{spec}}}", set_arg)

        s = s.replace(f"{{{macro}}}",macro_def)

def strip_brackets(u):
    return re.sub(r'[{}]', '', u)

def get_specials(opts: str):
    return re.findall('{(.+?)}',str(opts))

def get_uniforms(opts: str):
    # return get_specials(opts)
    return [uni for uni in get_specials(opts) if not is_macro(uni)]

def get_macros(opts: str):
    return [uni for uni in get_specials(opts) if is_macro(uni)]

def check_cyclic_uniforms(uniforms: dict):
    for uniform_key in uniforms:
        for self_uniform_key in get_specials(uniforms[uniform_key]):
            if is_macro(self_uniform_key): continue
            if uniform_key in get_specials(uniforms[self_uniform_key]):
                print(f"Hard Error!! Cyclic dependency between uniforms {uniform_key} and {self_uniform_key}!!")
                return True
    
    return False

def recurse_uniforms(uni: str, uniforms: dict):
    for r_opt in get_uniforms(uni):
        uni = uni.replace(f"{{{r_opt}}}",str(uniforms[r_opt]))
    
    return uni

def apply_opts_params(opts: str,uniforms: dict, macros: dict[str,str] = None):
    """
    Looks in `opts` for specials in `uniforms` and replaces them.
    """

    unis = get_uniforms(opts)
    # macs = get_macros(opts)
    print(f"uniforms: {unis}")
    # print(f"macros: {macs}")
    

    if check_cyclic_uniforms(uniforms):
        quit()

    for i, opt_u in enumerate(unis):
        if opt_u in uniforms:
            uni = recurse_uniforms(uniforms[opt_u],uniforms)
            opts = opts.replace(f"{{{unis[i]}}}",str(uni))
            
        else:
            print("Fatal error: \"" + opt_u + "\" in opts doesn't match any uniform in config:\n")
            print("opts:", opts)
            print("uniforms (parsed from opts):", unis)
            print("uniforms (defined in config):", uniforms)
            return
    
    if macros == None: return opts
    
    # macs = get_macros(opts)
    
    
    return opts