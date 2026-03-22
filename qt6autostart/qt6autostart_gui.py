#!/usr/bin/env python3

# V. 0.9.3

from PyQt6.QtWidgets import QApplication, QWidget, QLineEdit, QFileDialog, QLabel, QCheckBox, QMessageBox, QDialog, QDialogButtonBox, QAbstractItemView, QGridLayout, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication
import sys,os,shutil,subprocess,datetime
from xdg import DesktopEntry
from cfg_qt6autostart import *

WORKING_DIR = os.path.dirname(os.path.realpath(sys.argv[0]))
os.chdir(WORKING_DIR)

WINW = 800
WINH = 800
WINM = "False"
WIN_SIZE_FILE = os.path.join(WORKING_DIR, "winsize.cfg")

def on_winsize():
    if not os.path.exists(WIN_SIZE_FILE):
        try:
            with open(WIN_SIZE_FILE, "w") as ifile:
                ifile.write("800;600;False")
        except:
            print("winsize.cfg cannot be created")
            sys.exit()

    if not os.access(WIN_SIZE_FILE, os.R_OK):
        print("winsize.cfg cannot be read")
        sys.exit()
    
    try:
        global WINW
        global WINH
        with open(WIN_SIZE_FILE, "r") as ifile:
            fcontent = ifile.readline()
        aw, ah, am = fcontent.split(";")
        WINW = int(aw)
        WINH = int(ah)
        # WINM = am.strip()
    except:
        try:
            with open(WIN_SIZE_FILE, "w") as ifile:
                ifile.write("800;600;False")
        except:
            print("winsize.cfg cannot be created")
            sys.exit()


SYSTEM_AUTOSTART = "/etc/xdg/autostart/"
USER_AUTOSTART = os.path.join(os.path.expanduser("~"), ".config", "autostart")


a_list = os.listdir(SYSTEM_AUTOSTART)
b_list = os.listdir(USER_AUTOSTART)


