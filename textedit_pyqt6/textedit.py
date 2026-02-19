#!/usr/bin/env python3


#############################################################################
##
## Copyright (C) 2013 Riverbank Computing Limited
## Copyright (C) 2010 Hans-Peter Jansen <hpj@urpla.net>.
## Copyright (C) 2010 Nokia Corporation and/or its subsidiary(-ies).
## All rights reserved.
##
## This file is part of the examples of PyQt.
##
## $QT_BEGIN_LICENSE:LGPL$
## Commercial Usage
## Licensees holding valid Qt Commercial licenses may use this file in
## accordance with the Qt Commercial License Agreement provided with the
## Software or, alternatively, in accordance with the terms contained in
## a written agreement between you and Nokia.
##
## GNU Lesser General Public License Usage
## Alternatively, this file may be used under the terms of the GNU Lesser
## General Public License version 2.1 as published by the Free Software
## Foundation and appearing in the file LICENSE.LGPL included in the
## packaging of this file.  Please review the following information to
## ensure the GNU Lesser General Public License version 2.1 requirements
## will be met: http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
##
## In addition, as a special exception, Nokia gives you certain additional
## rights.  These rights are described in the Nokia Qt LGPL Exception
## version 1.1, included in the file LGPL_EXCEPTION.txt in this package.
##
## GNU General Public License Usage
## Alternatively, this file may be used under the terms of the GNU
## General Public License version 3.0 as published by the Free Software
## Foundation and appearing in the file LICENSE.GPL included in the
## packaging of this file.  Please review the following information to
## ensure the GNU General Public License version 3.0 requirements will be
## met: http://www.gnu.org/copyleft/gpl.html.
##
## If you have questions regarding the use of this file, please contact
## Nokia at qt-info@nokia.com.
## $QT_END_LICENSE$
##
#############################################################################


import sys,os

from PyQt6.QtCore import (QByteArray, QFile, QFileInfo, Qt, QSettings, QPoint)
from PyQt6.QtGui import (QGuiApplication, QTextDocument, QTextCursor, QPalette, QAction, QActionGroup, QFont, QFontDatabase, QFontInfo, QIcon, QKeySequence,
        QPixmap, QTextBlockFormat, QTextCharFormat, QTextCursor, QBrush, QIntValidator, 
        QTextDocumentWriter, QTextListFormat, QTextTableFormat, QTextTableCellFormat, QColor)
from PyQt6.QtWidgets import (QApplication, QColorDialog, QDialog, QBoxLayout, 
        QFormLayout, QComboBox, QFileDialog, QFontComboBox, QMainWindow, QMenu, QMessageBox,
        QTextEdit, QToolBar, QLineEdit, QHBoxLayout, QPushButton)
from PyQt6.QtPrintSupport import (QPrintDialog, QPrinter, QPrintPreviewDialog)

import textedit_rc


# if sys.platform.startswith('darwin'):
    # rsrcPath = ":/images/mac"
# else:
rsrcPath = ":/images/win"

# this program working directory
curr_dir = os.getcwd()

