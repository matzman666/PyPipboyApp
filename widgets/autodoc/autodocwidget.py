import os
import logging
from PyQt5 import QtCore, uic
from widgets import widgets
from .autodocsettingsdialog import AutoDocSettingsDialog

class MedicalFeature:
    Enabled = None
    Setting = None
    Limit = None
    FormID = None
    
    Num = None
    Active = None
    
    UseFlag = None
    UseTimer = None
    UseTimerDelay = None
    UseMethod = None
    
    def __init__(self, startEnabled, startSetting, startLimit, formID):
        self.Enabled = startEnabled
        self.Setting = startSetting
        self.Limit = startLimit
        self.FormID = formID
        
        self.Num = 0
        self.Active = False
        
        self.UseFlag = False
        self.UseTimer = QtCore.QTimer()
        self.UseTimer.setSingleShot(True)
        self.UseTimer.timeout.connect(self.UseTimerTimeout)
        self.UseTimerDelay = 2000
    
    def connect(self, useMethod):
        self.UseMethod = useMethod
    
    def Use(self):
        if self.Enabled:
            if (self.Num > self.Limit) and (self.Num > 0):
                if not self.Active:
                    if not self.UseFlag:
                        self.UseMethod(self.FormID)
                        self.UseTimer.start(self.UseTimerDelay)
                        self.UseFlag = True
        
    def UseTimerTimeout(self):
        self.UseFlag = False

class AutoDocWidget(widgets.WidgetBase):
    
#############################
###                       ###
###   WIDGET PROPERTIES   ###
###                       ###
#############################
    
    UIUpdateSignal = QtCore.pyqtSignal()
    AutoDocSignal = QtCore.pyqtSignal()
    
    Widgets = None
    Logger = None
    Settings = None
    
    DataManager = None
    PlayerInfoData = None
    StatsData = None
    InventoryData = None
    
    WidgetEnabled = True
    
    HPCur = 0
    HPLast = 0
    HPMax = 0
    HPPercent = 0
    
    # RadStates:
    # 0 - Clean
    # 1 - Been Irradiated
    # 2 - Being Irradiated
    RadState = 0
    Addicted = False
    Aquaperson = False
    InWater = False
    
    StimpakRadAwayFlag = False
    # Activates when you trigger the no heal case because of radiation.
    # Prevents additional stims from being taken
    
    Stimpak = MedicalFeature(True, 80, 10, 145206)
    MedX = MedicalFeature(False, 0, 5, 210809)
    RadAway = MedicalFeature(True, 0, 10, 145218)
    RadX = MedicalFeature(False, 0, 5, 147543)
    Addictol = MedicalFeature(False, 0, 5, 285125)
    
#########################################
###                                   ###
###   WIDGET INITIALIZATION METHODS   ###
###                                   ###
#########################################
    
    def __init__(self, mhandle, parent):
        super().__init__("Auto Doc", parent)
        
        self.Logger = logging.getLogger("pypipboyapp.widgets.autodoc")
        
        self.Widgets = uic.loadUi(os.path.join(mhandle.basepath, "ui", "autodocwidget.ui"))
        self.setWidget(self.Widgets)
        
        self.UIUpdateSignal.connect(self.UpdateUI)
        self.AutoDocSignal.connect(self.RunAutoDoc)
        
        self.Widgets.openSettingsButton.clicked.connect(self.OpenSettingsButtonClicked)
        
        self.Stimpak.connect(self.UseAidItem)
        self.MedX.connect(self.UseAidItem)
        self.RadAway.connect(self.UseAidItem)
        self.RadX.connect(self.UseAidItem)
        self.Addictol.connect(self.UseAidItem)
    
    def init(self, app, dataManager):
        super().init(app, dataManager)
        
        self.Settings = app.settings
        self.UpdateSettings()
        
        self.DataManager = dataManager
        self.DataManager.registerRootObjectListener(self.DataManagerUpdated)
        
