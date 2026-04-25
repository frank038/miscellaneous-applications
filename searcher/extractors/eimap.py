#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import glob
import importlib
import time

from email.parser import Parser
from email.policy import default
from email.policy import SMTP

# name of the module
nameModule = 'eimap'
# mimetype handled
docType = ['message/rfc822','application/mbox']
# command execute - TRUE meand it is an internal procedure
command_execute = "TRUE"
# how to identify the file
fidentify="imap/mbox"
# file metadata
metadata1 = ""
# special tags
tag1=""
# name of the module and file type
hhendler = (nameModule,docType)
# the module return: metadata, content, special tag
ereturn = ()

def nametype_Module():
    return hhendler

# if the attachments are in the following groups, they will be skipped from indexing process
_skip_family_mimetype = ["image","video"]

# mimetype allowed by groups
_allowed_family_mimetype = []

# 1 also the attachments will be indexed, otherwise 0
INDEX_ATTACHMENTS = 1

module_dir = os.getcwd()


def nametype_Module():
    return hhendler


class mailIdexer:
    def __init__(self, _type,_data):
        self._type = _type
        self._data = _data
        self.ePlugins = []
        self.extractors = []
        #
        os.chdir(module_dir)
        #
        self.ePlugins = glob.glob('*.py')
        #
        for _comm in self.ePlugins:
            mmodule = _comm.split(".")[0]
            try:
                #ee = importlib.import_module(module_dir+mmodule)
                ee = importlib.import_module(mmodule)
                self.extractors.append(ee)
            except ImportError as ioe:
                pass
        
    def _get_content(self):
        ret = False
        for ee in self.extractors:
            if self._type in ee.docType:
                ret = ee.ffile_content(self._data)
                break
        #
        return ret,self._type


def get_data_mail(ffile):
    try:
        msg = ""
        mail_content = ""
        att = []
        _f = open(ffile, "r")
        msg = _f.read()
        _f.close()
        #
        if msg != "":
            # pd
            _parser = Parser(policy=default)
            mail = _parser.parsestr(msg)
            #
            for el in ['to','cc','bc','ccn','bcc','from','subject','date']:
                _dd = mail[el]
                if _dd != None:
                    mail_content += el+": "+_dd+"\n"
            ############
            mail_content += mail.get_body().get_content()
            #
            for el in mail.iter_attachments():
                att.append(el)
            #
            if INDEX_ATTACHMENTS == 1:
                try:
                    i = 0
                    for el in mail.iter_attachments():
                        _content_type = el.get_content_type()
                        _file = "/tmp/gsearcher_att_{}.pdf".format(i)
                        with open(_file, 'wb') as fp:
                            fp.write(el.get_payload(decode=True))
                        #
                        MI = mailIdexer(_content_type,_file)
                        # tuple: metadata - content
                        _data,_type = MI._get_content()
                        if _data != False:
                            mail_content += "\n\nAttachment type: "+_type+"\n\n"
                            mail_content += _data[0]
                            mail_content += _data[1]
                            with open("/tmp/aaa.txt", "w") as _f:
                                _f.write(mail_content)
                        #
                        os.unlink(_file)
                    #
                    i += 1
                except:
                    pass
            #
            return mail_content
        else:
            return ""
    except:
        return ""

#if False is returned then no text has been extracted
def ffile_content(ffile):
    # metadata1
    try:
        bname = os.path.basename(ffile)
        bcdate = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.stat(ffile).st_mtime))
        bsize = round(os.stat(ffile).st_size/1024,2)
        metadata1 = "File Name    : {}\nCreation Date: {}\nFile Size    : {} kB".format(bname,bcdate,bsize)
    except:
        metadata1 = ""
    
    try:
        ctext = get_data_mail(ffile)
        if len(ctext) > 0:
            ereturn = (metadata1, ctext, tag1)
            return [ereturn]
        else:
            return False
    except:
        return False

