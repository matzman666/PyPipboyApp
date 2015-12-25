# -*- coding: utf-8 -*-


import re
from PyQt5 import QtCore
from pypipboy import inventoryutils


    

class SortProxyModel(QtCore.QSortFilterProxyModel):
    def __init__(self, settings, prefix, qparent = None):
        super().__init__(qparent)
        self.settings = settings
        self._settingsPrefix = prefix
        self.sortColumn = int(self.settings.value(prefix + '/sortColumn', 0))
        # Buggy QSettings Linux implementation forces us to convert to int and then to bool
        self.sortReversed = bool(int(self.settings.value(prefix + '/sortReversed', 0)))
        self.filterString = ''
        
    def sort(self, column, order = QtCore.Qt.AscendingOrder):
        self.sortColumn = column
        if order == QtCore.Qt.DescendingOrder:
            self.sortReversed = True
        else:
            self.sortReversed = False
        self.settings.setValue(self._settingsPrefix + '/sortColumn', column)
        self.settings.setValue(self._settingsPrefix + '/sortReversed', int(self.sortReversed))
        super().sort(column, order)
        
    def filterAcceptsRow(self, source_row, source_parent):
        item = self.sourceModel().getPipValue(source_row)
        if item:
            if self.filterString and not re.search(self.filterString, item.child('text').value(), re.I):
                return False
            return True
        return False
    
    def lessThan(self, left, right):
        leftData = self.sourceModel().data(left)
        rightData = self.sourceModel().data(right)
        try:
            if left.column() != 0 and leftData == rightData:
                return super().lessThan(self.sourceModel().index(left.row(), 0), self.sourceModel().index(right.row(), 0))
        except:
            pass
        return super().lessThan(left, right)
    
    def headerData(self, section, orientation, role = QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Vertical:
            if role == QtCore.Qt.DisplayRole:
                return section + 1
        else:
            return super().headerData(section, orientation, role)
    
    @QtCore.pyqtSlot(str)
    def setFilterString(self, value):
        self.filterString = value
        self.invalidateFilter()



class WeaponSortProxyModel(SortProxyModel):
    def __init__(self, settings, prefix, qparent = None):
        super().__init__(settings, prefix, qparent)
    
    def lessThan(self, left, right):
        if self.sourceModel().headerData(left.column(), QtCore.Qt.Horizontal) == 'Damage':
            leftItem = self.sourceModel().getPipValue(left.row())
            rightItem = self.sourceModel().getPipValue(right.row())
            def _getDamage(item):
                cached = item.getUserCache('damagevalue')
                if not cached or cached.dirtyFlag:
                    value  = 0.0
                    damageInfos = inventoryutils.itemFindItemCardInfos(item, inventoryutils.eItemCardInfoValueText.Damage)                 
                    for info in damageInfos:
                        damageType = info.child('damageType').value()
                        ivalue = info.child('Value').value()
                        if damageType < 10:
                            value += ivalue
                    item.setUserCache('damagevalue', value, 10)
                else:
                    value = cached.value
                return value
            return _getDamage(leftItem) < _getDamage(rightItem)
        return super().lessThan(left, right)


class ApparelSortProxyModel(SortProxyModel):
    def __init__(self, settings, prefix, qparent = None):
        super().__init__(settings, prefix, qparent)
    
    def lessThan(self, left, right):
        if self.sourceModel().headerData(left.column(), QtCore.Qt.Horizontal) == 'DMG Resist':
            leftItem = self.sourceModel().getPipValue(left.row())
            rightItem = self.sourceModel().getPipValue(right.row())
            def _getDamageResist(item):
                cached = item.getUserCache('damageresistvalue')
                if not cached or cached.dirtyFlag:
                    value  = 0.0
                    damageInfos = inventoryutils.itemFindItemCardInfos(item, inventoryutils.eItemCardInfoValueText.DamageResist)                 
                    for info in damageInfos:
                        damageType = info.child('damageType').value()
                        ivalue = info.child('Value').value()
                        if damageType < 10:
                            value += ivalue
                    item.setUserCache('damageresistvalue', value, 10)
                else:
                    value = cached.value
                return value
            return _getDamageResist(leftItem) < _getDamageResist(rightItem)
        return super().lessThan(left, right)
