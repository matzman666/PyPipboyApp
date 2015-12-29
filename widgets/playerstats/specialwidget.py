# -*- coding: utf-8 -*-
import os
from PyQt5 import QtCore, QtWidgets, QtGui, uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from widgets import widgets

# WIDGET CLASS
class SpecialWidget(widgets.WidgetBase):
    _signalInfoUpdated = QtCore.pyqtSignal()
    
    # CLASS INIT
    def __init__(self, mhandle, parent):
        super().__init__('S P E C I A L', parent)
        self.widget = uic.loadUi(os.path.join(mhandle.basepath, 'ui', 'specialwidget.ui'))
        self.setWidget(self.widget)
        self._signalInfoUpdated.connect(self.UpdateUI)
    
    # QT INIT
    def init(self, app, datamanager):
        super().init(app, datamanager)
        
        # Create a class level hook to the datamanager for updates and RPC methods
        self.dataManager = datamanager
        self.dataManager.registerRootObjectListener(self.DataManagerUpdated)
    
    # DATA MANAGER OBJECT HAS CHANGED AT SOME LEVEL
    def DataManagerUpdated(self, rootObject):
        # Create a class level hook to the data we are using
        self.SpecialData = rootObject.child("Special")
        
        # We want to track Special data down to its base level
        if self.SpecialData:
            self.SpecialData.registerValueUpdatedListener(self.DataUpdated, 2)
        
        # Update Widget information
        self._signalInfoUpdated.emit()

    # DATA IN THE MANAGER HAS CHANGED
    def DataUpdated(self, caller, value, pathObjs):
        # Update UI
        self._signalInfoUpdated.emit()
    
    # UPDATE UI ELEMENTS
    @QtCore.pyqtSlot()
    def UpdateUI(self):
        if self.SpecialData.childCount():
            for i in range(0, self.SpecialData.childCount()):
                Name = self.SpecialData.child(i).child("Name").value()
                Description = self.SpecialData.child(i).child("Description").value()
                Total = self.SpecialData.child(i).child("Value").value()
                Modifier = self.SpecialData.child(i).child("Modifier").value()
                Base = Total - Modifier
                
                TitleLabel = self.findChild(QtWidgets.QLabel, "titleS" + str(i + 1) + "Label")
                TitleLabel.setText(Name)
                TitleLabel.setToolTip(Description)
                
                BaseLabel = self.findChild(QtWidgets.QLabel, "baseS" + str(i + 1) + "Label")
                BaseLabel.setText(str(Base))
                
                ModLabel = self.findChild(QtWidgets.QLabel, "modS" + str(i + 1) + "Label")
                ModLabel.setText(str(Modifier))
                
                TotalLabel = self.findChild(QtWidgets.QLabel, "totalS" + str(i + 1) + "Label")
                TotalLabel.setText(str(Total))