class MainWin(QWidget):
    def __init__(self, parent=None):
        super(MainWin, self).__init__(parent)
        self.setWindowTitle("Autostart")
        self.pixel_ratio = 1 #self.devicePixelRatio()
        on_winsize()
        self.resize(int(WINW/self.pixel_ratio),int(WINH/self.pixel_ratio))
        ######## top container
        self.gbox = QGridLayout()
        self.gbox.setContentsMargins(0,0,0,0)
        self.setLayout(self.gbox)
        ######## system autostart
        lbl_system = QLabel("System")
        self.gbox.addWidget(lbl_system, 0, 0, 1, 12)
        self.listv_a = QListWidget()
        self.listv_a.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.gbox.addWidget(self.listv_a, 1, 0, 14, 12)
        if SYSTEM_START == 0:
            self.listv_a.setEnabled(False)
        ######## user autostart
        lbl_user = QLabel("User")
        self.gbox.addWidget(lbl_user, 15, 0, 1, 12)
        self.listv_b = QListWidget()
        self.listv_b.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.gbox.addWidget(self.listv_b, 16, 0, 10, 11)
        #### service buttons
        self.vbox_b = QVBoxLayout()
        self.gbox.addLayout(self.vbox_b, 16, 11, 1, 1)
        #
        self.btn_1 = QPushButton("Add")
        self.btn_1.clicked.connect(self.on_add)
        self.vbox_b.addWidget(self.btn_1)
        #
        self.btn_2 = QPushButton("Remove")
        self.btn_2.clicked.connect(self.on_remove)
        self.vbox_b.addWidget(self.btn_2)
        #
        self.btn_3 = QPushButton("Modify")
        self.btn_3.clicked.connect(self.on_modify)
        self.vbox_b.addWidget(self.btn_3)
        ####
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.on_close)
        self.gbox.addWidget(self.close_btn, 31, 11, 1, 1)
        #
        self.pop_system_user_list()
        
    
    def on_add(self):
        oac = onAdd(self, USER_AUTOSTART, 1)
        ret = oac.exec()
        retValue = oac.getValue()
        #
        if isinstance(retValue, list):
            dname = retValue[0]
            dexec = retValue[1]
            dcomm = retValue[2]
            ddesktop = retValue[3]
            # add the row in the listv_b
            item = QListWidgetItem() 
            widget = QWidget()
            item.fname = dname
            item.fexec = dexec
            widgetCheck = QCheckBox()
            widgetCheck.setChecked(True)
            widgetText = QLabel(dname)
            widgetText.setToolTip(dcomm+"\n"+dexec)
            widgetCheck.clicked.connect(self.on_ck_user)
            widgetCheck.ddesktop = ddesktop
            item.ddesktop = ddesktop
            widgetLayout = QHBoxLayout()
            widgetLayout.addWidget(widgetCheck)
            widgetLayout.addWidget(widgetText)
            #
            widgetLayout.addStretch()
            widget.setLayout(widgetLayout)  
            item.setSizeHint(widget.sizeHint())    
            #
            self.listv_b.addItem(item)
            self.listv_b.setItemWidget(item, widget)
    
    def on_remove(self):
        # QListWidgetItem
        if self.listv_b.selectedItems() == []:
            return
        item = self.listv_b.selectedItems()[0]
        item_idx = self.listv_b.selectedIndexes()[0].row()
        ddesktop = item.ddesktop
        fname = item.fname
        try:
            dlg = message("Question", "Remove {} ?".format(fname), "OC")
            ret = dlg.exec()
            if ret:
                os.remove(os.path.join(USER_AUTOSTART, ddesktop))
                self.listv_b.model().removeRow(item_idx)
        except Exception as E:
            dlg = message("Error", "\n{}.".format(str(E)), "O")
            dlg.exec()
        
    
    def on_modify(self):
        if self.listv_b.selectedItems() == []:
            return
        item = self.listv_b.selectedItems()[0]
        item_idx = self.listv_b.selectedIndexes()[0].row()
        ddesktop = item.ddesktop
        oac = onAdd(self, ddesktop, 2)
        ret = oac.exec()
        retValue = oac.getValue()
        #
        if isinstance(retValue, list):
            # dname = retValue[0]
            dexec = retValue[1]
            dcomm = retValue[2]
            #
            widget = self.listv_b.itemWidget(item)
            #
            if widget is not None:
                for el in widget.children():
                    if isinstance(el, QLabel):
                        el.setToolTip("{}\n{}".format(dcomm, dexec))
        
    # enable/disable system autoexec
    def on_ck_system(self):
        global b_list
        desktop_file = os.path.join(SYSTEM_AUTOSTART, self.sender().ddesktop)
        is_checked = self.sender().isChecked()
        # system program must be enabled
        if is_checked:
            # program is disabled - deleting the file in the user autostart folder
            if self.sender().ddesktop in b_list:
                desktop_file = os.path.join(USER_AUTOSTART, self.sender().ddesktop)
                try:
                    os.remove(desktop_file)
                    b_list = os.listdir(USER_AUTOSTART)
                except Exception as E:
                    dlg = message("Error", "\n{}.".format(str(E)), "O")
                    dlg.exec()
        # disable the program by creating a desktop file in the user autostart
        elif not is_checked:
            desktop_file = os.path.join(USER_AUTOSTART, self.sender().ddesktop)
            try:
                with open(desktop_file, "w") as wfile:
                    wfile.write("[Desktop Entry]\nHidden=true\n")
                b_list = os.listdir(USER_AUTOSTART)
            except Exception as E:
                dlg = message("Error", "\n{}.".format(str(E)), "O")
                dlg.exec()
    
    # enable/disable user autoexec
    def on_ck_user(self):
        desktop_file = os.path.join(USER_AUTOSTART, self.sender().ddesktop)
        is_checked = self.sender().isChecked()
        #
        d_file = None
        with open(desktop_file, "r") as dfile:
            d_file = dfile.readlines()
        #
        is_found = 0
        for el in d_file:
            if "Hidden" in el:
                el_idx = d_file.index(el)
                d_file[el_idx] = "Hidden={}\n".format(str(not is_checked).lower())
                is_found = 1
                break
        if not is_found:
            d_file.append("Hidden={}\n".format(str(not is_checked).lower()))
        #
        try:
            wfile = open(desktop_file, "w")
            for el in d_file:
                if el == "\n":
                    continue
                wfile.write(el)
            wfile.close()
        except Exception as E:
            dlg = message("Error", "\n{}.".format(str(E)), "O")
            dlg.exec()
    
    
    def pop_system_user_list(self):
        # system autostart
        for el in a_list:
            # name (or exec) - exec - comment (or exec) - hidden - valid or skipped (1 or -1) - list
            ret = self.get_system_entry(os.path.join(SYSTEM_AUTOSTART, el))
            #
            item = QListWidgetItem() 
            widget = QWidget()
            item.fname = ret[0]
            item.fexec = ret[1]
            widgetCheck = QCheckBox()
            widgetCheck.setChecked(True)
            widgetText =  QLabel(ret[0])
            #
            if el in b_list:
                ret2 = self.get_user_entry(os.path.join(USER_AUTOSTART, el))
                # hidden property setted to true
                if ret[4] == 1:
                    if ret2[3] == "true":
                        widgetCheck.setChecked(False)
                        t_tooltip = ret[2]+"\n"+ret[1]+"\nDisabled by user"
                        widgetText.setToolTip(t_tooltip)
                    elif ret2[3] == "false":
                        widgetCheck.setChecked(False)
                        t_tooltip = ret[2]+"\n"+ret[1]+"\nModified by user"
                        widgetText.setToolTip(t_tooltip)
                        widgetCheck.setEnabled(False)
                        widgetText.setEnabled(False)
                    #
                    widgetLayout = QHBoxLayout()
                    widgetLayout.addWidget(widgetCheck)
                    widgetLayout.addWidget(widgetText)
                    widgetLayout.addStretch()
                    widget.setLayout(widgetLayout)
                    item.setSizeHint(widget.sizeHint())
                    self.listv_a.addItem(item)
                    self.listv_a.setItemWidget(item, widget)
                    continue
            #
            widgetCheck.clicked.connect(self.on_ck_system)
            widgetCheck.ddesktop = el
            item.ddesktop = el
            widgetLayout = QHBoxLayout()
            widgetLayout.addWidget(widgetCheck)
            if ret[4] == -1:
                widgetCheck.setChecked(False)
                widgetCheck.setEnabled(False)
                widgetText.setEnabled(False)
                widgetText.setToolTip(ret[2]+"\n"+ret[1]+"\n"+ret[5])
            else:
                widgetText.setToolTip(ret[2]+"\n"+ret[1])
            widgetLayout.addWidget(widgetText)
            widgetLayout.addStretch()
            widget.setLayout(widgetLayout)
            item.setSizeHint(widget.sizeHint())
            #
            self.listv_a.addItem(item)
            self.listv_a.setItemWidget(item, widget)
        # user autostart
        for el in b_list:
            # # skip system entries
            # if el in a_list:
                # continue
            # name (or exec) - exec - comment (or exec) - hidden
            ret = self.get_user_entry(os.path.join(USER_AUTOSTART, el))
            # skip orphan entries
            if not ret[1]:
                continue
            #
            item = QListWidgetItem() 
            widget = QWidget()
            item.fname = ret[0]
            item.fexec = ret[1]
            widgetCheck = QCheckBox()
            widgetCheck.setChecked(True)
            widgetText =  QLabel(ret[0])
            if ret[4] == -1:
                widgetCheck.setChecked(False)
                widgetCheck.setEnabled(False)
                widgetText.setEnabled(False)
                widgetText.setToolTip(ret[2]+"\n"+ret[1]+"\n"+ret[5])
            else:
                widgetText.setToolTip(ret[2]+"\n"+ret[1])
            #
            if ret[3] == "true":
                widgetCheck.setChecked(False)
            widgetCheck.clicked.connect(self.on_ck_user)
            widgetCheck.ddesktop = el
            item.ddesktop = el
            widgetLayout = QHBoxLayout()
            widgetLayout.addWidget(widgetCheck)
            widgetLayout.addWidget(widgetText)
            #
            widgetLayout.addStretch()
            widget.setLayout(widgetLayout)  
            item.setSizeHint(widget.sizeHint())    
            #
            self.listv_b.addItem(item)
            self.listv_b.setItemWidget(item, widget)
        

    def on_close(self):
        new_w = self.size().width()
        new_h = self.size().height()
        if new_w != int(WINW) or new_h != int(WINH):
            try:
                ifile = open(WIN_SIZE_FILE, "w")
                ifile.write("{};{};False".format(new_w, new_h))
                ifile.close()
            except Exception as E:
                dlg = message("Error", "\n{}.".format(str(E)), "O")
                dlg.exec()
        #
        QApplication.quit()
        sys.exit()
        
    
    def get_system_entry(self, fpath):
        entry = DesktopEntry.DesktopEntry(fpath)
        fexec = entry.getExec() or ""
        fcomment = entry.getComment() or os.path.basename(fexec)
        fname = entry.getName() or os.path.basename(fexec)
        fhidden = str(entry.getHidden()).lower() or "false"
        #
        _onlyShowIn2 = entry.getOnlyShowIn()
        _onlyShowIn = []
        if _onlyShowIn2:
            for el in _onlyShowIn2[:]:
                if el == "" or el == " ":
                    _onlyShowIn2.remove(el)
            _onlyShowIn = [el.lower() for el in _onlyShowIn2]
        #
        _notShowIn2 = entry.getNotShowIn()
        _notShowIn = []
        if _notShowIn2:
            for el in _notShowIn2[:]:
                if el == "" or el == " ":
                    _notShowIn2.remove(el)
            _notShowIn = [el.lower() for el in _notShowIn2]
        #
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
        #
        #
        if _de:
            if _onlyShowIn:
                if not _de in _onlyShowIn:
                    return [fname, fexec, fcomment, fhidden, -1, "Only in: "+str(_onlyShowIn)] 
            if _notShowIn:
                if _de in _notShowIn:
                    return [fname, fexec, fcomment, fhidden, -1, "Not in: "+str(_notShowIn)] 
        #
        return [fname, fexec, fcomment, fhidden, 1] 
    
    
    def get_user_entry(self, fpath):
        entry = DesktopEntry.DesktopEntry(fpath)
        fexec = entry.getExec() or ""
        fcomment = entry.getComment() or os.path.basename(fexec)
        fname = entry.getName() or os.path.basename(fexec)
        fhidden = str(entry.getHidden()).lower() or "false"
        # if fhidden == "true":
            # return -1
        #
        _onlyShowIn2 = entry.getOnlyShowIn()
        _onlyShowIn = []
        if _onlyShowIn2:
            for el in _onlyShowIn2[:]:
                if el == "" or el == " ":
                    _onlyShowIn2.remove(el)
            _onlyShowIn = [el.lower() for el in _onlyShowIn2]
        #
        _notShowIn2 = entry.getNotShowIn()
        _notShowIn = []
        if _notShowIn2:
            for el in _notShowIn2[:]:
                if el == "" or el == " ":
                    _notShowIn2.remove(el)
            _notShowIn = [el.lower() for el in _notShowIn2]
        #
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
        #
        #
        if _de:
            if _onlyShowIn:
                if not _de in _onlyShowIn:
                    # return -1
                    return [fname, fexec, fcomment, fhidden, -1, "Only in: "+str(_onlyShowIn)] 
            if _notShowIn:
                if _de in _notShowIn:
                    # return -1
                    return [fname, fexec, fcomment, fhidden, -1, "Not in: "+str(_notShowIn)]
        #
        return [fname, fexec, fcomment, fhidden, 1] 


        
