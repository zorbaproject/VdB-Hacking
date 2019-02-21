#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide2.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QLabel
from PySide2.QtWidgets import QGraphicsScene
from PySide2.QtGui import QPixmap
from PySide2.QtWidgets import QMessageBox
from PySide2.QtCore import QFile
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QTableWidget
from PySide2.QtWidgets import QTableWidgetItem
from PySide2.QtWidgets import QTreeWidget
from PySide2.QtWidgets import QTreeWidgetItem
from PySide2.QtWidgets import QInputDialog

import re
import sys
import os

from forms import progress


class Form(QDialog):
    def __init__(self, mainwindow, parent=None):
        super(Form, self).__init__(parent)
        file = QFile(os.path.abspath(os.path.dirname(sys.argv[0]))+"/forms/alberofrasi.ui")
        file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.w = loader.load(file)
        layout = QVBoxLayout()
        layout.addWidget(self.w)
        self.setLayout(layout)
        self.w.accepted.connect(self.isaccepted)
        self.w.rejected.connect(self.isrejected)
        self.w.next.clicked.connect(self.next)
        self.w.prev.clicked.connect(self.prev)
        self.w.frase.valueChanged.connect(self.openphrase)
        self.setWindowTitle("Visualizza albero delle frasi")
        self.mycorpus = mainwindow.w.corpus
        self.corpuscols = mainwindow.corpuscols
        self.mainwindow = mainwindow
        self.setphraseRange()
        self.setcss()
        self.openphrase(0)

    def isaccepted(self):
        self.accept()
    def isrejected(self):
        self.reject()

    def setcss(self):
        css = ""
        css = css + "QTreeView::branch:has-siblings:!adjoins-item {\n"
        css = css + "border-image: url("+os.path.abspath(os.path.dirname(sys.argv[0]))+"/icons/stylesheet-vline.png) 0;\n"
        css = css + "}\n"
        css = css + "QTreeView::branch:has-siblings:adjoins-item {\n"
        css = css + "border-image: url("+os.path.abspath(os.path.dirname(sys.argv[0]))+"/icons/stylesheet-branch-more.png) 0;\n"
        css = css + "}\n"
        css = css + "QTreeView::branch:!has-children:!has-siblings:adjoins-item {\n"
        css = css + "border-image: url("+os.path.abspath(os.path.dirname(sys.argv[0]))+"/icons/stylesheet-branch-end.png) 0;\n"
        css = css + "}\n"
        css = css + "QTreeView::branch:has-children:!has-siblings:closed,\n"
        css = css + "QTreeView::branch:closed:has-children:has-siblings {\n"
        css = css + "border-image: none;\n"
        css = css + "image: url("+os.path.abspath(os.path.dirname(sys.argv[0]))+"/icons/stylesheet-branch-closed.png);\n"
        css = css + "}\n"
        css = css + "QTreeView::branch:open:has-children:!has-siblings,\n"
        css = css + "QTreeView::branch:open:has-children:has-siblings  {\n"
        css = css + "border-image: none;\n"
        css = css + "image: url("+os.path.abspath(os.path.dirname(sys.argv[0]))+"/icons/stylesheet-branch-open.png);\n"
        css = css + "}"
        self.w.treeWidget.setStyleSheet(css)

    def setphraseRange(self):
        IDphrase = -1
        for crow in range(self.mycorpus.rowCount()):
            if int(self.mycorpus.item(crow, self.corpuscols["IDphrase"]).text()) > IDphrase:
                IDphrase = int(self.mycorpus.item(crow, self.corpuscols["IDphrase"]).text())
        self.w.frase.setMinimum(0)
        self.w.frase.setMaximum(IDphrase)

    def next(self):
        v = self.w.frase.value()
        self.w.frase.setValue(v+1)

    def prev(self):
        v = self.w.frase.value()
        self.w.frase.setValue(v-1)

    def openphrase(self, arg1):
        self.w.treeWidget.clear()
        startrow = self.mainwindow.finditemincolumn(str(arg1), self.corpuscols["IDphrase"])
        endrow = startrow
        if startrow >= 0:
            self.Progrdialog = progress.Form(self.w)
            #self.Progrdialog.show()
            row = startrow
            words = {}
            gov = {}
            root = ""
            nsubj = ""
            totallines = self.mycorpus.rowCount()
            try:
                while self.mycorpus.item(row,self.corpuscols["IDphrase"]).text() == str(arg1):
                    endrow = row
                    self.Progrdialog.w.testo.setText("Sto leggendo la riga numero "+str(row))
                    self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                    QApplication.processEvents()
                    if self.Progrdialog.w.annulla.isChecked():
                        return
                    idparola = self.mycorpus.item(row,self.corpuscols["IDword"]).text()
                    parolagov = self.mycorpus.item(row,self.corpuscols["governor"]).text()
                    words[idparola] = str(row)
                    try:
                        gov[parolagov].append(idparola)
                    except:
                        gov[parolagov] = [idparola]
                    if self.mycorpus.item(row,self.corpuscols["dep"]).text() == "ROOT":
                        root = idparola
                    row = row + 1
            except:
                row = 0
            phtext = self.mainwindow.rebuildText(self.mycorpus, self.Progrdialog, self.corpuscols['Orig'], [], startrow, endrow+1)
            self.w.fraseLabel.setText(phtext)
            rootitem = QTreeWidgetItem(self.w.treeWidget)
            rootitem.setText(0,self.mycorpus.item(int(words[root]),self.corpuscols["Orig"]).text())
            rootitem.setText(1,self.mycorpus.item(int(words[root]),self.corpuscols["dep"]).text())
            rootitem.setText(2,self.mycorpus.item(int(words[root]),self.corpuscols["IDword"]).text())
            rootitem.setText(3,words[root])
            rootitem.setExpanded(True)
            active = True
            dipendenti = [root]
            olditems = [rootitem]
            livelli = 0
            tmplevels = 0
            while active:
                newitems = []
                newdipendenti = []
                tmplevels = tmplevels + 1
                for pi in range(len(dipendenti)):
                    parolagov = dipendenti[pi]
                    if not parolagov in gov:
                        continue
                    for elem in gov[parolagov]:
                        tritem = QTreeWidgetItem(olditems[pi])
                        tritem.setText(0,self.mycorpus.item(int(words[elem]),self.corpuscols["Orig"]).text())
                        tritem.setText(1,self.mycorpus.item(int(words[elem]),self.corpuscols["dep"]).text())
                        tritem.setText(2,self.mycorpus.item(int(words[elem]),self.corpuscols["IDword"]).text())
                        tritem.setText(3,words[elem])
                        tritem.setExpanded(True)
                        newdipendenti.append(elem)
                        newitems.append(tritem)
                olditems = newitems
                dipendenti = newdipendenti
                if tmplevels > livelli:
                    livelli = tmplevels
                if len(dipendenti)==0:
                    active = False
            self.Progrdialog.accept()
            for i in range(self.w.treeWidget.columnCount()):
                self.w.treeWidget.resizeColumnToContents(i)
            ampiezza = 0
            for governor in gov:
                if len(gov[governor]) > ampiezza:
                    ampiezza = len(gov[governor])
            self.w.ampiezza.setText(str(ampiezza))
            self.w.livelli.setText(str(livelli))