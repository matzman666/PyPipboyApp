# -*- coding: utf-8 -*-


import queue
import os
from PyQt5 import QtWidgets, uic, QtCore
from pypipboy.types import eValueType
from pypipboy.datamanager import eValueUpdatedEventType
from widgets import widgets
from widgets.shared import settings



class DataBrowserTreeModel(QtCore.QAbstractItemModel):
    _signalValueUpdated = QtCore.pyqtSignal()
    
    def __init__(self, treeView, datamanager, parent=None):
        super().__init__(parent)
        self.rootObject = None
        self.treeView = treeView
        self.treeView.setModel(self)
        self.datamanager = datamanager
        self.datamanager.registerRootObjectListener(self._onRootObjectEvent)
        self.datamanager.registerValueUpdatedListener(self._onValueUpdatedEvent)
        self._valueUpdates = queue.Queue()
        self._signalValueUpdated.connect(self._slotValueUpdated)
        
    def _onRootObjectEvent(self, rootObject):
        self.rootObject = rootObject
        self.modelReset.emit()
        
    def _onValueUpdatedEvent(self, value, eventtype):
        if eventtype == eValueUpdatedEventType.UPDATED:
            self._valueUpdates.put(value)
            self._signalValueUpdated.emit()
        
    @QtCore.pyqtSlot()        
    def _slotValueUpdated(self):
        try:
            value = self._valueUpdates.get_nowait()
            # Now we are in the correct thread to emit the dataChanged signal
            self.dataChanged.emit(self.createIndex(value.pipParentIndex, 0, value), self.createIndex(value.pipParentIndex, 4, value), [QtCore.Qt.EditRole])
            if value.valueType == eValueType.ARRAY or value.valueType == eValueType.OBJECT:
                self.layoutAboutToBeChanged.emit()
                self.layoutChanged.emit()
            self._valueUpdates.task_done()
        except:
            pass
            
        
    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            if section == 0:
                return "Record"
            elif section == 1:
                return "Value"
            elif section == 2:
                return "Type"
            elif section == 3:
                return "Children"
            elif section == 4:
                return "pipID"
        return None
        
        
    def index(self, row, column, parent):
        if not self.rootObject or not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()
        if not parent.isValid():
            parentItem = self.rootObject
        else:
            parentItem = parent.internalPointer()
        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

            
    def parent(self, index):
        if not self.rootObject or not index.isValid():
            return QtCore.QModelIndex()
        parent = index.internalPointer().pipParent
        if parent:
            return self.createIndex(parent.pipParentIndex, 0, parent)
        else:
            return QtCore.QModelIndex()
            


    def rowCount(self, parent):
        if not self.rootObject or parent.column() > 0:
            return 0
        if not parent.isValid():
            parentItem = self.rootObject
        else:
            parentItem = parent.internalPointer()
        return parentItem.childCount()


    def columnCount(self, parent):
        return 5


    def data(self, index, role):
        if not self.rootObject or not index.isValid():
            return None
        if role != QtCore.Qt.DisplayRole:
            return None
        item = index.internalPointer()
        if index.column() == 0:
            return str(item.pipParentKey)
        elif index.column() == 1:
            if item.valueType == eValueType.OBJECT:
                text = ""
            elif item.valueType == eValueType.ARRAY:
                text = ""
            else: 
                text = str(item.value())
            return text
        elif index.column() == 2:
            if item.valueType == eValueType.OBJECT:
                return "Object"
            elif item.valueType == eValueType.ARRAY:
                return "Array"
            elif item.valueType == eValueType.BOOL:
                return "Bool"
            elif item.valueType == eValueType.INT_8:
                return "Int8"
            elif item.valueType == eValueType.UINT_8:
                return "UInt8"
            elif item.valueType == eValueType.INT_32:
                return "Int32"
            elif item.valueType == eValueType.UINT_32:
                return "UInt32"
            elif item.valueType == eValueType.FLOAT:
                return "Float"
            elif item.valueType == eValueType.STRING:
                return "String"
            else:
                return "Unknown("+str(item.valueType)+")" 
        elif index.column() == 3:
            return item.childCount() 
        elif index.column() == 4:
            return item.pipId



