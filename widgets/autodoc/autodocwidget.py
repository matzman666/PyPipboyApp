import os
import logging
from PyQt5 import QtCore, uic
from widgets import widgets

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
    
    DataManager = None
    PlayerInfoData = None
    StatsData = None
    InventoryData = None
    
    Enabled = False
    StimpakEnabled = True
    MedXEnabled = False
    RadAwayEnabled = True
    RadXEnabled = False
    
    StimpakPercent = 80
    MedXSetting = 0
    RadAwaySetting = 0
    RadXSetting = 0
    
    StimpakLimit = 10
    MedXLimit = 5
    RadAwayLimit = 10
    RadXLimit = 5
    
    StimpakNum = 0
    MedXNum = 0
    RadAwayNum = 0
    RadXNum = 0
    
    HPCur = 0
    HPLast = 0
    HPMax = 0
    HPPercent = 0
    
    Irradiated = False
    
    StimpakApplied = False
    MedXApplied = False
    RadAwayApplied = False
    RadXApplied = False
    
    MedXFormID = 210809
    RadXFormID = 147543
    
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
        
        self.Widgets.useWidget.stateChanged.connect(self.UseWidgetStateChanged)
        
        self.Widgets.stimpakUse.stateChanged.connect(self.StimpakUseStateChanged)
        self.Widgets.stimpakPercent.valueChanged.connect(self.StimpakPercentValueChanged)
        self.Widgets.stimpakLimit.textChanged.connect(self.StimpakLimitTextChanged)
        
        self.Widgets.medxUse.stateChanged.connect(self.MedXUseStateChanged)
        self.Widgets.medxUseType.currentIndexChanged.connect(self.MedXUseTypeIndexChanged)
        self.Widgets.medxLimit.textChanged.connect(self.MedXLimitTextChanged)
        
        self.Widgets.radawayUse.stateChanged.connect(self.RadAwayUseStateChanged)
        self.Widgets.radawayUseType.currentIndexChanged.connect(self.RadAwayUseTypeIndexChanged)
        self.Widgets.radawayLimit.textChanged.connect(self.RadAwayLimitTextChanged)
        
        self.Widgets.radxUse.stateChanged.connect(self.RadXUseStateChanged)
        self.Widgets.radxUseType.currentIndexChanged.connect(self.RadXUseTypeIndexChanged)
        self.Widgets.radxLimit.textChanged.connect(self.RadXLimitTextChanged)
    
    def init(self, app, dataManager):
        super().init(app, dataManager)
        
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
    
    def UpdatePlayerInfoData(self, caller, value, pathObjs):
        if self.Enabled:
            self.UpdateVitals()
            
            self.AutoDocSignal.emit()
            self.UIUpdateSignal.emit()
    
    def UpdateStatsData(self, caller, value, pathObjs):
        if self.Enabled:
            self.UpdatePipItems()
            self.UpdateEffects()
            
            self.AutoDocSignal.emit()
            self.UIUpdateSignal.emit()
        
    def UpdateInventoryData(self, caller, value, pathObjs):
        if self.Enabled:
            self.UpdateInventory()
            
            self.UIUpdateSignal.emit()

