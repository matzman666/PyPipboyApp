# -*- coding: utf-8 -*-

import time
from PyQt5 import QtWidgets, QtCore, QtGui



class WorkshopTableModel(QtCore.QAbstractTableModel):
    _signalWorkshopsUpdate = QtCore.pyqtSignal()

    def __init__(self, view, qparent = None):
        super().__init__(qparent)
        self.view = view
        self.pipWorkshops = None
        self._workshops = []
        self._signalWorkshopsUpdate.connect(self._slotWorkshopsUpdate)

    def setPipWorkshops(self, datamanager, pipWorkshops):
        self.modelAboutToBeReset.emit()
        self.pipWorkshops = pipWorkshops
        self.datamanager = datamanager
        self.pipWorkshops.registerValueUpdatedListener(self._onPipWorkshopsUpdated, 10)
        self._workshops.clear()
        for w in self.pipWorkshops.value():
            if w.child('owned').value():
                self._workshops.append(w)
        self.modelReset.emit()

    def _onPipWorkshopsUpdated(self, caller, value, pathObjs):
        self._signalWorkshopsUpdate.emit()

    @QtCore.pyqtSlot()
    def _slotWorkshopsUpdate(self):
        self.layoutAboutToBeChanged.emit()
        self._workshops.clear()
        for w in self.pipWorkshops.value():
            if w.child('owned').value():
                self._workshops.append(w)
        self.layoutChanged.emit()

    def rowCount(self, parent = QtCore.QModelIndex()):
        return len(self._workshops)

    def columnCount(self, parent = QtCore.QModelIndex()):
        return 12

    def headerData(self, section, orientation, role = QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal:
            if role == QtCore.Qt.DisplayRole:
                if section == 0:
                    return 'Name'
                elif section == 1:
                    return 'People'
                elif section == 2:
                    return 'Food'
                elif section == 3:
                    return 'Water'
                elif section == 4:
                    return 'Power'
                elif section == 5:
                    return 'Defense'
                elif section == 6:
                    return 'Beds'
                elif section == 7:
                    return 'Happiness'
                elif section == 8:
                    return 'Food Diff'
                elif section == 9:
                    return 'Water Diff'
                elif section == 10:
                    return 'Defense Diff'
                elif section == 11:
                    return 'Beds Diff'
        return None

    def data(self, index, role = QtCore.Qt.DisplayRole):
        return self._data(self._workshops[index.row()], index.column(), role)

    def _data(self, workshop, column, role = QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if column == 0:
                text = workshop.child('text').value()
                if workshop.child('rating').value() < 0:
                    text += ' (!)'
                elif workshop.child('rating').value() > 0:
                    text += ' (+)'
                return text
            elif column == 1:
                value = workshop.child('workshopData').child(0).child('Value').value()
                rating = workshop.child('workshopData').child(0).child('rating').value()
                if rating < 0:
                    return '(-) ' + str(value)
                elif rating > 0:
                    return '(+) ' + str(value)
                else:
                    return str(value)
            elif column == 2:
                value = workshop.child('workshopData').child(1).child('Value').value()
                rating = workshop.child('workshopData').child(1).child('rating').value()
                if rating < 0:
                    return '(-) ' + str(value)
                elif rating > 0:
                    return '(+) ' + str(value)
                else:
                    return str(value)
            elif column == 3:
                value = workshop.child('workshopData').child(2).child('Value').value()
                rating = workshop.child('workshopData').child(2).child('rating').value()
                if rating < 0:
                    return '(-) ' + str(value)
                elif rating > 0:
                    return '(+) ' + str(value)
                else:
                    return str(value)
            elif column == 4:
                value = workshop.child('workshopData').child(3).child('Value').value()
                rating = workshop.child('workshopData').child(3).child('rating').value()
                if rating < 0:
                    return '(-) ' + str(value)
                elif rating > 0:
                    return '(+) ' + str(value)
                else:
                    return str(value)
            elif column == 5:
                value = workshop.child('workshopData').child(4).child('Value').value()
                rating = workshop.child('workshopData').child(4).child('rating').value()
                if rating < 0:
                    return '(-) ' + str(value)
                elif rating > 0:
                    return '(+) ' + str(value)
                else:
                    return str(value)
            elif column == 6:
                value = workshop.child('workshopData').child(5).child('Value').value()
                rating = workshop.child('workshopData').child(5).child('rating').value()
                if rating < 0:
                    return '(-) ' + str(value)
                elif rating > 0:
                    return '(+) ' + str(value)
                else:
                    return str(value)
            elif column == 7:
                value = workshop.child('workshopData').child(6).child('Value').value()
                rating = workshop.child('workshopData').child(6).child('rating').value()
                if rating < 0:
                    return '(-) ' + str(value)
                elif rating > 0:
                    return '(+) ' + str(value)
                else:
                    return str(value)
            elif column > 7 and column < 12:
                value = self._dataRaw(workshop, column, role)
                if value > 0:
                    return '+' + str(value)
                else:
                    return str(value)
        elif role == QtCore.Qt.TextAlignmentRole:
            if column == 0:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft
            else:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight
        elif role == QtCore.Qt.FontRole:
            if workshop.child('rating').value() < 0:
                font = QtGui.QFont()
                font.setBold(True)
                return font
        return None

    def dataRaw(self, index, role = QtCore.Qt.DisplayRole):
        return self._dataRaw(self._workshops[index.row()], index.column(), role)

    def _dataRaw(self, workshop, column, role = QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if column == 0:
                return workshop.child('text').value()
            elif column == 1:
                return workshop.child('workshopData').child(0).child('Value').value()
            elif column == 2:
                return workshop.child('workshopData').child(1).child('Value').value()
            elif column == 3:
                return workshop.child('workshopData').child(2).child('Value').value()
            elif column == 4:
                return workshop.child('workshopData').child(3).child('Value').value()
            elif column == 5:
                return workshop.child('workshopData').child(4).child('Value').value()
            elif column == 6:
                return workshop.child('workshopData').child(5).child('Value').value()
            elif column == 7:
                return workshop.child('workshopData').child(6).child('Value').value()
            elif column == 8:
                food = workshop.child('workshopData').child(1).child('Value').value()
                people = workshop.child('workshopData').child(0).child('Value').value()
                return food - people
            elif column == 9:
                water = workshop.child('workshopData').child(2).child('Value').value()
                people = workshop.child('workshopData').child(0).child('Value').value()
                return water - people
            elif column == 10:
                defense = workshop.child('workshopData').child(4).child('Value').value()
                food = workshop.child('workshopData').child(1).child('Value').value()
                water = workshop.child('workshopData').child(2).child('Value').value()
                return defense - (food + water)
            elif column == 11:
                beds = workshop.child('workshopData').child(5).child('Value').value()
                people = workshop.child('workshopData').child(0).child('Value').value()
                return beds - people
        return None

    def getPipValue(self, row):
        if len(self._workshops) > row:
            return self._workshops[row]
        else:
            return None




class SortProxyModel(QtCore.QSortFilterProxyModel):
    def __init__(self, settings, prefix, qparent = None):
        super().__init__(qparent)
        self.settings = settings
        self._settingsPrefix = prefix
        self.sortColumn = int(self.settings.value(prefix + '/sortColumn', 0))
        self.lastSortColumn = int(self.settings.value(prefix + '/lastSortColumn', 0))
        # Buggy QSettings Linux implementation forces us to convert to int and then to bool
        self.sortReversed = bool(int(self.settings.value(prefix + '/sortReversed', 0)))
        self.lastSortReversed = bool(int(self.settings.value(prefix + '/lastSortReversed', 0)))
        self.filterString = ''
        
    def sort(self, column, order = QtCore.Qt.AscendingOrder):
        if self.sortColumn != column:
            self.lastSortColumn = self.sortColumn
            self.settings.setValue(self._settingsPrefix + '/lastSortColumn', self.lastSortColumn)
            self.lastSortReversed = self.sortReversed
            self.settings.setValue(self._settingsPrefix + '/lastSortReversed', int(self.lastSortReversed))
            self.sortColumn = column
            self.settings.setValue(self._settingsPrefix + '/sortColumn', column)
        if order == QtCore.Qt.DescendingOrder:
            self.sortReversed = True
        else:
            self.sortReversed = False
        self.settings.setValue(self._settingsPrefix + '/sortReversed', int(self.sortReversed))
        super().sort(column, order)
    
    def lessThan(self, left, right):
        leftData = self.sourceModel().dataRaw(left)
        rightData = self.sourceModel().dataRaw(right)
        try:
            if leftData == rightData and left.column() != self.lastSortColumn:
                comp = self.lessThan(self.sourceModel().index(left.row(), self.lastSortColumn), 
                                        self.sourceModel().index(right.row(), self.lastSortColumn))
                if self.lastSortReversed:
                    return not comp
                else:
                    return comp
            else:
                return leftData < rightData
        except:
            pass
        return super().lessThan(left, right)
    
    def headerData(self, section, orientation, role = QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Vertical:
            if role == QtCore.Qt.DisplayRole:
                return section + 1
        else:
            return super().headerData(section, orientation, role)