#################################
###                           ###
###   DATA UPDATE LISTENERS   ###
###                           ###
#################################
    
    def DataManagerUpdated(self, rootObject):
        self.PlayerInfoData = rootObject.child("PlayerInfo")
        self.StatsData = rootObject.child("Stats")
        self.InventoryData = rootObject.child("Inventory")
        
        if self.PlayerInfoData:
            self.PlayerInfoData.registerValueUpdatedListener(self.UpdatePlayerInfoData, 1)
            self.UpdateVitals()
        
        if self.StatsData:
            self.StatsData.registerValueUpdatedListener(self.UpdateStatsData, 1)
            self.UpdatePipItems()
            self.UpdateEffects()

        if self.InventoryData:
            self.InventoryData.registerValueUpdatedListener(self.UpdateInventoryData, 1)
            self.UpdateInventory()
        
        self.UIUpdateSignal.emit()
    
    def UpdatePlayerInfoData(self, caller, value, pathObjs):
        if self.WidgetEnabled:
            self.UpdateVitals()
            
            self.AutoDocSignal.emit()
            self.UIUpdateSignal.emit()
    
    def UpdateStatsData(self, caller, value, pathObjs):
        if self.WidgetEnabled:
            self.UpdatePipItems()
            self.UpdateEffects()
            
            self.AutoDocSignal.emit()
            self.UIUpdateSignal.emit()
        
    def UpdateInventoryData(self, caller, value, pathObjs):
        if self.WidgetEnabled:
            self.UpdateInventory()
            
            self.UIUpdateSignal.emit()

##############################
###                        ###
###   WIDGET EVENT SLOTS   ###
###                        ###
##############################

    @QtCore.pyqtSlot()
    def OpenSettingsButtonClicked(self):
        SettingsWindow = AutoDocSettingsDialog(self.Settings)
        SettingsWindow.exec()
        
        self.UpdateSettings()
        self.UIUpdateSignal.emit()

#############################
###                       ###
###   SIGNAL EMIT SLOTS   ###
###                       ###
#############################

    # The AutoDoc runs so often (not a bad thing really) that it likes
    # to submit UseItem commands very quickly (oh the joys of async) and
    # therefore use multiple items before the game reports back that the
    # item in question is active. So each item has a timer associated
    # with it that trips a flag to prevent use for a time.

    @QtCore.pyqtSlot()
    def RunAutoDoc(self):
        if self.WidgetEnabled and (self.HPPercent > 0):
            # Stimpak Trigger
            if self.HPPercent < self.Stimpak.Setting:
                # Rad Away No Healing Trigger
                if self.Stimpak.Active:
                    if (self.HPCur == self.HPLast) and (self.HPCur != self.HPMax):
                        if (self.RadAway.Num <= self.RadAway.Limit) or (self.RadAway.Num == 0):
                            if not self.StimpakRadAwayFlag:
                                self.StimpakRadAwayFlag = True
                        
                        if self.RadAway.Setting == 1:
                            # Rad-X RadAway Use Trigger
                            if self.RadX.Setting == 1:
                                self.RadX.Use()
                                
                            self.RadAway.Use()
                else:
                    if not self.StimpakRadAwayFlag:
                        self.Stimpak.Use()
                
                # Med-X %HP Trigger
                if self.MedX.Setting == 1:
                    self.MedX.Use()
            
            # Med-X Damaged Trigger
            if self.HPCur < self.HPLast:
                if self.MedX.Setting == 0:
                    self.MedX.Use()
            
            # Med-X 3/4 Trigger
            if self.HPPercent < 75:
                if self.MedX.Setting == 2:
                    self.MedX.Use()
                
            # Med-X 1/2 Trigger
            if self.HPPercent < 50:
                if self.MedX.Setting == 3:
                    self.MedX.Use()
            
            # Med-X 1/4 Trigger
            if self.HPPercent < 25:
                if self.MedX.Setting == 4:
                    self.MedX.Use()
            
            if self.RadState > 0:
                # Rad-X Irradiated Trigger
                if self.RadX.Setting == 0:
                    self.RadX.Use()
                    
                # Rad Away Irradiated Trigger
                if self.RadAway.Setting == 0:
                    # Rad-X RadAway Use Trigger
                    if self.RadX.Setting == 1:
                        self.RadX.Use()
                        
                    self.RadAway.Use()
            
            # Addictol Trigger
            if self.Addicted:
                self.Addictol.Use()
            
    @QtCore.pyqtSlot()
    def UpdateUI(self):
        if self.WidgetEnabled:
            Output = "Health [ " + str(self.HPCur) + "/" + str(self.HPMax) + " ] "
            Output += "[ " + str(self.HPPercent) + "/" + str(self.Stimpak.Setting) + " ] "
            
            if self.RadState > 0:
                if self.RadState == 1:
                    Output += "<< Irradiated >> "
                elif self.RadState == 2:
                    Output += "<< Radiation >> "
            
            if self.Addicted:
                Output += "<< Addicted >>"
            
            Output += "\n"
            Output += "Chem Stock [ "
            
            if self.Stimpak.Enabled or self.MedX.Enabled or self.RadAway.Enabled or self.RadX.Enabled or self.Addictol.Enabled:
                if self.Stimpak.Enabled:
                    Output += "ST(" + str(self.Stimpak.Num) + "/" + str(self.Stimpak.Limit) + ") "
                
                if self.MedX.Enabled:
                    Output += "MX(" + str(self.MedX.Num) + "/" + str(self.MedX.Limit) + ") "
                
                if self.RadAway.Enabled:
                    Output += "RA(" + str(self.RadAway.Num) + "/" + str(self.RadAway.Limit) + ") "
                    
                if self.RadX.Enabled:
                    Output += "RX(" + str(self.RadX.Num) + "/" + str(self.RadX.Limit) + ") "
                
                if self.Addictol.Enabled:
                    Output += "AD(" + str(self.Addictol.Num) + "/" + str(self.Addictol.Limit) + ") "
            else:
                Output += "Disabled "
                
            Output += "]\n"
            Output += "Chem Applied [ "
            
            if self.Stimpak.Active or self.MedX.Active or self.RadAway.Active or self.RadX.Active:
                if self.Stimpak.Active:
                    Output += "Stimpak "
                
                if self.MedX.Active:
                    Output += "Med-X "
                    
                if self.RadAway.Active:
                    Output += "RadAway "
                
                if self.RadX.Active:
                    Output += "Rad-X "
            else:
                Output += "None "
                
            Output += "]\n"
            
            self.Widgets.watcherLabel.setText(Output)
        else:
            self.Widgets.watcherLabel.setText("The Auto Doc has been turned off!")
        
