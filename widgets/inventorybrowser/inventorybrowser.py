# -*- coding: utf-8 -*-


import os
from PyQt5 import QtWidgets, QtCore, uic
from widgets import widgets
from widgets.shared import settings
from pypipboy.datamanager import ePipboyValueType
from .inventorymodel import *
from .sortproxymodel import *



class InventoryBrowserWidget(widgets.WidgetBase):    
    def __init__(self, mhandle, parent):
        super().__init__('Inventory Browser', parent)
        self.widget = uic.loadUi(os.path.join(mhandle.basepath, 'ui', 'inventorybrowser.ui'))
        self.setWidget(self.widget)
        self.invTabUiPath = os.path.join(mhandle.basepath, 'ui', 'invTabTable.ui')
        self.pipInventory = None
        self.tabs = []
        self.models = []
        self.currentTabIndex = -1
        
    def init(self, app, datamanager):
        super().init(app, datamanager)
        self.app = app
        for cat in [ ('All', CatAllModel, SortProxyModel),
                     ('Weapons', CatWeaponsModel, WeaponSortProxyModel),
                     ('Apparel', CatApparelModel, ApparelSortProxyModel),
                     ('Aid', CatAidModel, SortProxyModel),
                     ('Misc', CatMiscModel, SortProxyModel),
                     ('Junk', CatJunkModel, SortProxyModel),
                     ('Mods', CatModsModel, SortProxyModel),
                     ('Ammo', CatAmmoModel, SortProxyModel),
                     ('Books', CatBooksModel, SortProxyModel),
                     ('Holotapes', CatHolotapeModel, SortProxyModel),
                     ('Keys', CatKeysModel, SortProxyModel),
                     ('Components', ComponentsTableModel, SortProxyModel)  ]:
            tab = self._addTab(cat[0], cat[1], cat[2])
            self.tabs.append(tab)
            self.models.append(tab.tableView.model().sourceModel())
        self.widget.tabWidget.currentChanged.connect(self._slotCatTabChanged)
        activeTab = int(self.app.settings.value('inventorybrowser/activeTab', 0))
        self.widget.tabWidget.setCurrentIndex(activeTab)
        settings.setSplitterState(self.widget.splitter1, self.app.settings.value('inventorybrowser/splitter1State', None))
        self.widget.splitter1.splitterMoved.connect(self._slotSplitter1Moved)
        settings.setSplitterState(self.widget.splitter2, self.app.settings.value('inventorybrowser/splitter2State', None))
        self.widget.splitter2.splitterMoved.connect(self._slotSplitter2Moved)
        self.propertyTreeHeader = self.widget.propertyTree.header()
        settings.setHeaderSectionSizes(self.propertyTreeHeader, self.app.settings.value('inventorybrowser/PropertyHeaderSectionSizes', []))
        self.propertyTreeHeader.sectionResized.connect(self._slotPropertyTreeSectionResized)
        self.widget.filterEdit.textChanged.connect(self._slotFilterTextChanged)
        self.dataManager = datamanager
        self.dataManager.registerRootObjectListener(self._onPipRootObjectEvent)
        
    def getMenuCategory(self):
        return 'Inventory && Gear'
        
    def _addTab(self, title, modelClass, proxyClass):
        skeySizes = 'inventorybrowser/' + title + '/headerSectionSizes'
        skeyMoved = 'inventorybrowser/' + title + '/headerSectionVisualIndices'
        tab = uic.loadUi(self.invTabUiPath)
        self.widget.tabWidget.addTab(tab, title)
        model = modelClass(tab)
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
            currentIndex = tab.tableView.selectionModel().currentIndex()
            if currentIndex.isValid():
                current = model.getPipValue(proxyModel.mapToSource(currentIndex).row())
            else:
                current = None
            selected = []
            for rowIndex in tab.tableView.selectionModel().selectedRows():
                item = model.getPipValue(proxyModel.mapToSource(rowIndex).row())
                if item:
                    selected.append(item)
            if current:
                model.showItemContextMenu(self.dataManager, current, selected, pos, tab.tableView)
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
    
    @QtCore.pyqtSlot(int)
    def _slotCatTabChanged(self, index):
        if self.currentTabIndex >= 0:
            self.tabs[self.currentTabIndex].tableView.model().setFilterString('')
            self.models[self.currentTabIndex].tabVisibilityChanged(False)
        self.models[index].tabVisibilityChanged(True)
        self.tabs[index].tableView.model().setFilterString(self.widget.filterEdit.text())
        self.currentTabIndex = index
        self.app.settings.setValue('inventorybrowser/activeTab', index)
    
    @QtCore.pyqtSlot(str)
    def _slotFilterTextChanged(self, text):
        self.tabs[self.widget.tabWidget.currentIndex()].tableView.model().setFilterString(text)
    
    def _onPipRootObjectEvent(self, rootObject):
        self.pipInventory = rootObject.child('Inventory')
        if self.pipInventory:
            self.pipInventory.registerValueUpdatedListener(self._onPipInventoryReset)
            self._onPipInventoryReset(None, None, None)
                
    def _onPipInventoryReset(self, caller, value, pathObjs):
        for m in self.models:
            m.setPipInventory(self.dataManager, self.pipInventory)
        
            
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
                    if k in ['formID', 'componentFormID']:
                        value = hex(prop.value())
                    else:
                        value = str(prop.value())
                    ti = QtWidgets.QTreeWidgetItem(parent)
                    ti.setText(0, title)
                    ti.setText(1, value)
            ti = QtWidgets.QTreeWidgetItem(self.widget.propertyTree)
            ti.setText(0, 'pipId')
            ti.setText(1, str(item.pipId))
            self.widget.propertyTree.addTopLevelItem(ti)
            for k in keys:
                prop = props[k]
                ti = _createTreeItem(prop, k)
                self.widget.propertyTree.addTopLevelItem(ti)
            
