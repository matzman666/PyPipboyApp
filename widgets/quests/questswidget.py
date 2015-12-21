# -*- coding: utf-8 -*-
import os
from PyQt5 import QtWidgets, QtCore, QtGui, uic
from PyQt5.QtGui import *
from widgets import widgets

class QuestsWidget(widgets.WidgetBase):
    _signalInfoUpdated = QtCore.pyqtSignal()
    QuestsModel = QStandardItemModel()
    ObjectivesModel = QStandardItemModel()
    
    def __init__(self, mhandle, parent):
        super().__init__('Quests', parent)
        self.widget = uic.loadUi(os.path.join(mhandle.basepath, 'ui', 'questswidget.ui'))
        self.setWidget(self.widget)
        self._signalInfoUpdated.connect(self._slotInfoUpdated)
        
    def init(self, app, datamanager):
        super().init(app, datamanager)
        
        self._app = app
        self.dataManager = datamanager
        self.dataManager.registerRootObjectListener(self._onPipRootObjectEvent)
        
        self.widget.questView.doubleClicked.connect(self._slotTableDoubleClicked)
        self.widget.questView.clicked.connect(self._slotTableClicked)
        
        self.QuestSelected = False
        self.SelectedQuestInfoId = -1
        
    def _onPipRootObjectEvent(self, rootObject):
        self.QuestData = rootObject.child('Quests')
        
        if self.QuestData:
            self.QuestData.registerValueUpdatedListener(self._onPipPlayerInfoUpdate, 4)
        
        self._signalInfoUpdated.emit()

    def _onPipPlayerInfoUpdate(self, caller, value, pathObjs):
        self._signalInfoUpdated.emit()
        
    @QtCore.pyqtSlot()
    def _slotInfoUpdated(self):
        self.UpdateQuests()
        self.UpdateQuestObjectives(self.SelectedQuestInfoId)
    
    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def _slotTableDoubleClicked(self, index):
        # Get Data from the Table Cell
        Model = self.widget.questView.model()
        ModelIndex = Model.index(index.row(), 0)
        DataId = int(Model.data(ModelIndex))
        PipboyId = self.QuestData.child(DataId)
        
        # Toggle the quest
        self.dataManager.rpcToggleQuestActive(PipboyId)
    
    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def _slotTableClicked(self, index):
        Model = self.widget.questView.model()
        ModelIndex = Model.index(index.row(), 0)
        DataId = int(Model.data(ModelIndex))
        
        if self.SelectedQuestInfoId == DataId:
            if self.QuestSelected:
                DataId = -1
                self.QuestSelected = False
            else:
                self.QuestSelected = True
        else:
            self.QuestSelected = True
        
        self.UpdateQuestObjectives(DataId)
        self.SelectedQuestInfoId = DataId
    
    def UpdateQuests(self):
        self.QuestsModel.clear()
        
        HighlightFont = QtGui.QFont()
        HighlightFont.setBold(True)
        
        for i in range(0, self.QuestData.childCount()):
            Name = str(self.QuestData.child(i).child('text').value())
            Active = self.QuestData.child(i).child('active').value()
            Enabled = self.QuestData.child(i).child('enabled').value()
            
            if Enabled:
                NameCell = QStandardItem(Name)
                
                if Active:
                    NameCell.setFont(HighlightFont)
                
                TableItem = [
                    QStandardItem(str(i)),
                    NameCell
                ]
                self.QuestsModel.appendRow(TableItem)
        
        self.widget.questView.horizontalHeader().setStretchLastSection(True)
        self.widget.questView.verticalHeader().setStretchLastSection(False)
        self.widget.questView.setModel(self.QuestsModel)
        self.widget.questView.sortByColumn(1, QtCore.Qt.AscendingOrder)
        self.widget.questView.hideColumn(0)

    def UpdateQuestObjectives(self, questInfoId):
        self.ObjectivesModel.clear()
        self.widget.descriptionLabel.setText("")
        
        if questInfoId != -1:
            HighlightFont = QtGui.QFont()
            HighlightFont.setBold(True)
            
            self.widget.descriptionLabel.setText(self.QuestData.child(questInfoId).child("desc").value())
            
            Objectives = self.QuestData.child(questInfoId).child("objectives")
            
            for i in range(0, Objectives.childCount()):
                Text = str(Objectives.child(i).child("text").value())
                Completed = Objectives.child(i).child("completed").value()
                Enabled = Objectives.child(i).child("enabled").value()
                
                TextCell = QStandardItem(Text)
                
                if Enabled and not Completed:
                    TextCell.setFont(HighlightFont)
                
                TableItem = [
                    TextCell,
                    QStandardItem(str(Completed))
                ]
                self.ObjectivesModel.appendRow(TableItem)
            
            self.widget.objectiveView.horizontalHeader().setStretchLastSection(True)
            self.widget.objectiveView.verticalHeader().setStretchLastSection(False)
            self.widget.objectiveView.setModel(self.ObjectivesModel)
            self.widget.objectiveView.sortByColumn(1, QtCore.Qt.AscendingOrder)
            self.widget.objectiveView.hideColumn(1)