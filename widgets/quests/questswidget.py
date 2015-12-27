# -*- coding: utf-8 -*-
import os
from PyQt5 import QtCore, QtWidgets, QtGui, uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from widgets import widgets

class QuestsWidget(widgets.WidgetBase):
    _signalInfoUpdated = QtCore.pyqtSignal()
    
    # CLASS INIT
    def __init__(self, mhandle, parent):
        super().__init__('Quests', parent)
        self.widget = uic.loadUi(os.path.join(mhandle.basepath, 'ui', 'questswidget.ui'))
        self.setWidget(self.widget)
        self._signalInfoUpdated.connect(self.UpdateTableViews)
    
    # QT INIT
    def init(self, app, datamanager):
        super().init(app, datamanager)
        
        # Hook up to the map because we can now show quests
        self.GlobalMap = app.iwcGetEndpoint("globalmapwidget")
        
        # Create a class level hook to the datamanager for updates and RPC methods
        self.dataManager = datamanager
        self.dataManager.registerRootObjectListener(self.DataManagerUpdated)
        
        # Event hooks
        self.widget.questView.clicked.connect(self.QuestViewClicked)
        self.widget.questView.doubleClicked.connect(self.QuestViewDoubleClicked)        
        self.widget.objectiveView.clicked.connect(self.ObjectiveViewClicked)
        self.widget.objectiveView.doubleClicked.connect(self.ObjectiveViewDoubleClicked)
        self.widget.showonmapButton.clicked.connect(self.MapButtonClicked)
        
        # Class properties for tracking purposes
        self.QuestsModel = QStandardItemModel()
        self.ObjectivesModel = QStandardItemModel()
        self.QuestSelected = False
        self.SelectedQuestDataId = -1
        self.SelectedFormId = -1
        self.MiscellaneousId = -1
    
    # DATA MANAGER OBJECT HAS CHANGED AT SOME LEVEL
    def DataManagerUpdated(self, rootObject):
        # Create a class level hook to the Quest data
        self.QuestData = rootObject.child('Quests')
        
        # We want to track Quest data changes down to the objectives level
        if self.QuestData:
            self.QuestData.registerValueUpdatedListener(self.QuestDataUpdated, 4)
        
        # Update Widget Table Views
        self._signalInfoUpdated.emit()

    # QUEST DATA IN THE MANAGER HAS CHANGED
    def QuestDataUpdated(self, caller, value, pathObjs):
        # Update Widget Table Views
        self._signalInfoUpdated.emit()
    
    # UPDATE UI ELEMENTS
    @QtCore.pyqtSlot()
    def UpdateTableViews(self):
        self.UpdateQuests()
        self.UpdateQuestObjectives(self.SelectedQuestDataId)
    
    # QUEST TABLE VIEW - CLICK SIGNAL
    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def QuestViewClicked(self, index):
        # Get data from the quest table cell
        Model = self.widget.questView.model() 
        ModelIndex = Model.index(index.row(), 0)
        DataId = int(Model.data(ModelIndex))
        
        # This allows the user to deselect a quest and to clear the objectives
        # table, or select a quest and populate the objectives table
        if self.SelectedQuestDataId == DataId:
            if self.QuestSelected:
                DataId = -1
                self.QuestSelected = False
                self.widget.showonmapButton.setEnabled(False)
            else:
                self.QuestSelected = True
        else:
            self.QuestSelected = True
        
        # Quest selected, set some tracking info
        self.UpdateQuestObjectives(DataId)
        self.SelectedQuestDataId = DataId
        
        # If quest objectives are showing, we want to set the QuestFormId and
        # then show the Map Button (except if the miscellaneous quest has been
        # selected)
        if DataId != -1:
            self.SelectedFormId = self.QuestData.child(DataId).child("formID").value()
            
            if self.SelectedFormId != 0:
                self.widget.showonmapButton.setEnabled(True)
            else:
                self.widget.showonmapButton.setEnabled(False)
    
    # QUEST TABLE VIEW - DOUBLE CLICK SIGNAL
    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def QuestViewDoubleClicked(self, index):
        # Get data from the quest table cell
        Model = self.widget.questView.model()
        ModelIndex = Model.index(index.row(), 0)
        DataId = int(Model.data(ModelIndex))
        PipboyId = self.QuestData.child(DataId)
        
        # Toggle the quest
        self.dataManager.rpcToggleQuestActive(PipboyId)
    
    # OBJECTIVE TABLE VIEW - CLICK SIGNAL
    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def ObjectiveViewClicked(self, index):
        # Only process objective view clicks if its the miscellaneous quest
        if self.SelectedQuestDataId == self.MiscellaneousId:
            # Get data from the objective table cell
            Model = self.widget.objectiveView.model()
            ModelIndex = Model.index(index.row(), 0)
            DataId = int(Model.data(ModelIndex))
            
            # Set the selected form id with the miscellaneous form id
            self.SelectedFormId = self.QuestData.child(self.SelectedQuestDataId).child("objectives").child(DataId).child("formID").value()
            self.widget.showonmapButton.setEnabled(True)
    
    # OBJECTIVE TABLE VIEW - DOUBLE CLICK SIGNAL
    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def ObjectiveViewDoubleClicked(self, index):
        # Only process objective view clicks if its the miscellaneous quest
        if self.SelectedQuestDataId == self.MiscellaneousId:
            # Get data from the objective table cell
            Model = self.widget.objectiveView.model()
            ModelIndex = Model.index(index.row(), 0)
            DataId = int(Model.data(ModelIndex))
            FormId = self.QuestData.child(self.SelectedQuestDataId).child("objectives").child(DataId).child("formID").value()
            Instance = self.QuestData.child(self.SelectedQuestDataId).child("objectives").child(DataId).child("instance").value()
            
            # Since Miscellaneous quests are just objectives, we have to spoof
            # the PipboyValue beings sent. So I'm opting to use the Miscellaneous
            # quest itself. I get it, then force its formID and instance values
            # to match the objectives values. I also save a copy of the original
            # instance ID, just in case that matters
            MiscellaneousQuest = self.QuestData.child(self.MiscellaneousId)
            SavedInstance = MiscellaneousQuest.child("instance").value()
            
            MiscellaneousQuest.child("formID")._value = FormId
            MiscellaneousQuest.child("instance")._value = Instance
            
            # Toggle the quest
            self.dataManager.rpcToggleQuestActive(MiscellaneousQuest)
            
            # Also it appears as if the entire quest item doesn't refresh, just
            # the objective information. So for Sanity Sakes, lets reset its
            # formID and instance back to what they were
            MiscellaneousQuest.child("formID")._value = 0
            MiscellaneousQuest.child("instance")._value = SavedInstance
    
    # SHOW ON MAP BUTTON - CLICK SIGNAL
    @QtCore.pyqtSlot()
    def MapButtonClicked(self):
        # Bring up the map and center on the quest marker
        if not self.GlobalMap.isVisible():
            self.GlobalMap.setVisible(True)
        self.GlobalMap.raise_()
        self.GlobalMap.iwcCenterOnQuest(self.SelectedFormId)
    
    # UPDATE QUEST TABLE VIEW
    def UpdateQuests(self):
        self.QuestsModel.clear()
        
        HighlightFont = QtGui.QFont()
        HighlightFont.setBold(True)
        
        for i in range(0, self.QuestData.childCount()):
            Name = str(self.QuestData.child(i).child('text').value())
            Active = self.QuestData.child(i).child('active').value()
            Enabled = self.QuestData.child(i).child('enabled').value()
            FormId = self.QuestData.child(i).child("formID").value()
            
            # Set Miscellaneous Id, because its important
            if FormId == 0:
                self.MiscellaneousId = i
            
            # Only show non-completed quests
            if Enabled:
                NameCell = QStandardItem(Name)
                
                if Active:
                    NameCell.setFont(HighlightFont)
                
                TableItem = [
                    QStandardItem(str(i)),
                    NameCell
                ]
                self.QuestsModel.appendRow(TableItem)
        
        # Update Quest View Table
        self.widget.questView.horizontalHeader().setStretchLastSection(True)
        self.widget.questView.verticalHeader().setStretchLastSection(False)
        self.widget.questView.setModel(self.QuestsModel)
        self.widget.questView.sortByColumn(1, QtCore.Qt.AscendingOrder)
        self.widget.questView.hideColumn(0)

    def UpdateQuestObjectives(self, questInfoId):
        self.ObjectivesModel.clear()
        self.widget.descriptionLabel.setText("")
        
        # Only update objective view if a proper id was passed
        if questInfoId != -1:
            HighlightFont = QtGui.QFont()
            HighlightFont.setBold(True)
            
            # If the selected quest is the Miscellaneous quest, set a custom
            # description. Otherwise, use the description of the quest
            if questInfoId == self.MiscellaneousId:
                self.widget.descriptionLabel.setText("Click on an objective to activate the Show on Map button. Double click an objective to activate or deactivate it.")
            else:
                if self.QuestData.child(questInfoId):
                    self.widget.descriptionLabel.setText(self.QuestData.child(questInfoId).child("desc").value())
            
            Objectives = self.QuestData.child(questInfoId).child("objectives")
            
            for i in range(0, Objectives.childCount()):
                Text = str(Objectives.child(i).child("text").value())
                Completed = Objectives.child(i).child("completed").value()
                Enabled = Objectives.child(i).child("enabled").value()
                ActiveItem = Objectives.child(i).child("active")
                
                TextCell = QStandardItem(Text)                
                
                if ActiveItem:
                    Active = ActiveItem.value()
                    
                    if Active:
                        TextCell.setFont(HighlightFont)
                else:
                    if Enabled and not Completed:
                        TextCell.setFont(HighlightFont)
                    
                TableItem = [
                    QStandardItem(str(i)),
                    TextCell,
                    QStandardItem(str(Completed))
                ]
                self.ObjectivesModel.appendRow(TableItem)
            
            # Update Quest View Table
            self.widget.objectiveView.horizontalHeader().setStretchLastSection(True)
            self.widget.objectiveView.verticalHeader().setStretchLastSection(False)
            self.widget.objectiveView.setModel(self.ObjectivesModel)
            self.widget.objectiveView.sortByColumn(2, QtCore.Qt.AscendingOrder)
            self.widget.objectiveView.hideColumn(0)
            self.widget.objectiveView.hideColumn(2)