#################################
###                           ###
###   SETTINGS UPDATE SLOTS   ###
###                           ###
#################################

    @QtCore.pyqtSlot(QtCore.Qt.CheckState)
    def UseWidgetStateChanged(self, state):
        self.Enabled = (state == QtCore.Qt.Checked)
        self.UIUpdateSignal.emit()
    
    @QtCore.pyqtSlot(QtCore.Qt.CheckState)
    def StimpakUseStateChanged(self, state):
        self.StimpakEnabled = (state == QtCore.Qt.Checked)
        self.UIUpdateSignal.emit()
    
    @QtCore.pyqtSlot(int)
    def StimpakPercentValueChanged(self, value):
        self.StimpakPercent = value
        self.Widgets.stimpakPercentLabel.setText(str(self.StimpakPercent))

    @QtCore.pyqtSlot(str)
    def StimpakLimitTextChanged(self, value):
        if value:
            self.StimpakLimit = int(value)
        else:
            self.Widgets.stimpakLimit.setText("0")
    
    @QtCore.pyqtSlot(QtCore.Qt.CheckState)
    def MedXUseStateChanged(self, state):
        self.MedXEnabled = (state == QtCore.Qt.Checked)
        self.UIUpdateSignal.emit()
    
    @QtCore.pyqtSlot(int)
    def MedXUseTypeIndexChanged(self, index):
        self.MedXSetting = index
    
    @QtCore.pyqtSlot(str)
    def MedXLimitTextChanged(self, value):
        if value:
            self.MedXLimit = int(value)
        else:
            self.Widgets.medxLimit.setText("0")
    
    @QtCore.pyqtSlot(QtCore.Qt.CheckState)
    def RadAwayUseStateChanged(self, state):
        self.RadAwayEnabled = (state == QtCore.Qt.Checked)
        self.UIUpdateSignal.emit()
    
    @QtCore.pyqtSlot(int)
    def RadAwayUseTypeIndexChanged(self, index):
        self.RadAwaySetting = index
    
    @QtCore.pyqtSlot(str)
    def RadAwayLimitTextChanged(self, value):
        if value:
            self.RadAwayLimit = int(value)
        else:
            self.Widgets.radawayLimit.setText("0")
    
    @QtCore.pyqtSlot(QtCore.Qt.CheckState)
    def RadXUseStateChanged(self, state):
        self.RadXEnabled = (state == QtCore.Qt.Checked)
        self.UIUpdateSignal.emit()

    @QtCore.pyqtSlot(int)
    def RadXUseTypeIndexChanged(self, index):
        self.RadXSetting = index
    
    @QtCore.pyqtSlot(str)
    def RadXLimitTextChanged(self, value):
        if value:
            self.RadXLimit = int(value)
        else:
            self.Widgets.radxLimit.setText("0")

