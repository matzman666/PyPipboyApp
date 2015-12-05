# -*- coding: utf-8 -*-


import datetime
import os
from PyQt5 import QtWidgets, QtGui, QtCore, uic
from pypipboy.types import eValueType
from widgets import widgets


class PlayerConditionWidget(widgets.WidgetBase):
    _signalStatsUpdated = QtCore.pyqtSignal()
    
    def __init__(self, handle, controller, parent):
        super().__init__('Player Condition', parent)
        self.controller = controller
        self.imageFactory = controller.imageFactory
        self.widget = uic.loadUi(os.path.join(handle.basepath, 'ui', 'playerconditionwidget.ui'))
        self.setWidget(self.widget)
        self.pipStats = None
        self.bodyFlags = 0
        self.headerFlags = 0
        self._signalStatsUpdated.connect(self._slotStatsUpdated)
        
    def init(self, app, datamanager):
        super().init(app, datamanager)
        self.statsColor = QtGui.QColor.fromRgb(20,255,23)
        self.dataManager = datamanager
        self.dataManager.registerRootObjectListener(self._onPipRootObjectEvent)
        self.statsView = self.widget.graphicsView
        self.statsScene = QtWidgets.QGraphicsScene()
        self.statsScene.setBackgroundBrush(QtGui.QBrush(QtGui.QColor.fromRgb(0,0,0)))
        self.statsView.setScene(self.statsScene)
        self.bodyCondFilePath = os.path.join('res', 'body_condition_0.svg')
        self.headCondFilePath = os.path.join('res', 'head_condition_0.svg')
        self.headCondition = 0
        headPixmap = self.imageFactory.getPixmap(self.headCondFilePath, height=50, color=self.statsColor)
        self.statsHeadItem = self.statsScene.addPixmap(headPixmap)
        self.statsHeadItem.setPos(-headPixmap.width()/2, 0)
        self.bodyCondition = 0
        bodyPixmap = self.imageFactory.getPixmap(self.bodyCondFilePath, height=100, color=self.statsColor)
        self.statsBodyItem = self.statsScene.addPixmap(bodyPixmap)
        self.statsBodyItem.setPos(-bodyPixmap.width()/2, 42)
        
    def _onPipRootObjectEvent(self, rootObject):
        self.pipStats = rootObject.child('Stats')
        if self.pipStats:
            self.pipStats.registerValueUpdatedListener(self._onPipStatsUpdate, 1)
        self._signalStatsUpdated.emit()

    def _onPipStatsUpdate(self, caller, value, pathObjs):
        self._signalStatsUpdated.emit()
        
    @QtCore.pyqtSlot()
    def _slotStatsUpdated(self):
        bodycondition = self.bodyCondition
        headcondition = self.headCondition
        pipBodyCond = self.pipStats.child('BodyFlags')
        if pipBodyCond:
            bodycondition = pipBodyCond.value()
        pipHeadCond = self.pipStats.child('HeadFlags')
        if pipHeadCond:
            headcondition = pipHeadCond.value()
        if self.headCondition != headcondition:
            self.headCondition = headcondition
            self.headCondFilePath = os.path.join('res', 'head_condition_' + str(self.headCondition) + '.svg')
            headPixmap = self.imageFactory.getPixmap(self.headCondFilePath, height=50, color=self.statsColor)
            self.statsHeadItem.setPixmap(headPixmap)
            self.statsHeadItem.setPos(-headPixmap.width()/2, 0)
        if self.bodyCondition != bodycondition:
            self.bodyCondition = bodycondition
            self.bodyCondFilePath = os.path.join('res', 'body_condition_' + str(self.bodyCondition) + '.svg')
            bodyPixmap = self.imageFactory.getPixmap(self.bodyCondFilePath, height=90, color=self.statsColor)
            self.statsBodyItem.setPixmap(bodyPixmap)
            self.statsBodyItem.setPos(-bodyPixmap.width()/2, 42)
            