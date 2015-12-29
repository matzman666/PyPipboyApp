# -*- coding: utf-8 -*-
import os
from PyQt5 import QtCore, uic
from widgets import widgets

class QuickAidWidget(widgets.WidgetBase):
    UIUpdateSignal = QtCore.pyqtSignal()
    
    # CLASS INIT
    def __init__(self, mhandle, parent):
        super().__init__('Quick Aid', parent)
        
        self.widget = uic.loadUi(os.path.join(mhandle.basepath, 'ui', 'quickaidwidget.ui'))
        self.setWidget(self.widget)
        
        self.UIUpdateSignal.connect(self.UpdateUI)

    # QT INIT
    def init(self, app, datamanager):
        super().init(app, datamanager)
        
        # Create a class level hook to the datamanager for updates and RPC methods
        self.dataManager = datamanager
        self.dataManager.registerRootObjectListener(self.DataManagerUpdated)
        
        # Connect click events to the buttons
        self.widget.stimpakButton.clicked.connect(self.StimpakButtonClicked)
        self.widget.radawayButton.clicked.connect(self.RadAwayButtonClicked)
        
    # DATA MANAGER OBJECT HAS CHANGED AT SOME LEVEL
    def DataManagerUpdated(self, rootObject):
        self.StatsData = rootObject.child("Stats")
        
        if self.StatsData:
            self.StatsData.registerValueUpdatedListener(self.StatsDataUpdated, 1)
        
        self.UIUpdateSignal.emit()
        
    # STATS DATA UPDATED
    def StatsDataUpdated(self, caller, value, pathObjs):
        self.UIUpdateSignal.emit()
    
    @QtCore.pyqtSlot()
    def UpdateUI(self):
        if self.StatsData.childCount():
            Stimpaks = self.StatsData.child("StimpakCount").value()
            Radaways = self.StatsData.child("RadawayCount").value()
            
            if Stimpaks > 0:
                self.widget.stimpakButton.setEnabled(True)
            else:
                self.widget.stimpakButton.setEnabled(False)
            
            if Radaways > 0:
                self.widget.radawayButton.setEnabled(True)
            else:
                self.widget.radawayButton.setEnabled(False)
                
            self.widget.stimpakButton.setText("STIMPAK (" + str(Stimpaks) + ")")
            self.widget.radawayButton.setText("RADAWAY (" + str(Radaways) + ")")
    
    @QtCore.pyqtSlot()
    def StimpakButtonClicked(self):
        # Apparently need to do this because it raises a no items exception
        if self.StatsData:
            Stimpaks = self.StatsData.child("StimpakCount").value()
            
            if Stimpaks > 0:
                self.dataManager.rpcUseStimpak()
    
    @QtCore.pyqtSlot()
    def RadAwayButtonClicked(self):
        # Apparently need to do this because it raises a no items exception
        if self.StatsData:
            Radaways = self.StatsData.child("RadawayCount").value()
            
            if Radaways > 0:
                self.dataManager.rpcUseRadAway()
        