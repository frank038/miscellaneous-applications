#!/usr/bin/env python3

from PIL import Image

list_mime = ['application/octet-stream', 'image/png', 'image/jpeg', 
             'image/gif', 'image/x-xpixmap', 'image/x-portable-anymap', 
             'image/x-portable-bitmap', 'image/x-portable-graymap', 
             'image/x-portable-pixmap', 'image/x-quicktime', 'image/qtif', 
             'image/tiff', 'image/x-tga', 'image/x-icon', 'image/x-ico', 
             'image/x-win-bitmap', 'image/vnd.microsoft.icon', 
             'application/ico', 'image/ico', 'image/icon', 'text/ico', 
             'image/x-icns', 'image/x-xbitmap', 'image/bmp', 'image/x-bmp', 
             'image/x-MS-bmp', 'application/x-navi-animation', 'image/x-dds', 
             'image/webp']

def picture_to_img(fpath):
    try:
        img = Image.open(fpath)
        w = img.size[0]
        h = img.size[1]
        
        if w > h:
            img = img.resize((254, int(254*h/w)), Image.Resampling.LANCZOS)
        elif h > w:
            img = img.resize((int(254*w/h), 254), Image.Resampling.LANCZOS)
        else:
            img = img.resize((254, 254), Image.Resampling.LANCZOS)
        
        return img
    except:
        return "Null"