class TextEdit(QMainWindow):
    def __init__(self, fileName=None, parent=None):
        super(TextEdit, self).__init__(parent)

        self.setWindowIcon(QIcon(os.path.join(curr_dir,'images/win/textedit.svg')))
        # self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonFollowStyle)
        self.setupFileActions()
        self.setupEditActions()
        self.setupTextActions()
        
        helpMenu = QMenu("Help", self)
        self.menuBar().addMenu(helpMenu)
        helpMenu.addAction("About", self.about)
        # helpMenu.addAction("About &Qt", QApplication.instance().aboutQt)
 
        self.textEdit = QTextEdit(self)
        self.textEdit.currentCharFormatChanged.connect(
                self.currentCharFormatChanged)
        self.textEdit.cursorPositionChanged.connect(self.cursorPositionChanged)
        self.setCentralWidget(self.textEdit)
        self.textEdit.setFocus()
        
        self.setCurrentFileName()
        self.fontChanged(self.textEdit.font())
        self.colorChanged(self.textEdit.textColor())
        self.alignmentChanged(self.textEdit.alignment())
        self.textEdit.document().modificationChanged.connect(
                self.actionSave.setEnabled)
        self.textEdit.document().modificationChanged.connect(
                self.setWindowModified)
        self.textEdit.document().undoAvailable.connect(
                self.actionUndo.setEnabled)
        self.textEdit.document().redoAvailable.connect(
                self.actionRedo.setEnabled)
        self.setWindowModified(self.textEdit.document().isModified())
        self.actionSave.setEnabled(self.textEdit.document().isModified())
        self.actionUndo.setEnabled(self.textEdit.document().isUndoAvailable())
        self.actionRedo.setEnabled(self.textEdit.document().isRedoAvailable())
        self.actionUndo.triggered.connect(self.textEdit.undo)
        self.actionRedo.triggered.connect(self.textEdit.redo)
        self.actionCut.setEnabled(False)
        self.actionCopy.setEnabled(False)
        self.actionCut.triggered.connect(self.textEdit.cut)
        self.actionCopy.triggered.connect(self.textEdit.copy)
        self.actionPaste.triggered.connect(self.textEdit.paste)
        self.textEdit.copyAvailable.connect(self.actionCut.setEnabled)
        self.textEdit.copyAvailable.connect(self.actionCopy.setEnabled)
        QApplication.clipboard().dataChanged.connect(self.clipboardDataChanged)
        
        self.this_width = 0
        self.this_height = 0
        self.read_settings()
        
        if fileName is None:
            self.fileNew()
        else:
            if not self.load(fileName):
                self.fileNew()
        # 
        self.TEBaseColorColor = self.textEdit.palette().color(QPalette.ColorRole.Base)
        self.TEBaseColor = self.textEdit.palette().color(QPalette.ColorRole.Base).toRgb().name(QColor.NameFormat.HexRgb)
                
    def closeEvent(self, e):
        if self.maybeSave():
            self.write_settings()
            e.accept()
        else:
            e.ignore()
    
    def write_settings(self):
        _w = self.geometry().width()
        _h = self.geometry().height()
        if _w != self.this_width or _h != self.this_height:
            settings = QSettings('QtTextEdit1', 'TextEdit1')
            settings.setValue('geometry', self.saveGeometry())
    
    def read_settings(self):
        settings = QSettings('QtTextEdit1', 'TextEdit1')
        geometry = settings.value('geometry', QByteArray())
        if geometry.size():
            self.restoreGeometry(geometry)
            self.this_width = self.geometry().width()
            self.this_height = self.geometry().height()
        else:
            self.resize(700, 400)
            self.this_with = 700
            self.this_height = 400
    
    def setupFileActions(self):
        tb = QToolBar(self)
        tb.setWindowTitle("File Actions")
        self.addToolBar(tb)

        menu = QMenu("&File", self)
        self.menuBar().addMenu(menu)

        self.actionNew = QAction(
                QIcon.fromTheme('document-new',
                        QIcon(rsrcPath + '/filenew.png')),
                "&New", self, priority=QAction.Priority.LowPriority,
                shortcut=QKeySequence.StandardKey.New, triggered=self.fileNew)
        tb.addAction(self.actionNew)
        menu.addAction(self.actionNew)

        self.actionOpen = QAction(
                QIcon.fromTheme('document-open',
                        QIcon(rsrcPath + '/fileopen.png')),
                "&Open...", self, shortcut=QKeySequence.StandardKey.Open,
                triggered=self.fileOpen)
        tb.addAction(self.actionOpen)
        menu.addAction(self.actionOpen)
        menu.addSeparator()

        self.actionSave = QAction(
                QIcon.fromTheme('document-save',
                        QIcon(rsrcPath + '/filesave.png')),
                "&Save", self, shortcut=QKeySequence.StandardKey.Save,
                triggered=self.fileSave, enabled=False)
        tb.addAction(self.actionSave)
        menu.addAction(self.actionSave)

        self.actionSaveAs = QAction("Save &As...", self,
                priority=QAction.Priority.LowPriority,
                shortcut=QKeySequence.StandardKey.SaveAs,
                triggered=self.fileSaveAs)
        menu.addAction(self.actionSaveAs)
        menu.addSeparator()
 
        self.actionPrint = QAction(
                QIcon.fromTheme('document-print',
                        QIcon(rsrcPath + '/fileprint.png')),
                "&Print...", self, priority=QAction.Priority.LowPriority,
                shortcut=QKeySequence.StandardKey.Print, triggered=self.filePrint)
        tb.addAction(self.actionPrint)
        menu.addAction(self.actionPrint)

        self.actionPrintPreview = QAction(
                QIcon.fromTheme('fileprint',
                        QIcon(rsrcPath + '/fileprint.png')),
                "Print Preview...", self,
                shortcut="Ctrl+Shift+D",
                triggered=self.filePrintPreview)
        menu.addAction(self.actionPrintPreview)

        self.actionPrintPdf = QAction(
                QIcon.fromTheme('exportpdf',
                        QIcon(rsrcPath + '/exportpdf.png')),
                "&Export PDF...", self, priority=QAction.Priority.LowPriority,
                shortcut="Ctrl+D",
                triggered=self.filePrintPdf)
        tb.addAction(self.actionPrintPdf)
        menu.addAction(self.actionPrintPdf)
        menu.addSeparator()

        self.actionQuit = QAction("&Quit", self, shortcut=QKeySequence.StandardKey.Quit,
                triggered=self.close)
        menu.addAction(self.actionQuit)

    def setupEditActions(self):
        tb = QToolBar(self)
        tb.setWindowTitle("Edit Actions")
        self.addToolBar(tb)

        menu = QMenu("&Edit", self)
        self.menuBar().addMenu(menu)

        self.actionUndo = QAction(
                QIcon.fromTheme('edit-undo',
                        QIcon(rsrcPath + '/editundo.png')),
                "&Undo", self, shortcut=QKeySequence.StandardKey.Undo)
        tb.addAction(self.actionUndo)
        menu.addAction(self.actionUndo)

        self.actionRedo = QAction(
                QIcon.fromTheme('edit-redo',
                        QIcon(rsrcPath + '/editredo.png')),
                "&Redo", self, priority=QAction.Priority.LowPriority,
                shortcut=QKeySequence.StandardKey.Redo)
        tb.addAction(self.actionRedo)
        menu.addAction(self.actionRedo)
        menu.addSeparator()

        self.actionCut = QAction(
                QIcon.fromTheme('edit-cut', QIcon(rsrcPath + '/editcut.png')),
                "Cu&t", self, priority=QAction.Priority.LowPriority,
                shortcut=QKeySequence.StandardKey.Cut)
        tb.addAction(self.actionCut)
        menu.addAction(self.actionCut)

        self.actionCopy = QAction(
                QIcon.fromTheme('edit-copy',
                        QIcon(rsrcPath + '/editcopy.png')),
                "&Copy", self, priority=QAction.Priority.LowPriority,
                shortcut=QKeySequence.StandardKey.Copy)
        tb.addAction(self.actionCopy)
        menu.addAction(self.actionCopy)

        self.actionPaste = QAction(
                QIcon.fromTheme('edit-paste',
                        QIcon(rsrcPath + '/editpaste.png')),
                "&Paste", self, priority=QAction.Priority.LowPriority,
                shortcut=QKeySequence.StandardKey.Paste,
                enabled=(len(QApplication.clipboard().text()) != 0))
        tb.addAction(self.actionPaste)
        menu.addAction(self.actionPaste)

    def setupTextActions(self):
        tb = QToolBar(self)
        tb.setWindowTitle("Format Actions")
        self.addToolBar(tb)

        menu = QMenu("F&ormat", self)
        self.menuBar().addMenu(menu)

        self.actionTextBold = QAction(
                QIcon.fromTheme('format-text-bold',
                        QIcon(rsrcPath + '/textbold.png')),
                "&Bold", self, priority=QAction.Priority.LowPriority,
                shortcut=QKeySequence.StandardKey.Bold, triggered=self.textBold,
                checkable=True)
        bold = QFont()
        bold.setBold(True)
        self.actionTextBold.setFont(bold)
        tb.addAction(self.actionTextBold)
        menu.addAction(self.actionTextBold)

        self.actionTextItalic = QAction(
                QIcon.fromTheme('format-text-italic',
                        QIcon(rsrcPath + '/textitalic.png')),
                "&Italic", self, priority=QAction.Priority.LowPriority,
                shortcut=QKeySequence.StandardKey.Italic, triggered=self.textItalic,
                checkable=True)
        italic = QFont()
        italic.setItalic(True)
        self.actionTextItalic.setFont(italic)
        tb.addAction(self.actionTextItalic)
        menu.addAction(self.actionTextItalic)

        self.actionTextUnderline = QAction(
                QIcon.fromTheme('format-text-underline',
                        QIcon(rsrcPath + '/textunder.png')),
                "&Underline", self, priority=QAction.Priority.LowPriority,
                shortcut=QKeySequence.StandardKey.Underline, triggered=self.textUnderline,
                checkable=True)
        underline = QFont()
        underline.setUnderline(True)
        self.actionTextUnderline.setFont(underline)
        tb.addAction(self.actionTextUnderline)
        menu.addAction(self.actionTextUnderline)
        
        self.actionTextOverline = QAction(
                        QIcon(rsrcPath + '/textover.png'),
                "&Overline", self, priority=QAction.Priority.LowPriority,
                triggered=self.textOverline,
                checkable=True)
        overline = QFont()
        overline.setOverline(True)
        self.actionTextOverline.setFont(overline)
        # tb.addAction(self.actionTextOverline)
        menu.addAction(self.actionTextOverline)
        
        self.actionTextStrikeout = QAction(
                QIcon.fromTheme('format-text-strikethrough',
                        QIcon(rsrcPath + '/textstrike.png')),
                "&Strikeout", self, priority=QAction.Priority.LowPriority,
                triggered=self.textStrikeout,
                checkable=True)
        strikeout = QFont()
        strikeout.setStrikeOut(True)
        self.actionTextStrikeout.setFont(strikeout)
        # tb.addAction(self.actionTextStrikeout)
        menu.addAction(self.actionTextStrikeout)
        
        menu.addSeparator()
        
        self.actionTextSup = QAction(
                QIcon.fromTheme('format-text-superscript',
                        QIcon(rsrcPath + '/textsup.png')),
                "&Sup", self, priority=QAction.Priority.LowPriority,
                triggered=self.textSup,
                checkable=False)
        menu.addAction(self.actionTextSup)
        
        self.actionTextSub = QAction(
                QIcon.fromTheme('format-text-subscript',
                        QIcon(rsrcPath + '/textsub.png')),
                "&Sub", self, priority=QAction.Priority.LowPriority,
                triggered=self.textSub,
                checkable=False)
        menu.addAction(self.actionTextSub)
        
        menu.addSeparator()
        self.actionRemoveFormatting = QAction(
                QIcon.fromTheme('format-text-remove-formatting',
                        QIcon(rsrcPath + '/textremoveformatting.png')),
                "&Remove all formattings", self, priority=QAction.Priority.LowPriority,
                triggered=self.textRemoveFormatting,
                checkable=False)
        menu.addAction(self.actionRemoveFormatting)
        
        menu.addSeparator()

        grp = QActionGroup(self, triggered=self.textAlign)

        # Make sure the alignLeft is always left of the alignRight.
        if QApplication.isLeftToRight():
            self.actionAlignLeft = QAction(
                    QIcon.fromTheme('format-justify-left',
                            QIcon(rsrcPath + '/textleft.png')),
                    "&Left", grp)
            self.actionAlignCenter = QAction(
                    QIcon.fromTheme('format-justify-center',
                            QIcon(rsrcPath + '/textcenter.png')),
                    "C&enter", grp)
            self.actionAlignRight = QAction(
                    QIcon.fromTheme('format-justify-right',
                            QIcon(rsrcPath + '/textright.png')),
                    "&Right", grp)
        else:
            self.actionAlignRight = QAction(
                    QIcon.fromTheme('format-justify-right',
                            QIcon(rsrcPath + '/textright.png')),
                    "&Right", grp)
            self.actionAlignCenter = QAction(
                    QIcon.fromTheme('format-justify-center',
                            QIcon(rsrcPath + '/textcenter.png')),
                    "C&enter", grp)
            self.actionAlignLeft = QAction(
                    QIcon.fromTheme('format-justify-left',
                            QIcon(rsrcPath + '/textleft.png')),
                    "&Left", grp)
 
        self.actionAlignJustify = QAction(
                QIcon.fromTheme('format-justify-fill',
                        QIcon(rsrcPath + '/textjustify.png')),
                "&Justify", grp)
        
        self.actionAlignLeft.setShortcut("Ctrl+L")
        self.actionAlignLeft.setCheckable(True)
        self.actionAlignLeft.setPriority(QAction.Priority.LowPriority)

        self.actionAlignCenter.setShortcut("Ctrl+E")
        self.actionAlignCenter.setCheckable(True)
        self.actionAlignCenter.setPriority(QAction.Priority.LowPriority)

        self.actionAlignRight.setShortcut("Ctrl+R")
        self.actionAlignRight.setCheckable(True)
        self.actionAlignRight.setPriority(QAction.Priority.LowPriority)

        self.actionAlignJustify.setShortcut("Ctrl+J")
        self.actionAlignJustify.setCheckable(True)
        self.actionAlignJustify.setPriority(QAction.Priority.LowPriority)

        tb.addActions(grp.actions())
        menu.addActions(grp.actions())
        menu.addSeparator()
        
        self.addTable = QAction(
                QIcon.fromTheme('table-new',
                        QIcon(rsrcPath + '/table_add.png')),
                "Add table", self, enabled=True, triggered=self.on_add_table)
        # tb.addAction(self.addTable)
        menu.addAction(self.addTable)
        
        self.modifyTable = QAction("Modify the table", 
                self, enabled=True, triggered=self.on_modify_table)
        # tb.addAction(self.modifyTable)
        menu.addAction(self.modifyTable)
        menu.addSeparator()
        
        pix = QPixmap(16, 16)
        pix.fill(Qt.GlobalColor.black)
        self.actionTextColor = QAction(QIcon(pix), "&Text color...", self,
                triggered=self.textColor)
        self.actionTextColor.setShortcut("Ctrl+T")
        tb.addAction(self.actionTextColor)
        menu.addAction(self.actionTextColor)
        
        pix2 = QPixmap(16, 16)
        pix2.fill(Qt.GlobalColor.white)
        self.actionDocColor = QAction(QIcon(pix2), "&Editor color...", self,
                triggered=self.DocColor)
        # self.actionDocColor.setShortcut("Ctrl+D")
        # tb.addAction(self.actionDocColor)
        menu.addAction(self.actionDocColor)
        
        self.actionRestoreDocColor = QAction("Restore Editor color...", self,
                triggered=self.restoreDocColor)
        menu.addAction(self.actionRestoreDocColor)

        tb = QToolBar(self)
        tb.setAllowedAreas(Qt.ToolBarArea.TopToolBarArea | Qt.ToolBarArea.BottomToolBarArea)
        tb.setWindowTitle("Format Actions")
        self.addToolBarBreak(Qt.ToolBarArea.TopToolBarArea)
        self.addToolBar(tb)

        comboStyle = QComboBox(tb)
        tb.addWidget(comboStyle)
        comboStyle.addItem("Standard")
        comboStyle.addItem("Bullet List (Disc)")
        comboStyle.addItem("Bullet List (Circle)")
        comboStyle.addItem("Bullet List (Square)")
        comboStyle.addItem("Ordered List (Decimal)")
        comboStyle.addItem("Ordered List (Alpha lower)")
        comboStyle.addItem("Ordered List (Alpha upper)")
        comboStyle.addItem("Ordered List (Roman lower)")
        comboStyle.addItem("Ordered List (Roman upper)")
        comboStyle.activated.connect(self.textStyle)

        self.comboFont = QFontComboBox(tb)
        tb.addWidget(self.comboFont)
        self.comboFont.activated.connect(self.textFamily)

        self.comboSize = QComboBox(tb)
        self.comboSize.setObjectName("comboSize")
        tb.addWidget(self.comboSize)
        self.comboSize.setEditable(True)
        
        for size in QFontDatabase.standardSizes():
            self.comboSize.addItem("%s" % (size))
        
        self.comboSize.activated.connect(self.textSize)
        self.comboSize.setCurrentIndex(
                self.comboSize.findText(
                        "%s" % (QApplication.font().pointSize())))
    
    def on_add_table(self):
        addTable(self, self.textEdit)
    
    def on_modify_table(self):
        curr_table = self.textEdit.textCursor().currentTable()
        if curr_table:
            askModifyTable(self, curr_table)
    
    def load(self, f):
        if not QFile.exists(f):
            return False

        fh = QFile(f)
        if not fh.open(QFile.OpenModeFlag.ReadOnly):
            return False

        data = fh.readAll()
        _aa = data.data()
        # codec = QTextCodec.codecForHtml(data)
        # unistr = codec.toUnicode(data)
        try:
            unistr = _aa.decode('utf-8')
            if Qt.mightBeRichText(unistr):
                self.textEdit.setHtml(unistr)
            else:
                self.textEdit.setPlainText(unistr)

            self.setCurrentFileName(f)
        except:
            pass
        
        return True

    def maybeSave(self):
        if not self.textEdit.document().isModified():
            return True

        if self.fileName.startswith(':/'):
            return True

        ret = QMessageBox.warning(self, "Application",
                "The document has been modified.\n"
                "Do you want to save your changes?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel)

        if ret == QMessageBox.StandardButton.Save:
            return self.fileSave()

        if ret == QMessageBox.StandardButton.Cancel:
            return False

        return True

    def setCurrentFileName(self, fileName=''):
        self.fileName = fileName
        self.textEdit.document().setModified(False)
        
        if not fileName:
            shownName = 'untitled.html'
        else:
            shownName = QFileInfo(fileName).fileName()

        # self.setWindowTitle(self.tr("%s[*] - %s" % (shownName, "Rich Text")))
        self.setWindowTitle(self.tr("%s[*]" % (shownName)))
        self.setWindowModified(False)

    def fileNew(self):
        if self.maybeSave():
            self.textEdit.clear()
            self.setCurrentFileName()

    def fileOpen(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Open File...", None,
                "HTML-Files (*.htm *.html);;All Files (*)")

        if fn:
            self.load(fn)

    def fileSave(self):
        
        if not self.fileName:
            return self.fileSaveAs()

        writer = QTextDocumentWriter(self.fileName)
        success = writer.write(self.textEdit.document())
        if success:
            self.textEdit.document().setModified(False)

        return success

    def fileSaveAs(self):
        # fn, _ = QFileDialog.getSaveFileName(self, "Save as...", None,
                # "ODF files (*.odt);;HTML-Files (*.htm *.html);;All Files (*)")
        
        fn, _ = QFileDialog.getSaveFileName(self, "Save as...", None,
                "HTML-Files (*.htm *.html);;All Files (*)")
        
        
        if not fn:
            return False

        lfn = fn.lower()
        # if not lfn.endswith(('.odt', '.htm', '.html')):
            # # The default.
            # fn += '.odt'
        
        if not lfn.endswith(('.htm', '.html')):
            # The default.
            fn += '.html'
        
        self.setCurrentFileName(fn)
        return self.fileSave()

    def filePrint(self):
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        
        if not self.fileName:
            _file = "Unkown"
        else:
            _file = self.fileName
        printer.setOutputFileName(_file+".pdf")
        
        dlg = QPrintDialog(printer, self)

        if self.textEdit.textCursor().hasSelection():
            dlg.addEnabledOption(QPrintDialog.PrintSelection)

        dlg.setWindowTitle("Print Document")

        if dlg.exec():# == QPrintDialog.accepted:
            self.textEdit.print(printer)

        del dlg

    def filePrintPreview(self):
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        preview = QPrintPreviewDialog(printer, self)
        preview.paintRequested.connect(self.printPreview)
        preview.exec()

    def printPreview(self, printer):
        self.textEdit.print(printer)

    def filePrintPdf(self):
        fn, _ = QFileDialog.getSaveFileName(self, "Export PDF", None,
                "PDF files (*.pdf);;All Files (*)")

        if fn:
            # if QFileInfo(fn).suffix().isEmpty():
            if QFileInfo(fn).suffix() == "":
                fn += '.pdf'

            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(fn)
            self.textEdit.document().print(printer)

    def textBold(self):
        fmt = QTextCharFormat()
        fmt.setFontWeight(self.actionTextBold.isChecked() and QFont.Weight.Bold or QFont.Weight.Normal)
        self.mergeFormatOnWordOrSelection(fmt)

    def textUnderline(self):
        fmt = QTextCharFormat()
        fmt.setFontUnderline(self.actionTextUnderline.isChecked())
        self.mergeFormatOnWordOrSelection(fmt)
    
    def textOverline(self):
        fmt = QTextCharFormat()
        fmt.setFontOverline(self.actionTextOverline.isChecked())
        self.mergeFormatOnWordOrSelection(fmt)
    
    def textStrikeout(self):
        fmt = QTextCharFormat()
        fmt.setFontStrikeOut(self.actionTextStrikeout.isChecked())
        self.mergeFormatOnWordOrSelection(fmt)
    
    def textSup(self):
        _t = self.textEdit.textCursor()
        _selected = _t.selectedText()
        _t.deleteChar()
        self.textEdit.insertHtml("<sup>{}</sup>".format(_selected))
        
    def textSub(self):
        _t = self.textEdit.textCursor()
        _selected = _t.selectedText()
        _t.deleteChar()
        self.textEdit.insertHtml("<sub>{}</sub>".format(_selected))
    
    def textRemoveFormatting(self):
        _t = self.textEdit.textCursor()
        _selected = _t.selectedText()
        _t.deleteChar()
        _t.insertText(_selected)
    
    def textItalic(self):
        fmt = QTextCharFormat()
        fmt.setFontItalic(self.actionTextItalic.isChecked())
        self.mergeFormatOnWordOrSelection(fmt)

    def textFamily(self, _family):
        family = self.comboFont.currentFont().family()
        fmt = QTextCharFormat()
        fmt.setFontFamily(family)
        self.mergeFormatOnWordOrSelection(fmt)

    # # def textSize(self, pointSize):
        # # pointSize = float(pointSize)
        # # if pointSize > 0:
            # # fmt = QTextCharFormat()
            # # fmt.setFontPointSize(pointSize)
            # # self.mergeFormatOnWordOrSelection(fmt)
    
    def textSize(self, _idx):
        pointSize = float(self.comboSize.itemText(_idx))
        if pointSize > 0:
            fmt = QTextCharFormat()
            fmt.setFontPointSize(pointSize)
            self.mergeFormatOnWordOrSelection(fmt)
    
    def textStyle(self, styleIndex):
        cursor = self.textEdit.textCursor()
        if styleIndex:
            styleDict = {
                1: QTextListFormat.Style.ListDisc,
                2: QTextListFormat.Style.ListCircle,
                3: QTextListFormat.Style.ListSquare,
                4: QTextListFormat.Style.ListDecimal,
                5: QTextListFormat.Style.ListLowerAlpha,
                6: QTextListFormat.Style.ListUpperAlpha,
                7: QTextListFormat.Style.ListLowerRoman,
                8: QTextListFormat.Style.ListUpperRoman,
            }

            style = styleDict.get(styleIndex, QTextListFormat.Style.ListDisc)
            cursor.beginEditBlock()
            blockFmt = cursor.blockFormat()
            listFmt = QTextListFormat()

            if cursor.currentList():
                listFmt = cursor.currentList().format()
            else:
                listFmt.setIndent(blockFmt.indent() + 1)
                blockFmt.setIndent(0)
                cursor.setBlockFormat(blockFmt)

            listFmt.setStyle(style)
            cursor.createList(listFmt)
            cursor.endEditBlock()
        else:
            bfmt = QTextBlockFormat()
            bfmt.setObjectIndex(-1)
            cursor.mergeBlockFormat(bfmt)

    def textColor(self):
        col = QColorDialog.getColor(self.textEdit.textColor(), self)
        if not col.isValid():
            return

        fmt = QTextCharFormat()
        fmt.setForeground(col)
        self.mergeFormatOnWordOrSelection(fmt)
        self.colorChanged(col)
    
    def DocColor(self):
        col = QColorDialog.getColor()
        if not col.isValid():
            return
            
        self.textEdit.setStyleSheet("background-color: {};".format(col.name(QColor.NameFormat.HexRgb)))
        pix = QPixmap(16, 16)
        pix.fill(col)
        self.actionDocColor.setIcon(QIcon(pix))
        
    def restoreDocColor(self):
        self.textEdit.setStyleSheet("background-color: {};".format(self.TEBaseColor))
        pix = QPixmap(16, 16)
        pix.fill(self.TEBaseColorColor)
        self.actionDocColor.setIcon(QIcon(pix))
        
    def textAlign(self, action):
        if action == self.actionAlignLeft:
            self.textEdit.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignAbsolute)
        elif action == self.actionAlignCenter:
            self.textEdit.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        elif action == self.actionAlignRight:
            self.textEdit.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignAbsolute)
        elif action == self.actionAlignJustify:
            self.textEdit.setAlignment(Qt.AlignmentFlag.AlignJustify)

    def currentCharFormatChanged(self, format):
        self.fontChanged(format.font())
        self.colorChanged(format.foreground().color())

    def cursorPositionChanged(self):
        self.alignmentChanged(self.textEdit.alignment())

    def clipboardDataChanged(self):
        self.actionPaste.setEnabled(len(QApplication.clipboard().text()) != 0)

    def about(self):
        QMessageBox.about(self, "About", 
                "A simple html editor.\nFree to use and modify.")

    def mergeFormatOnWordOrSelection(self, format):
        cursor = self.textEdit.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)

        cursor.mergeCharFormat(format)
        self.textEdit.mergeCurrentCharFormat(format)

    def fontChanged(self, font):
        self.comboFont.setCurrentIndex(
                self.comboFont.findText(QFontInfo(font).family()))
        self.comboSize.setCurrentIndex(
                self.comboSize.findText("%s" % font.pointSize()))
        self.actionTextBold.setChecked(font.bold())
        self.actionTextItalic.setChecked(font.italic())
        self.actionTextUnderline.setChecked(font.underline())
        self.actionTextOverline.setChecked(font.overline())
        self.actionTextStrikeout.setChecked(font.strikeOut())

    def colorChanged(self, color):
        pix = QPixmap(16, 16)
        pix.fill(color)
        self.actionTextColor.setIcon(QIcon(pix))

    def alignmentChanged(self, alignment):
        if alignment & Qt.AlignmentFlag.AlignLeft:
            self.actionAlignLeft.setChecked(True)
        elif alignment & Qt.AlignmentFlag.AlignHCenter:
            self.actionAlignCenter.setChecked(True)
        elif alignment & Qt.AlignmentFlag.AlignRight:
            self.actionAlignRight.setChecked(True)
        elif alignment & Qt.AlignmentFlag.AlignJustify:
            self.actionAlignJustify.setChecked(True)

