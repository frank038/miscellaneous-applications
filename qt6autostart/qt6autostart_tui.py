#!/usr/bin/env python3

# V. 0.9.3

import sys,os,shutil,subprocess,datetime
from xdg import DesktopEntry
from cfg_qt6autostart import *

WORKING_DIR = os.path.dirname(os.path.realpath(sys.argv[0]))
os.chdir(WORKING_DIR)

WINW = 800
WINH = 800
WINM = "False"
WIN_SIZE_FILE = os.path.join(WORKING_DIR, "winsize.cfg")


if DEST_LOG == "HOME":
    DEST_LOG = os.path.expanduser("~")
FILE_LOG = os.path.join(DEST_LOG, "commandLog.log")
LOG_FILE_W = []

SYSTEM_AUTOSTART = "/etc/xdg/autostart/"
USER_AUTOSTART = os.path.join(os.path.expanduser("~"), ".config", "autostart")


a_list = os.listdir(SYSTEM_AUTOSTART)
b_list = os.listdir(USER_AUTOSTART)


class TuiMode:
    def __init__(self):
        self.log_file = FILE_LOG
        try:
            if os.path.exists(self.log_file):
                os.remove(self.log_file)
        except:
            with open(os.path.join(os.getcwd(), "error_log.txt") , "w") as ffile:
                ffile.write("{} : Cannot remove the log file.".format(datetime.datetime.now()))
            sys.exit()
        
        if SYSTEM_START == 1:
            self.system_exec()
        self.user_exec()
        #
        if LOG_TO_FILE:
            self.logFile()
        #
        global LOG_FILE_W
        del LOG_FILE_W
        
        
    def logFile(self):
        try:
            ffile = open(FILE_LOG, "w")
            for el in LOG_FILE_W:
                ffile.write(el)
            ffile.close()
        except Exception as E:
            with open(os.path.join(os.getcwd(), "error_log.txt") , "w") as ffile:
                ffile.write( "{} : Cannot write the log file: {}.".format(datetime.datetime.now(), str(E)) )
            
    def _found_de(self):
        _de = None
        try:
            _de = os.environ['XDG_CURRENT_DESKTOP'].lower()
        except KeyError:
            try:
                _de = os.environ['XDG_SESSION_DESKTOP'].lower()
            except KeyError:
                try:
                    _de = os.environ['WINDOW_MANAGER'].lower()
                except:
                    pass
        return _de
        
    def _fonlyShowIn(self, path):
        _onlyShowIn2 = DesktopEntry.DesktopEntry(path).getOnlyShowIn()
        if _onlyShowIn2:
            for el in _onlyShowIn2[:]:
                if el == "" or el == " ":
                    _onlyShowIn2.remove(el)
            return [el.lower() for el in _onlyShowIn2]
        return []
    
    def _fnotShowIn(self, path):
        _notShowIn2 = DesktopEntry.DesktopEntry(path).getNotShowIn()
        if _notShowIn2:
            for el in _notShowIn2[:]:
                if el == "" or el == " ":
                    _notShowIn2.remove(el)
            return [el.lower() for el in _notShowIn2]
        return []
    
    def system_exec(self):
        can_execute = 0
        for el in a_list:
            # skip files in the user autostart folder
            if el in b_list:
                # if _hidden == "true":
                try:
                    LOG_FILE_W.append("{} : {} : System : {}\n".format(datetime.datetime.now(), el, "Modified by user"))
                except Exception as E:
                    LOG_FILE_W.append( "{} : {} : System : {}\n".format(datetime.datetime.now(), el, str(E)) )
                continue
            # skip
            _de = self._found_de()
            if _de:
                path = os.path.join(SYSTEM_AUTOSTART, el)
                _onlyShowIn = self._fonlyShowIn(path)
                if _onlyShowIn and not _de in _onlyShowIn:
                    LOG_FILE_W.append("{} : {} : System : {}\n".format(datetime.datetime.now(), el, "Not executed: Not in: "+str(_onlyShowIn)))
                    continue
                _notShowIn = self._fnotShowIn(path)
                if _de in _notShowIn:
                    LOG_FILE_W.append("{} : {} : System : {}\n".format(datetime.datetime.now(), el, "Not executed: Not to show if: "+str(_notShowIn)))
                    continue
            # else:
            dpath = os.path.join(SYSTEM_AUTOSTART, el)
            entry = DesktopEntry.DesktopEntry(dpath)
            #
            dtryexec = entry.getTryExec()
            dexec = entry.getExec()
            if dtryexec and shutil.which(dtryexec):
                if shutil.which(dexec):
                    can_execute = 1
            else:
                if shutil.which(dexec):
                    can_execute = 1
            #
            if can_execute:
                try:
                    subprocess.Popen(dexec.split(" "))
                    LOG_FILE_W.append( "{} : {} : System : {}\n".format(datetime.datetime.now(), dexec, "Executed") )
                except Exception as E:
                    LOG_FILE_W.append( "{} : {} : System : {}\n".format(datetime.datetime.now(), dexec, str(E)) )
            else:
                LOG_FILE_W.append( "{} : {} : System : Command not found\n".format(datetime.datetime.now(), dexec) )
                    
        
    def user_exec(self):
        can_execute = 0
        for el in b_list:
            # if el in a_list:
                # continue
            dpath = os.path.join(USER_AUTOSTART, el)
            entry = DesktopEntry.DesktopEntry(dpath)
            #
            dhidden = str(entry.getHidden()).lower()
            if dhidden == "true":
                LOG_FILE_W.append( "{} : {} : User : {}\n".format(datetime.datetime.now(), dpath, "Not executed: Skipped by user") )
                continue
            #
            # skip
            _de = self._found_de()
            if _de:
                path = os.path.join(USER_AUTOSTART, el)
                _onlyShowIn = self._fonlyShowIn(path)
                if _onlyShowIn and not _de in _onlyShowIn:
                    LOG_FILE_W.append("{} : {} : User : {}\n".format(datetime.datetime.now(), el, "Not executed: Not in: "+str(_onlyShowIn)))
                    continue
                _notShowIn = self._fnotShowIn(path)
                if _de in _notShowIn:
                    LOG_FILE_W.append("{} : {} : User : {}\n".format(datetime.datetime.now(), el, "Not executed: Not to show if: "+str(_notShowIn)))
                    continue
            #
            dtryexec = entry.getTryExec()
            dexec = entry.getExec()
            if dtryexec and shutil.which(dtryexec):
                if shutil.which(dexec):
                    can_execute = 1
            else:
                if shutil.which(dexec):
                    can_execute = 1
            #
            if can_execute:
                try:
                    subprocess.Popen(dexec.split(" "))
                    LOG_FILE_W.append( "{} : {} : User : {}\n".format(datetime.datetime.now(), dexec, "Executed") )
                except Exception as E:
                    LOG_FILE_W.append( "{} : {} : User : {}\n".format(datetime.datetime.now(), dexec, str(E)) )
            else:
                LOG_FILE_W.append( "{} : {} : User : Command not found\n".format(datetime.datetime.now(), dexec) )
                    

if __name__ == '__main__':
    if len(sys.argv) > 1:
        print("""Usage:
    qt5autostart = to execute the programs in the autostart directories;
    -gui         = execute the program in gui mode to manage the autoexec programs;
    --help       = this help.""")
    else:
        app = TuiMode()
