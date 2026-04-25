#!/usr/bin/env python3

import os
import subprocess
import time
# command to get the mimetype: file -b --mime-type FILE
# name of the module
nameModule = 'etext'
# mimetype handled
docType = ['text/plain']
# command execute
command_execute = "cat"
# how to identify the file
fidentify="text"
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
        bname = os.path.basename(ffile)
        bcdate = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.stat(ffile).st_mtime))
        bsize = round(os.stat(ffile).st_size/1024,2)
        metadata1 = "File Name    : {}\nCreation Date: {}\nFile Size    : {} kB".format(bname,bcdate,bsize)
    except:
        metadata1 = ""
    #try:
        #tag1 = "example"
    #except:
        #tag1 = ""
    try:
        ctext = subprocess.check_output(["cat", ffile], universal_newlines=True)
        if len(ctext) > 0:
            ereturn = (metadata1, ctext, tag1)
            return [ereturn]
        else:
            return False
    except:
        return False
