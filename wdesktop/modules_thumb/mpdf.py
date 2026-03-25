#!/usr/bin/env python3

from PIL import Image
from io import BytesIO
import subprocess

list_mime = ['application/pdf']

def picture_to_img(fpath):
    try:
        data = subprocess.check_output(["pdftocairo", "-png", "-singlefile", "-scale-to", "254", "-q", fpath, "-"])
        img = Image.open(BytesIO(data))
        return img
    except:
        return "Null"
