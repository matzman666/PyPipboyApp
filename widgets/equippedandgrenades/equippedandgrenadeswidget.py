# -*- coding: utf-8 -*-
import datetime
import os
from PyQt5 import QtWidgets, QtCore, uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from pypipboy.types import eValueType
from .. import widgets
from pypipboy import inventoryutils

import logging

itemCardInfoDamageTypes = [
    '_Padding0', # 0
    'Phy', # 1
    'Po', # 2
    '?(3)', # 3
    'En', # 4
    '?(5)', # 5
    'Rad', # 6
    ]

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
        self.widget.label_EquipedWeapon.setText("")

        self.pDmgIcon = QPixmap(16, 16)
        self.pDmgIcon.load(os.path.join("ui", "res", "dmg-physical.png"))
        self.widget.lblPdmgIcon.setPixmap(self.pDmgIcon)

        self.eDmgIcon = QPixmap(16, 16)
        self.eDmgIcon.load(os.path.join("ui", "res", "dmg-energy.png"))
        self.widget.lblEdmgIcon.setPixmap(self.eDmgIcon)

        self.rDmgIcon = QPixmap(16, 16)
        self.rDmgIcon.load(os.path.join("ui", "res", "dmg-radiation.png"))
        self.widget.lblRdmgIcon.setPixmap(self.rDmgIcon)

        self.poDmgIcon = QPixmap(16, 16)
        self.poDmgIcon.load(os.path.join("ui", "res", "dmg-poison.png"))
        self.widget.lblPodmgIcon.setPixmap(self.poDmgIcon)

        
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

    def _isItemReal(self, item):
        if(self.pipInventoryInfo):
            for i in range (0, self.pipInventoryInfo.child('sortedIDS').childCount()):
                if (item and item.pipId == self.pipInventoryInfo.child('sortedIDS').child(i).value()):
                    return True
        return False
        
    def updateWeaponViews(self):
        self.grenademodel.clear()
        selectedgrenade = -1
        grenadecounter = 0
        
        self.widget.label_EquipedWeapon.setText('')
        self.widget.lblRofAccRng.setText('')
        self.widget.lblPdmgIcon.setVisible(False)
        self.widget.lblPdmg.setVisible(False)
        self.widget.lblEdmgIcon.setVisible(False)
        self.widget.lblEdmg.setVisible(False)
        self.widget.lblRdmgIcon.setVisible(False)
        self.widget.lblRdmg.setVisible(False)
        self.widget.lblPodmgIcon.setVisible(False)
        self.widget.lblPodmg.setVisible(False)

        weapons = self.pipInventoryInfo.child('43')
        if(not weapons):
            return
        for i in range(0, weapons.childCount()):
            if not self._isItemReal(weapons.child(i)):
                continue
        
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
                    strAmmo = ''
                    valueAmmo = inventoryutils.itemFindItemCardInfoValue(weapons.child(i), 10, 'damageType')
                    if valueAmmo != None:
                        strAmmo += ' (' + str(valueAmmo) + ')'

                    self.widget.label_EquipedWeapon.setText(strEquipedWeapon +  strAmmo)
                    
                    damageInfos = inventoryutils.itemFindItemCardInfos(weapons.child(i), inventoryutils.eItemCardInfoValueText.Damage)                 
                    for info in damageInfos:
                        damageType = info.child('damageType').value()
                        value = info.child('Value').value()
                        if itemCardInfoDamageTypes[damageType] == 'Phy' and value != 0.0:
                            self.widget.lblPdmg.setText( str(int(value)))
                            self.widget.lblPdmg.setVisible(True)
                            self.widget.lblPdmgIcon.setVisible(True)
                        elif itemCardInfoDamageTypes[damageType] == 'En' and value != 0.0:
                            self.widget.lblEdmg.setText (str(int(value)))
                            self.widget.lblEdmg.setVisible(True)
                            self.widget.lblEdmgIcon.setVisible(True)
                        elif itemCardInfoDamageTypes[damageType] == 'Rad' and value != 0.0:
                            self.widget.lblRdmg.setText (str(int(value)))
                            self.widget.lblRdmg.setVisible(True)
                            self.widget.lblRdmgIcon.setVisible(True)
                        elif itemCardInfoDamageTypes[damageType] == 'Po' and value != 0.0:
                            self.widget.lblPodmg.setText (str(int(value)))
                            self.widget.lblPodmg.setVisible(True)
                            self.widget.lblPodmgIcon.setVisible(True)
                            pass

                    RofAccRngStr = ''
                            
                    rof = inventoryutils.itemFindItemCardInfoValue(weapons.child(i), inventoryutils.eItemCardInfoValueText.RateOfFire)
                    if rof == None:
                        speed = inventoryutils.itemFindItemCardInfoValue(weapons.child(i), inventoryutils.eItemCardInfoValueText.Speed)
                        if speed:
                            RofAccRngStr = 'Speed: ' + speed[1:].lower()
                    else:
                        RofAccRngStr = 'RoF: ' + str(round(rof, 2))

                    acc = inventoryutils.itemFindItemCardInfoValue(weapons.child(i), inventoryutils.eItemCardInfoValueText.Accuracy)
                    if acc != None:
                        RofAccRngStr += '  Acc: ' + str(round(acc, 2))

                    rng = inventoryutils.itemFindItemCardInfoValue(weapons.child(i), inventoryutils.eItemCardInfoValueText.Range)
                    if rng != None:
                        RofAccRngStr += '  Rng: ' + str(round(rng, 2))
                        
                        
                    self.widget.lblRofAccRng.setText(RofAccRngStr)
                            
                
        self.widget.grenadeView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.widget.grenadeView.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.widget.grenadeView.verticalHeader().setStretchLastSection(False)
        self.widget.grenadeView.horizontalHeader().setStretchLastSection(True)
        self.widget.grenadeView.setModel(self.grenademodel)

        
        if (selectedgrenade >=1):
            self.widget.grenadeView.selectRow(selectedgrenade-1)
        self.widget.grenadeView.hideColumn(0)
        self.widget.grenadeView.sortByColumn(1, QtCore.Qt.AscendingOrder)
            