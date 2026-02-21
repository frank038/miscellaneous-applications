#!/usr/bin/env python3


#############################################################################
##
## Copyright (C) 2013 Riverbank Computing Limited.
## Copyright (C) 2010 Nokia Corporation and/or its subsidiary(-ies).
## All rights reserved.
##
## This file is part of the examples of PyQt.
##
## $QT_BEGIN_LICENSE:BSD$
## You may use this file under the terms of the BSD license as follows:
##
## "Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are
## met:
##   * Redistributions of source code must retain the above copyright
##     notice, this list of conditions and the following disclaimer.
##   * Redistributions in binary form must reproduce the above copyright
##     notice, this list of conditions and the following disclaimer in
##     the documentation and/or other materials provided with the
##     distribution.
##   * Neither the name of Nokia Corporation and its Subsidiary(-ies) nor
##     the names of its contributors may be used to endorse or promote
##     products derived from this software without specific prior written
##     permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
## "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
## LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
## A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
## OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
## SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
## LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
## DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
## THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
## (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
## OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
## $QT_END_LICENSE$
##
#############################################################################


import math
import locale

from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtWidgets import (QApplication, QGridLayout, QLayout, QLineEdit,
        QSizePolicy, QToolButton, QWidget)
from PyQt6.QtGui import QKeyEvent, QGuiApplication

locale.setlocale(locale.LC_ALL, '')
_locale = locale.localeconv()
_decimal_point = _locale['decimal_point']
if _decimal_point == '':
    _decimal_point = '.'

_thousands_sep = _locale['thousands_sep']
if _thousands_sep == '':
    _thousands_sep = "'"

class Button(QToolButton):
    def __init__(self, text, parent=None):
        super(Button, self).__init__(parent)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setText(text)

    def sizeHint(self):
        size = super(Button, self).sizeHint()
        size.setHeight(size.height() + 20)
        size.setWidth(max(size.width(), size.height()))
        return size


