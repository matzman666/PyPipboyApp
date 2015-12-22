# -*- coding: utf-8 -*-


import os
import re
import threading
from PyQt5 import QtWidgets, QtCore, QtGui, uic
from widgets import widgets
from widgets.shared import settings
from pypipboy.datamanager import ePipboyValueType



class InventoryTableModel(QtCore.QAbstractTableModel):
    _signalInventoryUpdate = QtCore.pyqtSignal()
    
    def __init__(self, catLabel = None, qparent = None):
        super().__init__(qparent)
        self.pipInventory = None
        self._signalInventoryUpdate.connect(self._slotInventoryUpdate)
        self._items = []
        self.fullUpdate = False
        self.catLabel = catLabel
        self.updateQueue = []
        self.updateQueueLock = threading.Lock()
    
    def setPipInventory(self, pipValue):
        self.modelAboutToBeReset.emit()
        self.pipInventory = pipValue
        self._items = []
        cat = self.pipInventory.child(self.catLabel)
        if cat:
            self._items += cat.value()
            cat.registerValueUpdatedListener(self._onPipInventoryUpdate, 99)
        self.modelReset.emit()
    
    def _onPipInventoryUpdate(self, caller, value, pathObjs):
        if not self.fullUpdate and pathObjs and len(pathObjs) > 0:
            i = pathObjs[len(pathObjs)-1]
            self.updateQueueLock.acquire()
            try:
                self.updateQueue.index(i)
            except:
                self.updateQueue.append(i)
            self.updateQueueLock.release()
            self._signalInventoryUpdate.emit()
        else:
            self.fullUpdate = True
            self.updateQueue.clear()
            self._signalInventoryUpdate.emit()
        
    def _doFullUpdate(self):
        self._items = []
        cat = self.pipInventory.child(self.catLabel)
        if cat:
            self._items += cat.value()
        
    @QtCore.pyqtSlot()
    def _slotInventoryUpdate(self):
        if self.fullUpdate:
            self.layoutAboutToBeChanged.emit()
            self._doFullUpdate()
            self.fullUpdate = False
            self.layoutChanged.emit()
        else:
            self.updateQueueLock.acquire()
            q = self.updateQueue
            self.updateQueue = []
            self.updateQueueLock.release()
            for item in q:
                try:
                    t = self._items.index(item)
                    self.dataChanged.emit(self.index(t, 0), self.index(t, self.rowCount()))
                except:
                    pass
        
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
                text = item.child('text').value()
                #count = item.child('count').value()
                #if count > 1:
                #    text += ' (' + str(count) + ')'
                return text
            elif column == 1:
                return item.child('count').value()
            elif column == 2:
                vInfo = self._findItemCardInfoByText(item, '$val')
                if vInfo:
                    return vInfo.child('Value').value()
                else:
                    return None
            elif column == 3:
                wInfo = self._findItemCardInfoByText(item, '$wt')
                if wInfo:
                    return wInfo.child('Value').value()
                else:
                    return None
            elif column == 4:
                vInfo = self._findItemCardInfoByText(item, '$val')
                wInfo = self._findItemCardInfoByText(item, '$wt')
                if vInfo and wInfo:
                    value = vInfo.child('Value').value()
                    weight = wInfo.child('Value').value()
                    if weight > 0:
                        return value/weight
                    else:
                        return 'inf'
                else:
                    return '-'
        elif role == QtCore.Qt.FontRole:
            if item.child('equipState').value() > 0:
                font = QtGui.QFont()
                font.setBold(True)
                return font
        return None
    
    def _findItemCardInfoByText(self, item, text):
        infos = item.child('itemCardInfoList')
        for i in infos.value():
            if i.child('text').value() == text:
                return i
        return None
        
    def getPipValue(self, row):
        if len(self._items) > row:
            return self._items[row]
        else:
            return None
    
    def showItemContextMenu(self, datamanager, item, pos, view):
        menu = QtWidgets.QMenu(view)
        def _useItem():
            view.setCurrentIndex(QtCore.QModelIndex())
            datamanager.rpcUseItem(item)
        uaction = menu.addAction('Use Item')
        uaction.triggered.connect(_useItem)
        def _dropItem():
            view.setCurrentIndex(QtCore.QModelIndex())
            datamanager.rpcDropItem(item, 1)
        daction = menu.addAction('Drop Item')
        daction.triggered.connect(_dropItem)
        menu.exec(view.mapToGlobal(pos))
        
    def itemDoubleClicked(self, datamanager, item, view):
        view.setCurrentIndex(QtCore.QModelIndex())
        datamanager.rpcUseItem(item)
        
    

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


