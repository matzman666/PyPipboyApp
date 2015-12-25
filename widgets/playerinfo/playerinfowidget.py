# -*- coding: utf-8 -*-


import datetime
import os
import math
from PyQt5 import QtWidgets, QtCore, uic
from pypipboy.types import eValueType
from widgets import widgets


class PlayerInfoWidget(widgets.WidgetBase):
    _signalInfoUpdated = QtCore.pyqtSignal()
    
    def __init__(self, handle, controller, parent):
        super().__init__('Player Info', parent)
        self.controller = controller
        self.widget = uic.loadUi(os.path.join(handle.basepath, 'ui', 'playerinfowidget.ui'))
        self.setWidget(self.widget)
        self.pipPlayerInfo = None
        self.maxHP = 0
        self.curHP = 0
        self.maxAP = 0
        self.curAP = 0
        self.maxWT = 0
        self.curWT = 0
        self.xpLevel = 0
        self.xpProgress = 0.0
        self.caps = 0
        self.wtBarOverWeightState = False
        self.wtBarLastTextVisible = None
        self._signalInfoUpdated.connect(self._slotInfoUpdated)
        
    def init(self, app, datamanager):
        super().init(app, datamanager)
        self.dataManager = datamanager
        self.dataManager.registerRootObjectListener(self._onPipRootObjectEvent)
        
    def _onPipRootObjectEvent(self, rootObject):
        self.pipPlayerInfo = rootObject.child('PlayerInfo')
        if self.pipPlayerInfo:
            self.pipPlayerInfo.registerValueUpdatedListener(self._onPipPlayerInfoUpdate, 1)
        self._signalInfoUpdated.emit()

    def _onPipPlayerInfoUpdate(self, caller, value, pathObjs):
        self._signalInfoUpdated.emit()
        
    @QtCore.pyqtSlot()
    def _slotInfoUpdated(self):
        maxHP = self.pipPlayerInfo.child('MaxHP')
        if maxHP:
            self.maxHP = maxHP.value()
        curHP = self.pipPlayerInfo.child('CurrHP')
        if curHP:
            self.curHP = curHP.value()
        maxAP = self.pipPlayerInfo.child('MaxAP')
        if maxAP:
            self.maxAP = maxAP.value()
        curAP = self.pipPlayerInfo.child('CurrAP')
        if curAP:
            self.curAP = curAP.value()
        maxWT = self.pipPlayerInfo.child('MaxWeight')
        if maxWT:
            self.maxWT = maxWT.value()
        curWT = self.pipPlayerInfo.child('CurrWeight')
        if curWT:
            self.curWT = curWT.value()
        xpLevel = self.pipPlayerInfo.child('XPLevel')
        if xpLevel:
            self.xpLevel = xpLevel.value()
        xpProgress = self.pipPlayerInfo.child('XPProgressPct')
        if xpProgress:
            self.xpProgress = xpProgress.value()
        caps = self.pipPlayerInfo.child('Caps')
        if caps:
            self.caps = caps.value()
        if self.maxHP > 0:
            self.widget.hpBar.setValue((self.curHP*100)/self.maxHP)
        self.widget.hpLabel.setText(str(int(self.curHP)) + ' / ' + str(int(self.maxHP)))
        if self.maxAP > 0:
            self.widget.apBar.setValue((self.curAP*100)/self.maxAP)
        self.widget.apLabel.setText(str(int(self.curAP)) + ' / ' + str(int(self.maxAP)))
        if self.maxWT > 0:
            if self.curWT > self.maxWT:
                if not self.wtBarOverWeightState:
                    self.widget.weightBar.setValue(100)
                    self.wtBarLastTextVisible = self.widget.weightBar.isTextVisible()
                    self.widget.weightBar.setTextVisible(True)
                    self.widget.weightBar.setFormat('Overencumbered!')
                    self.wtBarOverWeightState = True
            else:
                if self.wtBarOverWeightState:
                    self.wtBarOverWeightState = False
                    if not self.wtBarLastTextVisible:
                        self.widget.weightBar.setTextVisible(False)
                self.widget.weightBar.setValue((self.curWT*100)/self.maxWT)
        self.widget.weightLabel.setText(str(int(self.curWT)) + ' / ' + str(int(self.maxWT)))
        
        XPNextLevel = 200 + ((self.xpLevel - 1) * 75)
        XPCurrentLevel = math.floor(XPNextLevel * self.xpProgress)
        self.widget.lvlLabel.setText("LVL: " + str(self.xpLevel) + " XP: " + str(XPCurrentLevel) + " / " + str(XPNextLevel))
        
        self.widget.lvlBar.setValue(self.xpProgress*100)
        self.widget.capsLabel.setText(str(self.caps))
            
            