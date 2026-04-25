#!/usr/bin/env python3

import sqlite3
import subprocess
import os
import sys
import glob
import magic
import importlib
from pathlib import Path
from time import sleep, gmtime, strftime, time
from searchercfg import INDEXER_LOG

# program directory
main_dir = os.getcwd()
# home directory
homepath = str(Path.home())

DATABASE = os.path.join(main_dir, "DATABASE", "default.db")

list_folders = []
try:
    list_tmp = None
    _f = open(os.path.join(main_dir, 'configs', 'path_list.cfg'))
    list_tmp = _f.readlines()
    _f.close()
    if list_tmp != None:
        for el in list_tmp:
            list_folders.append(el.strip("\n"))
except Exception as E:
    try:
        folderlog = open(os.path.join(main_dir, "LOGS", "folder_errors_log"),"w")
        folderlog.write(str(E))
        folderlog.close()
    except:
        pass
    
class vvar:
    def __init__(self):
        # how many files have been processed
        self.ii = 0
        # how many files have been added
        self.iii = 0
        # how many files have been deleted
        self.iiii = 0
        # how many files have been discharged
        self.iiiii = 0
        # folders not in place
        self.FFOLDER_NOT = 0
        # folders and files issues during indexing
        self.iiiiii = 0
        # metadata
        self.METADATA = ""
        # special tag1
        self.TAG1=""
        # list of files ready to be indexed, only name
        self.list_file = []
        # list of processed files with path
        self.pfiles = []
        # lfolder - folders to get indexed with absolute path
        # self.lfolder = []
        # self.lfolder = [os.path.join(main_dir,"test_folder")]
        self.lfolder = list_folders
        # lffolder - folders to get indexed with absolute path
        self.lffolder = []
        # date and time
        self.ddatettime = strftime("%Y %b %d %H:%M:%S", gmtime())
        # where to store the extractor plugins
        self.ePlugins = []
        # # imported modules 
        # self.extractor_objmodule = []
        # the mimetype of each module as they are loaded
        self.extractor_mimmodule = []
        # list of extractors
        self.extractors = []

        # connecting to the database
        self.con = sqlite3.connect(DATABASE)
        self.cur = self.con.cursor()
        ### the dir of the main program
        # main_dir = os.getcwd()
        ##### create or populate the log files
        # os.chdir("LOG")
        if INDEXER_LOG == 1:
            self.flog = open(os.path.join(main_dir, "LOGS", "log"),"w")
            self.flogd = open(os.path.join(main_dir, "LOGS", "file_discharged.log"),"w")
            self.flogadd = open(os.path.join(main_dir, "LOGS", "file_added.log"),"w")
        # os.chdir(main_dir)
        ####
        # import the extractor plugins
        # sys.path.append(main_dir+'/'+'extractors/')
        # module_dir = "extractors/"
        module_dir = os.path.join(main_dir, "extractors")
        sys.path.append(module_dir)
        #
        os.chdir(module_dir)
        #
        self.ePlugins = glob.glob('*.py')
        #
        #aa = 0
        #for asd in self.ePlugins:
        for _i,_comm in enumerate(self.ePlugins):
            mmodule = os.path.splitext(self.ePlugins[_i])[0]
            # mmodule = os.path.join(main_dir, "extractors", os.path.splitext(_comm)[0])
            try:
                ee = importlib.import_module(mmodule)
                # self.extractor_objmodule.append(ee)
                self.extractor_mimmodule.append(ee.docType)
                self.extractors.append([ee,ee.docType])
            except ImportError as ioe:
                if INDEXER_LOG == 1:
                    self.flog.write("{} Module {} failed to be imported.".format(self.ddatettime, ee))
                pass
            #aa += 1
        #
        os.chdir(main_dir)
    
    # creates the list of the files to be indexed
    def execute_indexing(self, folder_to_index):
        if (Path(folder_to_index).exists() == True) and (os.access(folder_to_index, os.R_OK) == True):
            os.chdir(folder_to_index)
            self.list_file = glob.glob("*")
            llist_file = self.list_file[:]
            for ffile in self.list_file:
                sleep(0.1)
                if not os.path.isfile(ffile):
                    llist_file.remove(ffile)
                    continue
                #
                _temp_iiiii = self.iiiii
                try:
                    pathfile = folder_to_index+"/"+ffile
                    if (Path(folder_to_index).exists()) and (os.access(pathfile, os.R_OK)):
                        file_magic = magic.detect_from_filename(ffile)[0]
                        #
                        self.ii += 1
                        self.pfiles.append(folder_to_index+"/"+ffile)
                        #
                        _is_found = 0
                        for el in self.extractor_mimmodule:
                            if file_magic in el:
                                _is_found = 1
                                break
                        # remove unhandled files
                        if _is_found == 0:
                            llist_file.remove(ffile)
                            if INDEXER_LOG == 1:
                                self.flogd.write("{} File discharged for wrong mimetype: {} in {}\n".format(self.ddatettime, ffile, folder_to_index))
                            self.iiiii += 1
                        # processing
                        else:
                            mmtime = os.stat(ffile).st_mtime
                            self.cur.execute("""select mtime from tabella where name=(?) and dir=(?)""", (ffile, folder_to_index))
                            mtcontent = self.cur.fetchone()
                            if mtcontent == None:
                                fmtime = 0
                            else:
                                fmtime = mtcontent[0]
                            # remove files not changed from previous processing
                            if mmtime == fmtime:
                                llist_file.remove(ffile)
                            elif fmtime == 0:
                                pass
                            # remve files to be reindexed
                            elif mmtime > fmtime:
                                self.cur.execute("""delete from tabella where name=(?) and dir=(?)""", (ffile,folder_to_index))
                                self.con.commit()
                                if INDEXER_LOG == 1:
                                    self.flog.write("{} File updated: {} in {}\n".format(self.ddatettime, ffile, folder_to_index))
                    else:
                        # remove files caused issues while indexing
                        llist_file.remove(ffile)
                        if INDEXER_LOG == 1:
                            self.flogd.write("{} File discharged for issue during indexing: {} in {}\n".format(self.ddatettime, ffile, folder_to_index))
                        self.iiiiii += 1
                except Exception as E:
                    if INDEXER_LOG == 1:
                        self.flogd.write("{} File discharged: {} in {} - Reason: {}\n".format(self.ddatettime, ffile, folder_to_index, str(E)))
                    self.iiiii = _temp_iiiii+1
        else:
            self.FFOLDER_NOT += 1
            if INDEXER_LOG == 1:
                self.flog.write("{} Folder issue during indexing: {}\n".format(self.ddatettime, folder_to_index))
            self.iiiiii += 1
        #
        # return llist_file,mmbox_file
        return llist_file
    
    # the name of all files stored
    def all_name_file(self):
        cname = []
        self.cur.execute("select name,dir from tabella")
        cname1 = self.cur.fetchall()
        for aa in cname1:
            cname.append(aa[1]+"/"+aa[0])
        return cname
    
    # checks if folders exist
    def check_ffolder(self):
        for ffolder in self.lfolder:
            if os.access(ffolder, os.R_OK) is not True:
                self.FFOLDER_NOT += 1
                if INDEXER_LOG == 1:
                    self.flog.write("{} Folder not accessible: {}\n".format(self.ddatettime, ffolder))
            elif Path(ffolder).exists() == True:
                self.lffolder.append(ffolder)
            else:
                self.FFOLDER_NOT += 1
                if INDEXER_LOG == 1:
                    self.flog.write("{} Folder not found: {}\n".format(self.ddatettime, ffolder))
    
    # indexing process
    def ins_db(self):
        self.check_ffolder()
        for folder_to_index in self.lffolder:
            #
            flist_file = self.execute_indexing(folder_to_index)
            if flist_file != []:
                for fti in flist_file:
                    mmtime = os.stat(fti).st_mtime
                    fmime = magic.detect_from_filename(fti)[0]
                    #nmod = self.extractor_mimmodule.index(fmime)
                    # obj = self.extractor_objmodule[nmod]
                    obj = None
                    #
                    for ell in self.extractors:
                        # if fmime in ell[1] and ell[0].fidentify != "mbox":
                        if fmime in ell[1]:
                            obj = ell[0]
                            break
                    # maybe redundant
                    if obj == None:
                        if INDEXER_LOG == 1:
                            self.flogd.write("{} File discharged for no content: {} in {}\n".format(self.ddatettime, fti, folder_to_index))
                        self.iiiii += 1
                        return
                    #
                    freturn = obj.ffile_content(folder_to_index+"/"+fti)
                    if freturn == False:
                        if INDEXER_LOG == 1:
                            self.flogd.write("{} File discharged for no content: {} in {}\n".format(self.ddatettime, fti, folder_to_index))
                        self.iiiii += 1
                        pass
                    else:
                        for el in freturn:
                            self.iii += 1
                            # self.METADATA = freturn[0]
                            _METADATA = el[0]
                            ccontent = el[1]
                            # self.TAG1 = freturn[2]
                            _TAG1 = el[2]
                            # self.cur.execute("""insert into tabella (name, mime, mtime, dir, content, metadata, tag1) values (?,?,?,?,?,?,?)""", (fti, fmime, mmtime, folder_to_index, ccontent, self.METADATA, self.TAG1))
                            self.cur.execute("""insert into tabella (name, mime, mtime, dir, content, metadata, tag1) values (?,?,?,?,?,?,?)""", (fti, fmime, mmtime, folder_to_index, ccontent, _METADATA, _TAG1))
                            self.con.commit()
                            if INDEXER_LOG == 1:
                                self.flogadd.write("{} File added: {} in {}\n".format(self.ddatettime, fti, folder_to_index))
        # delete deleted files
        self.delete_notfile_row()
    
    # deletes the related row if file is accessible no more
    def delete_notfile_row(self):
        cname = self.all_name_file()
        for fname in cname:
            if fname not in self.pfiles:
                self.iiii += 1
                (rfolder_to_index, rfile) = os.path.split(fname)
                self.cur.execute("""delete from tabella where name=(?) and dir=(?)""", (rfile, rfolder_to_index))
                self.con.commit()
                if INDEXER_LOG == 1:
                    self.flog.write("{} File deleted from database because the folder doesn't exist anymore': {} in {}\n".format(self.ddatettime, rfile, rfolder_to_index))
        
    # return to the main program some data
    def return_file(self):
        llist = "{} {} {} {} {} {}".format(self.ii, self.iii, self.iiii, self.iiiii, self.FFOLDER_NOT, self.iiiiii)
        # close everything
        # self.flog.close()
        # self.flogd.close()
        # self.flogadd.close()
        self.con.commit()
        self.cur.close()
        self.con.close()
        return llist
    
    def _index(self):
        self.ins_db()
        # self.delete_notfile_row()
        aaa = self.return_file()
        print(aaa)

app = vvar()   
app._index()
