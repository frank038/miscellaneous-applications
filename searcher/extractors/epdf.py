#!/usr/bin/env python3

import os
import subprocess

# name of the module
nameModule = 'epdf'
# mimetype handled
docType = ['application/pdf']
# command executed
command_execute = "pdftotext"
# how to identify the file
fidentify="pdf"
# file metadata
metadata1 = ""
# special tag
tag1=""
# name of the module and file type
hhendler = (nameModule,docType)
# the module return: metadata, content, special tag
ereturn = ()

def nametype_Module():
    return hhendler

#if False is returned then no text has been extract
def ffile_content(ffile):
    try:
        metadata1 = subprocess.check_output(["exiftool", "-FileName", "-Title", "-Subject", "-Keywords", "-PageCount", "-CreateDate", "-FileSize", ffile], universal_newlines=True)
    except:
        metadata1 = ""
    try:
        ctext = subprocess.check_output(["pdftotext", "-nopgbrk", ffile, "-"], universal_newlines=True)
        if len(ctext) > 0:
            ereturn = (metadata1, ctext, tag1)
            return [ereturn]
        else:
            return False
    except:
        return False
