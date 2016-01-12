# -*- coding: utf-8 -*-

import time
from PyQt5 import QtWidgets, QtCore, QtGui
from pypipboy import inventoryutils


itemCardInfoDamageTypes = [
    '_Padding0', # 0
    'Phy', # 1
    'Po', # 2
    '?(3)', # 3
    'En', # 4
    '?(5)', # 5
    'Rad', # 6
    ]

itemApparelPaperDollSections = [
    'Body', # 0
    'LLeg', # 1
    'RLeg', # 2
    'LArm', # 3
    'RArm', # 4
    'Chest', # 5
    'Helmet', # 6
    'Goggles', # 7
    'Mouth', # 8
    ]

class InventoryTableModel(QtCore.QAbstractTableModel):
    _signalItemUpdate = QtCore.pyqtSignal(object)
    _signalSortedIdsUpdate = QtCore.pyqtSignal()

    def __init__(self, view, qparent = None):
        super().__init__(qparent)
        self.view = view
        self.pipInventory = None
        self.pipInvSortedIds = None
        self.tabIsVisible = False
        self.isDirty = False
        self._items = []
        self._signalItemUpdate.connect(self._slotItemUpdate)
        self._signalSortedIdsUpdate.connect(self._slotSortedIdsUpdate)

    def setPipInventory(self, datamanager, pipInventory):
        self.modelAboutToBeReset.emit()

        self.pipInventory = pipInventory
        self.datamanager = datamanager

        for i in self._items:
            i.unregisterValueUpdatedListener(self._onPipItemUpdate)
        self._items.clear()
        if self.pipInvSortedIds:
            self.pipInvSortedIds.unregisterValueUpdatedListener(self._onPipSortedIdsUpdate)
        self.pipInvSortedIds = self.pipInventory.child('sortedIDS')
        if self.pipInvSortedIds:
            self.pipInvSortedIds.registerValueUpdatedListener(self._onPipSortedIdsUpdate)
            self._items = inventoryutils.inventoryGetItems(self.pipInventory, self._acceptItem)
            for item in self._items:
                item.registerValueUpdatedListener(self._onPipItemUpdate)
        self.modelReset.emit()

    def _acceptItem(self, item):
        return True

    def _onPipItemUpdate(self, caller, value, pathObjs):
        self._signalItemUpdate.emit(caller)

    @QtCore.pyqtSlot(object)
    def _slotItemUpdate(self, item):
        try:
            t = self._items.index(item)
            self.dataChanged.emit(self.index(t, 0), self.index(t, self.rowCount()))
        except:
            pass

    def _onPipSortedIdsUpdate(self, caller, value, pathObjs):
        if self.tabIsVisible:
            self._signalSortedIdsUpdate.emit()
        else:
            self.isDirty = True

    @QtCore.pyqtSlot()
    def _slotSortedIdsUpdate(self):
        self.layoutAboutToBeChanged.emit()
        for i in self._items:
            i.unregisterValueUpdatedListener(self._onPipItemUpdate)
        self._items.clear()
        self._items = inventoryutils.inventoryGetItems(self.pipInventory, self._acceptItem)
        for item in self._items:
            item.registerValueUpdatedListener(self._onPipItemUpdate)
        self.layoutChanged.emit()

    def rowCount(self, parent = QtCore.QModelIndex()):
        return len(self._items)

    def columnCount(self, parent = QtCore.QModelIndex()):
        return 5

    def headerData(self, section, orientation, role = QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal:
            if role == QtCore.Qt.DisplayRole:
                if section == 0:
                    return 'Name'
                elif section == 1:
                    return 'Count'
                elif section == 2:
                    return 'Value'
                elif section == 3:
                    return 'Weight'
                elif section == 4:
                    return 'Val/Wt'
        return None

    def data(self, index, role = QtCore.Qt.DisplayRole):
        return self._data(self._items[index.row()], index.column(), role)

    def _data(self, item, column, role = QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if column == 0:
                return item.child('text').value()
            elif column == 1:
                return item.child('count').value()
            elif column == 2:
                return round(inventoryutils.itemFindItemCardInfoValue(item,
                                inventoryutils.eItemCardInfoValueText.Value), 2)
            elif column == 3:
                return round(inventoryutils.itemFindItemCardInfoValue(item,
                                inventoryutils.eItemCardInfoValueText.Weight), 2)
            elif column == 4:
                value = inventoryutils.itemFindItemCardInfoValue(item,
                            inventoryutils.eItemCardInfoValueText.Value)
                weight = inventoryutils.itemFindItemCardInfoValue(item,
                            inventoryutils.eItemCardInfoValueText.Weight)
                try:
                    if value == 0.0:
                        return 0.0
                    elif weight == 0.0:
                        return float('inf')
                    else:
                        return round(value/weight, 2)
                except:
                    return None
        elif role == QtCore.Qt.TextAlignmentRole:
            if column == 0:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft
            elif column == 1:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight
            elif column == 2:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight
            elif column == 3:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight
            elif column == 4:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight
        elif role == QtCore.Qt.FontRole:
            if item.child('equipState').value() > 0:
                font = QtGui.QFont()
                font.setBold(True)
                return font
        return None

    def getPipValue(self, row):
        if len(self._items) > row:
            return self._items[row]
        else:
            return None

    def _cmIsUseActionEnabled(self, item, selected):
        return True

    def _cmIsDropActionEnabled(self, item, selected):
        return True

    def _cmUseActionText(self, item, selected):
        return 'Use Item'

    def _cmDropActionText(self, item, selected):
        return 'Drop Item'

    def showItemContextMenu(self, datamanager, item, selected, pos, view):
        menu = QtWidgets.QMenu(view)
        actionCount = 0
        if self._cmIsUseActionEnabled(item, selected):
            actionCount += 1
            def _useItem():
                for item in selected:
                    datamanager.rpcUseItem(item)
                    time.sleep(0.1)
            uaction = menu.addAction(self._cmUseActionText(item, selected))
            uaction.triggered.connect(_useItem)
        if self._cmIsDropActionEnabled(item, selected):
            actionCount += 1
            def _dropItem():
                for item in selected:
                    datamanager.rpcDropItem(item, 1)
                    time.sleep(0.1)
            daction = menu.addAction(self._cmDropActionText(item, selected))
            daction.triggered.connect(_dropItem)
        if actionCount > 0:
            menu.exec(view.mapToGlobal(pos))

    def itemDoubleClicked(self, datamanager, item, view):
        datamanager.rpcUseItem(item)

    def tabVisibilityChanged(self, visible):
        self.tabIsVisible = visible
        if self.tabIsVisible and self.isDirty:
            self._slotSortedIdsUpdate()
            self.isDirty = False



class CatAllModel(InventoryTableModel):
    def __init__(self, qparent = None):
        super().__init__(qparent)

    def columnCount(self, parent = QtCore.QModelIndex()):
        return super().columnCount(parent) + 3

    def headerData(self, section, orientation, role = QtCore.Qt.DisplayRole):
        pc = super().columnCount()
        if orientation == QtCore.Qt.Horizontal:
            if role == QtCore.Qt.DisplayRole:
                if section == pc:
                    return 'E'
                elif section == pc + 1:
                    return 'L'
                elif section == pc + 2:
                    return 'Category'
        return super().headerData(section, orientation, role)

    def _data(self, item, column, role = QtCore.Qt.DisplayRole):
        pc = super().columnCount()
        if role == QtCore.Qt.DisplayRole:
            if column == pc:
                if item.child('equipState').value() > 0:
                    return '◼'
                else:
                    return ''
            elif column == pc + 1:
                if item.child('isLegendary').value() > 0:
                    return '◼'
                else:
                    return ''
            elif column == pc + 2:
                cached = item.getUserCache('categorytext')
                if not cached or cached.dirtyFlag:
                    text = ''
                    isFirst = True
                    for cat in [ (inventoryutils.eItemFilterCategory.Aid, 'Aid'),
                                 (inventoryutils.eItemFilterCategory.Ammo, 'Ammo'),
                                 (inventoryutils.eItemFilterCategory.Apparel, 'Apparel'),
                                 (inventoryutils.eItemFilterCategory.Book, 'Book'),
                                 (inventoryutils.eItemFilterCategory.Holotape, 'Holotape'),
                                 (inventoryutils.eItemFilterCategory.Junk, 'Junk'),
                                 (inventoryutils.eItemFilterCategory.Misc, 'Misc'),
                                 (inventoryutils.eItemFilterCategory.Mods, 'Mods'),
                                 (inventoryutils.eItemFilterCategory.Weapon, 'Weapons'),
                                 (inventoryutils.eItemFilterCategory.Favorite, 'Favorite') ]:
                        if inventoryutils.itemHasAnyFilterCategory(item, cat[0]):
                            if isFirst:
                                isFirst = False
                            else:
                                text += ', '
                            text += cat[1]
                    item.setUserCache('categorytext', text, 1)
                else:
                    text = cached.value
                return text
        elif role == QtCore.Qt.TextAlignmentRole:
            if column == pc:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignCenter
            elif column == pc + 1:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignCenter
            elif column == pc + 2:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft
        return super()._data(item, column, role)



class CatWeaponsModel(InventoryTableModel):
    def __init__(self, qparent = None):
        super().__init__(qparent)

    def _acceptItem(self, item):
        return inventoryutils.itemHasAnyFilterCategory(item,
            inventoryutils.eItemFilterCategory.Weapon)

    def columnCount(self, parent = QtCore.QModelIndex()):
        return super().columnCount(parent) + 9

    def headerData(self, section, orientation, role = QtCore.Qt.DisplayRole):
        pc = super().columnCount()
        if orientation == QtCore.Qt.Horizontal:
            if role == QtCore.Qt.DisplayRole:
                if section == pc:
                    return 'E'
                elif section == pc + 1:
                    return 'L'
                elif section == pc + 2:
                    return 'Damage'
                elif section == pc + 3:
                    return 'ROF'
                elif section == pc + 4:
                    return 'Range'
                elif section == pc + 5:
                    return 'Accuracy'
                elif section == pc + 6:
                    return 'Effects'
                elif section == pc + 7:
                    return 'Type'
                elif section == pc + 8:
                    return 'Ammo'
        return super().headerData(section, orientation, role)

    def _data(self, item, column, role = QtCore.Qt.DisplayRole):
        pc = super().columnCount()
        if role == QtCore.Qt.DisplayRole:
            if column == pc:
                if item.child('equipState').value() > 0:
                    return '◼'
                else:
                    return ''
            elif column == pc + 1:
                if item.child('isLegendary').value() > 0:
                    return '◼'
                else:
                    return ''
            elif column == pc + 2:
                cached = item.getUserCache('damagetext')
                if not cached or cached.dirtyFlag:
                    text  =''
                    isFirst = True
                    damageInfos = inventoryutils.itemFindItemCardInfos(item, inventoryutils.eItemCardInfoValueText.Damage)
                    for info in damageInfos:
                        damageType = info.child('damageType').value()
                        value = info.child('Value').value()
                        if damageType < 10 and value != 0.0:
                            if isFirst:
                                isFirst = False
                            else:
                                text += ' + '
                            text += str(int(value))
                            text += ' ' + itemCardInfoDamageTypes[damageType]
                    item.setUserCache('damagetext', text, 10)
                else:
                    text = cached.value
                return text
            elif column == pc + 3:
                rof = inventoryutils.itemFindItemCardInfoValue(item,
                        inventoryutils.eItemCardInfoValueText.RateOfFire)
                if rof == None:
                    speed = inventoryutils.itemFindItemCardInfoValue(item,
                             inventoryutils.eItemCardInfoValueText.Speed)
                    if speed:
                        return 'Speed: ' + speed[1:].lower()
                    else:
                        return None
                else:
                    return round(rof, 2)
            elif column == pc + 4:
                rng = inventoryutils.itemFindItemCardInfoValue(item,
                        inventoryutils.eItemCardInfoValueText.Range)
                if rng == None:
                    return None
                else:
                    return round(rng, 2)
            elif column == pc + 5:
                val = inventoryutils.itemFindItemCardInfoValue(item,
                        inventoryutils.eItemCardInfoValueText.Accuracy)
                if val == None:
                    return None
                else:
                    return round(val, 2)
            elif column == pc + 6:
                return inventoryutils.itemFindItemCardInfoValue(item, True, 'showAsDescription', 'text')
            elif column == pc + 7:
                if inventoryutils.itemIsWeaponGun(item):
                    return 'Gun'
                elif inventoryutils.itemIsWeaponMelee(item):
                    return 'Melee'
                elif inventoryutils.itemIsWeaponThrowable(item):
                    return 'Grenade'
                else:
                    return 'Unknown'
            elif column == pc + 8:
                value = inventoryutils.itemFindItemCardInfoValue(item, 10, 'damageType')
                text = None
                if value != None:
                    text = inventoryutils.itemFindItemCardInfoValue(item, 10, 'damageType', 'text')
                    text += ' (' + str(value) + ')'
                return text
        elif role == QtCore.Qt.TextAlignmentRole:
            if column == pc:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignCenter
            elif column == pc + 1:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignCenter
            elif column == pc + 2:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight
            elif column == pc + 3:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight
            elif column == pc + 4:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight
            elif column == pc + 5:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight
            elif column == pc + 6:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft
            elif column == pc + 7:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft
            elif column == pc + 8:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft
        return super()._data(item, column, role)

    def _cmUseActionText(self, item, selected):
        return "Use Weapon"

    def _cmDropActionText(self, item, selected):
        return 'Drop Weapon'



class CatApparelModel(InventoryTableModel):
    def __init__(self, qparent = None):
        super().__init__(qparent)

    def _acceptItem(self, item):
        return inventoryutils.itemHasAnyFilterCategory(item,
            inventoryutils.eItemFilterCategory.Apparel)

    def columnCount(self, parent = QtCore.QModelIndex()):
        return super().columnCount(parent) + 5

    def headerData(self, section, orientation, role = QtCore.Qt.DisplayRole):
        pc = super().columnCount()
        if orientation == QtCore.Qt.Horizontal:
            if role == QtCore.Qt.DisplayRole:
                if section == pc:
                    return 'E'
                elif section == pc + 1:
                    return 'L'
                elif section == pc + 2:
                    return 'DMG Resist'
                elif section == pc + 3:
                    return 'Effects'
                elif section == pc + 4:
                    return 'Slots'
        return super().headerData(section, orientation, role)

    def _data(self, item, column, role = QtCore.Qt.DisplayRole):
        pc = super().columnCount()
        if role == QtCore.Qt.DisplayRole:
            if column == pc:
                if item.child('equipState').value() > 0:
                    return '◼'
                else:
                    return ''
            elif column == pc + 1:
                if item.child('isLegendary').value() > 0:
                    return '◼'
                else:
                    return ''
            elif column == pc + 2:
                cached = item.getUserCache('damageresisttext')
                if not cached or cached.dirtyFlag:
                    text  =''
                    isFirst = True
                    damageInfos = inventoryutils.itemFindItemCardInfos(item, inventoryutils.eItemCardInfoValueText.DamageResist)
                    for info in damageInfos:
                        damageType = info.child('damageType').value()
                        value = info.child('Value').value()
                        if damageType < 10 and value != 0.0:
                            if isFirst:
                                isFirst = False
                            else:
                                text += ' + '
                            text += str(int(value))
                            text += ' ' + itemCardInfoDamageTypes[damageType]
                    item.setUserCache('damageresisttext', text, 10)
                else:
                    text = cached.value
                return text
            elif column == pc + 3:
                cached = item.getUserCache('effectstext')
                descCount = 0
                if not cached or cached.dirtyFlag:
                    text  =''
                    isFirst = True
                    for info in item.child('itemCardInfoList').value():
                        itext = info.child('text').value()
                        isDesc = info.child('showAsDescription')
                        ivalue = info.child('Value').value()
                        if not itext[0] == '$' and not itext[0] == '%' and ((isDesc and isDesc.value() and descCount == 0) or ivalue != 0.0):
                            if isFirst:
                                isFirst = False
                            else:
                                text += ', '
                            text += itext
                            if not isDesc or not isDesc.value():
                                duration = info.child('duration')
                                scaleWithDur = info.child('scaleWithDuration')
                                if scaleWithDur and scaleWithDur.value():
                                    ivalue *= duration.value()
                                asPercent = info.child('showAsPercent')
                                if (not asPercent or not asPercent.value()) and ivalue > 0:
                                    text += ' +' + str(int(ivalue))
                                else:
                                    text += ' ' + str(int(ivalue))
                                if asPercent and asPercent.value():
                                    text += '%'
                                if duration and duration.value() > 0.0:
                                    if scaleWithDur and scaleWithDur.value():
                                        text += ' over '
                                    else:
                                        text += ' ('
                                    text += str(int(duration.value())) + 'sec'
                                    if scaleWithDur and scaleWithDur.value():
                                        pass
                                    else:
                                        text += ')'
                            else:
                                descCount += 1
                    item.setUserCache('effectstext', text, 10)
                else:
                    text = cached.value
                return text
                #return inventoryutils.itemFindItemCardInfoValue(item, True, 'showAsDescription', 'text')
            elif column == pc + 4:
                text = ''
                i = 0
                isFirst = True
                for section in item.child('PaperdollSection').value():
                    if section.value():
                        if isFirst:
                            isFirst = False
                        else:
                            text += ', '
                        text += itemApparelPaperDollSections[i]
                    i += 1
                return text
        elif role == QtCore.Qt.TextAlignmentRole:
            if column == pc:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignCenter
            elif column == pc + 1:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignCenter
            elif column == pc + 2:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight
            elif column == pc + 3:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft
            elif column == pc + 4:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft
        return super()._data(item, column, role)

    def _cmUseActionText(self, item, selected):
        return 'Use Apparel'

    def _cmDropActionText(self, item, selected):
        return 'Drop Apparel'



class CatBooksModel(InventoryTableModel):
    def __init__(self, qparent = None):
        super().__init__(qparent)

    def _acceptItem(self, item):
        return inventoryutils.itemHasAnyFilterCategory(item,
            inventoryutils.eItemFilterCategory.Book)

    def _cmUseActionText(self, item, selected):
        return 'Read Book'

    def _cmDropActionText(self, item, selected):
        return 'Drop Book'



class CatAmmoModel(InventoryTableModel):
    def __init__(self, qparent = None):
        super().__init__(qparent)

    def _acceptItem(self, item):
        return inventoryutils.itemHasAnyFilterCategory(item,
            inventoryutils.eItemFilterCategory.Ammo)

    def _cmIsUseActionEnabled(self, item, selected):
        return False

    def _cmDropActionText(self, item, selected):
        return 'Drop Ammo'



class CatKeysModel(InventoryTableModel):
    def __init__(self, qparent = None):
        super().__init__(qparent)

    def _acceptItem(self, item):
        return inventoryutils.itemIsAKey(item)

    def _cmIsUseActionEnabled(self, item, selected):
        return False

    def _cmIsDropActionEnabled(self, item, selected):
        return False



class CatAidModel(InventoryTableModel):
    def __init__(self, qparent = None):
        super().__init__(qparent)

    def _acceptItem(self, item):
        return inventoryutils.itemHasAnyFilterCategory(item,
            inventoryutils.eItemFilterCategory.Aid)

    def columnCount(self, parent = QtCore.QModelIndex()):
        return super().columnCount(parent) + 1

    def headerData(self, section, orientation, role = QtCore.Qt.DisplayRole):
        pc = super().columnCount()
        if orientation == QtCore.Qt.Horizontal:
            if role == QtCore.Qt.DisplayRole:
                if section == pc:
                    return 'Effects'
        return super().headerData(section, orientation, role)

    def _data(self, item, column, role = QtCore.Qt.DisplayRole):
        pc = super().columnCount()
        if role == QtCore.Qt.DisplayRole:
            if column == pc:
                cached = item.getUserCache('effectstext')
                descCount = 0
                if not cached or cached.dirtyFlag:
                    text  =''
                    isFirst = True
                    for info in item.child('itemCardInfoList').value():
                        itext = info.child('text').value()
                        isDesc = info.child('showAsDescription')
                        ivalue = info.child('Value').value()
                        if not itext[0] == '$' and not itext[0] == '%' and ((isDesc and isDesc.value() and descCount == 0) or ivalue != 0.0):
                            if isFirst:
                                isFirst = False
                            else:
                                text += ', '
                            text += itext
                            if not isDesc or not isDesc.value():
                                duration = info.child('duration')
                                scaleWithDur = info.child('scaleWithDuration')
                                if scaleWithDur and scaleWithDur.value():
                                    ivalue *= duration.value()
                                asPercent = info.child('showAsPercent')
                                if (not asPercent or not asPercent.value()) and ivalue > 0:
                                    text += ' +' + str(int(ivalue))
                                else:
                                    text += ' ' + str(int(ivalue))
                                if asPercent and asPercent.value():
                                    text += '%'
                                if duration and duration.value() > 0.0:
                                    if scaleWithDur and scaleWithDur.value():
                                        text += ' over '
                                    else:
                                        text += ' ('
                                    text += str(int(duration.value())) + 'sec'
                                    if scaleWithDur and scaleWithDur.value():
                                        pass
                                    else:
                                        text += ')'
                            else:
                                descCount += 1
                    item.setUserCache('effectstext', text, 10)
                else:
                    text = cached.value
                return text
        elif role == QtCore.Qt.TextAlignmentRole:
            if column == pc:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft
        return super()._data(item, column, role)

    def _cmUseActionText(self, item, selected):
        return 'Use Aid'

    def _cmDropActionText(self, item, selected):
        return 'Drop Aid'



class CatHolotapeModel(InventoryTableModel):
    def __init__(self, qparent = None):
        super().__init__(qparent)

    def _acceptItem(self, item):
        return inventoryutils.itemHasAnyFilterCategory(item,
            inventoryutils.eItemFilterCategory.Holotape)

    def _cmUseActionText(self, item, selected):
        return 'Play Holotape'

    def _cmDropActionText(self, item, selected):
        return 'Drop holotape'



class CatMiscModel(InventoryTableModel):
    def __init__(self, qparent = None):
        super().__init__(qparent)

    def _acceptItem(self, item):
        return (inventoryutils.itemHasExactFilterCategory(item,
            inventoryutils.eItemFilterCategory.Misc)
            and not inventoryutils.itemIsAKey(item))

    def _cmIsUseActionEnabled(self, item, selected):
        return False

    def _cmDropActionText(self, item, selected):
        return 'Drop Item'



class CatJunkModel(InventoryTableModel):
    def __init__(self, qparent = None):
        super().__init__(qparent)

    def _acceptItem(self, item):
        return inventoryutils.itemHasAnyFilterCategory(item,
            inventoryutils.eItemFilterCategory.Junk)

    def columnCount(self, parent = QtCore.QModelIndex()):
        return super().columnCount(parent) + 2

    def headerData(self, section, orientation, role = QtCore.Qt.DisplayRole):
        pc = super().columnCount()
        if orientation == QtCore.Qt.Horizontal:
            if role == QtCore.Qt.DisplayRole:
                if section == pc:
                    return 'Tagged'
                elif section == pc + 1:
                    return 'Components'
        return super().headerData(section, orientation, role)

    def _data(self, item, column, role = QtCore.Qt.DisplayRole):
        pc = super().columnCount()
        if role == QtCore.Qt.DisplayRole:
            if column == pc:
                if item.child('taggedForSearch').value():
                    return '◼'
                else:
                    return ''
            elif column == pc + 1:
                cached = item.getUserCache('componentstext')
                if not cached or cached.dirtyFlag:
                    text  =''
                    isFirst = True
                    for c in item.child('components').value():
                        if isFirst:
                            isFirst = False
                        else:
                            text += ', '
                        text += c.child('text').value()
                        count = c.child('count').value()
                        if count > 1:
                            text += '(' + str(count) + ')'
                    item.setUserCache('componentstext', text, 10)
                else:
                    text = cached.value
                return text
        elif role == QtCore.Qt.TextAlignmentRole:
            if column == pc:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignCenter
            elif column == pc + 1:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft
        return super()._data(item, column, role)

    def _cmIsUseActionEnabled(self, item, selected):
        return False

    def _cmDropActionText(self, item, selected):
        return 'Drop Item'



class CatModsModel(InventoryTableModel):
    def __init__(self, qparent = None):
        super().__init__(qparent)

    def _acceptItem(self, item):
        return inventoryutils.itemHasAnyFilterCategory(item,
            inventoryutils.eItemFilterCategory.Mods)

    def _cmIsUseActionEnabled(self, item, selected):
        return False

    def _cmDropActionText(self, item, selected):
        return 'Drop Mod'
    
    
    
class ComponentsTableModel(QtCore.QAbstractTableModel):
    _signalComponentsUpdate = QtCore.pyqtSignal(object)

    def __init__(self, view, qparent = None):
        super().__init__(qparent)
        self.view = view
        self.pipInventory = None
        self.pipComponents = None
        self.tabIsVisible = False
        self.isDirty = False
        self._components = []
        self._signalComponentsUpdate.connect(self._slotComponentsUpdate)

    def setPipInventory(self, datamanager, pipInventory):
        self.modelAboutToBeReset.emit()
        self.pipInventory = pipInventory
        self.datamanager = datamanager
        pipComponents = self.pipInventory.child('InvComponents')
        if pipComponents:
            self._components = pipComponents.value()
            if self.pipComponents:
                self.pipComponents.unregisterValueUpdatedListener(self._onPipComponentsUpdate)
            self.pipComponents = pipComponents
            self.pipComponents.registerValueUpdatedListener(self._onPipComponentsUpdate, 10)
        else:
            self._components = []
        self.modelReset.emit()

    def _onPipComponentsUpdate(self, caller, value, pathObjs):
        self._signalComponentsUpdate.emit(caller)

    @QtCore.pyqtSlot()
    def _slotComponentsUpdate(self):
        self.layoutAboutToBeChanged.emit()
        self._components = self.pipComponents.value()
        self.layoutChanged.emit()

    def rowCount(self, parent = QtCore.QModelIndex()):
        return len(self._components)

    def columnCount(self, parent = QtCore.QModelIndex()):
        return 4

    def headerData(self, section, orientation, role = QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal:
            if role == QtCore.Qt.DisplayRole:
                if section == 0:
                    return 'Name'
                elif section == 1:
                    return 'Count'
                elif section == 2:
                    return 'T'
                elif section == 3:
                    return 'Items'
        return None

    def data(self, index, role = QtCore.Qt.DisplayRole):
        return self._data(self._components[index.row()], index.column(), role)

    def _data(self, component, column, role = QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if column == 0:
                return component.child('text').value()
            elif column == 1:
                return component.child('count').value()
            elif column == 2:
                if component.child('taggedForSearch').value():
                    return '◼'
                else:
                    return ''
            elif column == 3:
                text = ''
                isFirst = True
                for item in component.child('componentOwners').value():
                    if isFirst:
                        isFirst = False
                    else:
                        text += ', '
                    text += item.child('text').value()
                return text
        elif role == QtCore.Qt.TextAlignmentRole:
            if column == 0:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft
            elif column == 1:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight
            elif column == 2:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignCenter
            elif column == 3:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft
        elif role == QtCore.Qt.FontRole:
            if component.child('taggedForSearch').value():
                font = QtGui.QFont()
                font.setBold(True)
                return font
        return None

    def getPipValue(self, row):
        if len(self._components) > row:
            return self._components[row]
        else:
            return None

    def showItemContextMenu(self, datamanager, component, selected, pos, view):
        menu = QtWidgets.QMenu(view)
        if self._data(component, 2):
            labelTxt = 'Un-tag for Search'
        else:
            labelTxt = 'Tag for Search'
        def _toggleComponentFavorite():
            datamanager.rpcToggleComponentFavorite(component)
        action = menu.addAction(labelTxt)
        action.triggered.connect(_toggleComponentFavorite)
        menu.exec(view.mapToGlobal(pos))

    def itemDoubleClicked(self, datamanager, component, view):
        datamanager.rpcToggleComponentFavorite(component)

    def tabVisibilityChanged(self, visible):
        pass
    

