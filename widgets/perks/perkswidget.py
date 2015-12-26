# -*- coding: utf-8 -*-
import os
import math
from PyQt5 import QtCore, QtWidgets, QtGui, uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from widgets import widgets

class PerksWidget(widgets.WidgetBase):
    # As I've learned, this allows for proper and seamless updates of the
    # widget ui. So you should only make ui updates through the signal
    _signalInfoUpdated = QtCore.pyqtSignal()
    
    # QT INIT
    def __init__(self, mhandle, parent):
        super().__init__('Perks', parent)
        self.widget = uic.loadUi(os.path.join(mhandle.basepath, 'ui', 'perkswidget.ui'))
        self.setWidget(self.widget)
        self._signalInfoUpdated.connect(self.UpdateUI)
    
    # CLASS INIT
    def init(self, app, datamanager):
        super().init(app, datamanager)
		
        # Create a class level hook to the datamanager for updates and RPC methods
        self.dataManager = datamanager
        self.dataManager.registerRootObjectListener(self.DataManagerUpdated)
        
        # Event hooks
        self.widget.perkView.clicked.connect(self.PerkViewClicked)
        self.widget.prevButton.clicked.connect(self.PrevButtonClicked)
        self.widget.nextButton.clicked.connect(self.NextButtonClicked)
        
        # Class properties for tracking purposes
        self.PerksModel = QStandardItemModel()
        self.SelectedPerkId = -1
        self.SelectedPerkRMax = -1
        self.SelectedPerkRCur = -1
        
        # Fancy Graphics Stuff
        self.StarsImage = QPixmap(512, 256)
        self.StarsImage.load(os.path.join("ui", "res", "Stars-GreenOnBlack.png"))
        self.StarDefaultWidth = 30
        self.StarDefaultEmpty = self.StarsImage.copy(QRect(0, 0, 256, 256)).scaledToWidth(self.StarDefaultWidth)
        self.StarDefaultFilled = self.StarsImage.copy(QRect(256, 0, 256, 256)).scaledToWidth(self.StarDefaultWidth)
        self.StarScene = QGraphicsScene()
    
    # DATA MANAGER OBJECT HAS CHANGED AT SOME LEVEL
    def DataManagerUpdated(self, rootObject):
        # Create a class level hook to the Perks data
        self.PerksData = rootObject.child('Perks')
        
        # We want to track Perk data changes down to the Rank level
        if self.PerksData:
            self.PerksData.registerValueUpdatedListener(self.PerksDataUpdated, 2)
        
        # Update Widget Table Views
        self._signalInfoUpdated.emit()

    # PERK DATA IN THE MANAGER HAS CHANGED
    def PerksDataUpdated(self, caller, value, pathObjs):
        # Update Widget Table Views
        self._signalInfoUpdated.emit()
    
    # UPDATE UI ELEMENTS
    @QtCore.pyqtSlot()
    def UpdateUI(self):
        self.UpdatePerks()
        self.UpdatePerkDescription()
        self.UpdateStarView()
    
    # PERK TABLE VIEW - CLICK SIGNAL
    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def PerkViewClicked(self, index):
        ModelIndex = self.PerksModel.index(index.row(), 0)
        DataId = int(self.PerksModel.data(ModelIndex))
        
        self.SetPerkViewData(DataId)
    
    # PREVIEOUS PERK BUTTON - CLICK SIGNAL
    @QtCore.pyqtSlot()
    def PrevButtonClicked(self):
        self.SelectedPerkRCur -= 1
        self.UpdatePerkDescription()
        self.UpdateStarView()
        self.SetPerkButtons()
    
    # NEXT PERK BUTTON - CLICK SIGNAL
    @QtCore.pyqtSlot()
    def NextButtonClicked(self):
        self.SelectedPerkRCur += 1
        self.UpdatePerkDescription()
        self.UpdateStarView()
        self.SetPerkButtons()
    
    # SET CURRENTLY SELECTED PERK INDEX AND RELATED SETTINGS
    def SetPerkViewData(self, dataId):
        self.SelectedPerkId = dataId
        self.SelectedPerkRCur = self.PerksData.child(dataId).child("Rank").value()
        self.SelectedPerkRMax = self.PerksData.child(dataId).child("MaxRank").value()
        
        self.SetPerkButtons()
        self.UpdatePerkDescription()
        self.UpdateStarView()
    
    # SET PERK RANK BUTTONS TO BE DISABLED OR ENABLED
    def SetPerkButtons(self):
        if self.SelectedPerkRCur == 1:
            self.widget.prevButton.setEnabled(False)
        else:
            self.widget.prevButton.setEnabled(True)
        
        if self.SelectedPerkRCur == self.SelectedPerkRMax:
            self.widget.nextButton.setEnabled(False)
        else:
            self.widget.nextButton.setEnabled(True)
    
    # UPDATE PERK TABLE VIEW
    def UpdatePerks(self):
        self.PerksModel.clear()
        
        for i in range(0, self.PerksData.childCount()):
            Visible = self.PerksData.child(i).child("ListVisible").value()
            PlayerRank = self.PerksData.child(i).child("Rank").value()
            
            if Visible and PlayerRank != 0:
                Name = self.PerksData.child(i).child("Name").value()
                
                TableItem = [
                    QStandardItem(str(i)),
                    QStandardItem(str(PlayerRank)),
                    QStandardItem(Name)
                ]
                self.PerksModel.appendRow(TableItem)
        
        self.widget.perkView.horizontalHeader().setStretchLastSection(True)
        self.widget.perkView.verticalHeader().setStretchLastSection(False)
        self.widget.perkView.setModel(self.PerksModel)
        self.widget.perkView.sortByColumn(2, QtCore.Qt.AscendingOrder)
        self.widget.perkView.hideColumn(0)
        self.widget.perkView.setColumnWidth(1, 20)
        
        # If no perk has been selected yet, select first one in sorted view
        if self.SelectedPerkId == -1:
            Index = self.PerksModel.index(0, 0)
            data = self.PerksModel.data(Index)
            if data:
                DataId = int(data)
            
                self.SetPerkViewData(DataId)
    
    # UPDATE PERK DESCRIPTION BASED ON RANK SELECTED
    def UpdatePerkDescription(self):
        perk = self.PerksData.child(self.SelectedPerkId)
        if perk:
            Text = self.PerksData.child(self.SelectedPerkId).child("Perks").child(self.SelectedPerkRCur - 1).child("Description").value()
            self.widget.descriptionLabel.setText(Text)
    
    # UPDATE STAR GRAPHIC VIEW BASED ON RANK SELECTED
    def UpdateStarView(self):
        perk = self.PerksData.child(self.SelectedPerkId)
        if perk:
            AreaWidth = self.widget.rankStars.rect().width()
            StarWidth = self.StarDefaultWidth
            Override = False
            StarFilled = None
            StarEmpty = None
            
            # Stars are too big to fit in to current view. Resize default images
            if (AreaWidth / StarWidth) < self.SelectedPerkRMax:
                StarWidth = math.floor(AreaWidth / self.SelectedPerkRMax)
                Override = True
                StarFilled = self.StarDefaultFilled.scaledToWidth(StarWidth)
                StarEmpty = self.StarDefaultEmpty.scaledToWidth(StarWidth)
            
            StarMaxWidth = self.SelectedPerkRMax * StarWidth
            
            # Create scene and set its area
            self.StarScene = QGraphicsScene(None)
            self.StarScene.setSceneRect(0, 0, StarMaxWidth, StarWidth)
            
            Star = None
            
            # Filled Stars
            for i in range(0, self.SelectedPerkRCur):
                if Override:
                    Star = self.StarScene.addPixmap(StarFilled)
                else:
                    Star = self.StarScene.addPixmap(self.StarDefaultFilled)
                    
                Star.setOffset(i * StarWidth, 0)
            
            # Empty Stars
            for i in range(self.SelectedPerkRCur, self.SelectedPerkRMax):
                if Override:
                    Star = self.StarScene.addPixmap(StarEmpty)
                else:
                    Star = self.StarScene.addPixmap(self.StarDefaultEmpty)
                    
                Star.setOffset(i * StarWidth, 0)
    
            # Set the widget and show its glory
            self.widget.rankStars.setScene(self.StarScene)
            self.widget.rankStars.show()
