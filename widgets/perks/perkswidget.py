import os
import math
import logging
from PyQt5 import QtCore, QtWidgets, QtGui, uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from widgets import widgets
from widgets.shared.PipboyIcon import PipboyIcon

class PerksWidget(widgets.WidgetBase):
    PerkListSignal = QtCore.pyqtSignal()
    PerkInfoSignal = QtCore.pyqtSignal()
    PerkStarsSignal = QtCore.pyqtSignal()
    ColorUpdateSignal = QtCore.pyqtSignal(QColor)
    
    PerkListModel = QStandardItemModel()
    
    Widgets = None
    
    DataManager = None
    PerkData = None
    ColorData = None
    
    SelectedPerkId = -1
    SelectedPerkRMax = -1
    SelectedPerkRCur = -1
    StarFilled = None
    StarEmpty = None
    
    # CLASS INIT
    def __init__(self, mhandle, parent):
        super().__init__('Perks', parent)
        self.Widgets = uic.loadUi(os.path.join(mhandle.basepath, 'ui', 'perkswidget.ui'))
        self.setWidget(self.Widgets)
        
        self.StarFilled = PipboyIcon("StarFilled.svg")
        self.StarEmpty = PipboyIcon("StarEmpty.svg")
        
        self.PerkListSignal.connect(self.UpdatePerkList)
        self.PerkInfoSignal.connect(self.UpdatePerkInfo)
        self.PerkStarsSignal.connect(self.UpdatePerkStars)
        self.ColorUpdateSignal.connect(self.UpdateIconColor)
        
        self.Widgets.perkList.setModel(self.PerkListModel) # we need to call setModel() before selectionModel() (and never afterwards)
        self.Widgets.perkList.selectionModel().currentChanged.connect(self.PerkListCurrentChanged)
        self.Widgets.prevButton.clicked.connect(self.PrevButtonClicked)
        self.Widgets.nextButton.clicked.connect(self.NextButtonClicked)
    
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
        self.PerkData = rootObject.child('Perks')
        self.ColorData = rootObject.child("Status").child("EffectColor")
        
        # We want to track Perk data changes down to the Rank level
        if self.PerkData:
            self.PerkData.registerValueUpdatedListener(self.PerkDataUpdated, 2)
            
        # We want to track pip boy color changes
        if self.ColorData:
            self.ColorData.registerValueUpdatedListener(self.ColorDataUpdated, 2)
            
            R = self.ColorData.child(0).value() * 255
            G = self.ColorData.child(1).value() * 255
            B = self.ColorData.child(2).value() * 255
            
            self.ColorUpdateSignal.emit(QColor.fromRgb(R, G, B))

        self.PerkListSignal.emit()
        self.PerkInfoSignal.emit()

    # PERK DATA IN THE MANAGER HAS CHANGED
    def PerkDataUpdated(self, caller, value, pathObjs):
        self.PerkListSignal.emit()
        self.PerkInfoSignal.emit()
    
    def ColorDataUpdated(self, caller, value, pathObjs):
        R = self.ColorData.child(0).value() * 255
        G = self.ColorData.child(1).value() * 255
        B = self.ColorData.child(2).value() * 255
        
        self.ColorUpdateSignal.emit(QColor.fromRgb(R, G, B))
    
    # SET CURRENTLY SELECTED PERK INDEX AND RELATED SETTINGS
    def SetPerkId(self, perkId):
        self.SelectedPerkId = perkId
        self.SelectedPerkRCur = self.PerkData.child(self.SelectedPerkId).child("Rank").value()
        self.SelectedPerkRMax = self.PerkData.child(self.SelectedPerkId).child("MaxRank").value()
        
        self.PerkInfoSignal.emit()
        self.PerkStarsSignal.emit()
    
    # PERK TABLE VIEW - CLICK SIGNAL
    @QtCore.pyqtSlot(QtCore.QModelIndex, QtCore.QModelIndex)
    def PerkListCurrentChanged(self, index, previous):
        ModelIndex = self.PerkListModel.index(index.row(), 0)
        DataId = self.PerkListModel.data(ModelIndex)
        
        if DataId:
            self.SetPerkId(int(DataId))
    
    # PREVIEOUS PERK BUTTON - CLICK SIGNAL
    @QtCore.pyqtSlot()
    def PrevButtonClicked(self):
        self.SelectedPerkRCur -= 1
        
        self.PerkInfoSignal.emit()
        self.PerkStarsSignal.emit()
    
    # NEXT PERK BUTTON - CLICK SIGNAL
    @QtCore.pyqtSlot()
    def NextButtonClicked(self):
        self.SelectedPerkRCur += 1
        
        self.PerkInfoSignal.emit()
        self.PerkStarsSignal.emit()
    
    # UPDATE STAR COLORS
    @QtCore.pyqtSlot(QColor)
    def UpdateIconColor(self, pipboyColor):
        self.StarFilled.Color = pipboyColor
        self.StarFilled.Update()
        
        self.StarEmpty.Color = pipboyColor
        self.StarEmpty.Update()
        
        self.PerkStarsSignal.emit()
    
    @QtCore.pyqtSlot()
    def UpdatePerkList(self):
        if self.isVisible():
            self.PerkListModel.clear()
            
            if self.PerkData.childCount():
                for i in range(0, self.PerkData.childCount()):
                    Visible = self.PerkData.child(i).child("ListVisible").value()
                    PlayerRank = self.PerkData.child(i).child("Rank").value()
                    
                    if Visible and PlayerRank != 0:
                        Name = self.PerkData.child(i).child("Name").value()
                        
                        if Name != "":
                            ListItem = [
                                QStandardItem(str(i)),
                                QStandardItem(str(PlayerRank)),
                                QStandardItem(Name)
                            ]
                            self.PerkListModel.appendRow(ListItem)
    
                self.Widgets.perkList.sortByColumn(2, QtCore.Qt.AscendingOrder)
                self.Widgets.perkList.hideColumn(0)
                self.Widgets.perkList.resizeColumnToContents(1)
    
                if self.SelectedPerkId == -1:
                    ModelIndex = self.PerkListModel.index(0, 0)
                    DataId = self.PerkListModel.data(ModelIndex)
                    
                    if DataId:
                        self.SetPerkId(int(DataId))
    
    @QtCore.pyqtSlot()
    def UpdatePerkInfo(self):
        if self.isVisible():
            if self.PerkData.childCount():
                if self.PerkData.child(self.SelectedPerkId):
                    Text = self.PerkData.child(self.SelectedPerkId).child("Perks").child(self.SelectedPerkRCur - 1).child("Description").value()
                    self.Widgets.descriptionLabel.setText(Text)
                
                    if self.SelectedPerkRCur == 1:
                        self.Widgets.prevButton.setEnabled(False)
                    else:
                        self.Widgets.prevButton.setEnabled(True)
                    
                    if self.SelectedPerkRCur == self.SelectedPerkRMax:
                        self.Widgets.nextButton.setEnabled(False)
                    else:
                        self.Widgets.nextButton.setEnabled(True)
    
    @QtCore.pyqtSlot()
    def UpdatePerkStars(self):
        if self.isVisible():
            if self.PerkData:
                AreaWidth = self.Widgets.rankStars.rect().width()
                MaxStarSize = math.floor(AreaWidth / self.SelectedPerkRMax)
                
                # The stars only get so large
                if MaxStarSize > 30:
                    MaxStarSize = 30
                
                # Update Star Size and Images
                self.StarFilled.Size = MaxStarSize
                self.StarFilled.Update()
                
                self.StarEmpty.Size = MaxStarSize
                self.StarEmpty.Update()
                
                MaxStarArea = self.SelectedPerkRMax * MaxStarSize
                
                # Create scene and set its area
                StarScene = QGraphicsScene()
                StarScene.setSceneRect(0, 0, MaxStarArea, MaxStarSize)
    
                # Filled Stars
                for i in range(0, self.SelectedPerkRCur):
                    Star = StarScene.addPixmap(self.StarFilled.ImageData)
                    Star.setOffset(i * MaxStarSize, 0)
                
                # Empty Stars
                for i in range(self.SelectedPerkRCur, self.SelectedPerkRMax):
                    Star = StarScene.addPixmap(self.StarEmpty.ImageData)  
                    Star.setOffset(i * MaxStarSize, 0)
        
                # Set the widget and show its glory
                self.Widgets.rankStars.setScene(StarScene)
                self.Widgets.rankStars.show()
