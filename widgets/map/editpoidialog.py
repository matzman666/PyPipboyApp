import os
from PyQt5 import QtWidgets, QtCore, QtGui, uic, QtSvg
from widgets.shared.graphics import ImageFactory
from widgets import widgets
from widgets.shared import settings
from widgets.shared.PipboyIcon import PipboyIcon

class EditPOIDialog(QtWidgets.QDialog):

    signalSetColor = QtCore.pyqtSignal(QtGui.QColor)
    def __init__(self, parent=None, color=None):
        super().__init__(parent)
        self.basepath = os.path.join("widgets", "map")
        uic.loadUi(os.path.join(self.basepath, 'ui', 'editpoidialog.ui'), self)

        if (color == None):
            self.selectedColor = QtCore.Qt.black
        else:
            self.selectedColor = color
        
        iconFiles = [
            "mapmarkerpoi_1.svg",
            "Target.svg",
            "Warning.svg",
            "Shield.svg",
            "StarEmpty.svg",
            "StarFilled.svg"
        ]
        self.Icons = []

        icondir = os.path.join(self.basepath, os.pardir, 'shared', 'res') 
        for filename in os.listdir(icondir):
         if os.path.isfile(os.path.join(icondir,filename)):
             if filename.find('poi_') == 0:
                 iconFiles.append(filename)

        numitems = len(iconFiles)
        itemsperrow = 6
        rows = numitems/itemsperrow
        row = 0
        col = 0
        for i in range(0, numitems):
            gv = QtWidgets.QGraphicsView()
            gv.setObjectName('gvIconPreview_'+str(i))
            gv.setFixedSize(28,28)
            gv.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            gv.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            rdo = QtWidgets.QRadioButton()
            rdo.setObjectName('rdoIcon_'+str(i))
            rdo.toggled.connect(self.iconSelectionChanged)
            self.gridLayout.addWidget(gv, row, col, 1, 1)
            self.gridLayout.addWidget(rdo, row, col+1, 1, 1)
            
            pi = PipboyIcon(iconFiles[i], gv, 28)
            self.Icons.append(pi)
            pi.Color = self.selectedColor 
            pi.BGColor = QtCore.Qt.transparent
            pi.Update()

            col += 2
            if col >= itemsperrow*2:
                col = 0
                row += 1

        self.IconFile = self.Icons[0].FileName
        self.signalSetColor.connect(self.setColor)        
        self.btnColor.clicked.connect(self._slotPOIColorSelectionTriggered)
        
        rdo = self.findChild(QtWidgets.QRadioButton, 'rdoIcon_0')
        rdo.setChecked(True)
        
    def setSelectedIcon(self, iconname):
        count = 0
        for i in self.Icons:
            if i.FileName == iconname:
                rdo = self.findChild(QtWidgets.QRadioButton, 'rdoIcon_'+str(count))
                rdo.setChecked(True)
                return
            count +=1
        
    @QtCore.pyqtSlot(bool)        
    def iconSelectionChanged(self, value):
        if (value):
            count = 0
            for i in self.Icons:
                rdo = self.findChild(QtWidgets.QRadioButton, 'rdoIcon_'+str(count))
                if rdo.isChecked():
                    self.IconFile = self.Icons[count].FileName
                    return
                count +=1
        
    @QtCore.pyqtSlot()        
    def _slotPOIColorSelectionTriggered(self):
        color = QtWidgets.QColorDialog.getColor(self.selectedColor, self)
        if color.isValid():
            self.selectedColor = color
            self.signalSetColor.emit(color)
            
    @QtCore.pyqtSlot(QtGui.QColor)
    def setColor(self, color, update = True):
        for i in self.Icons:
            i.Color = color
            i.Update() 
