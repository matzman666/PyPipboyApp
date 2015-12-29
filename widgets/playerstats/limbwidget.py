# -*- coding: utf-8 -*-
import os
from PyQt5 import QtCore, QtWidgets, QtGui, uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from widgets import widgets

# WIDGET CLASS
class LimbWidget(widgets.WidgetBase):
    _signalInfoUpdated = QtCore.pyqtSignal()
    
    # CLASS INIT
    def __init__(self, mhandle, parent):
        super().__init__('Limb Status', parent)
        self.widget = uic.loadUi(os.path.join(mhandle.basepath, 'ui', 'limbwidget.ui'))
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
        self.StatsData = rootObject.child("Stats")

        # We want to track Stats data down to its base level
        if self.StatsData:
            self.StatsData.registerValueUpdatedListener(self.DataUpdated, 1)

        # Update Widget information
        self._signalInfoUpdated.emit()

    # DATA IN THE MANAGER HAS CHANGED
    def DataUpdated(self, caller, value, pathObjs):
        # Update UI
        self._signalInfoUpdated.emit()
    
    # UPDATE UI ELEMENTS
    @QtCore.pyqtSlot()
    def UpdateUI(self):
        if self.StatsData.childCount():
            self.widget.headStatus.setValue(self.StatsData.child("HeadCondition").value())
            self.widget.bodyStatus.setValue(self.StatsData.child("TorsoCondition").value())
            self.widget.leftarmStatus.setValue(self.StatsData.child("LArmCondition").value())
            self.widget.rightarmStatus.setValue(self.StatsData.child("RArmCondition").value())
            self.widget.leftlegStatus.setValue(self.StatsData.child("LLegCondition").value())
            self.widget.rightlegStatus.setValue(self.StatsData.child("RLegCondition").value())
 