# -*- coding: utf-8 -*-
import os
from PyQt5 import QtCore, QtWidgets, QtGui, uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from widgets.shared.graphics import ImageFactory
from widgets import widgets

# EFFECT ENUMERATION - Represents a damage/resist type
class eEffectType:
    NORMAL = 1
    POISON = 2
    ENERGY = 4
    RADIATION = 6

# DAMAGE RESIST ICON CLASS
class DamageResistIcon:
    def __init__(self, imageFactory, imageFileName, widget, toolTip = ""):
        self.ImageFactory = imageFactory
        self.ImageName = imageFileName
        self.Widget = widget
        self.Text = str(toolTip)
        self.Color = QColor.fromRgb(255, 255, 255)
        self.Size = 39
        
        self.ImageData = None
        self.Scene = None
    
    def Update(self):
        self.ImageData = self.ImageFactory.getPixmap(self.ImageName, self.Size, self.Size, self.Color)
        
        self.Scene = QGraphicsScene()
        self.Scene.setSceneRect(0, 0, 40, 40)
        self.Scene.setBackgroundBrush(QBrush(QColor.fromRgb(0,0,0)))
        self.Scene.addPixmap(self.ImageData)
        
        if self.Text:
            self.Widget.setToolTip(self.Text)
            
        self.Widget.setScene(self.Scene)
        self.Widget.show()

