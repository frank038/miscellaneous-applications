#!/usr/bin/env python3

from gi.repository.GdkPixbuf import Pixbuf
from PIL import Image

list_mime = ['image/svg+xml', 'image/svg', 'image/svg-xml', 
             'image/vnd.adobe.svg+xml', 'text/xml-svg', 
             'image/svg+xml-compressed']

def picture_to_img(fpath):
    try:
        pixbuf = Pixbuf.new_from_file(fpath)
        data = pixbuf.get_pixels()
        width = pixbuf.props.width
        height = pixbuf.props.height
        stride = pixbuf.props.rowstride
        mode = "RGB"
        if pixbuf.props.has_alpha == True:
            mode = "RGBA"
        img = Image.frombytes(mode, (width, height), data, "raw", mode, stride)
        
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
