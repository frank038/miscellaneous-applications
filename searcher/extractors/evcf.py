#!/usr/bin/env python3

import os
import subprocess
import time
# command to get the mimetype: file -b --mime-type FILE
# name of the module
nameModule = 'etext'
# mimetype handled
docType = ['text/vcard']
# command execute
command_execute = "TRUE"
# how to identify the file
fidentify="contact"
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

# put all the events from the file in list_events
def get_all_events(_events):
    if _events is None:
        return
    if _events == []:
        return
    #
    list_events = []
    dict_event = {}
    data_event = ""
    c_event = None
    #
    _bes = _events.find("BEGIN:VCARD")
    while _bes != -1:
        _bes2 = _events.find('AGENT:BEGIN:VCARD', _bes)
        if _bes != -1:
            _bee2 = _events.find('END:VCARD', _bes2)
            _bee = _events.find('END:VCARD', _bee2)
        else:
            _bee = _events.find('END:VCARD', _bes)
        list_events.append(_events[_bes+12:_bee-1])
        _bes = _bes = _events.find("BEGIN:VCARD", _bee)
    #
    return list_events

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
        all_events = None
        with open(ffile, "r") as f:
            all_events = f.read()
        # print("130", all_events, type(all_events))
        list_events = get_all_events(all_events)
        #
        if list_events == []:
            return False
        #
        else:
            all_data = []
            for el in list_events:
                all_data.append([metadata1, el, tag1])
            return all_data
    except:
        return False