# dialog for adding autostart programs
class onAdd(QDialog):
    def __init__(self, parent, dfile, dtype):
        super(onAdd, self).__init__(parent)
        self.parent = parent
        self.destination_file = dfile
        self.dtype = dtype
        # this dialog is open
        self.parent.search_is_open = 1
        # self.setWindowIcon(QIcon("icons/program.svg"))
        if self.dtype == 1:
            wtitle = "Add"
        elif self.dtype == 2:
            wtitle = "Modify"
        self.setWindowTitle(wtitle)
        self.resize(DIALOGWIDTH, 300)
        #
        vbox = QGridLayout()
        vbox.setContentsMargins(5,5,5,5)
        self.setLayout(vbox)
        # name - exec - comment
        lbl_name = QLabel("Name")
        vbox.addWidget(lbl_name, 0,0)
        #
        lbl_exec = QLabel("Program")
        vbox.addWidget(lbl_exec, 1,0)
        #
        lbl_comment = QLabel("Comment")
        vbox.addWidget(lbl_comment, 2,0)
        #
        self.dhidden = "false"
        #########
        self.le_name = QLineEdit()
        if self.dtype == 2:
            self.le_name.setEnabled(False)
        vbox.addWidget(self.le_name, 0,1,1,4)
        #
        self.le_exec = QLineEdit()
        vbox.addWidget(self.le_exec, 1,1,1,3)
          #
        le_exec_btn = QPushButton("F")
        le_exec_btn.clicked.connect(self.on_le_exec_btn)
        vbox.addWidget(le_exec_btn, 1,4)
        #
        self.le_comment = QLineEdit()
        vbox.addWidget(self.le_comment, 2,1,1,4)
        ###########
        ok_canc_box = QHBoxLayout()
        vbox.addLayout(ok_canc_box, 4,0,1,5)
        #
        lbl_ok = QPushButton("Ok")
        lbl_ok.clicked.connect(self.on_ok)
        ok_canc_box.addWidget(lbl_ok)
        #
        lbl_exit = QPushButton("Cancel")
        lbl_exit.clicked.connect(self.close)
        ok_canc_box.addWidget(lbl_exit)
        #
        if self.dtype == 2:
            self.pop_dialog()
        # string list or 1 for success
        self.value = None
        #
        self.show()
    
        
    def on_ok(self):
        # add
        if self.dtype == 1:
            dname = self.le_name.text()
            dexec = self.le_exec.text()
            dcomm = self.le_comment.text()
            if dname == "":
                dname = os.path.basename(dexec).split()[0]
            # the complete name of the desktop file
            ddesktop = dname.split()[0]+".desktop"
            try:
                dstring = "[Desktop Entry]\nType=Application\nName={}\nExec={}\nComment={}\n".format(dname,dexec,dcomm)
                with open(os.path.join(USER_AUTOSTART, ddesktop), "w") as wfile:
                    wfile.write(dstring)
            except Exception as E:
                dlg = message("Error", "\n{}.".format(str(E)), "O")
                dlg.exec()
                self.close()
            #
            self.value = [dname, dexec, dcomm, ddesktop]
        # modification
        elif self.dtype == 2:
            dexec = self.le_exec.text()
            dcomm = self.le_comment.text()
            dfile = os.path.join(USER_AUTOSTART, self.destination_file)
            dcontent = None
            try:
                with open(dfile , "r") as wfile:
                    dcontent = wfile.readlines()
            except Exception as E:
                dlg = message("Error", "\n{}.".format(str(E)), "O")
                dlg.exec()
                self.close()
            #
            exec_found = None
            comm_found = None
            for el in dcontent:
                if "Exec" in el:
                    exec_idx = dcontent.index(el)
                    exec_found = exec_idx
                elif "Comment" in el:
                    comm_idx = dcontent.index(el)
                    comm_found = comm_idx
            #
            if exec_found:
                dcontent[exec_found] = "Exec={}\n".format(dexec)
                if comm_found:
                    dcontent[comm_found] = "Comment={}\n".format(dcomm)
            else:
                dlg = message("Error", "Exec entry not found.", "O")
                dlg.exec()
                self.close()
            #    
            try:
                with open(dfile, "w") as wfile:
                    for el in dcontent:
                        wfile.write(el)
            except Exception as E:
                dlg = message("Error", "\n{}.".format(str(E)), "O")
                dlg.exec()
                self.close()
            #
            self.value = ["", dexec, dcomm]
        #
        self.close()
    
    def getValue(self):
        return self.value
    
    def pop_dialog(self):
        dfile = os.path.join(USER_AUTOSTART, self.destination_file)
        entry = DesktopEntry.DesktopEntry(dfile)
        dname = entry.getName()
        self.le_name.setText(dname)
        dexec = entry.getExec()
        self.le_exec.setText(dexec)
        dcomm = entry.getComment()
        self.le_comment.setText(dcomm)
    
        
    def on_le_exec_btn(self):
        # options = QFileDialog.Options()
        # if self.dtype == 1:
        dialog_filters = "*.*"
        fileName, _ = QFileDialog.getOpenFileName(self, 'Choose File', os.path.expanduser("~"), dialog_filters)#, options=options)
        if fileName:
            self.le_exec.setText(fileName)

# dialog
class message(QDialog):
    def __init__(self, itype, msg, mtype):
        super().__init__()
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.title = "Info"
        # self.resize(800,400)
        # main box
        self.vbox = QVBoxLayout()
        self.setLayout(self.vbox)
        #
        self.label = QLabel(msg)
        self.vbox.addWidget(self.label)
        #
        if mtype == "OC":
            btns = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        elif mtype == "O":
            btns = QDialogButtonBox.StandardButton.Ok
        self.buttonBox = QDialogButtonBox(btns)
        self.buttonBox.accepted.connect(self.accept)
        if mtype == "OC":
            self.buttonBox.rejected.connect(self.reject)
        self.vbox.addWidget(self.buttonBox)
        #

    def close(self):
        self.close()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        print("""Usage:
    qt6autostart_gui = to execute the programs in the autostart directories.""")
    else:
        app = QApplication(sys.argv)
        QGuiApplication.setDesktopFileName("qt6autostart_gui")
        mw = MainWin()
        mw.show()
        sys.exit(app.exec())
