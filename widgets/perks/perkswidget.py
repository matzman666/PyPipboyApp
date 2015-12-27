# -*- coding: utf-8 -*-
import os
import math
from PyQt5 import QtCore, QtWidgets, QtGui, uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from widgets.shared.graphics import ImageFactory
from widgets import widgets

class PerksWidget(widgets.WidgetBase):
    _signalInfoUpdated = QtCore.pyqtSignal()
    PipboyColorUpdatedSignal = QtCore.pyqtSignal(QColor)
    
    # CLASS INIT
    def __init__(self, mhandle, parent):
        super().__init__('Perks', parent)
        self.widget = uic.loadUi(os.path.join(mhandle.basepath, 'ui', 'perkswidget.ui'))
        self.setWidget(self.widget)
        self._signalInfoUpdated.connect(self.UpdateUI)
        self.PipboyColorUpdatedSignal.connect(self.UpdateColorData)
    
    # QT INIT
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
        self.ImageLoader = ImageFactory(os.path.join("ui", "res"))
        self.StarColor = QColor.fromRgb(255, 255, 255)
        self.StarSize = 29
        self.StarFilled = None
        self.StarEmpty = None
    
    # DATA MANAGER OBJECT HAS CHANGED AT SOME LEVEL
    def DataManagerUpdated(self, rootObject):
        # Create a class level hook to the Perks data
        self.PerksData = rootObject.child('Perks')
        
        # Create a class level hook to the pip boy color data
        self.PipboyColorData = rootObject.child("Status").child("EffectColor")
        
        # We want to track Perk data changes down to the Rank level
        if self.PerksData:
            self.PerksData.registerValueUpdatedListener(self.PerksDataUpdated, 2)
            
        # We want to track pip boy color changes
        if self.PipboyColorData:
            self.PipboyColorData.registerValueUpdatedListener(self.PipboyColorDataUpdated, 2)
            
            R = self.PipboyColorData.child(0).value() * 255
            G = self.PipboyColorData.child(1).value() * 255
            B = self.PipboyColorData.child(2).value() * 255
            self.PipboyColorUpdatedSignal.emit(QColor.fromRgb(R, G, B))
        
        # Update Widget Table Views
        self._signalInfoUpdated.emit()

    # PERK DATA IN THE MANAGER HAS CHANGED
    def PerksDataUpdated(self, caller, value, pathObjs):
        # Update Widget Table Views
        self._signalInfoUpdated.emit()
    
    def PipboyColorDataUpdated(self, caller, value, pathObjs):
        R = self.PipboyColorData.child(0).value() * 255
        G = self.PipboyColorData.child(1).value() * 255
        B = self.PipboyColorData.child(2).value() * 255
        self.PipboyColorUpdatedSignal.emit(QColor.fromRgb(R, G, B))
    
    # UPDATE UI ELEMENTS
    @QtCore.pyqtSlot()
    def UpdateUI(self):
        self.UpdatePerks()
        self.UpdatePerkDescription()
        self.UpdateStarView()
    
    # UPDATE STAR COLORS
    @QtCore.pyqtSlot(QColor)
    def UpdateColorData(self, pipboyColor):
        self.StarColor = pipboyColor
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
            MaxStarSize = math.floor(AreaWidth / self.SelectedPerkRMax)
            
            # The stars only get so large
            if MaxStarSize > 29:
                MaxStarSize = 29
            
            # Update Star Size and Images
            self.StarSize = MaxStarSize
            self.StarFilled = self.ImageLoader.getPixmap("star-filled.svg", self.StarSize, self.StarSize, self.StarColor)
            self.StarEmpty = self.ImageLoader.getPixmap("star-empty.svg", self.StarSize, self.StarSize, self.StarColor)
            
            MaxStarArea = self.SelectedPerkRMax * self.StarSize
            
            # Create scene and set its area
            StarScene = QGraphicsScene()
            StarScene.setSceneRect(0, 0, MaxStarArea, self.StarSize)

            # Filled Stars
            for i in range(0, self.SelectedPerkRCur):
                Star = StarScene.addPixmap(self.StarFilled)
                Star.setOffset(i * self.StarSize, 0)
            
            # Empty Stars
            for i in range(self.SelectedPerkRCur, self.SelectedPerkRMax):
                Star = StarScene.addPixmap(self.StarEmpty)  
                Star.setOffset(i * self.StarSize, 0)
    
            # Set the widget and show its glory
            self.widget.rankStars.setScene(StarScene)
            self.widget.rankStars.show()
