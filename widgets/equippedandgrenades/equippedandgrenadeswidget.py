# -*- coding: utf-8 -*-
import datetime
import os
from PyQt5 import QtWidgets, QtCore, uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from pypipboy.types import eValueType
from .. import widgets

import logging

class EquippedAndGrenadesWidget(widgets.WidgetBase):
    _signalInfoUpdated = QtCore.pyqtSignal()
    grenademodel = QStandardItemModel()
    
    def __init__(self, mhandle, parent):
        super().__init__('Equipped and Grenades', parent)
        self.widget = uic.loadUi(os.path.join(mhandle.basepath, 'ui', 'equippedandgrenadeswidget.ui'))
        self._logger = logging.getLogger('pypipboyapp.equippedandgrenadeswidget')
        self.setWidget(self.widget)
        self.pipPlayerInfo = None
        self.pipInventoryInfo = None
        
        self._signalInfoUpdated.connect(self._slotInfoUpdated)
        
    def init(self, app, datamanager):
        super().init(app, datamanager)
        self.dataManager = datamanager
        self.dataManager.registerRootObjectListener(self._onPipRootObjectEvent)
        
        self._app = app
        
    def _onPipRootObjectEvent(self, rootObject):
        self.pipInventoryInfo = rootObject.child('Inventory')
        if self.pipInventoryInfo:
            self.pipInventoryInfo.registerValueUpdatedListener(self._onPipPlayerInfoUpdate, 1)
        self._signalInfoUpdated.emit()

    def _onPipPlayerInfoUpdate(self, caller, value, pathObjs):
        self._signalInfoUpdated.emit()
        
    @QtCore.pyqtSlot()
    def _slotInfoUpdated(self):
        self.updateWeaponViews()

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
                
                item[2].setData(QtCore.Qt.AlignCenter, QtCore.Qt.TextAlignmentRole)
                
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
        self.widget.grenadeView.horizontalHeader().setStretchLastSection(True)
        self.widget.grenadeView.setModel(self.grenademodel)

        
        if (selectedgrenade >=1):
            self.widget.grenadeView.selectRow(selectedgrenade-1)
        self.widget.grenadeView.hideColumn(0)
        self.widget.grenadeView.sortByColumn(1, QtCore.Qt.AscendingOrder)
            