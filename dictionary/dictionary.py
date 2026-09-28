#!/usr/bin/env python3

# V 1.0

import sys, os, json, subprocess, ast
from PyQt6.QtWidgets import (QMainWindow,QApplication,QWidget,QPlainTextEdit,QVBoxLayout,QHBoxLayout,QSizePolicy,QPushButton,QLabel,QLineEdit)
from PyQt6.QtGui import QIcon,QGuiApplication

curr_dir = os.getcwd()

WINW = 800
WINH = 800


class dictMainWindow(QMainWindow):
    
    def __init__(self):
        super(dictMainWindow, self).__init__()
        self.setContentsMargins(2,2,2,2)
        # self.setWindowIcon(QIcon("icons/program.svg"))
        self.setWindowIcon(QIcon().fromTheme(QIcon.ThemeIcon.SystemSearch, QIcon(os.path.join(curr_dir, "icons", "searching.png"))))
        self.pixel_ratio = self.devicePixelRatio()
        self.resize(int(WINW/self.pixel_ratio), int(WINH/self.pixel_ratio))
        self.setWindowTitle("Dictionary")
        #
        self.main_box = QVBoxLayout()
        self.main_box.setContentsMargins(0,0,0,0)
        _widget = QWidget()
        _widget.setLayout(self.main_box)
        self.setCentralWidget(_widget)
        #
        self.search_box = QHBoxLayout()
        self.main_box.addLayout(self.search_box)
        #
        self.search_le = QLineEdit()
        self.search_box.addWidget(self.search_le)
        self.search_le.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.search_le.setClearButtonEnabled(True)
        self.search_le.returnPressed.connect(self.on_search_btn)
        #
        self.search_btn = QPushButton()
        self.search_btn.setIcon(QIcon().fromTheme(QIcon.ThemeIcon.SystemSearch, QIcon(os.path.join(curr_dir, "icons", "searching.png"))))
        self.search_box.addWidget(self.search_btn)
        self.search_btn.clicked.connect(self.on_search_btn)
        # zoom in
        self.zoomin = QPushButton()
        self.zoomin.setIcon(QIcon().fromTheme(QIcon.ThemeIcon.ZoomIn, QIcon(os.path.join(curr_dir, "icons", "zoom-in.png"))))
        self.search_box.addWidget(self.zoomin)
        # zoom out
        self.zoomout = QPushButton()
        self.zoomout.setIcon(QIcon().fromTheme(QIcon.ThemeIcon.ZoomOut, QIcon(os.path.join(curr_dir, "icons", "zoom-out.png"))))
        self.search_box.addWidget(self.zoomout)
        #
        self.text_edit = QPlainTextEdit()
        self.main_box.addWidget(self.text_edit)
        self.text_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.text_edit.setReadOnly(True)
        #
        self.zoomin.clicked.connect(self.text_edit_zoomIn)
        self.zoomout.clicked.connect(self.text_edit_zoomOut)
        #
        self.actual_search = ""
        #
        self.exit_btn = QPushButton("Close")
        self.main_box.addWidget(self.exit_btn)
        self.exit_btn.clicked.connect(self.close)
        #
        self.show()
        #
        self.search_le.setText("")
        # curl
        if len(sys.argv) == 3:
            if sys.argv[1].lower() == "-curl":
                self.search_le.setText(sys.argv[2].lower())
                self.on_search_btn()
        # dict
        elif len(sys.argv) == 4:
            if sys.argv[1].lower() == "-dict":
                self.search_le.setText(sys.argv[3].lower())
                self.on_search_btn()
    
    def text_edit_zoomIn(self):
        self.text_edit.zoomIn()
        
    def text_edit_zoomOut(self):
        self.text_edit.zoomOut()
        
    def on_search_btn(self):
        if self.search_le.text() == "":
            return
        if self.actual_search == self.search_le.text():
            return
        #
        try:
            if sys.argv[1].lower() == "-curl":
                _cmd = ['curl', 'https://en.wiktionary.org/w/api.php?action=query&format=json&prop=extracts&titles={}'.format(self.search_le.text())]
                _ret = subprocess.check_output(_cmd)
                dict_result = ast.literal_eval(_ret.decode())
                self.actual_search = self.search_le.text()
                #
                _idx = list(dict_result["query"]["pages"])[0]
                _extract = dict_result["query"]["pages"][_idx]["extract"]
                self.text_edit.setPlainText("")
                self.text_edit.appendHtml(_extract)
            elif sys.argv[1].lower() == "-dict":
                _cmd = ['sdcv', '-2', sys.argv[2].lower(), '-0', '-e', '-n', '{}'.format(self.search_le.text())]
                _ret = subprocess.check_output(_cmd)
                self.text_edit.setPlainText("")
                self.text_edit.appendHtml(_ret.decode("utf-8"))
            # self.text_edit.zoomIn()
        except Exception as E:
            print("ERROR: ", str(E))
        #
        self.text_edit.verticalScrollBar().setSliderPosition(0)
    
    def closeEvent(self, event):
        QApplication.quit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    QGuiApplication.setDesktopFileName("dictionary-1")
    myGUI = dictMainWindow()
    sys.exit(app.exec())