class CatAllModel(InventoryTableModel):
    def __init__(self, qparent = None):
        super().__init__(None, qparent)
    
    def setPipInventory(self, pipValue):
        self.modelAboutToBeReset.emit()
        self.pipInventory = pipValue
        self._items = []
        for i in ['29', '30', '35', '43', '44', '47', '48', '50']:
            cat = self.pipInventory.child(i)
            if cat:
                self._items += cat.value()
                cat.registerValueUpdatedListener(self._onPipInventoryUpdate, 99)
        self.modelReset.emit()
        
    def _doFullUpdate(self):
        self._items = []
        for i in ['29', '30', '35', '43', '44', '47', '48', '50']:
            cat = self.pipInventory.child(i)
            if cat:
                self._items += cat.value()
        
    def columnCount(self, parent = QtCore.QModelIndex()):
        return super().columnCount(parent) + 2
    
    def headerData(self, section, orientation, role = QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal:
            pc = super().columnCount()
            if role == QtCore.Qt.DisplayRole:
                if section == pc:
                    return 'equipped'
                if section == pc + 1:
                    return 'legendary'
                elif section == pc + 2:
                    return 'filterFlag'
        return super().headerData(section, orientation, role)
        
    def _data(self, item, column, role = QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            pc = super().columnCount()
            if column == pc:
                return item.child('equipState').value()
            elif column == pc + 1:
                return item.child('isLegendary').value()
            elif column == pc + 2:
                return item.child('filterFlag').value()
        return super()._data(item, column, role)


class CatWeaponsModel(InventoryTableModel):
    def __init__(self, qparent = None):
        super().__init__('43', qparent)
        
    def columnCount(self, parent = QtCore.QModelIndex()):
        return super().columnCount(parent) + 3
    
    def headerData(self, section, orientation, role = QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal:
            pc = super().columnCount()
            if role == QtCore.Qt.DisplayRole:
                if section == pc:
                    return 'equipped'
                if section == pc + 1:
                    return 'legendary'
                elif section == pc + 2:
                    return 'filterFlag'
        return super().headerData(section, orientation, role)
        
    def _data(self, item, column, role = QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            pc = super().columnCount()
            if column == pc:
                return item.child('equipState').value()
            elif column == pc + 1:
                return item.child('isLegendary').value()
            elif column == pc + 2:
                return item.child('filterFlag').value()
        return super()._data(item, column, role)


class CatApparelModel(InventoryTableModel):
    def __init__(self, qparent = None):
        super().__init__('29', qparent)


class CatBooksModel(InventoryTableModel):
    def __init__(self, qparent = None):
        super().__init__('30', qparent)


class CatAmmoModel(InventoryTableModel):
    def __init__(self, qparent = None):
        super().__init__('44', qparent)


class CatKeysModel(InventoryTableModel):
    def __init__(self, qparent = None):
        super().__init__('47', qparent)


class CatAidModel(InventoryTableModel):
    def __init__(self, qparent = None):
        super().__init__('48', qparent)


class CatHolotapeModel(InventoryTableModel):
    def __init__(self, qparent = None):
        super().__init__('50', qparent)


class CatMiscModel(InventoryTableModel):
    def __init__(self, qparent = None):
        super().__init__('35', qparent)
    
    def setPipInventory(self, pipValue):
        self.modelAboutToBeReset.emit()
        self.pipInventory = pipValue
        self._items = []
        cat = self.pipInventory.child(self.catLabel)
        if cat:
            for i in cat.value():
                if i.child('filterFlag').value() == 512:
                    self._items.append(i)
            cat.registerValueUpdatedListener(self._onPipInventoryUpdate, 99)
        self.modelReset.emit()
        
    def _doFullUpdate(self):
        self._items = []
        cat = self.pipInventory.child(self.catLabel)
        if cat:
            for i in cat.value():
                if i.child('filterFlag').value() == 512:
                    self._items.append(i)


class CatJunkModel(InventoryTableModel):
    def __init__(self, qparent = None):
        super().__init__('35', qparent)
    
    def setPipInventory(self, pipValue):
        self.modelAboutToBeReset.emit()
        self.pipInventory = pipValue
        self._items = []
        cat = self.pipInventory.child(self.catLabel)
        if cat:
            for i in cat.value():
                if i.child('filterFlag').value() == 1024:
                    self._items.append(i)
            cat.registerValueUpdatedListener(self._onPipInventoryUpdate, 99)
        self.modelReset.emit()
        
    def _doFullUpdate(self):
        self._items = []
        cat = self.pipInventory.child(self.catLabel)
        if cat:
            for i in cat.value():
                if i.child('filterFlag').value() == 1024:
                    self._items.append(i)
        
    def columnCount(self, parent = QtCore.QModelIndex()):
        return super().columnCount(parent) + 2
    
    def headerData(self, section, orientation, role = QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal:
            pc = super().columnCount()
            if role == QtCore.Qt.DisplayRole:
                if section == pc:
                    return 'tagged'
                elif section == pc + 1:
                    return 'Components'
        return super().headerData(section, orientation, role)
        
    def _data(self, item, column, role = QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            pc = super().columnCount()
            if column == pc:
                return item.child('taggedForSearch').value()
            elif column == pc + 1:
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
                return text
        return super()._data(item, column, role)


class CatModsModel(InventoryTableModel):
    def __init__(self, qparent = None):
        super().__init__('35', qparent)
    
    def setPipInventory(self, pipValue):
        self.modelAboutToBeReset.emit()
        self.pipInventory = pipValue
        self._items = []
        cat = self.pipInventory.child(self.catLabel)
        if cat:
            for i in cat.value():
                if i.child('filterFlag').value() == 2048:
                    self._items.append(i)
            cat.registerValueUpdatedListener(self._onPipInventoryUpdate, 99)
        self.modelReset.emit()
        
    def _doFullUpdate(self):
        self._items = []
        cat = self.pipInventory.child(self.catLabel)
        if cat:
            for i in cat.value():
                if i.child('filterFlag').value() == 2048:
                    self._items.append(i)
    
    


class InventoryBrowserWidget(widgets.WidgetBase):    
    def __init__(self, mhandle, parent):
        super().__init__('Inventory Browser', parent)
        self.widget = uic.loadUi(os.path.join(mhandle.basepath, 'ui', 'inventorybrowser.ui'))
        self.setWidget(self.widget)
        self.invTabUiPath = os.path.join(mhandle.basepath, 'ui', 'invTabTable.ui')
        self.pipInventory = None
        self.tabs = []
        self.models = []
        
    def init(self, app, datamanager):
        super().init(app, datamanager)
        self.app = app
        for cat in [ ('All', CatAllModel, SortProxyModel),
                     ('Weapons', CatWeaponsModel, SortProxyModel),
                     ('Apparel', CatApparelModel, SortProxyModel),
                     ('Aid', CatAidModel, SortProxyModel),
                     ('Misc', CatMiscModel, SortProxyModel),
                     ('Junk', CatJunkModel, SortProxyModel),
                     ('Mods', CatModsModel, SortProxyModel),
                     ('Ammo', CatAmmoModel, SortProxyModel),
                     ('Books', CatBooksModel, SortProxyModel),
                     ('Holotapes', CatHolotapeModel, SortProxyModel),
                     ('Keys', CatKeysModel, SortProxyModel) ]:
            tab = self._addTab(cat[0], cat[1], cat[2])
            self.tabs.append(tab)
            self.models.append(tab.tableView.model().sourceModel())
        settings.setSplitterState(self.widget.splitter1, self.app.settings.value('inventorybrowser/splitter1State', None))
        self.widget.splitter1.splitterMoved.connect(self._slotSplitter1Moved)
        settings.setSplitterState(self.widget.splitter2, self.app.settings.value('inventorybrowser/splitter2State', None))
        self.widget.splitter2.splitterMoved.connect(self._slotSplitter2Moved)
        self.propertyTreeHeader = self.widget.propertyTree.header()
        settings.setHeaderSectionSizes(self.propertyTreeHeader, self.app.settings.value('inventorybrowser/PropertyHeaderSectionSizes', []))
        self.propertyTreeHeader.sectionResized.connect(self._slotPropertyTreeSectionResized)
        self.dataManager = datamanager
        self.dataManager.registerRootObjectListener(self._onPipRootObjectEvent)
        
    def _addTab(self, title, modelClass, proxyClass):
        skeySizes = 'inventorybrowser/' + title + '/headerSectionSizes'
        skeyMoved = 'inventorybrowser/' + title + '/headerSectionVisualIndices'
        tab = uic.loadUi(self.invTabUiPath)
        self.widget.tabWidget.addTab(tab, title)
        model = modelClass()
        proxyModel = proxyClass(self.app.settings, 'inventorybrowser/' + title)
        proxyModel.setSourceModel(model)
        tab.tableView.setModel(proxyModel)
        tableHeader = tab.tableView.horizontalHeader()
        tableHeader.setSectionsMovable(True)
        settings.setHeaderSectionSizes(tableHeader, self.app.settings.value(skeySizes, []))
        settings.setHeaderSectionVisualIndices(tableHeader, self.app.settings.value(skeyMoved, []))
        if proxyModel.sortReversed:
            tab.tableView.sortByColumn(proxyModel.sortColumn, QtCore.Qt.DescendingOrder)
        else:
            tab.tableView.sortByColumn(proxyModel.sortColumn, QtCore.Qt.AscendingOrder)
        @QtCore.pyqtSlot(int, int, int)
        def _slotSectionResized(logicalIndex, oldSize, newSize):
            self.app.settings.setValue(skeySizes, settings.getHeaderSectionSizes(tableHeader))
        tableHeader.sectionResized.connect(_slotSectionResized)
        @QtCore.pyqtSlot(int, int, int)
        def _slotSectionMoved(logicalIndex, oldVisualIndex, newVisualIndex):
            self.app.settings.setValue(skeyMoved, settings.getHeaderSectionVisualIndices(tableHeader))
        tableHeader.sectionMoved.connect(_slotSectionMoved)
        @QtCore.pyqtSlot(QtCore.QModelIndex, QtCore.QModelIndex)
        def _slotItemSelected(index, previous):
            rindex = proxyModel.mapToSource(index)
            item = model.getPipValue(rindex.row())
            if item:
                self.showItemProperties(item)
        tab.tableView.selectionModel().currentChanged.connect(_slotItemSelected)
        @QtCore.pyqtSlot(QtCore.QPoint)
        def _slotItemContextMenu(pos):
            index = tab.tableView.selectionModel().currentIndex()
            if index.isValid():
                value = model.getPipValue(proxyModel.mapToSource(index).row())
                if value:
                    model.showItemContextMenu(self.dataManager, value, pos, tab.tableView)
        tab.tableView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        tab.tableView.customContextMenuRequested.connect(_slotItemContextMenu)
        @QtCore.pyqtSlot(QtCore.QModelIndex)
        def _slotItemDoubleClicked(index):
            index = tab.tableView.selectionModel().currentIndex()
            if index.isValid():
                value = model.getPipValue(proxyModel.mapToSource(index).row())
                if value:
                    model.itemDoubleClicked(self.dataManager, value, tab.tableView)
        tab.tableView.doubleClicked.connect(_slotItemDoubleClicked)
        return tab
            
       
    @QtCore.pyqtSlot(int, int)
    def _slotSplitter1Moved(self, pos, index):
        self.app.settings.setValue('inventorybrowser/splitter1State', settings.getSplitterState(self.widget.splitter1))
       
    @QtCore.pyqtSlot(int, int)
    def _slotSplitter2Moved(self, pos, index):
        self.app.settings.setValue('inventorybrowser/splitter2State', settings.getSplitterState(self.widget.splitter2))
        
    @QtCore.pyqtSlot(int, int, int)
    def _slotPropertyTreeSectionResized(self, logicalIndex, oldSize, newSize):
        self.app.settings.setValue('inventorybrowser/PropertyHeaderSectionSizes', settings.getHeaderSectionSizes(self.propertyTreeHeader))
        
    def _onPipRootObjectEvent(self, rootObject):
        self.pipInventory = rootObject.child('Inventory')
        if self.pipInventory:
            self.pipInventory.registerValueUpdatedListener(self._onPipInventoryReset)
            self._onPipInventoryReset(None, None, None)
                
    def _onPipInventoryReset(self, caller, value, pathObjs):
        for m in self.models:
            m.setPipInventory(self.pipInventory)
        
            
    def showItemProperties(self, item):
        if item:
            props = item.value()
            self.widget.propertyTree.clear()
            keys = list(props.keys())
            keys.sort()
            def _createTreeItem(prop, title, parent = self.widget.propertyTree):
                if prop.pipType == ePipboyValueType.ARRAY:
                    ti = QtWidgets.QTreeWidgetItem(parent)
                    ti.setText(0, title)
                    for i in range(0, prop.childCount()):
                        _createTreeItem(prop.value()[i], str(i), ti)
                elif prop.pipType == ePipboyValueType.OBJECT:
                    ti = QtWidgets.QTreeWidgetItem(parent)
                    ti.setText(0, title)
                    for i in prop.value():
                        _createTreeItem(prop.value()[i], str(i), ti)
                else:
                    if k in ['formID']:
                        value = hex(prop.value())
                    else:
                        value = str(prop.value())
                    ti = QtWidgets.QTreeWidgetItem(parent)
                    ti.setText(0, title)
                    ti.setText(1, value)
            for k in keys:
                prop = props[k]
                ti = _createTreeItem(prop, k)
                self.widget.propertyTree.addTopLevelItem(ti)
            
