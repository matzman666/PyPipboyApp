import os
from PyQt5 import QtCore, QtWidgets, QtGui, uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from widgets import widgets

# WIDGET CLASS
class LimbWidget(widgets.WidgetBase):
    UIUpdateSignal = QtCore.pyqtSignal()
    
    Widgets = None
    
    DataManager = None
    StatsData = None
    
    # CLASS INIT
    def __init__(self, mhandle, parent):
        super().__init__('Limb Status', parent)
        self.Widgets = uic.loadUi(os.path.join(mhandle.basepath, 'ui', 'limbwidget.ui'))
        self.setWidget(self.Widgets)
        
        self.UIUpdateSignal.connect(self.UpdateUI)
    
    # QT INIT
    def init(self, app, dataManager):
        super().init(app, dataManager)
        
        # Create a class level hook to the datamanager for updates and RPC methods
        self.DataManager = dataManager
        self.DataManager.registerRootObjectListener(self.DataManagerUpdated)
        
    def getMenuCategory(self):
        return 'Player Status'
    
    # DATA MANAGER OBJECT HAS CHANGED AT SOME LEVEL
    def DataManagerUpdated(self, rootObject):
        # Create a class level hook to the data we are using
        self.StatsData = rootObject.child("Stats")

        # We want to track Stats data down to its base level
        if self.StatsData:
            self.StatsData.registerValueUpdatedListener(self.StatsDataUpdated, 1)

        # Update Widget information
        self.UIUpdateSignal.emit()

    # DATA IN THE MANAGER HAS CHANGED
    def StatsDataUpdated(self, caller, value, pathObjs):
        self.UIUpdateSignal.emit()
    
    # UPDATE UI ELEMENTS
    @QtCore.pyqtSlot()
    def UpdateUI(self):
        if self.isVisible():
            if self.StatsData:
                if self.StatsData.childCount():
                    self.Widgets.headStatus.setValue(self.StatsData.child("HeadCondition").value())
                    self.Widgets.bodyStatus.setValue(self.StatsData.child("TorsoCondition").value())
                    self.Widgets.leftarmStatus.setValue(self.StatsData.child("LArmCondition").value())
                    self.Widgets.rightarmStatus.setValue(self.StatsData.child("RArmCondition").value())
                    self.Widgets.leftlegStatus.setValue(self.StatsData.child("LLegCondition").value())
                    self.Widgets.rightlegStatus.setValue(self.StatsData.child("RLegCondition").value())