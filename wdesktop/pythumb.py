#!/usr/bin/python3
"""
main thumbnailer module
"""
PIL_FOUND = 1
try:
    from PIL import Image, ImageOps
    from PIL import PngImagePlugin
except:
    PIL_FOUND = 0

if PIL_FOUND == 1:
    import os
    import sys
    from shutil import which
    import hashlib
    import urllib.parse
    import subprocess
    import glob
    import importlib

# check the main module is installed
def pil_is_found():
    return PIL_FOUND


# import optional modules for the menus
sys.path.append("modules_thumb")
mmod_bg = glob.glob("modules_thumb/*.py")
# list of the filenames of the menu modules
menu_bg_module = []
for el in mmod_bg:
    try:
        ee = importlib.import_module(os.path.basename(el)[:-3])
        menu_bg_module.append(ee)
    except ImportError as ioe:
        print("Error while importing the plugin {}".format(ioe))


# md5 of the file
def eencode(fpath):
    hmd5 = hashlib.md5(bytes("file://"+urllib.parse.quote(fpath, safe='/', encoding=None, errors=None),"utf-8")).hexdigest()
    return hmd5

# return the mtimes of the file and the metadata in the thumbnail 
def check_mtime(fpath, xdgpath):
    omtime = -1
    fmtime = int(os.path.getmtime(fpath))
    hmd5 = eencode(fpath)
    tpath = xdgpath+hmd5+".png"
    if os.path.isfile(tpath):
        try:
            img = Image.open(tpath)
        except:
            return [-1,-1]
    
        for k,v in img.info.items():
            if k == "Thumb MTime":
                omtime = int(v)
        img.close()
    
    return [fmtime, omtime]

# create the thumbnails
def createimagethumb(fpath, el, xdgpath):
    md5=eencode(fpath)
    infile = os.path.basename(fpath)
    uuri = "file://"+urllib.parse.quote(fpath, safe='/', encoding=None, errors=None)
    fmtime = int(os.path.getmtime(fpath))
    try:
        #
        img = el.picture_to_img(fpath)
        if img == "Null":
            return "Null"
        if img.mode == "P":
            img = img.convert("RGBA")
        # try:
            # bimg = ImageOps.expand(img, border=1, fill=BORDER_COLOR)
        # except:
            # bimg = img
        
        try:
            meta = PngImagePlugin.PngInfo()
            
            meta.add_text("Thumb URI", uuri, 0)
            meta.add_text("Thumb MTime", str(int(fmtime)), 0)
            meta.add_text("Software", "PYTHON::PIL", 0)
            
            # bimg.save(xdgpath+md5+".png", "PNG", pnginfo=meta)
            img.save(xdgpath+md5+".png", "PNG", pnginfo=meta)
            
            img.close()
            return md5
            
        except:
            return "Null"

    except:
        return "Null"

# main function to call - return the file name without its extension
def create_thumbnail(ffile, fdir, fmime, xdgpath):
    path = os.path.join(fdir, ffile)
    fmtime, omtime = check_mtime(path, xdgpath)
    if fmtime == -1 and omtime == -1:
        return "Null"
    md5 = None

    if fmtime != omtime:
        
        ii = 0
        while ii < len(menu_bg_module):
            if fmime in menu_bg_module[ii].list_mime:
                md5 = createimagethumb(path, menu_bg_module[ii], xdgpath)
                return str(md5)
            ii += 1
        return "Null"
    
    else:
        return eencode(path)

# if the file is not present delete the thumbnail
def delete_thumb(xdgpath):
    cache_files = os.listdir(xdgpath)
    for ffile in cache_files:
        tpath = os.path.join(xdgpath, ffile)
        try:
            img = Image.open(tpath)
        except:
            pass
    
        for k,v in img.info.items():
            if k == "Thumb URI":

                tfile = urllib.parse.unquote(v)[7:]
                if not os.path.exists(tfile):
                    try:
                        os.unlink(tpath)
                    except:
                        pass
        img.close()
