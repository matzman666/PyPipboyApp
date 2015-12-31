# -*- coding: utf-8 -*-
import datetime
import os
from PyQt5 import QtGui, QtWidgets, QtCore, uic
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
    _signalColorUpdated = QtCore.pyqtSignal(QtGui.QColor)
    grenademodel = QStandardItemModel()
    
    def __init__(self, mhandle, parent):
        super().__init__('Equipped and Grenades', parent)
        self.widget = uic.loadUi(os.path.join(mhandle.basepath, 'ui', 'equippedandgrenadeswidget.ui'))
        self._logger = logging.getLogger('pypipboyapp.equippedandgrenadeswidget')
        self.setWidget(self.widget)
        self.pipColour = None
        self.pipInventoryInfo = None
        self.iconColor = QtGui.QColor.fromRgb(0,255,0)
        
        
        self._signalInfoUpdated.connect(self._slotInfoUpdated)
        self._signalColorUpdated.connect(self._slotColorUpdated)

    def init(self, app, datamanager):
        super().init(app, datamanager)
        self.dataManager = datamanager
        self.dataManager.registerRootObjectListener(self._onPipRootObjectEvent)
        
        self._app = app
        self.widget.label_EquipedWeapon.setText("")

        #self.pDmgIcon = QPixmap(16, 16)
        #self.pDmgIcon.load(os.path.join("ui", "res", "dmg-physical.png"))
        #self.widget.lblPdmgIcon.setPixmap(self.pDmgIcon)

        self._slotColorUpdated(self.iconColor)

    def colouriseIcon(self, img, colour):
        size = img.size()
        image = QImage(QtCore.QSize(size.width()+1,size.height()+1), QImage.Format_ARGB32_Premultiplied)
        image.fill(QtCore.Qt.transparent)
        p = QPainter(image)
        p.setCompositionMode(QPainter.CompositionMode_SourceOver)
        p.drawImage(QtCore.QRect(1,1,size.width(), size.height()), img)
        p.setCompositionMode(QPainter.CompositionMode_SourceAtop)
        p.setBrush(colour)
        p.drawRect(QtCore.QRect(0,0,size.width()+1,size.height()+1))
        p.end()
        return QPixmap.fromImage(image)        
        
    def _onPipRootObjectEvent(self, rootObject):
        self.pipInventoryInfo = rootObject.child('Inventory')
        if self.pipInventoryInfo:
            self.pipInventoryInfo.registerValueUpdatedListener(self._onPipPlayerInfoUpdate, 1)
        self._signalInfoUpdated.emit()

        self.pipColor = rootObject.child('Status').child('EffectColor')
        self.pipColor.registerValueUpdatedListener(self._onPipColorChanged, 1)
        self._onPipColorChanged(None, None, None)
        
    def _onPipColorChanged(self, caller, value, pathObjs):
        if self.pipColor:
            r = self.pipColor.child(0).value() * 255
            g = self.pipColor.child(1).value() * 255
            b = self.pipColor.child(2).value() * 255
            self.iconColor = QtGui.QColor.fromRgb(r,g,b)
            self._signalColorUpdated.emit(self.iconColor)

        
    def _onPipPlayerInfoUpdate(self, caller, value, pathObjs):
        self._signalInfoUpdated.emit()

    @QtCore.pyqtSlot(QtGui.QColor)
    def _slotColorUpdated(self, color):
        self.pDmgIcon = self.colouriseIcon(QImage(os.path.join("ui", "res", "dmg-physical.png")), self.iconColor)
        self.widget.lblPdmgIcon.setPixmap(self.pDmgIcon)
        
        self.eDmgIcon = self.colouriseIcon(QImage(os.path.join("ui", "res", "dmg-energy.png")), self.iconColor)
        self.widget.lblEdmgIcon.setPixmap(self.eDmgIcon)

        self.rDmgIcon = self.colouriseIcon(QImage(os.path.join("ui", "res", "dmg-radiation.png")), self.iconColor)
        self.widget.lblRdmgIcon.setPixmap(self.rDmgIcon)

        self.poDmgIcon = self.colouriseIcon(QImage(os.path.join("ui", "res", "dmg-poison.png")), self.iconColor)
        self.widget.lblPodmgIcon.setPixmap(self.poDmgIcon)
        return
        
    @QtCore.pyqtSlot()
    def _slotInfoUpdated(self):
        self.updateWeaponViews()

    def _isItemReal(self, item):
        if(self.pipInventoryInfo):
            # Better to iterate over value(), range() causes race conditions
            for i in self.pipInventoryInfo.child('sortedIDS').value():
                
                if (item and item.pipId == tmp.value()):
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
        def _filterFunc(item):
            return inventoryutils.itemHasAnyFilterCategory(item, inventoryutils.eItemFilterCategory.Weapon)
        weapons = inventoryutils.inventoryGetItems(self.pipInventoryInfo, _filterFunc)
        if(not weapons):
            return
        for weapon in weapons:
            name = weapon.child('text').value()
            if inventoryutils.itemIsWeaponThrowable(weapon):
                grenadecounter += 1
                
                count = str(weapon.child('count').value())
                if (weapon.child('equipState').value() == 3):
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
                if ( weapon.child('equipState').value() > 0):
                    strEquipedWeapon = weapon.child('text').value()
                    strAmmo = ''
                    valueAmmo = inventoryutils.itemFindItemCardInfoValue(weapon, 10, 'damageType')
                    if valueAmmo != None:
                        strAmmo += ' (' + str(valueAmmo) + ')'

                    self.widget.label_EquipedWeapon.setText(strEquipedWeapon +  strAmmo)
                    
                    damageInfos = inventoryutils.itemFindItemCardInfos(weapon, inventoryutils.eItemCardInfoValueText.Damage)                 
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
                            
                    rof = inventoryutils.itemFindItemCardInfoValue(weapon, inventoryutils.eItemCardInfoValueText.RateOfFire)
                    if rof == None:
                        speed = inventoryutils.itemFindItemCardInfoValue(weapon, inventoryutils.eItemCardInfoValueText.Speed)
                        if speed:
                            RofAccRngStr = 'Speed: ' + speed[1:].lower()
                    else:
                        RofAccRngStr = 'RoF: ' + str(round(rof, 2))

                    acc = inventoryutils.itemFindItemCardInfoValue(weapon, inventoryutils.eItemCardInfoValueText.Accuracy)
                    if acc != None:
                        RofAccRngStr += '  Acc: ' + str(round(acc, 2))

                    rng = inventoryutils.itemFindItemCardInfoValue(weapon, inventoryutils.eItemCardInfoValueText.Range)
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
            