#############################
###                       ###
###   SIGNAL EMIT SLOTS   ###
###                       ###
#############################

    @QtCore.pyqtSlot()
    def RunAutoDoc(self):
        if self.Enabled and (self.HPPercent > 0):
            # Stimpak Trigger
            if self.HPPercent < self.StimpakPercent:
                # Rad Away No Healing Trigger
                if self.StimpakApplied:
                    if self.HPCur == self.HPLast:
                        if self.RadAwaySetting == 1:
                            self.UseRadAway()
                            
                            # Rad-X RadAway Use Trigger
                            if self.RadXSetting == 1:
                                self.UseRadX()
                else:
                    self.UseStimpack()
                
                # Med-X %HP Trigger
                if self.MedXSetting == 1:
                    self.UseMedX()
            
            # Med-X Damaged Trigger
            if self.HPCur < self.HPLast:
                if self.MedXSetting == 0:
                    self.UseMedX()
            
            # Med-X 3/4 Trigger
            if self.HPPercent < 75:
                if self.MedXSetting == 2:
                    self.UseMedX()
                
            # Med-X 1/2 Trigger
            if self.HPPercent < 50:
                if self.MedXSetting == 3:
                    self.UseMedX()
            
            # Med-X 1/4 Trigger
            if self.HPPercent < 25:
                if self.MedXSetting == 4:
                    self.UseMedX()
            
            if self.Irradiated:
                # Rad Away Irradiated Trigger
                if self.RadAwaySetting == 0:
                    self.UseRadAway()
                    
                    # Rad-X RadAway Use Trigger
                    if self.RadXSetting == 1:
                        self.UseRadX()
                
                # Rad-X Irradiated Trigger
                if self.RadXSetting == 0:
                    self.UseRadX()
            
    @QtCore.pyqtSlot()
    def UpdateUI(self):
        if self.Enabled:

            Output = "Health [ " + str(self.HPCur) + "/" + str(self.HPMax) + " ] "
            Output += "[ " + str(self.HPPercent) + "/" + str(self.StimpakPercent) + " ] "
            
            if self.Irradiated:
                Output += "<< Irradiated >>"
            
            Output += "\n"
            Output += "Chem Stock [ "
            
            if self.StimpakEnabled or self.MedXEnabled or self.RadAwayEnabled or self.RadXEnabled:
                if self.StimpakEnabled:
                    Output += "ST(" + str(self.StimpakNum) + "/" + str(self.StimpakLimit) + ") "
                
                if self.MedXEnabled:
                    Output += "MX(" + str(self.MedXNum) + "/" + str(self.MedXLimit) + ") "
                
                if self.RadAwayEnabled:
                    Output += "RA(" + str(self.RadAwayNum) + "/" + str(self.RadAwayLimit) + ") "
                    
                if self.RadXEnabled:
                    Output += "RX(" + str(self.RadXNum) + "/" + str(self.RadXLimit) + ") "
            else:
                Output += "Disabled "
                
            Output += "]\n"
            Output += "Chem Applied [ "
            
            if self.StimpakApplied or self.MedXApplied or self.RadAwayApplied or self.RadXApplied:
                if self.StimpakApplied:
                    Output += "Stimpak "
                
                if self.MedXApplied:
                    Output += "Med-X "
                    
                if self.RadAwayApplied:
                    Output += "RadAway "
                
                if self.RadXApplied:
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
    
    def UpdateVitals(self):
        self.HPLast = self.HPCur
        
        if self.PlayerInfoData.childCount():
            self.HPCur = int(self.PlayerInfoData.child("CurrHP").value())
            self.HPMax = int(self.PlayerInfoData.child("MaxHP").value())
            
            if self.HPMax != 0:
                self.HPPercent = int((self.HPCur / self.HPMax) * 100)
    
    def UpdatePipItems(self):
        if self.StatsData.childCount():
            self.StimpakNum = self.StatsData.child("StimpakCount").value()
            self.RadAwayNum = self.StatsData.child("RadawayCount").value()
    
    def UpdateEffects(self):
        self.StimpakApplied = False
        self.MedXApplied = False
        self.RadAwayApplied = False
        self.RadXApplied = False
        self.Irradiated = False
        
        if self.StatsData:
            if self.StatsData.child("ActiveEffects"):
                ActiveEffectsData = self.StatsData.child("ActiveEffects")
                
                for i in range(0, ActiveEffectsData.childCount()):
                    TypeID = ActiveEffectsData.child(i).child("type").value()
                    
                    if TypeID == 54:
                        for j in range(0, ActiveEffectsData.child(i).child("Effects").childCount()):
                            EffectName = ActiveEffectsData.child(i).child("Effects").child(j).child("Name").value()
                            
                            if EffectName == "Rads":
                                self.Irradiated = True
                    
                    if TypeID == 44:
                        self.StimpakApplied = True
                        
                    if TypeID == 41:
                        for j in range(0, ActiveEffectsData.child(i).child("Effects").childCount()):
                            EffectName = ActiveEffectsData.child(i).child("Effects").child(j).child("Name").value()
                            
                            if EffectName == "DMG Resist":
                                self.MedXApplied = True
                            
                            if EffectName == "Rads":
                                if ActiveEffectsData.child(i).child("Effects").child(j).child("Value").value() < 0:
                                    self.RadAwayApplied = True
                            
                            if EffectName == "Rad Resist":
                                self.RadXApplied = True
    
    def UpdateInventory(self):
        if self.InventoryData:
            if self.InventoryData.child("48"):
                AidData = self.InventoryData.child("48")

                for i in range(0, AidData.childCount()):
                    FormID = AidData.child(i).child("formID").value()
                    Count = AidData.child(i).child("count").value()
                    
                    if FormID == self.MedXFormID:
                        self.MedXNum = Count
                    
                    if FormID == self.RadXFormID:
                        self.RadXNum = Count
            
    def UseStimpack(self):
        if (self.StimpakNum > self.StimpakLimit) and (self.StimpakNum > 0):
            if not self.StimpakApplied:
                if self.StimpakEnabled:
                    self.DataManager.rpcUseStimpak()
    
    def UseMedX(self):
        if (self.MedXNum > self.MedXLimit) and (self.MedXNum > 0):
            if not self.MedXApplied:
                if self.MedXEnabled:
                    self.UseAidItem(self.MedXFormID)
    
    def UseRadAway(self):
        if (self.RadAwayNum > self.RadAwayLimit) and (self.RadAwayNum > 0):
            if not self.RadAwayApplied:
                if self.RadAwayEnabled:
                    self.DataManager.rpcUseRadAway()
    
    def UseRadX(self):
        if (self.RadXNum > self.RadXLimit) and (self.RadXNum > 0):
            if not self.RadXApplied:
                if self.RadXEnabled:
                    self.UseAidItem(self.RadXFormID)
    
    def UseAidItem(self, formID):
        if self.InventoryData:
            if self.InventoryData.child("48"):
                for i in range(0, self.InventoryData.child("48").childCount()):
                    if self.InventoryData.child("48").child(i).child("formID").value() == formID:
                        self.DataManager.rpcUseItem(self.InventoryData.child("48").child(i))