class Calculator(QWidget):
    NumDigitButtons = 10
    
    def __init__(self, parent=None):
        super(Calculator, self).__init__(parent)

        self.pendingAdditiveOperator = ''
        self.pendingMultiplicativeOperator = ''

        self.sumInMemory = 0.0
        self.sumSoFar = 0.0
        self.factorSoFar = 0.0
        self.waitingForOperand = True

        self.display = QLineEdit('0')
        self.display.setReadOnly(True)
        self.display.setAlignment(Qt.AlignmentFlag.AlignRight)
        # maximum number of digit to display
        self.max_display_lenght = 20
        self.display.setMaxLength(self.max_display_lenght)

        font = self.display.font()
        font.setPointSize(font.pointSize() + 8)
        self.display.setFont(font)

        # from 0 to 9
        self.digitButtons = []
        
        for i in range(Calculator.NumDigitButtons):
            self.digitButtons.append(self.createButton(str(i),
                    self.digitClicked))

        # self.pointButton = self.createButton(".", self.pointClicked)
        self.pointButton = self.createButton(_decimal_point, self.pointClicked)
        self.changeSignButton = self.createButton(u"\N{PLUS-MINUS SIGN}",
                self.changeSignClicked)

        self.backspaceButton = self.createButton("Backspace",
                self.backspaceClicked)
        self.clearButton = self.createButton("Clear", self.clear)
        self.clearAllButton = self.createButton("Clear All", self.clearAll)

        self.clearMemoryButton = self.createButton("MC", self.clearMemory)
        self.readMemoryButton = self.createButton("MR", self.readMemory)
        self.setMemoryButton = self.createButton("MS", self.setMemory)
        self.addToMemoryButton = self.createButton("M+", self.addToMemory)

        self.divisionButton = self.createButton(u"\N{DIVISION SIGN}",
                self.multiplicativeOperatorClicked)
        self.timesButton = self.createButton(u"\N{MULTIPLICATION SIGN}",
                self.multiplicativeOperatorClicked)
        self.minusButton = self.createButton("-", self.additiveOperatorClicked)
        self.plusButton = self.createButton("+", self.additiveOperatorClicked)

        self.squareRootButton = self.createButton("Sqrt",
                self.unaryOperatorClicked)
        self.powerButton = self.createButton(u"x\N{SUPERSCRIPT TWO}",
                self.unaryOperatorClicked)
        self.reciprocalButton = self.createButton("1/x",
                self.unaryOperatorClicked)
        self.equalButton = self.createButton("=", self.equalClicked)

        mainLayout = QGridLayout()
        mainLayout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        mainLayout.addWidget(self.display, 0, 0, 1, 6)
        mainLayout.addWidget(self.backspaceButton, 1, 0, 1, 2)
        mainLayout.addWidget(self.clearButton, 1, 2, 1, 2)
        mainLayout.addWidget(self.clearAllButton, 1, 4, 1, 2)

        mainLayout.addWidget(self.clearMemoryButton, 2, 0)
        mainLayout.addWidget(self.readMemoryButton, 3, 0)
        mainLayout.addWidget(self.setMemoryButton, 4, 0)
        mainLayout.addWidget(self.addToMemoryButton, 5, 0)

        for i in range(1, Calculator.NumDigitButtons):
            # row = ((9 - i) / 3) + 2
            # column = ((i - 1) % 3) + 1
            row = int( ((9 - i) / 3) + 2 )
            column = int( ((i - 1) % 3) + 1 )
            mainLayout.addWidget(self.digitButtons[i], row, column)

        mainLayout.addWidget(self.digitButtons[0], 5, 1)
        mainLayout.addWidget(self.pointButton, 5, 2)
        mainLayout.addWidget(self.changeSignButton, 5, 3)

        mainLayout.addWidget(self.divisionButton, 2, 4)
        mainLayout.addWidget(self.timesButton, 3, 4)
        mainLayout.addWidget(self.minusButton, 4, 4)
        mainLayout.addWidget(self.plusButton, 5, 4)

        mainLayout.addWidget(self.squareRootButton, 2, 5)
        mainLayout.addWidget(self.powerButton, 3, 5)
        mainLayout.addWidget(self.reciprocalButton, 4, 5)
        mainLayout.addWidget(self.equalButton, 5, 5)
        self.setLayout(mainLayout)

        self.setWindowTitle("Calculator")
        self.installEventFilter(self)
    
    def eventFilter(self, obj, e):
        if isinstance(e, QKeyEvent):
            if e.key() == Qt.Key.Key_Backspace:
                self.backspaceButton.animateClick()
                return True
            elif e.modifiers() == Qt.KeyboardModifier.AltModifier:
                if e.key() == Qt.Key.Key_Delete:
                    self.clearAllButton.animateClick()
                    return True
            elif e.key() == Qt.Key.Key_Delete:
                self.clearButton.animateClick()
                return True
            #
            if e.type() == QEvent.Type.KeyPress:
                if e.key() == Qt.Key.Key_0:
                    self.digitButtons[0].animateClick()
                    return True
                elif e.key() == Qt.Key.Key_1:
                    self.digitButtons[1].animateClick()
                    return True
                elif e.key() == Qt.Key.Key_2:
                    self.digitButtons[2].animateClick()
                    return True
                elif e.key() == Qt.Key.Key_3:
                    self.digitButtons[3].animateClick()
                    return True
                elif e.key() == Qt.Key.Key_4:
                    self.digitButtons[4].animateClick()
                    return True
                elif e.key() == Qt.Key.Key_5:
                    self.digitButtons[5].animateClick()
                    return True
                elif e.key() == Qt.Key.Key_6:
                    self.digitButtons[6].animateClick()
                    return True
                elif e.key() == Qt.Key.Key_7:
                    self.digitButtons[7].animateClick()
                    return True
                elif e.key() == Qt.Key.Key_8:
                    self.digitButtons[8].animateClick()
                    return True
                elif e.key() == Qt.Key.Key_9:
                    self.digitButtons[9].animateClick()
                    return True
                elif e.key() == Qt.Key.Key_Return or e.key() == Qt.Key.Key_Enter:
                    self.equalButton.animateClick()
                    return True
                elif e.key() == Qt.Key.Key_Plus:
                    self.plusButton.animateClick()
                    return True
                elif e.key() == Qt.Key.Key_Minus:
                    self.minusButton
                    return True
                elif e.key() == Qt.Key.Key_Asterisk:
                    self.timesButton.animateClick()
                    return True
                elif e.key() == Qt.Key.Key_Slash:
                    self.divisionButton.animateClick()
                    return True
                elif e.key() == Qt.Key.Key_Period:
                    self.pointButton.animateClick()
                    return True
                elif e.key() == Qt.Key.Key_Comma:
                    self.pointButton.animateClick()
                    return True
        return super().eventFilter(obj, e)
        
    def digitClicked(self):
        clickedButton = self.sender()
        digitValue = int(clickedButton.text())
        
        if self.display.text() == '0' and digitValue == 0.0:
            return

        if self.waitingForOperand:
            self.display.clear()
            self.waitingForOperand = False

        self.display.setText(self.display.text() + str(digitValue))

    def unaryOperatorClicked(self):
        clickedButton = self.sender()
        clickedOperator = clickedButton.text()
        try:
            # operand = float(self.display.text())
            operand = float(self.display.text().replace(_decimal_point,'.'))
        except:
            return
        if clickedOperator == "Sqrt":
            if operand < 0.0:
                self.abortOperation()
                return

            result = math.sqrt(operand)
            if str(result).endswith(".0"):
                result = int(result)
        elif clickedOperator == u"x\N{SUPERSCRIPT TWO}":
            result = math.pow(operand, 2.0)
            if str(result).endswith(".0"):
                result = int(result)
        elif clickedOperator == "1/x":
            if operand == 0.0:
                self.abortOperation()
                return

            result = 1.0 / operand

        # self.display.setText(str(result))
        # self.display.setText(str(result).replace('.',_decimal_point))
        
        result = "{:.18f}".format(float(result))
        _text = str(result).replace('.', _decimal_point)
        if _text == "0" + _decimal_point + (self.max_display_lenght-2)*"0":
            _text = "0" + _decimal_point + (self.max_display_lenght-3)*"0" + "1"
        self.display.setText(_text)
        
        self.waitingForOperand = True

    def additiveOperatorClicked(self):
        clickedButton = self.sender()
        clickedOperator = clickedButton.text()
        
        try:
            # operand = float(self.display.text())
            operand = float(self.display.text().replace(_decimal_point,'.'))
        except:
            return
        
        _text = "{:.18f}".format(float(operand))
        if _text == "0." + (self.max_display_lenght-2)*"0":
            _text = "0." + (self.max_display_lenght-3)*"0" + "1"
        operand = float(_text)
        
        if self.pendingMultiplicativeOperator:
            if not self.calculate(operand, self.pendingMultiplicativeOperator):
                self.abortOperation()
                return

            # self.display.setText(str(self.factorSoFar))
            self.display.setText(str(self.factorSoFar).replace('.',_decimal_point))
            operand = self.factorSoFar
            self.factorSoFar = 0.0
            self.pendingMultiplicativeOperator = ''

        if self.pendingAdditiveOperator:
            if not self.calculate(operand, self.pendingAdditiveOperator):
                self.abortOperation()
                return

            # self.display.setText(str(self.sumSoFar))
            self.display.setText(str(self.sumSoFar).replace('.',_decimal_point))
        else:
            self.sumSoFar = operand

        self.pendingAdditiveOperator = clickedOperator
        self.waitingForOperand = True

    def multiplicativeOperatorClicked(self):
        clickedButton = self.sender()
        clickedOperator = clickedButton.text()
        try:
            # operand = float(self.display.text())
            operand = float(self.display.text().replace(_decimal_point,'.'))
        except:
            return
        
        if self.pendingMultiplicativeOperator:
            if not self.calculate(operand, self.pendingMultiplicativeOperator):
                self.abortOperation()
                return

            self.display.setText(str(self.factorSoFar))
        else:
            self.factorSoFar = operand

        self.pendingMultiplicativeOperator = clickedOperator
        self.waitingForOperand = True

    def equalClicked(self):
        self.display.text().replace(_decimal_point,'.')
        try:
            # operand = float(self.display.text())
            operand = float(self.display.text().replace(_decimal_point,'.'))
        except:
            return
            
        if self.pendingMultiplicativeOperator:
            if not self.calculate(operand, self.pendingMultiplicativeOperator):
                self.abortOperation()
                return
            
            operand = self.factorSoFar
            
            if str(operand).endswith(".0"):
                operand = int(operand)
            
            self.factorSoFar = 0.0
            self.pendingMultiplicativeOperator = ''

        if self.pendingAdditiveOperator:
            if not self.calculate(operand, self.pendingAdditiveOperator):
                self.abortOperation()
                return

            self.pendingAdditiveOperator = ''
        else:
            self.sumSoFar = operand
        
        if str(self.sumSoFar).endswith(".0"):
            self.sumSoFar = int(self.sumSoFar)
        
        self.sumSoFar = "{:.18f}".format(float(self.sumSoFar))
        # self.display.setText(str(self.sumSoFar))
        # self.display.setText(str(self.sumSoFar).replace('.', _decimal_point))
        _text = str(self.sumSoFar).replace('.', _decimal_point)
        if _text == "0" + _decimal_point + (self.max_display_lenght-2)*"0":
            _text = "0" + _decimal_point + (self.max_display_lenght-3)*"0" + "1"
        self.display.setText(_text)
        
        self.sumSoFar = 0.0
        self.waitingForOperand = True

    def pointClicked(self):
        if self.waitingForOperand:
            self.display.setText('0')

        # if "." not in self.display.text():
            # self.display.setText(self.display.text() + ".")
        if _decimal_point not in self.display.text():
            self.display.setText(self.display.text() + _decimal_point)
            
        self.waitingForOperand = False

    def changeSignClicked(self):
        text = self.display.text()
        # text = self.display.text().replace(_decimal_point,'.')
        value = float(text)

        if value > 0.0:
            text = "-" + text
        elif value < 0.0:
            text = text[1:]

        self.display.setText(text)

    def backspaceClicked(self):
        if self.waitingForOperand:
            return
        
        text = self.display.text()[:-1]
        # text = self.display.text().replace(_decimal_point,'.')[:-1]
        if not text:
            text = '0'
            self.waitingForOperand = True

        self.display.setText(text)

    def clear(self):
        if self.waitingForOperand:
            return

        self.display.setText('0')
        self.waitingForOperand = True

    def clearAll(self):
        self.sumSoFar = 0.0
        self.factorSoFar = 0.0
        self.pendingAdditiveOperator = ''
        self.pendingMultiplicativeOperator = ''
        self.display.setText('0')
        self.waitingForOperand = True

    def clearMemory(self):
        self.sumInMemory = 0.0

    def readMemory(self):
        if '.'in str(self.sumInMemory):
            self.display.setText(str(self.sumInMemory).replace('.', _decimal_point))
        # self.display.setText(str(self.sumInMemory))
        self.waitingForOperand = True

    def setMemory(self):
        self.equalClicked()
        self.sumInMemory = float(self.display.text())

    def addToMemory(self):
        self.equalClicked()
        if _decimal_point in self.display.text():
            _ret = self.display.text().replace(_decimal_point,'.')
            self.sumInMemory += float(ret)
        else:
            self.sumInMemory += float(self.display.text())

    def createButton(self, text, member):
        button = Button(text)
        button.clicked.connect(member)
        return button

    def abortOperation(self):
        self.clearAll()
        self.display.setText("####")

    def calculate(self, rightOperand, pendingOperator):
        if pendingOperator == "+":
            self.sumSoFar += rightOperand
            
        elif pendingOperator == "-":
            self.sumSoFar -= rightOperand
        elif pendingOperator == u"\N{MULTIPLICATION SIGN}":
            self.factorSoFar *= rightOperand
        elif pendingOperator == u"\N{DIVISION SIGN}":
            if rightOperand == 0.0:
                return False
            
            self.factorSoFar /= rightOperand

        return True


if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)
    QGuiApplication.setDesktopFileName("qtqalc1")
    calc = Calculator()
    calc.show()
    sys.exit(app.exec())
