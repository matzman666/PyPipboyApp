import os
from PyQt5 import QtCore, QtGui, uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from widgets import widgets

class GameStatsWidget(widgets.WidgetBase):
    SectionsListSignal = QtCore.pyqtSignal()
    StatsListSignal = QtCore.pyqtSignal()
    SectionsListModel = QStandardItemModel()
    StatsListModel = QStandardItemModel()
    
    DataManager = None
    SectionsData = None
    StatsData = None
    
    SelectedSectionId = -1
    
    def __init__(self, mhandle, parent):
        super().__init__("Game Statistics", parent)
        
        self.widget = uic.loadUi(os.path.join(mhandle.basepath, "ui", "gamestatswidget.ui"))
        self.setWidget(self.widget)
        
        self.SectionsListSignal.connect(self.UpdateSectionsList)
        self.StatsListSignal.connect(self.UpdateStatsList)
    
    def init(self, app, dataManager):
        super().init(app, dataManager)
        
        self.DataManager = dataManager
        self.DataManager.registerRootObjectListener(self.DataManagerUpdated)
        
        self.widget.sectionsList.clicked.connect(self.SectionsListClicked)
    
    def DataManagerUpdated(self, rootObject):
        self.SectionsData = rootObject.child("Log")
        
        if self.SectionsData:
            self.SectionsData.registerValueUpdatedListener(self.SectionsDataUpdated, 2)
        
        if self.SelectedSectionId == -1:
            self.SetSectionId(0)
        
        self.SectionsListSignal.emit()
        self.StatsListSignal.emit()
    
    def SectionsDataUpdated(self, caller, value, pathObjs):
        self.SectionsListSignal.emit()
    
    def StatsDataUpdated(self, called, value, pathObjs):
        self.StatsListSignal.emit()
        
    def SetSectionId(self, sectionId):
        self.SelectedSectionId = sectionId
        
        if self.SectionsData.childCount():
            if self.StatsData:
                self.StatsData.unregisterValueUpdatedListener(self.StatsDataUpdated)
            
            self.StatsData = self.SectionsData.child(self.SelectedSectionId).child("statArray")
            self.StatsData.registerValueUpdatedListener(self.StatsDataUpdated, 2)
        
        self.StatsListSignal.emit()

    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def SectionsListClicked(self, index):
        ClickedIndex = self.SectionsListModel.index(index.row(), 0)
        DataId = int(self.SectionsListModel.data(ClickedIndex))
        
        self.SetSectionId(DataId)
    
    @QtCore.pyqtSlot()
    def UpdateSectionsList(self):
        self.SectionsListModel.clear()
        
        if self.SectionsData:
            for i in range(0, self.SectionsData.childCount()):
                Text = self.SectionsData.child(i).child("text").value()
                Text = Text[1:]
                
                ListItem = [
                    QStandardItem(str(i)),
                    QStandardItem(Text)
                ]
                self.SectionsListModel.appendRow(ListItem)
            
            self.widget.sectionsList.setModel(self.SectionsListModel)
            self.widget.sectionsList.hideColumn(0)
    
    @QtCore.pyqtSlot()
    def UpdateStatsList(self):
        self.StatsListModel.clear()
        
        if self.StatsData:
            for i in range(0, self.StatsData.childCount()):
                Value = self.StatsData.child(i).child("Value").value()
                ShowIfZero = self.StatsData.child(i).child("showIfZero").value()
                OkayToShow = False
                
                if ShowIfZero:
                    OkayToShow = True
                else:
                    if Value != 0:
                        OkayToShow = True
                
                if OkayToShow:
                    Text = self.StatsData.child(i).child("text").value()
                    
                    ListItem = [
                        QStandardItem(str(Value))
                        , QStandardItem(Text)
                    ]
                    self.StatsListModel.appendRow(ListItem)
            
            self.widget.statsList.setModel(self.StatsListModel)
            self.widget.statsList.resizeColumnToContents(0)