# WIDGET CLASS
class StatsWidget(widgets.WidgetBase):
    _signalInfoUpdated = QtCore.pyqtSignal()
    PipColorUpdatedSignal = QtCore.pyqtSignal(QColor)
    
    # CLASS INIT
    def __init__(self, mhandle, parent):
        super().__init__('Player Statistics', parent)
        self.BasePath = mhandle.basepath
        self.widget = uic.loadUi(os.path.join(self.BasePath, 'ui', 'statswidget.ui'))
        self.setWidget(self.widget)
        self._signalInfoUpdated.connect(self.UpdateUI)
        self.PipColorUpdatedSignal.connect(self.UpdateIconColors)
    
    # QT INIT
    def init(self, app, datamanager):
        super().init(app, datamanager)
        
        # Create a class level hook to the datamanager for updates and RPC methods
        self.dataManager = datamanager
        self.dataManager.registerRootObjectListener(self.DataManagerUpdated)
        
        ImageLoader = ImageFactory(os.path.join(self.BasePath, "res"))
        self.Icons = [
            DamageResistIcon(ImageLoader, "damageicon.svg", self.widget.damageView, "Damage"),
            DamageResistIcon(ImageLoader, "resisticon.svg", self.widget.resistView, "Resists"),
            DamageResistIcon(ImageLoader, "effecttype-normal.svg", self.widget.typeNormalView, "Normal Typed"),
            DamageResistIcon(ImageLoader, "effecttype-energy.svg", self.widget.typeEnergyView, "Energy Typed"),
            DamageResistIcon(ImageLoader, "effecttype-poison.svg", self.widget.typePoisonView, "Poison Typed"),
            DamageResistIcon(ImageLoader, "effecttype-radiation.svg", self.widget.typeRadiationView, "Radiation Typed")
            ]
        for i in self.Icons:
            i.Update()
    
    # DATA MANAGER OBJECT HAS CHANGED AT SOME LEVEL
    def DataManagerUpdated(self, rootObject):
        # Create a class level hook to the data we are using
        self.PlayerInfoData = rootObject.child("PlayerInfo")
        self.StatsData = rootObject.child("Stats")
        self.StatusData = rootObject.child("Status").child("EffectColor")
        self.SpecialData = rootObject.child("Special")
        
        # We want to track Player Info data down to total damage/resist level
        if self.PlayerInfoData:
            self.PlayerInfoData.registerValueUpdatedListener(self.DataUpdated, 4)
        
        # We want to track Stats data down to its base level
        if self.StatsData:
            self.StatsData.registerValueUpdatedListener(self.DataUpdated, 2)
        
        # We want to track Status data down to its color information
        if self.StatusData:
            self.StatusData.registerValueUpdatedListener(self.ColorDataUpdated, 1)
            
            R = self.StatusData.child(0).value() * 255
            G = self.StatusData.child(1).value() * 255
            B = self.StatusData.child(2).value() * 255
            self.PipColorUpdatedSignal.emit(QColor.fromRgb(R, G, B))
        
        # We want to track Special data down to its base level
        if self.SpecialData:
            self.SpecialData.registerValueUpdatedListener(self.DataUpdated, 2)
        
        # Update Widget information
        self._signalInfoUpdated.emit()

    # DATA IN THE MANAGER HAS CHANGED
    def DataUpdated(self, caller, value, pathObjs):
        # Update UI
        self._signalInfoUpdated.emit()
    
    # PIPBOY COLOR IN THE MANAGER HAS CHANGED
    def ColorDataUpdated(self, caller, value, pathObjs):
        R = self.StatusData.child(0).value() * 255
        G = self.StatusData.child(1).value() * 255
        B = self.StatusData.child(2).value() * 255
        self.PipColorUpdatedSignal.emit(QColor.fromRgb(R, G, B))
    
    # UPDATE UI ELEMENTS
    @QtCore.pyqtSlot()
    def UpdateUI(self):
        self.UpdateLimbStatus()
        self.UpdateDamageResist()
        self.UpdateSpecial()
    
    # UPDATE ICONS
    @QtCore.pyqtSlot(QColor)
    def UpdateIconColors(self, iconColor):
        for i in self.Icons:
            i.Color = iconColor
            i.Update()
    
    # UPDATE LIMB STATUS
    def UpdateLimbStatus(self):
        if self.StatsData.childCount():
            self.widget.headStatus.setValue(self.StatsData.child("HeadCondition").value())
            self.widget.bodyStatus.setValue(self.StatsData.child("TorsoCondition").value())
            self.widget.leftarmStatus.setValue(self.StatsData.child("LArmCondition").value())
            self.widget.rightarmStatus.setValue(self.StatsData.child("RArmCondition").value())
            self.widget.leftlegStatus.setValue(self.StatsData.child("LLegCondition").value())
            self.widget.rightlegStatus.setValue(self.StatsData.child("RLegCondition").value())
    
    # UPDATE DAMAGE AND RESIST VALUES
    def UpdateDamageResist(self):
        self.widget.damageNormalLabel.setText("0")
        self.widget.damageEnergyLabel.setText("0")
        self.widget.damagePoisonLabel.setText("0")
        self.widget.damageRadiationLabel.setText("0")
        self.widget.resistNormalLabel.setText("0")
        self.widget.resistEnergyLabel.setText("0")
        self.widget.resistPoisonLabel.setText("0")
        self.widget.resistRadiationLabel.setText("0")
        
        if self.PlayerInfoData.childCount():
            for i in range(0, self.PlayerInfoData.child("TotalDamages").childCount()):
                DamageValue = int(self.PlayerInfoData.child("TotalDamages").child(i).child("Value").value())
                DamageType = self.PlayerInfoData.child("TotalDamages").child(i).child("type").value()
                
                if DamageType == eEffectType.NORMAL:
                    self.widget.damageNormalLabel.setText(str(DamageValue))
                elif DamageType == eEffectType.ENERGY:
                    self.widget.damageEnergyLabel.setText(str(DamageValue))
                elif DamageType == eEffectType.POISON:
                    self.widget.damagePoisonLabel.setText(str(DamageValue))
                elif DamageType == eEffectType.RADIATION:
                    self.widget.damageRadiationLabel.setText(str(DamageValue))
            
            for i in range(0, self.PlayerInfoData.child("TotalResists").childCount()):
                ResistValue = int(self.PlayerInfoData.child("TotalResists").child(i).child("Value").value())
                ResistType = self.PlayerInfoData.child("TotalResists").child(i).child("type").value()
                
                if ResistType == eEffectType.NORMAL:
                    self.widget.resistNormalLabel.setText(str(ResistValue))
                elif ResistType == eEffectType.ENERGY:
                    self.widget.resistEnergyLabel.setText(str(ResistValue))
                elif ResistType == eEffectType.POISON:
                    self.widget.resistPoisonLabel.setText(str(ResistValue))
                elif ResistType == eEffectType.RADIATION:
                    self.widget.resistRadiationLabel.setText(str(ResistValue))
    
    # UPDATE SPECIAL VALUES
    def UpdateSpecial(self):
        if self.SpecialData.childCount():
            for i in range(0, self.SpecialData.childCount()):
                Name = self.SpecialData.child(i).child("Name").value()
                Description = self.SpecialData.child(i).child("Description").value()
                Total = self.SpecialData.child(i).child("Value").value()
                Modifier = self.SpecialData.child(i).child("Modifier").value()
                Base = Total - Modifier
                
                TitleLabel = self.findChild(QtWidgets.QLabel, "titleS" + str(i + 1) + "Label")
                TitleLabel.setText(Name)
                TitleLabel.setToolTip(Description)
                
                BaseLabel = self.findChild(QtWidgets.QLabel, "baseS" + str(i + 1) + "Label")
                BaseLabel.setText(str(Base))
                
                ModLabel = self.findChild(QtWidgets.QLabel, "modS" + str(i + 1) + "Label")
                ModLabel.setText(str(Modifier))
                
                TotalLabel = self.findChild(QtWidgets.QLabel, "totalS" + str(i + 1) + "Label")
                TotalLabel.setText(str(Total))