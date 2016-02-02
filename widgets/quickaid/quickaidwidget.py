# -*- coding: utf-8 -*-
import os
from PyQt5 import QtCore, uic
from widgets import widgets

class QuickAidWidget(widgets.WidgetBase):
    UIUpdateSignal = QtCore.pyqtSignal()
    
    Widgets = None
    
    DataManager = None
    StatsData = None
    
    # CLASS INIT
    def __init__(self, mhandle, parent):
        super().__init__('Quick Aid', parent)
        
        self.Widgets = uic.loadUi(os.path.join(mhandle.basepath, 'ui', 'quickaidwidget.ui'))
        self.setWidget(self.Widgets)
        
        self.UIUpdateSignal.connect(self.UpdateUI)
        
        self.Widgets.stimpakButton.clicked.connect(self.StimpakButtonClicked)
        self.Widgets.radawayButton.clicked.connect(self.RadAwayButtonClicked)

    # QT INIT
    def init(self, app, dataManager):
        super().init(app, dataManager)

        self.DataManager = dataManager
        self.DataManager.registerRootObjectListener(self.DataManagerUpdated)
        
    def getMenuCategory(self):
        return 'Player Status'
        
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
    def StimpakButtonClicked(self):
        # Apparently need to do this because it raises a no items exception
        if self.StatsData:
            Stimpaks = self.StatsData.child("StimpakCount").value()
            
            if Stimpaks > 0:
                self.DataManager.rpcUseStimpak()
    
    @QtCore.pyqtSlot()
    def RadAwayButtonClicked(self):
        # Apparently need to do this because it raises a no items exception
        if self.StatsData:
            Radaways = self.StatsData.child("RadawayCount").value()
            
            if Radaways > 0:
                self.DataManager.rpcUseRadAway()
    
    @QtCore.pyqtSlot()
    def UpdateUI(self):
        if self.isVisible():
            if self.StatsData:
                Stimpaks = self.StatsData.child("StimpakCount").value()
                Radaways = self.StatsData.child("RadawayCount").value()
                
                if Stimpaks > 0:
                    self.Widgets.stimpakButton.setEnabled(True)
                else:
                    self.Widgets.stimpakButton.setEnabled(False)
                
                if Radaways > 0:
                    self.Widgets.radawayButton.setEnabled(True)
                else:
                    self.Widgets.radawayButton.setEnabled(False)
                    
                self.Widgets.stimpakButton.setText("STIMPAK (" + str(Stimpaks) + ")")
                self.Widgets.radawayButton.setText("RADAWAY (" + str(Radaways) + ")")