class DataBrowserWidget(widgets.WidgetBase):
    def __init__(self, mhandle, parent):
        super().__init__('Data Browser', parent)
        self.widget = uic.loadUi(os.path.join(mhandle.basepath, 'ui', 'databrowser.ui'))
        self.setWidget(self.widget)
        
    def init(self, app, datamanager):
        super().init(app, datamanager)
        self.dataManager = datamanager
        self.app = app
        self.treeModel = DataBrowserTreeModel(self.widget.treeView, self.dataManager)
        self.widget.treeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.widget.treeView.customContextMenuRequested.connect(self._slotShowTreeCustomContextMenu)
        self.treeHeader = self.widget.treeView.header()
        self.treeHeader.setSectionsMovable(True)
        self.treeHeader.setStretchLastSection(True)
        settings.setHeaderSectionSizes(self.treeHeader, self.app.settings.value('databrowserwidget/HeaderSectionSizes', []))
        settings.setHeaderSectionVisualIndices(self.treeHeader, self.app.settings.value('databrowserwidget/headerSectionVisualIndices', []))
        self.treeHeader.sectionResized.connect(self._slotTreeSectionResized)
        self.treeHeader.sectionMoved.connect(self._slotTreeSectionMoved)

        
    @QtCore.pyqtSlot(QtCore.QPoint)
    def _slotShowTreeCustomContextMenu(self, point):
        selection = self.widget.treeView.selectedIndexes()
        if len(selection) > 0:
            self.selectedTreeItem = selection[0].internalPointer()
            contextMenu = QtWidgets.QMenu(self.widget.treeView)
            rpcMenu = contextMenu.addMenu('RPC')
            toggleRadioAction = rpcMenu.addAction('Toggle Radio')
            toggleRadioAction.triggered.connect(self._slotRpcToggleRadio)
            useItemAction = rpcMenu.addAction('Use Item')
            useItemAction.triggered.connect(self._slotRpcUseItem)
            dropItemAction = rpcMenu.addAction('Drop Item')
            dropItemAction.triggered.connect(self._slotRpcDropItem)
            fastTravelAction = rpcMenu.addAction('Fast Travel')
            fastTravelAction.triggered.connect(self._slotRpcFastTravel)
            toggleQuestAction = rpcMenu.addAction('Toggle Quest Active')
            toggleQuestAction.triggered.connect(self._slotRpcToggleQuest)
            toggleComponentAction = rpcMenu.addAction('Toggle Component Favorite')
            toggleComponentAction.triggered.connect(self._slotRpcToggleComponentFavorite)
            setFavoriteAction = rpcMenu.addAction('Set Favorite')
            setFavoriteAction.triggered.connect(self._slotRpcSetFavorite)
            reqLocalMapAction = rpcMenu.addAction('send Local Map Request')
            reqLocalMapAction.triggered.connect(self._slotRpcReqLocalMap)
            clearIdleAction = rpcMenu.addAction('Send Clear Idle Request')
            clearIdleAction.triggered.connect(self._slotRpcReqClearIdle)
            useStimpakAction = rpcMenu.addAction('Use Stimpak')
            useStimpakAction.triggered.connect(self._slotRpcUseStimpak)
            useRadawayAction = rpcMenu.addAction('Use RadAway')
            useRadawayAction.triggered.connect(self._slotRpcUseRadAway)
            contextMenu.exec(self.widget.treeView.mapToGlobal(point))
        else:
            self.selectedTreeItem = None
        
    @QtCore.pyqtSlot(int, int, int)
    def _slotTreeSectionResized(self, logicalIndex, oldSize, newSize):
        self.app.settings.setValue('databrowserwidget/HeaderSectionSizes', settings.getHeaderSectionSizes(self.treeHeader))
        
    @QtCore.pyqtSlot(int, int, int)
    def _slotTreeSectionMoved(self, logicalIndex, oldVisualIndex, newVisualIndex):
        self.app.settings.setValue('databrowserwidget/headerSectionVisualIndices', settings.getHeaderSectionVisualIndices(self.treeHeader))
        
        
    @QtCore.pyqtSlot()
    def _slotRpcToggleRadio(self):
        self.dataManager.rpcToggleRadioStation(self.selectedTreeItem)
    
    @QtCore.pyqtSlot()
    def _slotRpcUseItem(self):
        self.dataManager.rpcUseItem(self.selectedTreeItem)
    
    @QtCore.pyqtSlot()
    def _slotRpcDropItem(self):
        self.dataManager.rpcDropItem(self.selectedTreeItem, 1)
    
    @QtCore.pyqtSlot()
    def _slotRpcFastTravel(self):
        #def _callback(resp):
        #    print('FastTravel response: ', resp)
        #self.dataManager.rpcFastTravel(self.selectedTreeItem, _callback)
        self.dataManager.rpcFastTravel(self.selectedTreeItem)
    
    @QtCore.pyqtSlot()
    def _slotRpcToggleQuest(self):
        self.dataManager.rpcToggleQuestActive(self.selectedTreeItem)
        
    @QtCore.pyqtSlot()
    def _slotRpcToggleComponentFavorite(self):
        self.dataManager.rpcToggleComponentFavorite(self.selectedTreeItem)
        
    @QtCore.pyqtSlot()
    def _slotRpcSetFavorite(self):
        self.dataManager.rpcSetFavorite(self.selectedTreeItem, 1)
        
    @QtCore.pyqtSlot()
    def _slotRpcReqLocalMap(self):
        self.dataManager.rpcRequestLocalMapSnapshot()
        
    @QtCore.pyqtSlot()
    def _slotRpcReqClearIdle(self):
        self.dataManager.rpcSendClearIdleRequest()
        
    @QtCore.pyqtSlot()
    def _slotRpcUseStimpak(self):
        self.dataManager.rpcUseStimpak()
        
    @QtCore.pyqtSlot()
    def _slotRpcUseRadAway(self):
        self.dataManager.rpcUseRadAway()