# dialog - return of the choise yes or no
class retDialogBox(QMessageBox):
    def __init__(self, *args):
        super(retDialogBox, self).__init__(args[-1])
        # self.setWindowIcon(QIcon("icons/program.svg"))
        self.setWindowTitle(args[0])
        self.setContentsMargins(0,0,0,0)
        if args[0] == "Info":
            self.setIcon(QMessageBox.Icon.Information)
        elif args[0] == "Error":
            self.setIcon(QMessageBox.Icon.Critical)
        elif args[0] == "Question":
            self.setIcon(QMessageBox.Icon.Question)
        self.resize(DIALOGWIDTH, 100)
        self.setText(args[1])
        self.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        #
        self.Value = None
        retval = self.exec()
        #
        if retval == QMessageBox.StandardButton.Yes:
            self.Value = 1
        elif retval == QMessageBox.StandardButton.Cancel:
            self.Value = 0
    
    def getValue(self):
        return self.Value

# ask for table modifications
class askModifyTable(QDialog):
    def __init__(self, parent, curr_table):
        super(askModifyTable, self).__init__(parent)
        self.parent = parent
        self.curr_table = curr_table
        self.setWindowTitle("Modify the table?")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.resize(50, 50)
        #
        vbox = QBoxLayout(QBoxLayout.Direction.TopToBottom)
        vbox.setContentsMargins(4,4,4,4)
        self.setLayout(vbox)
        #
        btn10 = QPushButton("Prepend rows")
        btn10.clicked.connect(lambda: self.on_btn_action("ar"))
        vbox.addWidget(btn10)
        btn15 = QPushButton("Add rows")
        btn15.clicked.connect(lambda: self.on_btn_action("ar2"))
        vbox.addWidget(btn15)
        btn20 = QPushButton("Prepend columns")
        btn20.clicked.connect(lambda: self.on_btn_action("ac"))
        vbox.addWidget(btn20)
        btn25 = QPushButton("Add columns")
        btn25.clicked.connect(lambda: self.on_btn_action("ac2"))
        vbox.addWidget(btn25)
        btn30 = QPushButton("Merge celles")
        btn30.clicked.connect(lambda: self.on_btn_action("mc"))
        vbox.addWidget(btn30)
        btn40 = QPushButton("Splip celles")
        btn40.clicked.connect(lambda: self.on_btn_action("sc"))
        vbox.addWidget(btn40)
        btn50 = QPushButton("Remove rows")
        btn50.clicked.connect(lambda: self.on_btn_action("rr"))
        vbox.addWidget(btn50)
        btn60 = QPushButton("Remove columns")
        btn60.clicked.connect(lambda: self.on_btn_action("rc"))
        vbox.addWidget(btn60)
        #
        btnClose = QPushButton("Close")
        btnClose.clicked.connect(self.close)
        vbox.addWidget(btnClose)
        #
        self.show()
        
    def on_btn_action(self, _c):
        modifyTable(self.parent, self.curr_table, _c)
        self.close()

