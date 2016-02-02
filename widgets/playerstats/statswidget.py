import os
from PyQt5 import QtCore, QtWidgets, QtGui, uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from widgets.shared.graphics import ImageFactory
from widgets import widgets
from widgets.shared.PipboyIcon import PipboyIcon

# EFFECT ENUMERATION - Represents a damage/resist type
class eEffectType:
    NORMAL = 1
    POISON = 2
    ENERGY = 4
    RADIATION = 6

# WIDGET CLASS
class StatsWidget(widgets.WidgetBase):
    UIUpdateSignal = QtCore.pyqtSignal()
    ColorUpdateSignal = QtCore.pyqtSignal(QColor)
    
    Widgets = None
    
    DataManager = None
    PlayerInfoData = None
    ColorData = None
    
    Icons = None
    
    # CLASS INIT
    def __init__(self, mhandle, parent):
        super().__init__('Combat Stats', parent)
        self.Widgets = uic.loadUi(os.path.join(mhandle.basepath, 'ui', 'statswidget.ui'))
        self.setWidget(self.Widgets)
        
        self.Icons = [
            PipboyIcon("Target.svg", self.Widgets.damageView, 40, "Damage"),
            PipboyIcon("Shield.svg", self.Widgets.resistView, 40, "Resists"),
            PipboyIcon("Pow.svg", self.Widgets.typeNormalView, 40, "Normal Typed"),
            PipboyIcon("Energy.svg", self.Widgets.typeEnergyView, 40, "Energy Typed"),
            PipboyIcon("Drop.svg", self.Widgets.typePoisonView, 40, "Poison Typed"),
            PipboyIcon("Radiation.svg", self.Widgets.typeRadiationView, 40, "Radiation Typed")
        ]
        
        for i in self.Icons:
            i.Update()
        
        self.UIUpdateSignal.connect(self.UpdateUI)
        self.ColorUpdateSignal.connect(self.UpdateIconColor)
    
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
        # Create a class level hook to the data we are using
        self.PlayerInfoData = rootObject.child("PlayerInfo")
        self.ColorData = rootObject.child("Status").child("EffectColor")
        
        if self.PlayerInfoData:
            self.PlayerInfoData.registerValueUpdatedListener(self.DataUpdated, 4)
            
        # We want to track Status data down to its color information
        if self.ColorData:
            self.ColorData.registerValueUpdatedListener(self.ColorDataUpdated, 1)
            
            R = self.ColorData.child(0).value() * 255
            G = self.ColorData.child(1).value() * 255
            B = self.ColorData.child(2).value() * 255
            
            self.ColorUpdateSignal.emit(QColor.fromRgb(R, G, B))

        # Update Widget information
        self.UIUpdateSignal.emit()

    # DATA IN THE MANAGER HAS CHANGED
    def DataUpdated(self, caller, value, pathObjs):
        self.UIUpdateSignal.emit()
    
    # PIPBOY COLOR IN THE MANAGER HAS CHANGED
    def ColorDataUpdated(self, caller, value, pathObjs):
        R = self.ColorData.child(0).value() * 255
        G = self.ColorData.child(1).value() * 255
        B = self.ColorData.child(2).value() * 255
        
        self.ColorUpdateSignal.emit(QColor.fromRgb(R, G, B))

    # UPDATE ICONS
    @QtCore.pyqtSlot(QColor)
    def UpdateIconColor(self, iconColor):
        for i in self.Icons:
            i.Color = iconColor
            i.Update()      
    
    # UPDATE UI ELEMENTS
    @QtCore.pyqtSlot()
    def UpdateUI(self):
        if self.isVisible():
            self.Widgets.damageNormalLabel.setText("0")
            self.Widgets.damageEnergyLabel.setText("0")
            self.Widgets.damagePoisonLabel.setText("0")
            self.Widgets.damageRadiationLabel.setText("0")
            self.Widgets.resistNormalLabel.setText("0")
            self.Widgets.resistEnergyLabel.setText("0")
            self.Widgets.resistPoisonLabel.setText("0")
            self.Widgets.resistRadiationLabel.setText("0")
            
            if self.PlayerInfoData:
                DamageData = self.PlayerInfoData.child("TotalDamages")
                ResistsData = self.PlayerInfoData.child("TotalResists")
                
                if DamageData:
                    for i in range(0, DamageData.childCount()):
                        DamageValue = int(DamageData.child(i).child("Value").value())
                        DamageType = DamageData.child(i).child("type").value()
                        
                        if DamageType == eEffectType.NORMAL:
                            self.Widgets.damageNormalLabel.setText(str(DamageValue))
                        elif DamageType == eEffectType.ENERGY:
                            self.Widgets.damageEnergyLabel.setText(str(DamageValue))
                        elif DamageType == eEffectType.POISON:
                            self.Widgets.damagePoisonLabel.setText(str(DamageValue))
                        elif DamageType == eEffectType.RADIATION:
                            self.Widgets.damageRadiationLabel.setText(str(DamageValue))
                
                if ResistsData:
                    for i in range(0, ResistsData.childCount()):
                        ResistValue = int(ResistsData.child(i).child("Value").value())
                        ResistType = ResistsData.child(i).child("type").value()
                        
                        if ResistType == eEffectType.NORMAL:
                            self.Widgets.resistNormalLabel.setText(str(ResistValue))
                        elif ResistType == eEffectType.ENERGY:
                            self.Widgets.resistEnergyLabel.setText(str(ResistValue))
                        elif ResistType == eEffectType.POISON:
                            self.Widgets.resistPoisonLabel.setText(str(ResistValue))
                        elif ResistType == eEffectType.RADIATION:
                            self.Widgets.resistRadiationLabel.setText(str(ResistValue))