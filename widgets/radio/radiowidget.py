# -*- coding: utf-8 -*-


import os
from PyQt5 import QtWidgets, QtCore, QtGui, uic
from widgets import widgets
from widgets.shared import settings


class RadioTableModel(QtCore.QAbstractTableModel):
    _signalRadioUpdate = QtCore.pyqtSignal()
    
    def __init__(self, settings, qparent = None):
        super().__init__(qparent)
        self.settings = settings
        self.pipRadio = None
        self.sortColumn = int(self.settings.value('radiowidget/sortColumn', 0))
        self.sortReversed = bool(int(self.settings.value('radiowidget/sortReversed', 0)))
        self.itemList = []
        self._signalRadioUpdate.connect(self._slotRadioUpdate)
    
    def setPipRadio(self, pipValue):
        self.modelAboutToBeReset.emit()
        self.pipRadio = pipValue
        self.itemList = self.pipRadio.value()
        self._sortItemList()
        self.modelReset.emit()
        self.pipRadio.registerValueUpdatedListener(self._onPipRadioUpdate, 2)
    
    def _onPipRadioUpdate(self, caller, value, pathObjs):
        self._signalRadioUpdate.emit()
    
    @QtCore.pyqtSlot()
    def _slotRadioUpdate(self):
        self.layoutAboutToBeChanged.emit()
        self.itemList = self.pipRadio.value()
        self._sortItemList()
        self.layoutChanged.emit()
        
        
    def _sortItemList(self):
        def _sortKey(pipValue):
            if self.sortColumn == 0:
                return pipValue.child('text').value()
            elif self.sortColumn == 1:
                return pipValue.child('frequency').value()
            elif self.sortColumn == 2:
                return pipValue.child('inRange').value()
        self.itemList.sort(key=_sortKey, reverse=self.sortReversed)
        
        
    def rowCount(self, parent = QtCore.QModelIndex()):
        if self.pipRadio:
            return self.pipRadio.childCount()
        else:
            return 0
        
    def columnCount(self, parent = QtCore.QModelIndex()):
        return 3
    
    def headerData(self, section, orientation, role = QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal:
            if role == QtCore.Qt.DisplayRole:
                if section == 0:
                    return 'Name'
                elif section == 1:
                    return 'Frequency'
                elif section == 2:
                    return 'In Range'
        return None
    
    def data(self, index, role = QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            radio = self.itemList[index.row()]
            if index.column() == 0:
                return radio.child('text').value()
            elif index.column() == 1:
                return radio.child('frequency').value()
            elif index.column() == 2:
                return radio.child('inRange').value()
        elif role == QtCore.Qt.FontRole:
            radio = self.itemList[index.row()]
            if radio.child('active').value():
                font = QtGui.QFont()
                font.setBold(True)
                return font
        elif role == QtCore.Qt.ForegroundRole:
            radio = self.itemList[index.row()]
            if not radio.child('inRange').value():
                return QtGui.QColor.fromRgb(150,150,150)
        return None
    
    def sort(self, column, order = QtCore.Qt.AscendingOrder):
        self.layoutAboutToBeChanged.emit()
        self.sortColumn = column
        if order == QtCore.Qt.DescendingOrder:
            self.sortReversed = True
        else:
            self.sortReversed = False
        self.settings.setValue('radiowidget/sortColumn', column)
        self.settings.setValue('radiowidget/sortReversed', int(self.sortReversed))
        self._sortItemList()
        self.layoutChanged.emit()
        
    def getPipValue(self, row):
        if self.itemList and len(self.itemList) > row:
            return self.itemList[row]
        else:
            return None
    
        


class RadioWidget(widgets.WidgetBase):
    
    def __init__(self, mhandle, parent):
        super().__init__('Radio', parent)
        self.widget = uic.loadUi(os.path.join(mhandle.basepath, 'ui', 'radiowidget.ui'))
        self.setWidget(self.widget)
        
    def init(self, app, datamanager):
        super().init(app, datamanager)
        self.app = app
        self.radioViewModel = RadioTableModel(self.app.settings)
        self.widget.radioView.setModel(self.radioViewModel)
        self.widget.radioView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.widget.radioView.customContextMenuRequested.connect(self._slotTableContextMenu)
        self.widget.radioView.doubleClicked.connect(self._slotTableDoubleClicked)
        self.tableHeader = self.widget.radioView.horizontalHeader()
        self.tableHeader.setSectionsMovable(True)
        self.tableHeader.setStretchLastSection(True)
        settings.setHeaderSectionSizes(self.tableHeader, self.app.settings.value('radiowidget/HeaderSectionSizes', []))
        settings.setHeaderSectionVisualIndices(self.tableHeader, self.app.settings.value('radiowidget/headerSectionVisualIndices', []))
        if self.radioViewModel.sortReversed:
            self.widget.radioView.sortByColumn(self.radioViewModel.sortColumn, QtCore.Qt.DescendingOrder)
        else:
            self.widget.radioView.sortByColumn(self.radioViewModel.sortColumn, QtCore.Qt.AscendingOrder)
        self.tableHeader.sectionResized.connect(self._slotTableSectionResized)
        self.tableHeader.sectionMoved.connect(self._slotTableSectionMoved)
        self.dataManager = datamanager
        self.dataManager.registerRootObjectListener(self._onPipRootObjectEvent)
        
    @QtCore.pyqtSlot(QtCore.QPoint)
    def _slotTableContextMenu(self, pos):
        index = self.widget.radioView.selectionModel().currentIndex()
        if index.isValid():
            value = self.radioViewModel.getPipValue(index.row())
            if value:
                menu = QtWidgets.QMenu(self.widget.radioView)
                def _toggleRadio():
                    self.dataManager.rpcToggleRadioStation(value)
                taction = menu.addAction('Toggle Radio')
                taction.triggered.connect(_toggleRadio)
                menu.exec(self.widget.radioView.mapToGlobal(pos))
    
    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def _slotTableDoubleClicked(self, index):
        value = self.radioViewModel.getPipValue(index.row())
        if value:
            self.dataManager.rpcToggleRadioStation(value)
            
    @QtCore.pyqtSlot(int, int, int)
    def _slotTableSectionResized(self, logicalIndex, oldSize, newSize):
        self.app.settings.setValue('radiowidget/HeaderSectionSizes', settings.getHeaderSectionSizes(self.tableHeader))
        
    @QtCore.pyqtSlot(int, int, int)
    def _slotTableSectionMoved(self, logicalIndex, oldVisualIndex, newVisualIndex):
        self.app.settings.setValue('radiowidget/headerSectionVisualIndices', settings.getHeaderSectionVisualIndices(self.tableHeader))
        
        
    def _onPipRootObjectEvent(self, rootObject):
        self.pipRadio = rootObject.child('Radio')
        if self.pipRadio:
            self.radioViewModel.setPipRadio(self.pipRadio)
        
