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
        self.TotalDamageData = rootObject.child("PlayerInfo").child("TotalDamages")
        self.TotalResistsData = rootObject.child("PlayerInfo").child("TotalResists")
        self.StatusData = rootObject.child("Status").child("EffectColor")
        
        if self.TotalDamageData:
            self.TotalDamageData.registerValueUpdatedListener(self.DataUpdated, 2)
        
        if self.TotalResistsData:
            self.TotalResistsData.registerValueUpdatedListener(self.DataUpdated, 2)

        # We want to track Status data down to its color information
        if self.StatusData:
            self.StatusData.registerValueUpdatedListener(self.ColorDataUpdated, 1)
            
            R = self.StatusData.child(0).value() * 255
            G = self.StatusData.child(1).value() * 255
            B = self.StatusData.child(2).value() * 255
            self.PipColorUpdatedSignal.emit(QColor.fromRgb(R, G, B))

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

    # UPDATE ICONS
    @QtCore.pyqtSlot(QColor)
    def UpdateIconColors(self, iconColor):
        for i in self.Icons:
            i.Color = iconColor
            i.Update()      
    
    # UPDATE UI ELEMENTS
    @QtCore.pyqtSlot()
    def UpdateUI(self):
        self.widget.damageNormalLabel.setText("0")
        self.widget.damageEnergyLabel.setText("0")
        self.widget.damagePoisonLabel.setText("0")
        self.widget.damageRadiationLabel.setText("0")
        self.widget.resistNormalLabel.setText("0")
        self.widget.resistEnergyLabel.setText("0")
        self.widget.resistPoisonLabel.setText("0")
        self.widget.resistRadiationLabel.setText("0")
        
        if self.TotalDamageData:
            for i in range(0, self.TotalDamageData.childCount()):
                DamageValue = int(self.TotalDamageData.child(i).child("Value").value())
                DamageType = self.TotalDamageData.child(i).child("type").value()
                
                if DamageType == eEffectType.NORMAL:
                    self.widget.damageNormalLabel.setText(str(DamageValue))
                elif DamageType == eEffectType.ENERGY:
                    self.widget.damageEnergyLabel.setText(str(DamageValue))
                elif DamageType == eEffectType.POISON:
                    self.widget.damagePoisonLabel.setText(str(DamageValue))
                elif DamageType == eEffectType.RADIATION:
                    self.widget.damageRadiationLabel.setText(str(DamageValue))
            
        if self.TotalResistsData:
            for i in range(0, self.TotalResistsData.childCount()):
                ResistValue = int(self.TotalResistsData.child(i).child("Value").value())
                ResistType = self.TotalResistsData.child(i).child("type").value()
                
                if ResistType == eEffectType.NORMAL:
                    self.widget.resistNormalLabel.setText(str(ResistValue))
                elif ResistType == eEffectType.ENERGY:
                    self.widget.resistEnergyLabel.setText(str(ResistValue))
                elif ResistType == eEffectType.POISON:
                    self.widget.resistPoisonLabel.setText(str(ResistValue))
                elif ResistType == eEffectType.RADIATION:
                    self.widget.resistRadiationLabel.setText(str(ResistValue))