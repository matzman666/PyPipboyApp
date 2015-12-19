# -*- coding: utf-8 -*-


import datetime
import os
from PyQt5 import QtWidgets, QtCore, uic
from pypipboy.types import eValueType
from widgets import widgets
import math


class SmallPlayerInfoWidget(widgets.WidgetBase):
    _signalInfoUpdated = QtCore.pyqtSignal()
    
    def __init__(self, handle,  parent):
        super().__init__('Small Player Info', parent)
        self.widget = uic.loadUi(os.path.join(handle.basepath, 'ui', 'smallplayerinfowidget.ui'))
        self.setWidget(self.widget)
        self.pipPlayerInfo = None
        self.pipCurrWorldspace = None
        self.pipStats = None
        self.pipRadioInfo = None
        self.maxHP = 0
        self.curHP = 0
        self.maxAP = 0
        self.curAP = 0
        self.maxWT = 0
        self.curWT = 0
        self.xpLevel = 0
        self.xpProgress = 0.0
        self.caps = 0
        self._signalInfoUpdated.connect(self._slotInfoUpdated)
        
    def init(self, app, datamanager):
        super().init(app, datamanager)
        self.dataManager = datamanager
        self.dataManager.registerRootObjectListener(self._onPipRootObjectEvent)
        
    def _onPipRootObjectEvent(self, rootObject):
        self.pipPlayerInfo = rootObject.child('PlayerInfo')
        if self.pipPlayerInfo:
            self.pipPlayerInfo.registerValueUpdatedListener(self._onPipPlayerInfoUpdate, 1)
        
        self.pipCurrWorldspace = rootObject.child('Map').child('CurrWorldspace')
        if (self.pipCurrWorldspace):
            self.pipCurrWorldspace.registerValueUpdatedListener(self._onPipPlayerInfoUpdate, 1)

        self.pipStats = rootObject.child('Stats')
        if (self.pipStats):
            self.pipStats.registerValueUpdatedListener(self._onPipPlayerInfoUpdate, 1)

        self.pipRadioInfo = rootObject.child('Radio')
        if self.pipRadioInfo:
            self.pipRadioInfo.registerValueUpdatedListener(self._onPipPlayerInfoUpdate, 2)
            
        self._signalInfoUpdated.emit()


    def _onPipPlayerInfoUpdate(self, caller, value, pathObjs):
        self._signalInfoUpdated.emit()
        
    @QtCore.pyqtSlot()
    def _slotInfoUpdated(self):
        dateDay = self.pipPlayerInfo.child('DateDay')
        dateMonth = self.pipPlayerInfo.child('DateMonth')
        dateYear = self.pipPlayerInfo.child('DateYear')
        timeHour = self.pipPlayerInfo.child('TimeHour')

        if (dateDay and dateMonth and dateYear and timeHour):
            hour = math.floor(timeHour.value())
            minute = math.floor((timeHour.value() - math.floor(timeHour.value()))*60)
        
            timeStr = str(hour).zfill(2) + ":" + str(minute).zfill(2)
            dateStr = str(dateDay.value()) + "\\" + str(dateMonth.value()) + "\\2" + str(dateYear.value())
            self.widget.lblTime.setText(timeStr)
            self.widget.lblDate.setText(dateStr)
            
        location = self.pipCurrWorldspace
        locationStr = ""
        if(location):
            locationStr = location.value()
            self.widget.lblLocation.setText(location.value())

        activeEffects = self.pipStats.child('ActiveEffects')
        radChange = 0
        listEffects = []
        listEffectsSeperator = ', '
        
        
        if (activeEffects):
            for i in range(0, activeEffects.childCount()):
                if (activeEffects.child(i) and activeEffects.child(i).child('Effects')):    
                    #41 drugs\addiction
                    #42 food
                    #44 stimpak
                    #53 stealth boy
                    if (activeEffects.child(i).child('type') and activeEffects.child(i).child('type').value() in [41,42,44,53]):
                                listEffects.append(activeEffects.child(i).child('Source').value())

                    effects = activeEffects.child(i).child('Effects')
                    for j in range(0, effects.childCount()):
                        effect = effects.child(j)
                        if (effect.child('Name') 
                        and effect.child('IsActive').value() == True):
                            if (effect.child('Name').value() == 'Rads'):
                                radChange += effect.child('Value').value()
                   
        radChangePrefix = ''
        if (radChange > 0):
            radChangePrefix = '+'
            
        self.widget.radChangeLabel.setText(radChangePrefix + str(round(radChange)))
        self.widget.lblActiveEffects.setText(listEffectsSeperator.join(listEffects))
        
        currentRadioStationName = 'Radio off'
        if(self.pipRadioInfo):
            for i in range(0, self.pipRadioInfo.childCount()):
                station = self.pipRadioInfo.child(i)
                if station.child('active').value():
                    currentRadioStationName = station.child('text').value()

        self.widget.lblRadio.setText(currentRadioStationName)
        
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
        if self.maxAP > 0:
            self.widget.apBar.setValue((self.curAP*100)/self.maxAP)
        if self.maxWT > 0:
            self.widget.weightLabel.setText(str(int(self.curWT)) + ' / ' + str(int(self.maxWT)))
        self.widget.capsLabel.setText(str(self.caps))
            
            