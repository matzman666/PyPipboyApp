# -*- coding: utf-8 -*-
import datetime
import os
from PyQt5 import QtWidgets, QtCore, uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from pypipboy.types import eValueType
from .. import widgets

import logging
import win32con

class AKStatusWidget(widgets.WidgetBase):
    _signalInfoUpdated = QtCore.pyqtSignal()

    grenademodel = QStandardItemModel()
    aidmodel = QStandardItemModel()

    
    def __init__(self, mhandle, parent):
        super().__init__('Status', parent)
        self.widget = uic.loadUi(os.path.join(mhandle.basepath, 'ui', 'akstatuswidget.ui'))
        self._logger = logging.getLogger('pypipboyapp.akstatus')
        self.setWidget(self.widget)
        self.pipPlayerInfo = None
        self.pipInventoryInfo = None
        
        self._signalInfoUpdated.connect(self._slotInfoUpdated)
        
    def init(self, app, datamanager):
        super().init(app, datamanager)
        self.dataManager = datamanager
        self.dataManager.registerRootObjectListener(self._onPipRootObjectEvent)
        
        self._app = app
        self._app._hm.registerHotkey(0x47, 0, self.equipNextGrenade) #g
        self._app._hm.registerHotkey(45, 0, datamanager.rpcUseStimpak) #insert
        self._app._hm.registerHotkey(36, 0, datamanager.rpcUseRadAway) #home
        self._app._hm.registerHotkey(33, 0, self.useJet) #pageup
        

    def useJet(self):   
        strJet = "jet"
        aid = self.pipInventoryInfo.child('48')
        for i in range(0, aid.childCount()):
            name = aid.child(i).child('text').value()
            if (name.lower() == strJet):
                self.dataManager.rpcUseItem(aid.child(i))
        pass
        
    def equipNextGrenade(self):
        self._logger.debug ("start equipNextGrenade")
        self._logger.debug ("self.grenademodel.rowCount():" + str(self.grenademodel.rowCount()))

        nextGrenade = None
        
        for i in range (0, self.grenademodel.rowCount()):
            if (self.grenademodel.item(i,0).text() == "+"):
                self._logger.debug ("current grenade is: " + self.grenademodel.item(i,1).text())

                if (i+1 >= self.grenademodel.rowCount()):
                    nextGrenade = self.grenademodel.item(0,1).text() 
                    self._logger.debug ("next grenade is: " + nextGrenade )
                else:
                    nextGrenade = self.grenademodel.item(i+1,1).text() 
                    self._logger.debug ("next grenade is: " + nextGrenade)

        if (nextGrenade == None and self.grenademodel.rowCount() >= 0 ):
            nextGrenade = self.grenademodel.item(0,1).text() 

        if (nextGrenade != None):
            weapons = self.pipInventoryInfo.child('43')
            for i in range(0, weapons.childCount()):
                name = weapons.child(i).child('text').value()
                if (name.lower() == nextGrenade.lower()): 
                    self.dataManager.rpcUseItem(weapons.child(i))
        
        nextGrenade = None
        
    def _onPipRootObjectEvent(self, rootObject):
        self.pipPlayerInfo = rootObject.child('PlayerInfo')
        if self.pipPlayerInfo:
            self.pipPlayerInfo.registerValueUpdatedListener(self._onPipPlayerInfoUpdate, 1)
        self._signalInfoUpdated.emit()

        self.pipInventoryInfo = rootObject.child('Inventory')
        if self.pipInventoryInfo:
            self.pipInventoryInfo.registerValueUpdatedListener(self._onPipPlayerInfoUpdate, 1)
        self._signalInfoUpdated.emit()

    def _onPipPlayerInfoUpdate(self, caller, value, pathObjs):
        self._signalInfoUpdated.emit()
        
    @QtCore.pyqtSlot()
    def _slotInfoUpdated(self):
        self.updateWeaponViews()
        self.updateAidView()

    def updateWeaponViews(self):
        self.grenademodel.clear()
        selectedgrenade = -1
        grenadecounter = 0

        weapons = self.pipInventoryInfo.child('43')
        for i in range(0, weapons.childCount()):
            name = weapons.child(i).child('text').value()
            if (name.lower().find('mine') > -1 
            or name.lower().find('grenade') > -1 
            or name.lower().find('molotov') > -1 ):
                grenadecounter += 1
                
                count = str(weapons.child(i).child('count').value())
                if (weapons.child(i).child('equipState').value() == 3):
                    equipState = "+"
                else:
                    equipState = ""

                if (equipState == "+"):
                    selectedgrenade = grenadecounter
                
                item = [
                    QStandardItem(equipState) , 
                    QStandardItem(name) , 
                    QStandardItem(count)
                ]
                
                self.grenademodel.appendRow(item)
     
            else:
                if ( weapons.child(i).child('equipState').value() > 0):
                    strEquipedWeapon = weapons.child(i).child('text').value()
                    for j in range(0, weapons.child(i).child('itemCardInfoList').childCount()):
                        if (weapons.child(i).child('itemCardInfoList').child(j).child('text').value().find("$") < 0):
                            ammocount = weapons.child(i).child('itemCardInfoList').child(j).child('Value').value()
                            strEquipedWeapon += " (" + str(ammocount) + ")"
                            break
 
                    self.widget.label_EquipedWeapon.setText(strEquipedWeapon)
                
        self.widget.grenadeView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.widget.grenadeView.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.widget.grenadeView.verticalHeader().setStretchLastSection(False)
        self.widget.grenadeView.setModel(self.grenademodel)

        
        if (selectedgrenade >=1):
            self.widget.grenadeView.selectRow(selectedgrenade-1)
        self.widget.grenadeView.hideColumn(0)
        self.widget.grenadeView.sortByColumn(1, QtCore.Qt.AscendingOrder)
            
    def updateAidView(self):
        self.aidmodel.clear()
        aidcounter = 0
        aid = self.pipInventoryInfo.child('48')
        for i in range(0, aid.childCount()):
            name = aid.child(i).child('text').value()
            if (name.lower() == 'stimpak'
            or name.lower() == 'jet'
            or name.lower() == 'radaway'
            or name.lower() == 'rad-x'
            or name.lower() == 'purified water'):
                
                count = str(aid.child(i).child('count').value())
                
                item = [
                    QStandardItem(name) , 
                    QStandardItem(count)
                ]
                
                self.aidmodel.appendRow(item)
        
        self.widget.aidView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.widget.aidView.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.widget.aidView.verticalHeader().setStretchLastSection(False)
        self.widget.aidView.setModel(self.aidmodel)

        self.widget.aidView.sortByColumn(0, QtCore.Qt.AscendingOrder)