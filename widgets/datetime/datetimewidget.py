# -*- coding: utf-8 -*-


import datetime
import os
from PyQt5 import QtWidgets, QtCore, uic
from .. import widgets


class DateTimeWidget(widgets.WidgetBase):
    _signalInfoUpdated = QtCore.pyqtSignal()
    
    def __init__(self, mhandle, parent):
        super().__init__('Date/Time', parent)
        self.widget = uic.loadUi(os.path.join(mhandle.basepath, 'ui', 'datetimewidget.ui'))
        self.setWidget(self.widget)
        self.pipPlayerInfo = None
        self.dateYear = 0
        self.dateMonth = 0
        self.dateDay = 0
        self.timeHour = 0
        self.timeMin = 0
        self.realClockTimer = QtCore.QTimer()
        self.realClockTimer.timeout.connect(self._realClockUpdate)
        self._signalInfoUpdated.connect(self._slotInfoUpdated)
        
    def init(self, app, datamanager):
        super().init(app, datamanager)
        self.dataManager = datamanager
        self._realClockUpdate()
        self.realClockTimer.start(1000)
        self.dataManager.registerRootObjectListener(self._onPipRootObjectEvent)
        
    def _onPipRootObjectEvent(self, rootObject):
        self.pipPlayerInfo = rootObject.child('PlayerInfo')
        if self.pipPlayerInfo:
            self.pipPlayerInfo.registerValueUpdatedListener(self._onPipPlayerInfoUpdate, 1)
        self._signalInfoUpdated.emit()

    def _onPipPlayerInfoUpdate(self, caller, value, pathObjs):
        self._signalInfoUpdated.emit()
    
    @QtCore.pyqtSlot()
    def _realClockUpdate(self):
        realTime = datetime.datetime.now()
        self.widget.realTimeLabel.setText(realTime.strftime('%H:%M'))
        
    @QtCore.pyqtSlot()
    def _slotInfoUpdated(self):
        dateYear = self.pipPlayerInfo.child('DateYear')
        if dateYear:
            self.dateYear = dateYear.value() + 2000
        dateMonth = self.pipPlayerInfo.child('DateMonth')
        if dateMonth:
            self.dateMonth = dateMonth.value()
        dateDay = self.pipPlayerInfo.child('DateDay')
        if dateDay:
            self.dateDay = dateDay.value()
        timeHour = self.pipPlayerInfo.child('TimeHour')
        if timeHour:
            self.timeHour = int(timeHour.value())
            self.timeMin = int((timeHour.value()-self.timeHour)*60)
        # This does not work on damn Windows (complains that date is too far in the future)
        # Works fine on Linux though
        #gameDate = datetime.date(self.dateYear, self.dateMonth, self.dateDay)
        gameDate = str()
        if self.dateDay < 10:
            gameDate += '0' + str(self.dateDay) + '.'
        else:
            gameDate += str(self.dateDay)+ '.'
        if self.dateMonth < 10:
            gameDate += '0' + str(self.dateMonth) + '.'
        else:
            gameDate += str(self.dateMonth)+ '.'
        gameDate += str(self.dateYear)
        gameTime = datetime.time(int(self.timeHour), self.timeMin)
        self.widget.gameTimeLabel.setText(gameTime.strftime('%H:%M'))
        self.widget.gameDateLabel.setText(gameDate)
        