# modify table dialog
class modifyTable(QDialog):
    def __init__(self, parent, curr_table, _c):
        super(modifyTable, self).__init__(parent)
        self.parent = parent
        self.curr_table = curr_table
        self._choise = _c
        # self.setWindowIcon(QIcon("icons/program.svg"))
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.resize(50, 50)
        #
        vbox = QBoxLayout(QBoxLayout.Direction.TopToBottom)
        vbox.setContentsMargins(4,4,4,4)
        self.setLayout(vbox)
        #
        self.form_layout = QFormLayout()
        vbox.addLayout(self.form_layout)
        #
        selected_cells = self.parent.textEdit.textCursor().selectedTableCells()
        if self._choise == "ar" and selected_cells == (-1, -1, -1, -1):
            self.setWindowTitle("Prepend rows")
            self.le2 = QLineEdit()
            self.le2.setValidator(QIntValidator())
            self.form_layout.addRow("How many rows:", self.le2)
        elif self._choise == "ar2" and selected_cells == (-1, -1, -1, -1):
            self.setWindowTitle("Append rows")
            self.le2 = QLineEdit()
            self.le2.setValidator(QIntValidator())
            self.form_layout.addRow("How many rows:", self.le2)
        elif self._choise == "ac" and selected_cells == (-1, -1, -1, -1):
            self.setWindowTitle("Prepend columns")
            self.le2 = QLineEdit()
            self.le2.setValidator(QIntValidator())
            self.form_layout.addRow("How many columns:", self.le2)
        elif self._choise == "ac2" and selected_cells == (-1, -1, -1, -1):
            self.setWindowTitle("Append columns")
            self.le2 = QLineEdit()
            self.le2.setValidator(QIntValidator())
            self.form_layout.addRow("How many columns:", self.le2)
        elif self._choise == "mc"  and selected_cells != (-1, -1, -1, -1):
            self.setWindowTitle("Merge cells")
            self.on_btn1()
        elif self._choise == "sc" and selected_cells == (-1, -1, -1, -1):
            TC = self.curr_table.cellAt(self.parent.textEdit.textCursor())
            if (TC.rowSpan() != 1 and TC.rowSpan() > 0) or (TC.columnSpan() != 1 and TC.columnSpan() > 0):
                self.setWindowTitle("Split cells")
                self.le3 = QLineEdit()
                self.le3.setValidator(QIntValidator())
                self.form_layout.addRow("Number of rows to keep: ", self.le3)
                self.le4 = QLineEdit()
                self.le4.setValidator(QIntValidator())
                self.form_layout.addRow("Number or columns to keep:", self.le4)
            else:
                self.close()
        elif self._choise == "rr" and selected_cells == (-1, -1, -1, -1):
            self.setWindowTitle("Remove rows")
            self.le2 = QLineEdit()
            self.le2.setValidator(QIntValidator())
            self.form_layout.addRow("How many rows:", self.le2)
        elif self._choise == "rc" and selected_cells == (-1, -1, -1, -1):
            self.setWindowTitle("Remove columns")
            self.le2 = QLineEdit()
            self.le2.setValidator(QIntValidator())
            self.form_layout.addRow("How many columns:", self.le2)
        # buttons
        button_box = QHBoxLayout()
        vbox.addLayout(button_box)
        self.btn1 = QPushButton("Accept")
        self.btn1.clicked.connect(self.on_btn1)
        button_box.addWidget(self.btn1)
        
        self.btn2 = QPushButton("Close")
        button_box.addWidget(self.btn2)
        self.btn2.clicked.connect(self.close)
        #
        self._value = None
        self.show()
    
    def on_btn1(self):
        if self._choise == "ar":
            if self.le2.text() == "" or int(self.le2.text()) < 1:
                return
            tableCell = self.curr_table.cellAt(self.parent.textEdit.textCursor())
            _r = tableCell.row()
            self.curr_table.insertRows(_r, int(self.le2.text()))
        elif self._choise == "ar2":
            if self.le2.text() == "" or int(self.le2.text()) < 1:
                return
            tableCell = self.curr_table.cellAt(self.parent.textEdit.textCursor())
            _r = tableCell.row()
            self.curr_table.insertRows(_r+1, int(self.le2.text()))
        elif self._choise == "ac":
            if self.le2.text() == "" or int(self.le2.text()) < 1:
                return
            tableCell = self.curr_table.cellAt(self.parent.textEdit.textCursor())
            _c = tableCell.column()
            self.curr_table.insertColumns(_c, int(self.le2.text()))
        elif self._choise == "ac2":
            if self.le2.text() == "" or int(self.le2.text()) < 1:
                return
            tableCell = self.curr_table.cellAt(self.parent.textEdit.textCursor())
            _c = tableCell.column()
            self.curr_table.insertColumns(_c+1, int(self.le2.text()))
        elif self._choise == "mc":
            self.curr_table.mergeCells(self.parent.textEdit.textCursor())
        elif self._choise == "sc":
            if self.le3.text() == "" or self.le4.text() == "":
                return
            if int(self.le3.text()) <= 0 or int(self.le4.text()) <= 0:
                return
            tableCell = self.curr_table.cellAt(self.parent.textEdit.textCursor())
            self.curr_table.splitCell(tableCell.row(), tableCell.column(),  int(self.le3.text()), int(self.le4.text()))
        elif self._choise == "rr":
            if self.le2.text() == "" or int(self.le2.text()) < 1:
                return
            tableCell = self.curr_table.cellAt(self.parent.textEdit.textCursor())
            _r = tableCell.row()
            self.curr_table.removeRows(_r, int(self.le2.text()))
        elif self._choise == "rc":
            if self.le2.text() == "" or int(self.le2.text()) < 1:
                return
            tableCell = self.curr_table.cellAt(self.parent.textEdit.textCursor())
            _c = tableCell.column()
            self.curr_table.removeColumns(_c, int(self.le2.text()))
        self.close()
    
    def closeEvent(self, e):
        self.close()


