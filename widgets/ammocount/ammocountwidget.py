import os
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from widgets import widgets
from pypipboy import inventoryutils
from widgets.shared import settings
from ..shared.graphics import ImageFactory
from ..shared.PipboyIcon import PipboyIcon
from os import path

GlobalImageLoader2 = ImageFactory(path.join("widgets", "shared", "res"))

class AmmoCountWidget(widgets.WidgetBase):
    _signalInfoUpdated = QtCore.pyqtSignal()

    def __init__(self, mhandle, parent):
        super().__init__("Ammo Count", parent)
        self.widget  = uic.loadUi(os.path.join(mhandle.basepath, "ui", "ammocountwidget.ui"))
        self.setWidget( self.widget)
        self._signalInfoUpdated.connect(self._slotInfoUpdated)
        self.AmmoListModel = QStandardItemModel()
        self.ammoWatchListModel = QStandardItemModel()
        self.widget.ammoList.setModel(self.AmmoListModel) # we need to call setModel() before selectionModel() (and never afterwards)
        self.AmmoListModel.itemChanged.connect(self.on_item_changed)
        self.ammoNameLabelDict = {}
        self.ammoNumberLabelDict = {}
        self.ammoSpacerDict = {}
        self.AmmoWatchList = []


    def init(self, app, dataManager):
        super().init(app, dataManager)
        self._app = app
        self.DataManager = dataManager
        self.DataManager.registerRootObjectListener(self._onPipRootObjectEvent)
        self.AmmoWatchList = self._app.settings.value('ammocount/savedAmmoWatchList', [])
        if not self.AmmoWatchList: # QSettings are buggy on Linux
            self.AmmoWatchList = []
        settings.setSplitterState(self.widget.splitter, self._app.settings.value('ammocount/splitterState2', None))
        self.widget.splitter.splitterMoved.connect(self._slotSplitterMoved)
        self.setAmmoWatch()

    def _onPipRootObjectEvent(self, rootObject):
        self.pipInventoryInfo = rootObject.child('Inventory')
        if self.pipInventoryInfo:
            self.pipInventoryInfo.registerValueUpdatedListener(self._onPipInventoryInfoUpdate, 1)
        self._signalInfoUpdated.emit()
        self.ammoWatchListUpdate()

    def _onPipInventoryInfoUpdate(self, caller, value, pathObjs):
        self._signalInfoUpdated.emit()

    @QtCore.pyqtSlot()
    def _slotInfoUpdated(self):
        self.getAmmoItems()
        self.ammoWatchListUpdate()
    def getAmmoItems(self):
        if (self.pipInventoryInfo):
            self.AmmoListModel.clear()
            def _filterFunc(item):
                return inventoryutils.itemHasAnyFilterCategory(item, inventoryutils.eItemFilterCategory.Ammo)

            ammo_list = inventoryutils.inventoryGetItems(self.pipInventoryInfo, _filterFunc)
            for ammo_item in ammo_list:
                item = QStandardItem(ammo_item.child('text').value())
                item.setCheckable(True)
                if ammo_item.child('text').value() in self.AmmoWatchList:
                   item.setCheckState(Qt.Checked)

                else:
                    item.setCheckState(Qt.Unchecked)
                self.AmmoListModel.appendRow(item)

    def on_item_changed(self, item):
        # If the changed item is not checked, don't bother checking others
        index = self.AmmoListModel.index(item.row(), 0)
        itemName = self.AmmoListModel.data(index)

        if item.checkState():
            self.AmmoWatchList.append(itemName)
            self.ammoWatchListUpdate()
        else:
            self.AmmoWatchList.remove(itemName)
            self.ammoWatchListUpdate()
        self._app.settings.setValue('ammocount/savedAmmoWatchList', self.AmmoWatchList)

    @QtCore.pyqtSlot(int, int)
    def _slotSplitterMoved(self, pos, index):
        self._app.settings.setValue('ammocount/splitterState2', settings.getSplitterState(self.widget.splitter))


    def setAmmoWatch(self):
        i =1
        for ammoItem in self.AmmoWatchList:
            i+=1

    @QtCore.pyqtSlot()
    def ammoWatchListUpdate(self):

        self.ammoWatchListModel.clear()
        itemList = self.AmmoWatchList
        if (self.pipInventoryInfo):

            def _filterFunc(item):
                if (inventoryutils.itemHasAnyFilterCategory(item,inventoryutils.eItemFilterCategory.Ammo)
                        and (itemList == None or item.child('text').value() in itemList)):
                    return True
                else:
                    return False
            ammoItems = inventoryutils.inventoryGetItems(self.pipInventoryInfo, _filterFunc)
            if(not ammoItems):
                return
            for i in ammoItems:
                name = i.child('text').value()
                count = str(i.child('count').value())
                item = [
                    QStandardItem(name) ,
                    QStandardItem(count)
                ]

                item[1].setData(QtCore.Qt.AlignCenter, QtCore.Qt.TextAlignmentRole)
                self.ammoWatchListModel.appendRow(item)
            self.widget.ammoTableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            self.widget.ammoTableView.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
            self.widget.ammoTableView.verticalHeader().setStretchLastSection(False)
            self.widget.ammoTableView.horizontalHeader().setStretchLastSection(True)
            self.widget.ammoTableView.setModel(self.ammoWatchListModel)

            self.widget.ammoTableView.sortByColumn(0, QtCore.Qt.AscendingOrder)