########################
###                  ###
###   USER METHODS   ###
###                  ###
########################
    
    def UpdateSettings(self):
        self.WidgetEnabled = bool(int(self.Settings.value("AutoDocWidget/Enabled", 0)))
        self.Stimpak.Enabled = bool(int(self.Settings.value("AutoDocWidget/Stimpak/Enabled", 1)))
        self.MedX.Enabled = bool(int(self.Settings.value("AutoDocWidget/MedX/Enabled", 0)))
        self.RadAway.Enabled = bool(int(self.Settings.value("AutoDocWidget/RadAway/Enabled", 1)))
        self.RadX.Enabled = bool(int(self.Settings.value("AutoDocWidget/RadX/Enabled", 0)))
        self.Addictol.Enabled = bool(int(self.Settings.value("AutoDocWidget/Addictol/Enabled", 0)))
       
        TimerDelay = int(self.Settings.value("AutoDocWidget/General/TimerDelay", 2000))
        self.Stimpak.UseTimerDelay = TimerDelay
        self.MedX.UseTimerDelay = TimerDelay
        self.RadAway.UseTimerDelay = TimerDelay
        self.RadX.UseTimerDelay = TimerDelay
        self.Addictol.UseTimerDelay = TimerDelay
        
        self.Stimpak.Setting = int(self.Settings.value("AutoDocWidget/Stimpak/Percent", 80))
        self.Stimpak.Limit = int(self.Settings.value("AutoDocWidget/Stimpak/Limit", 10))
        
        self.MedX.Setting = int(self.Settings.value("AutoDocWidget/MedX/Use", 0))
        self.MedX.Limit = int(self.Settings.value("AutoDocWidget/MedX/Limit", 5))
        
        self.RadAway.Setting = int(self.Settings.value("AutoDocWidget/RadAway/Use", 0))
        self.RadAway.Limit = int(self.Settings.value("AutoDocWidget/RadAway/Limit", 10))
        
        self.RadX.Setting = int(self.Settings.value("AutoDocWidget/RadX/Use", 0))
        self.RadX.Limit = int(self.Settings.value("AutoDocWidget/RadX/Limit", 5))
        
        self.Addictol.Limit = int(self.Settings.value("AutoDocWidget/Addictol/Limit", 5))
    
    def UpdateVitals(self):
        self.HPLast = self.HPCur
        
        if self.PlayerInfoData.childCount():
            self.HPCur = int(self.PlayerInfoData.child("CurrHP").value())
            self.HPMax = int(self.PlayerInfoData.child("MaxHP").value())
            
            if self.HPMax != 0:
                self.HPPercent = int((self.HPCur / self.HPMax) * 100)
    
    def UpdatePipItems(self):
        if self.StatsData.childCount():
            self.Stimpak.Num = self.StatsData.child("StimpakCount").value()
            self.RadAway.Num = self.StatsData.child("RadawayCount").value()
    
    def UpdateEffects(self):
        self.Stimpak.Active = False
        self.MedX.Active = False
        self.RadAway.Active = False
        self.RadX.Active = False
        
        self.Addicted = False
        self.InWater = False
        
        if self.RadState == 2:
            self.RadState = 1
        else:
            self.RadState = 0
        
        if self.StatsData:
            if self.StatsData.child("ActiveEffects"):
                ActiveEffectsData = self.StatsData.child("ActiveEffects")
                
                for i in range(0, ActiveEffectsData.childCount()):
                    TypeID = ActiveEffectsData.child(i).child("type").value()
                    
                    if TypeID == 54:
                        for j in range(0, ActiveEffectsData.child(i).child("Effects").childCount()):
                            EffectName = ActiveEffectsData.child(i).child("Effects").child(j).child("Name").value()
                            
                            if (EffectName == "Waterbreathing") and not self.Aquaperson:
                                self.Aquaperson = True
                                
                            if EffectName == "Rads":
                                if ActiveEffectsData.child(i).child("Source").value() == "Water Radiation":
                                    self.InWater = True
                                else:
                                    self.RadState = 2
                    
                    if TypeID == 49:
                        if ActiveEffectsData.child(i).child("Source").value() == "Alcohol Addiction":
                            self.Addicted = True
                    
                    if TypeID == 44:
                        self.Stimpak.Active = True
                        
                    if TypeID == 41:
                        for j in range(0, ActiveEffectsData.child(i).child("Effects").childCount()):
                            EffectName = ActiveEffectsData.child(i).child("Effects").child(j).child("Name").value()
                            
                            if EffectName == "CA_AddictionEffect":
                                self.Addicted = True
                            
                            if EffectName == "DMG Resist":
                                if ActiveEffectsData.child(i).child("Effects").child(j).child("Value").value() > 0:
                                    self.MedX.Active = True
                            
                            if EffectName == "Rads":
                                if ActiveEffectsData.child(i).child("Effects").child(j).child("Value").value() < 0:
                                    self.RadAway.Active = True
                                    self.StimpakRadAwayFlag = False
                                    self.RadState = 0
                            
                            if EffectName == "Rad Resist":
                                if ActiveEffectsData.child(i).child("Effects").child(j).child("Value").value() > 0:
                                    self.RadX.Active = True
        
        if self.InWater and not self.Aquaperson:
            self.RadState = 2
    
    def UpdateInventory(self):
        if self.InventoryData:
            if self.InventoryData.child("48"):
                AidData = self.InventoryData.child("48")
                MedXFound = False
                RadXFound = False
                AddictolFound = False

                for i in range(0, AidData.childCount()):
                    FormID = AidData.child(i).child("formID").value()
                    Count = AidData.child(i).child("count").value()
                    
                    if FormID == self.MedX.FormID:
                        self.MedX.Num = Count
                        MedXFound = True
                    
                    if FormID == self.RadX.FormID:
                        self.RadX.Num = Count
                        RadXFound = True
                    
                    if FormID == self.Addictol.FormID:
                        self.Addictol.Num = Count
                        AddictolFound = True
                
                if not MedXFound:
                    self.MedX.Num = 0
                
                if not RadXFound:
                    self.RadX.Num = 0
                
                if not AddictolFound:
                    self.Addictol.Num = 0
    
    def UseAidItem(self, formID):
        if self.InventoryData:
            if self.InventoryData.child("48"):
                for i in range(0, self.InventoryData.child("48").childCount()):
                    if self.InventoryData.child("48").child(i).child("formID").value() == formID:
                        self.DataManager.rpcUseItem(self.InventoryData.child("48").child(i))