# add table dialog
class addTable(QDialog):
    def __init__(self, parent, editor):
        super(addTable, self).__init__(parent)
        self.parent = parent
        self.editor = editor
        # self.setWindowIcon(QIcon("icons/program.svg"))
        self.setWindowTitle("Add table")
        # self.setWindowModality(Qt.ApplicationModal)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.resize(50, 50)
        #
        vbox = QBoxLayout(QBoxLayout.Direction.TopToBottom)
        vbox.setContentsMargins(4,4,4,4)
        self.setLayout(vbox)
        #
        self.form_layout = QFormLayout()
        vbox.addLayout(self.form_layout)
        self.le1 = QLineEdit()
        self.le1.setValidator(QIntValidator())
        self.form_layout.addRow("Rows", self.le1)
        self.le2 = QLineEdit()
        self.le2.setValidator(QIntValidator())
        self.form_layout.addRow("Columns", self.le2)
        # buttons
        button_box = QHBoxLayout()
        vbox.addLayout(button_box)
        self.btn1 = QPushButton("Accept")
        self.btn1.clicked.connect(self.on_btn1)
        button_box.addWidget(self.btn1)
        
        self.btn2 = QPushButton("Close")
        button_box.addWidget(self.btn2)
        self.btn2.clicked.connect(self.close)
        #
        self._value = None
        self.show()
    
    def on_btn1(self):
        if self.le1.text() and self.le2.text():
            _r = int(self.le1.text())
            _c = int(self.le2.text())
            format = QTextTableFormat()
            format.setBorderCollapse(False)
            # format.setBorder(4)
            # _bb = QBrush()
            # _bb.setColor(Qt.GlobalColor.black)
            # _bb.setStyle(Qt.BrushStyle.SolidPattern)
            # format.setBorderBrush(_bb)
            format.setCellPadding(6)
            format.setCellSpacing(0)
            
            if _r > 0 and _c > 0:
                self.editor.textCursor().insertTable(_r, _c, format)
            
                self.close()
    
    def closeEvent(self, e):
        self.close()





if __name__ == '__main__':
    app = QApplication(sys.argv)
    QGuiApplication.setDesktopFileName("qttextedit1")
    
    mainWindows = []
    if len(sys.argv) > 1:
        fn = os.path.realpath(sys.argv[1])
    else:
        fn = None
    textEdit = TextEdit(fn)
    textEdit.show()
    mainWindows.append(textEdit)

    sys.exit(app.exec())
