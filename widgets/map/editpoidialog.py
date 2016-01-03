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
        uic.loadUi(os.path.join(self.basepath, 'ui', 'editpoimarker.ui'), self)
        if (color == None):
            self.selectedColor = QtCore.Qt.black
        else:
            self.selectedColor = color
            
        self.Icons = [
            PipboyIcon("mapmarkerpoi_1.svg", self.gvIconPreview_1, 28, "preview"),
            PipboyIcon("Target.svg", self.gvIconPreview_2, 28, "preview"),
            PipboyIcon("Warning.svg", self.gvIconPreview_3, 28, "preview"),
            PipboyIcon("Shield.svg", self.gvIconPreview_4, 28, "preview"),
            PipboyIcon("StarEmpty.svg", self.gvIconPreview_5, 28, "preview"),
            PipboyIcon("StarFilled.svg", self.gvIconPreview_6, 28, "preview")
        ]
            
        for i in self.Icons:
            i.Color = self.selectedColor 
            i.BGColor = QtCore.Qt.transparent
            i.Update()

        self.IconFile = self.Icons[0].FileName
        self.signalSetColor.connect(self.setColor)        
        self.btnColor.clicked.connect(self._slotPOIColorSelectionTriggered)
        self.rdoIcon_1.toggled.connect(self.iconSelectionChanged)
        self.rdoIcon_2.toggled.connect(self.iconSelectionChanged)
        self.rdoIcon_3.toggled.connect(self.iconSelectionChanged)
        self.rdoIcon_4.toggled.connect(self.iconSelectionChanged)
        self.rdoIcon_5.toggled.connect(self.iconSelectionChanged)
        self.rdoIcon_6.toggled.connect(self.iconSelectionChanged)

    def setSelectedIcon(self, iconname):
        count = 1
        for i in self.Icons:
            #print ('rdoIcon_'+str(count))
            if i.FileName == iconname:
                print ('matched')
                rdo = getattr(self, 'rdoIcon_'+str(count))
                rdo.setChecked(True)
                return
            count +=1
        
    @QtCore.pyqtSlot(bool)        
    def iconSelectionChanged(self, value):
        if (value):
            if self.rdoIcon_1.isChecked():
                self.IconFile = self.Icons[0].FileName
            elif self.rdoIcon_2.isChecked():
                self.IconFile = self.Icons[1].FileName
            elif self.rdoIcon_3.isChecked():
                self.IconFile = self.Icons[2].FileName
            elif self.rdoIcon_4.isChecked():
                self.IconFile = self.Icons[3].FileName
            elif self.rdoIcon_5.isChecked():
                self.IconFile = self.Icons[4].FileName
            elif self.rdoIcon_6.isChecked():
                self.IconFile = self.Icons[5].FileName
        
        
    @QtCore.pyqtSlot()        
    def _slotPOIColorSelectionTriggered(self):
        print ('in btn handler')
        color = QtWidgets.QColorDialog.getColor(self.selectedColor, self)
        if color.isValid:
            self.selectedColor = color
            self.signalSetColor.emit(color)
            
    @QtCore.pyqtSlot(QtGui.QColor)
    def setColor(self, color, update = True):
        print ('in set color')
        for i in self.Icons:
            i.Color = color
            i.Update() 
