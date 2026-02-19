# Copyright (C) 2013 Riverbank Computing Limited.
# Copyright (C) 2022 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause
from __future__ import annotations

from argparse import ArgumentParser, RawTextHelpFormatter
import sys,os

from PyQt6.QtCore import (QByteArray, QFile, QFileInfo, QSaveFile, QSettings,
                            QTextStream, Qt)
from PyQt6.QtGui import QGuiApplication, QAction, QIcon, QKeySequence, QTextOption, QPalette
from PyQt6.QtWidgets import (QApplication, QFileDialog, QMainWindow,
                               QMessageBox, QPlainTextEdit)
from PyQt6.QtPrintSupport import QPrintDialog, QPrinter, QPrintPreviewDialog

import notepad_rc  # noqa: F401

# this program working directory
curr_dir = os.getcwd()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(os.path.join(curr_dir,'images/notepad.svg')))
        
        self._cur_file = ''

        self._text_edit = QPlainTextEdit()
        _font = self._text_edit.font()
        _font.setFamily("Monospace")
        self._text_edit.setFont(_font)
        self.zoom_level = 0
        self.setCentralWidget(self._text_edit)

        self.create_actions()
        self.create_menus()
        self.create_tool_bars()
        # self.create_status_bar()
        
        self.this_width = 0
        self.this_height = 0
        self.this_zoom = 0
        self.this_wordwrap = 0
        self.read_settings()
        
        self.setStyleSheet("QPlainTextEdit{background-color: black; color: white;}")
        
        self._text_edit.document().contentsChanged.connect(self.document_was_modified)

        self.set_current_file('')
        self.setUnifiedTitleAndToolBarOnMac(True)

    def closeEvent(self, event):
        if self.maybe_save():
            self.write_settings()
            event.accept()
        else:
            event.ignore()

    
    def new_file(self):
        if self.maybe_save():
            self._text_edit.clear()
            self.set_current_file('')

    
    def open(self):
        if self.maybe_save():
            fileName, filtr = QFileDialog.getOpenFileName(self)
            if fileName:
                self.load_file(fileName)

    
    def save(self):
        if self._cur_file:
            return self.save_file(self._cur_file)

        return self.save_as()

    
    def save_as(self):
        fileName, filtr = QFileDialog.getSaveFileName(self)
        if fileName:
            return self.save_file(fileName)

        return False
    
    def filePrint(self):
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        if self._cur_file:
            _file = self._cur_file
        else:
            _file = "Unknown"
        printer.setOutputFileName(_file+".pdf")
        dlg = QPrintDialog(printer, self)
        if self._text_edit.textCursor().hasSelection():
            dlg.addEnabledOption(QPrintDialog.PrintSelection)
        dlg.setWindowTitle("Print Document")

        if dlg.exec():# == QPrintDialog.accepted:
            self._text_edit.print(printer)
        del dlg
    
    def about(self):
        QMessageBox.about(self, "About",
                          "A simple notepad.")

    
    def document_was_modified(self):
        self.setWindowModified(self._text_edit.document().isModified())

    def create_actions(self):
        icon = QIcon.fromTheme(QIcon.ThemeIcon.DocumentNew, QIcon(':/images/new.png'))
        self._new_act = QAction(icon, "&New", self, shortcut=QKeySequence.StandardKey.New,
                                statusTip="Create a new file", triggered=self.new_file)

        icon = QIcon.fromTheme(QIcon.ThemeIcon.DocumentOpen, QIcon(':/images/open.png'))
        self._open_act = QAction(icon, "&Open...", self,
                                 shortcut=QKeySequence.StandardKey.Open,
                                 statusTip="Open an existing file",
                                 triggered=self.open)

        icon = QIcon.fromTheme(QIcon.ThemeIcon.DocumentSave, QIcon(':/images/save.png'))
        self._save_act = QAction(icon, "&Save", self,
                                 shortcut=QKeySequence.StandardKey.Save,
                                 statusTip="Save the document to disk", triggered=self.save)

        self._save_as_act = QAction("Save &As...", self,
                                    shortcut=QKeySequence.StandardKey.SaveAs,
                                    statusTip="Save the document under a new name",
                                    triggered=self.save_as)
        
        icon = QIcon.fromTheme('document-print', QIcon(':/images/fileprint.png'))
        self.actionPrint = QAction(icon, "&Print...", self,
                                    shortcut=QKeySequence.StandardKey.Print,
                                    statusTip="Print the document",
                                    triggered=self.filePrint)
        
        icon = QIcon.fromTheme(QIcon.ThemeIcon.ApplicationExit)
        self._exit_act = QAction(icon, "E&xit", self, shortcut="Ctrl+Q",
                                 statusTip="Exit the application", triggered=self.close)

        icon = QIcon.fromTheme(QIcon.ThemeIcon.EditCut, QIcon(':/images/cut.png'))
        self._cut_act = QAction(icon, "Cu&t", self, shortcut=QKeySequence.StandardKey.Cut,
                                statusTip="Cut the current selection's contents to the clipboard",
                                triggered=self._text_edit.cut)

        icon = QIcon.fromTheme(QIcon.ThemeIcon.EditCopy, QIcon(':/images/copy.png'))
        self._copy_act = QAction(icon, "&Copy",
                                 self, shortcut=QKeySequence.StandardKey.Copy,
                                 statusTip="Copy the current selection's contents to the clipboard",
                                 triggered=self._text_edit.copy)

        icon = QIcon.fromTheme(QIcon.ThemeIcon.EditPaste, QIcon(':/images/paste.png'))
        self._paste_act = QAction(icon, "&Paste",
                                  self, shortcut=QKeySequence.StandardKey.Paste,
                                  statusTip="Paste the clipboard's contents into the current "
                                  "selection",
                                  triggered=self._text_edit.paste)
        
        icon = QIcon.fromTheme(QIcon.ThemeIcon.ZoomIn, QIcon(':/images/zoomin.png'))
        self._zoomin_act = QAction(icon, "Zoom in",
                                  self,
                                  statusTip="Increase the font size.",
                                  triggered=self.on_zoomin)

        icon = QIcon.fromTheme(QIcon.ThemeIcon.ZoomOut, QIcon(':/images/zoomout.png'))
        self._zoomout_act = QAction(icon, "Zoom out",
                                  self,
                                  statusTip="Decrease the font size.",
                                  triggered=self.on_zoomout)
        
        self._wrapmode_act = QAction("Word wrap",
                                  self,
                                  statusTip="Word wrap mode.",
                                  triggered=self.on_wordwrap)
        self._wrapmode_act.setCheckable(True)
        
        icon = QIcon.fromTheme(QIcon.ThemeIcon.HelpAbout)
        self._about_act = QAction(icon, "&About", self,
                                  triggered=self.about)

        # self._about_qt_act = QAction("About &Qt", self,
                                     # statusTip="Show the Qt library's About box",
                                     # triggered=qApp.aboutQt)  # noqa: F821

        self._cut_act.setEnabled(False)
        self._copy_act.setEnabled(False)
        self._text_edit.copyAvailable.connect(self._cut_act.setEnabled)
        self._text_edit.copyAvailable.connect(self._copy_act.setEnabled)
    
    def on_zoomin(self):
        self._text_edit.zoomIn()
        self.zoom_level += 1
        
    def on_zoomout(self):
        self._text_edit.zoomOut()
        self.zoom_level -= 1
        
    def on_wordwrap(self):
        _wm = self._text_edit.wordWrapMode()
        if _wm != QTextOption.WrapMode.NoWrap:
            self._text_edit.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        else:
            self._text_edit.setWordWrapMode(QTextOption.WrapMode.WrapAnywhere)
        
    def create_menus(self):
        self._file_menu = self.menuBar().addMenu("&File")
        self._file_menu.addAction(self._new_act)
        self._file_menu.addAction(self._open_act)
        self._file_menu.addAction(self._save_act)
        self._file_menu.addAction(self._save_as_act)
        self._file_menu.addAction(self.actionPrint)
        self._file_menu.addSeparator()
        self._file_menu.addAction(self._exit_act)

        self._edit_menu = self.menuBar().addMenu("&Edit")
        self._edit_menu.addAction(self._cut_act)
        self._edit_menu.addAction(self._copy_act)
        self._edit_menu.addAction(self._paste_act)
        self._edit_menu.addSeparator()
        self._edit_menu.addAction(self._zoomin_act)
        self._edit_menu.addAction(self._zoomout_act)
        self._edit_menu.addSeparator()
        self._edit_menu.addAction(self._wrapmode_act)

        self.menuBar().addSeparator()

        self._help_menu = self.menuBar().addMenu("&Help")
        self._help_menu.addAction(self._about_act)
        # self._help_menu.addAction(self._about_qt_act)

    def create_tool_bars(self):
        self._file_tool_bar = self.addToolBar("File")
        self._file_tool_bar.addAction(self._new_act)
        self._file_tool_bar.addAction(self._open_act)
        self._file_tool_bar.addAction(self._save_act)

        self._edit_tool_bar = self.addToolBar("Edit")
        self._edit_tool_bar.addAction(self._cut_act)
        self._edit_tool_bar.addAction(self._copy_act)
        self._edit_tool_bar.addAction(self._paste_act)

    # def create_status_bar(self):
        # self.statusBar().showMessage("Ready")

    def read_settings(self):
        settings = QSettings('QtNotepad1', 'Notepad1')
        geometry = settings.value('geometry', QByteArray())
        if geometry.size():
            self.restoreGeometry(geometry)
            self.this_width = self.geometry().width()
            self.this_height = self.geometry().height()
        
        _zoom_level = settings.value('zoom', QByteArray())
        if _zoom_level:
            self.zoom_level = int(_zoom_level.data())
            self.this_zoom = int(_zoom_level.data())
            if self.zoom_level > 0:
                for i in range(self.zoom_level):
                    self._text_edit.zoomIn()
            elif self.zoom_level < 0:
                for i in range(self.zoom_level):
                    self._text_edit.zoomOut()
        
        _w = settings.value('wordwrap', QByteArray())
        self.this_wordwrap = str(_w.data().decode('utf-8'))
        if str(_w.data().decode('utf-8')) == "True":
            self._wrapmode_act.setChecked(True)
            self._text_edit.setWordWrapMode(QTextOption.WrapMode.WrapAnywhere)
        else:
            self._text_edit.setWordWrapMode(QTextOption.WrapMode.NoWrap)

    def write_settings(self):
        # settings = QSettings('QtNotepad1', 'Notepad1')
        # settings.setValue('geometry', self.saveGeometry())
        
        _ba = QByteArray()
        _ba.append(bytes(str(self.zoom_level), encoding='utf-8'))
        # settings.setValue('zoom', _ba)
        
        _wr = str(self._wrapmode_act.isChecked())
        _bw = QByteArray()
        _bw.append(bytes(_wr, encoding='utf-8'))
        
        _w = self.geometry().width()
        _h = self.geometry().height()
        _z = self.zoom_level
        _ww = _wr
        
        if _w != self.this_width or _h != self.this_height or _z != self.this_zoom or _ww != self.this_wordwrap:
            settings = QSettings('QtNotepad1', 'Notepad1')
            settings.setValue('geometry', self.saveGeometry())
            settings.setValue('zoom', _ba)
            settings.setValue('wordwrap', _bw)

    def maybe_save(self):
        if self._text_edit.document().isModified():
            ret = QMessageBox.warning(self, "Application",
                                      "The document has been modified.\nDo you want to save "
                                      "your changes?",
                                      QMessageBox.StandardButton.Save
                                      | QMessageBox.StandardButton.Discard
                                      | QMessageBox.StandardButton.Cancel)
            if ret == QMessageBox.StandardButton.Save:
                return self.save()
            elif ret == QMessageBox.StandardButton.Cancel:
                return False
        return True

    def load_file(self, fileName):
        file = QFile(fileName)
        if not file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
            reason = file.errorString()
            QMessageBox.warning(self, "Application", f"Cannot read file {fileName}:\n{reason}.")
            return

        inf = QTextStream(file)
        # with QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor):
        self._text_edit.setPlainText(inf.readAll())

        self.set_current_file(fileName)
        # self.statusBar().showMessage("File loaded", 2000)

    def save_file(self, fileName):
        error = None
        # with QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor):
        file = QSaveFile(fileName)
        if file.open(QFile.OpenModeFlag.WriteOnly | QFile.OpenModeFlag.Text):
            outf = QTextStream(file)
            outf << self._text_edit.toPlainText()
            if not file.commit():
                reason = file.errorString()
                error = f"Cannot write file {fileName}:\n{reason}."
        else:
            reason = file.errorString()
            error = f"Cannot open file {fileName}:\n{reason}."

        if error:
            QMessageBox.warning(self, "Application", error)
            return False

        self.set_current_file(fileName)
        # self.statusBar().showMessage("File saved", 2000)
        return True

    def set_current_file(self, fileName):
        self._cur_file = fileName
        self._text_edit.document().setModified(False)
        self.setWindowModified(False)

        if self._cur_file:
            shown_name = self.stripped_name(self._cur_file)
        else:
            shown_name = 'untitled.txt'

        self.setWindowTitle(f"{shown_name}[*]")

    def stripped_name(self, fullFileName):
        return QFileInfo(fullFileName).fileName()


if __name__ == '__main__':
    argument_parser = ArgumentParser(description='Application Example',
                                     formatter_class=RawTextHelpFormatter)
    argument_parser.add_argument("file", help="File",
                                 nargs='?', type=str)
    options = argument_parser.parse_args()

    app = QApplication(sys.argv)
    QGuiApplication.setDesktopFileName("qtnotepad1")
    main_win = MainWindow()
    # if options.file:
        # main_win.load_file(options.file)
    if len(sys.argv) > 1:
        fn = os.path.realpath(sys.argv[1])
        main_win.load_file(fn)
    main_win.show()
    sys.exit(app.exec())
