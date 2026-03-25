#!/usr/bin/env python3

from PIL import Image
from io import BytesIO
import subprocess

list_mime = ['video/mp4', 'video/x-msvideo', 'video/x-flv', 'video/x-ms-wmv', 
            'video/quicktime', 'video/x-matroska', 'video/3gpp', 'video/mpeg', 
            'video/ogg', 'video/webm']

def picture_to_img(fpath):
    
    try:
        data = subprocess.check_output(["ffmpegthumbnailer", "-i", fpath, "-s", "254", "-o", "/dev/stdout"])
        img = Image.open(BytesIO(data))
        return img
    except:
        return "Null"
