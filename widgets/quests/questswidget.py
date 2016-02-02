# -*- coding: utf-8 -*-
import os
from PyQt5 import QtCore, QtWidgets, QtGui, uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from widgets import widgets

class QuestsWidget(widgets.WidgetBase):
    QuestListSignal = QtCore.pyqtSignal()
    ObjectiveListSignal = QtCore.pyqtSignal()
    
    QuestListModel = QStandardItemModel()
    ObjectiveListModel = QStandardItemModel()
    
    Widgets = None
    GlobalMap = None
    
    DataManager = None
    QuestData = None
    ObjectiveData = None

    SelectedQuestId = -1
    SelectedFormId = -1
    MiscellaneousId = -1
    
    # CLASS INIT
    def __init__(self, mhandle, parent):
        super().__init__('Quest Browser', parent)
        
        self.Widgets = uic.loadUi(os.path.join(mhandle.basepath, 'ui', 'questswidget.ui'))
        self.setWidget(self.Widgets)
        
        self.QuestListSignal.connect(self.UpdateQuestList)
        self.ObjectiveListSignal.connect(self.UpdateObjectiveList)
        
        self.Widgets.questList.setModel(self.QuestListModel) # we need to call setModel() before selectionModel() (and never afterwards)
        self.Widgets.questList.selectionModel().currentChanged.connect(self.QuestListCurentChanged)
        self.Widgets.questList.doubleClicked.connect(self.QuestListDoubleClicked)
        self.Widgets.objectiveList.setModel(self.ObjectiveListModel)
        self.Widgets.objectiveList.selectionModel().currentChanged.connect(self.ObjectiveListCurrentChanged)
        self.Widgets.objectiveList.doubleClicked.connect(self.ObjectiveListDoubleClicked)
        self.Widgets.showonmapButton.clicked.connect(self.MapButtonClicked)
    
    # QT INIT
    def init(self, app, dataManager):
        super().init(app, dataManager)
        
        # Hook up to the map because we can now show quests
        self.GlobalMap = app.iwcGetEndpoint("globalmapwidget")
        
        # Create a class level hook to the datamanager for updates and RPC methods
        self.DataManager = dataManager
        self.DataManager.registerRootObjectListener(self.DataManagerUpdated)
    
    # DATA MANAGER OBJECT HAS CHANGED AT SOME LEVEL
    def DataManagerUpdated(self, rootObject):
        # Create a class level hook to the Quest data
        self.QuestData = rootObject.child('Quests')
        
        # We want to track Quest data changes down to the objectives level
        if self.QuestData:
            self.QuestData.registerValueUpdatedListener(self.QuestDataUpdated, 2)

        self.QuestListSignal.emit()
        self.ObjectiveListSignal.emit()

    # QUEST DATA IN THE MANAGER HAS CHANGED
    def QuestDataUpdated(self, caller, value, pathObjs):
        self.QuestListSignal.emit()
    
    def ObjectiveDataUpdated(self, caller, value, pathObjs):
        self.ObjectiveListSignal.emit()
    
    def SetQuestId(self, questId):
        self.SelectedQuestId = questId
        
        if self.QuestData:
            if self.ObjectiveData:
                self.ObjectiveData.unregisterValueUpdatedListener(self.ObjectiveDataUpdated)
            
            self.ObjectiveData = self.QuestData.child(self.SelectedQuestId).child("objectives")
            self.ObjectiveData.registerValueUpdatedListener(self.ObjectiveDataUpdated, 2)
        
        self.ObjectiveListSignal.emit()
    
    # QUEST TABLE VIEW - CLICK SIGNAL
    @QtCore.pyqtSlot(QtCore.QModelIndex, QtCore.QModelIndex)
    def QuestListCurentChanged(self, index, previous):
        ModelIndex = self.QuestListModel.index(index.row(), 0)
        DataId = self.QuestListModel.data(ModelIndex)
        
        if DataId:
            self.SetQuestId(int(DataId))
        
        if self.QuestData:
            FormId = self.QuestData.child(self.SelectedQuestId).child("formID").value()
            
            self.SelectedFormId = FormId
        
        if self.SelectedQuestId == self.MiscellaneousId:
            self.Widgets.showonmapButton.setEnabled(False)
        else:
            self.Widgets.showonmapButton.setEnabled(True)
    
    # QUEST TABLE VIEW - DOUBLE CLICK SIGNAL
    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def QuestListDoubleClicked(self, index):
        ModelIndex = self.QuestListModel.index(index.row(), 0)
        DataId = self.QuestListModel.data(ModelIndex)
        
        if DataId:
            if self.QuestData.childCount():
                PipboyId = self.QuestData.child(int(DataId))
                self.DataManager.rpcToggleQuestActive(PipboyId)
    
    # OBJECTIVE TABLE VIEW - CLICK SIGNAL
    @QtCore.pyqtSlot(QtCore.QModelIndex, QtCore.QModelIndex)
    def ObjectiveListCurrentChanged(self, index, previous):
        if self.SelectedQuestId == self.MiscellaneousId:
            ModelIndex = self.ObjectiveListModel.index(index.row(), 0)
            DataId = self.ObjectiveListModel.data(ModelIndex)
            
            if DataId:
                if self.ObjectiveData:
                    if self.ObjectiveData.child(int(DataId)).child("formID"):
                        self.SelectedFormId = self.ObjectiveData.child(int(DataId)).child("formID").value()
                    
            self.Widgets.showonmapButton.setEnabled(True)
    
    # OBJECTIVE TABLE VIEW - DOUBLE CLICK SIGNAL
    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def ObjectiveListDoubleClicked(self, index):
        # Only process objective view clicks if its the miscellaneous quest
        if self.SelectedQuestId == self.MiscellaneousId:
            if self.QuestData.childCount():
                ModelIndex = self.ObjectiveListModel.index(index.row(), 0)
                DataId = self.ObjectiveListModel.data(ModelIndex)
                
                if DataId:
                    FormId = self.QuestData.child(self.SelectedQuestId).child("objectives").child(int(DataId)).child("formID").value()
                    Instance = self.QuestData.child(self.SelectedQuestId).child("objectives").child(int(DataId)).child("instance").value()
                    
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
                    self.DataManager.rpcToggleQuestActive(MiscellaneousQuest)
                    
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

    @QtCore.pyqtSlot()
    def UpdateQuestList(self):
        if self.isVisible():
            self.QuestListModel.clear()
            
            HighlightFont = QtGui.QFont()
            HighlightFont.setBold(True)
            
            if self.QuestData:
                for i in range(0, self.QuestData.childCount()):
                    Enabled = self.QuestData.child(i).child("enabled").value()
                    FormId = self.QuestData.child(i).child("formID").value()
                    
                    if FormId == 0:
                        self.MiscellaneousId = i
                    
                    if Enabled:
                        Name = self.QuestData.child(i).child("text").value()
                        Active = self.QuestData.child(i).child("active").value()
                        
                        NameCell = QStandardItem(Name)
                        
                        if Active:
                            NameCell.setFont(HighlightFont)
                        
                        ListItem = [
                            QStandardItem(str(i))
                            , NameCell
                        ]
                        self.QuestListModel.appendRow(ListItem)
                
                self.Widgets.questList.sortByColumn(1, Qt.AscendingOrder)
                self.Widgets.questList.hideColumn(0)
                
                if self.SelectedQuestId == -1:
                    ModelIndex = self.QuestListModel.index(0,0)
                    DataId = self.QuestListModel.data(ModelIndex)
                    
                    if DataId:
                        self.SetQuestId(int(DataId))
    
    @QtCore.pyqtSlot()
    def UpdateObjectiveList(self):
        if self.isVisible():
            self.ObjectiveListModel.clear()
            self.Widgets.descriptionLabel.setText("")
            
            HighlightFont = QtGui.QFont()
            HighlightFont.setBold(True)
            
            if self.QuestData and self.ObjectiveData:
                if self.SelectedQuestId == self.MiscellaneousId:
                    self.Widgets.descriptionLabel.setText("Double click an objective to activate or deactivate it.")
                else:
                    if self.QuestData.child(self.SelectedQuestId):
                        Description = self.QuestData.child(self.SelectedQuestId).child("desc").value()
                        self.Widgets.descriptionLabel.setText(Description)
                
                for i in range(0, self.ObjectiveData.childCount()):
                    Text = self.ObjectiveData.child(i).child("text").value()
                    Completed = self.ObjectiveData.child(i).child("completed").value()
                    Enabled = self.ObjectiveData.child(i).child("enabled").value()
                    ActiveItem = self.ObjectiveData.child(i).child("active")
                    
                    TextCell = QStandardItem(Text)
                    
                    if ActiveItem:
                        Active = ActiveItem.value()
                        
                        if Active:
                            TextCell.setFont(HighlightFont)
                    else:
                        if Enabled and not Completed:
                            TextCell.setFont(HighlightFont)
                    
                    ListItem = [
                        QStandardItem(str(i))
                        , TextCell
                        , QStandardItem(str(Completed))
                    ]
                    self.ObjectiveListModel.appendRow(ListItem)
                
                self.Widgets.objectiveList.sortByColumn(2, Qt.AscendingOrder)
                self.Widgets.objectiveList.hideColumn(0)
                self.Widgets.objectiveList.hideColumn(2)