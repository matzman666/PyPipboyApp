# -*- coding: utf-8 -*-


import os
import re
from PyQt5 import QtWidgets, QtCore, QtGui, uic
from widgets import widgets
from widgets.shared import settings


class LocationTableModel(QtCore.QAbstractTableModel):
    _signalLocationsUpdate = QtCore.pyqtSignal()
    
    def __init__(self, settings, qparent = None):
        super().__init__(qparent)
        self.settings = settings
        self.pipWorldLocations = None
        self._signalLocationsUpdate.connect(self._slotLocationsUpdate)
    
    def setPipLocations(self, pipValue):
        self.modelAboutToBeReset.emit()
        self.pipWorldLocations = pipValue
        self.modelReset.emit()
        self.pipWorldLocations.registerValueUpdatedListener(self._onPipLocationsUpdate, 99)
    
    def _onPipLocationsUpdate(self, caller, value, pathObjs):
        self._signalLocationsUpdate.emit()
    
    @QtCore.pyqtSlot()
    def _slotLocationsUpdate(self):
        self.layoutAboutToBeChanged.emit()
        self.layoutChanged.emit()
        
    def rowCount(self, parent = QtCore.QModelIndex()):
        if self.pipWorldLocations:
            return self.pipWorldLocations.childCount()
        else:
            return 0
        
    def columnCount(self, parent = QtCore.QModelIndex()):
        return 8
    
    def headerData(self, section, orientation, role = QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal:
            if role == QtCore.Qt.DisplayRole:
                if section == 0:
                    return 'Name'
                elif section == 1:
                    return 'Type'
                elif section == 2:
                    return 'Discovered'
                elif section == 3:
                    return 'Cleared'
                elif section == 4:
                    return 'Owned'
                elif section == 5:
                    return 'Population'
                elif section == 6:
                    return 'Happiness'
                elif section == 7:
                    return 'Visible'
        return None
    
    def data(self, index, role = QtCore.Qt.DisplayRole):
        return self._data(self.pipWorldLocations.child(index.row()), index.column(), role)
        
    def _data(self, location, column, role = QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if column == 0:
                return location.child('Name').value()
            elif column == 1:
                return location.child('type').value()
            elif column == 2:
                discovered = location.child('Discovered')
                if discovered:
                    if discovered.value():
                        return 'yes'
                    else:
                        return 'no'
                else:
                    return '-'
            elif column == 3:
                cleared = location.child('ClearedStatus')
                if cleared:
                    if cleared.value():
                        return 'yes'
                    else:
                        return 'no'
                else:
                    return '-'
            elif column == 4:
                owned = location.child('WorkshopOwned')
                if owned:
                    if owned.value():
                        return 'yes'
                    else:
                        return 'no'
                else:
                    return '-'
            elif column == 5:
                pop = location.child('WorkshopPopulation')
                if pop:
                    return pop.value()
                else:
                    return '-'
            elif column == 6:
                hap = location.child('WorkshopHappinessPct')
                if hap:
                    return hap.value()
                else:
                    return '-'
            elif column == 7:
                    if location.child('Visible').value():
                        return 'yes'
                    else:
                        return 'no'
        elif role == QtCore.Qt.TextAlignmentRole:
            if column == 0:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft
            else:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight
        return None
        
    def getPipValue(self, row):
        if self.pipWorldLocations and self.pipWorldLocations.childCount() > row:
            return self.pipWorldLocations.child(row)
        else:
            return None
    

class SortProxyModel(QtCore.QSortFilterProxyModel):
    def __init__(self, settings, qparent = None):
        super().__init__(qparent)
        self.settings = settings
        self.sortColumn = int(self.settings.value('locationbrowserwidget/sortColumn', 0))
        # Buggy QSettings Linux implementation forces us to convert to int and then to bool
        self.sortReversed = bool(int(self.settings.value('locationbrowserwidget/sortReversed', 0)))
        self.showUnknown = bool(int(self.settings.value('locationbrowserwidget/showUnknown', 0)))
        self.nameFilterString = ''
        
    def sort(self, column, order = QtCore.Qt.AscendingOrder):
        self.sortColumn = column
        if order == QtCore.Qt.DescendingOrder:
            self.sortReversed = True
        else:
            self.sortReversed = False
        self.settings.setValue('locationbrowserwidget/sortColumn', column)
        self.settings.setValue('locationbrowserwidget/sortReversed', int(self.sortReversed))
        super().sort(column, order)
        
    def filterAcceptsRow(self, source_row, source_parent):
        loc = self.sourceModel().getPipValue(source_row)
        if loc:
            if self.nameFilterString and not re.search(self.nameFilterString, loc.child('Name').value(), re.I):
                return False
            if self.showUnknown or loc.child('Visible').value():
                return True
        return False
    
    def headerData(self, section, orientation, role = QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Vertical:
            if role == QtCore.Qt.DisplayRole:
                return section + 1
        else:
            return super().headerData(section, orientation, role)
        
    @QtCore.pyqtSlot(bool)        
    def showUnknownLocations(self, value):
        self.showUnknown = value
        self.settings.setValue('locationbrowserwidget/showUnknown', int(value))
        self.invalidateFilter()
    
    @QtCore.pyqtSlot(str)
    def setNameFilterString(self, value):
        self.nameFilterString = value
        self.invalidateFilter()


class LocationBrowserWidget(widgets.WidgetBase):
    
    def __init__(self, mhandle, parent):
        super().__init__('Location Browser', parent)
        self.widget = uic.loadUi(os.path.join(mhandle.basepath, 'ui', 'locationbrowser.ui'))
        self.setWidget(self.widget)
        
    def init(self, app, datamanager):
        super().init(app, datamanager)
        self.app = app
        self.globalMap = app.iwcGetEndpoint('globalmapwidget')
        self.pipMapObject = None
        self.pipMapWorldObject = None
        self.pipWorldLocations = None
        self.locationViewModel = LocationTableModel(self.app.settings)
        self.sortProxyModel = SortProxyModel(self.app.settings)
        self.sortProxyModel.setSourceModel(self.locationViewModel)
        self.widget.locationView.setModel(self.sortProxyModel)
        self.widget.locationView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.widget.locationView.customContextMenuRequested.connect(self._slotLocationTableContextMenu)
        self.widget.locationView.selectionModel().currentChanged.connect(self._slotLocationItemSelected)
        self.widget.locationView.doubleClicked.connect(self._slotLocationItemDoubleClicked)
        self.locationTableHeader = self.widget.locationView.horizontalHeader()
        self.locationTableHeader.setSectionsMovable(True)
        self.locationTableHeader.setStretchLastSection(True)
        self.propertyTableHeader = self.widget.propertyTable.horizontalHeader()
        settings.setHeaderSectionSizes(self.locationTableHeader, self.app.settings.value('locationbrowserwidget/LocationHeaderSectionSizes', []))
        settings.setHeaderSectionVisualIndices(self.locationTableHeader, self.app.settings.value('locationbrowserwidget/LocationHeaderSectionVisualIndices', []))
        if self.sortProxyModel.sortReversed:
            self.widget.locationView.sortByColumn(self.sortProxyModel.sortColumn, QtCore.Qt.DescendingOrder)
        else:
            self.widget.locationView.sortByColumn(self.sortProxyModel.sortColumn, QtCore.Qt.AscendingOrder)
        self.locationTableHeader.sectionResized.connect(self._slotLocationTableSectionResized)
        self.locationTableHeader.sectionMoved.connect(self._slotLocationTableSectionMoved)
        self.propertyTableHeader = self.widget.propertyTable.horizontalHeader()
        settings.setHeaderSectionSizes(self.propertyTableHeader, self.app.settings.value('locationbrowserwidget/PropertyHeaderSectionSizes', []))
        self.propertyTableHeader.sectionResized.connect(self._slotPropertyTableSectionResized)
        settings.setSplitterState(self.widget.splitter1, self.app.settings.value('locationbrowserwidget/splitter1State', None))
        self.widget.splitter1.splitterMoved.connect(self._slotSplitter1Moved)
        settings.setSplitterState(self.widget.splitter2, self.app.settings.value('locationbrowserwidget/splitter2State', None))
        self.widget.splitter2.splitterMoved.connect(self._slotSplitter2Moved)
        self.widget.showUnknownCheckBox.setChecked(self.sortProxyModel.showUnknown)
        self.widget.showUnknownCheckBox.stateChanged.connect(self.sortProxyModel.showUnknownLocations)
        self.widget.filterNameLineEdit.textEdited.connect(self.sortProxyModel.setNameFilterString)
        self.dataManager = datamanager
        self.dataManager.registerRootObjectListener(self._onPipRootObjectEvent)
        
    def getMenuCategory(self):
        return 'Map && Locations'
        
    @QtCore.pyqtSlot(QtCore.QPoint)
    def _slotLocationTableContextMenu(self, pos):
        index = self.widget.locationView.selectionModel().currentIndex()
        if index.isValid():
            value = self.locationViewModel.getPipValue(self.sortProxyModel.mapToSource(index).row())
            if value:
                menu = QtWidgets.QMenu(self.widget.locationView)
                def _showOnMap():
                    if not self.globalMap.isVisible():
                        self.globalMap.setVisible(True)
                    self.globalMap.raise_()
                    self.globalMap.iwcCenterOnLocation(value.pipId)
                action = menu.addAction('Show On Map')
                action.triggered.connect(_showOnMap)
                menu.exec(self.widget.locationView.mapToGlobal(pos))
    
    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def _slotLocationItemDoubleClicked(self, index):
        index = self.widget.locationView.selectionModel().currentIndex()
        if index.isValid():
            value = self.locationViewModel.getPipValue(self.sortProxyModel.mapToSource(index).row())
            if value:
                if not self.globalMap.isVisible():
                    self.globalMap.setVisible(True)
                self.globalMap.raise_()
                self.globalMap.iwcCenterOnLocation(value.pipId)
                
    @QtCore.pyqtSlot(QtCore.QModelIndex, QtCore.QModelIndex)
    def _slotLocationItemSelected(self, index, previous):
        rindex = self.sortProxyModel.mapToSource(index)
        loc = self.locationViewModel.getPipValue(rindex.row())
        if loc:
            self.showLocationProperties(loc)
            
    def showLocationProperties(self, location):
        if location:
            props = location.value()
            self.widget.propertyTable.setRowCount(len(props))
            keys = list(props.keys())
            keys.sort()
            r = 0
            for k in keys:
                prop = props[k]
                nameItem = QtWidgets.QTableWidgetItem(prop.pipParentKey)
                if k in ['locationformid', 'locationmarkerformid']:
                    value = hex(prop.value())
                else:
                    value = str(prop.value())
                valueItem = QtWidgets.QTableWidgetItem(value)
                self.widget.propertyTable.setItem(r, 0, nameItem)
                self.widget.propertyTable.setItem(r, 1, valueItem)
                r += 1
                
            
            
    @QtCore.pyqtSlot(int, int, int)
    def _slotLocationTableSectionResized(self, logicalIndex, oldSize, newSize):
        self.app.settings.setValue('locationbrowserwidget/LocationHeaderSectionSizes', settings.getHeaderSectionSizes(self.locationTableHeader))
        
    @QtCore.pyqtSlot(int, int, int)
    def _slotPropertyTableSectionResized(self, logicalIndex, oldSize, newSize):
        self.app.settings.setValue('locationbrowserwidget/PropertyHeaderSectionSizes', settings.getHeaderSectionSizes(self.propertyTableHeader))
        
    @QtCore.pyqtSlot(int, int, int)
    def _slotLocationTableSectionMoved(self, logicalIndex, oldVisualIndex, newVisualIndex):
        self.app.settings.setValue('locationbrowserwidget/LocationHeaderSectionVisualIndices', settings.getHeaderSectionVisualIndices(self.locationTableHeader))
       
    @QtCore.pyqtSlot(int, int)
    def _slotSplitter1Moved(self, pos, index):
        self.app.settings.setValue('locationbrowserwidget/splitter1State', settings.getSplitterState(self.widget.splitter1))
       
    @QtCore.pyqtSlot(int, int)
    def _slotSplitter2Moved(self, pos, index):
        self.app.settings.setValue('locationbrowserwidget/splitter2State', settings.getSplitterState(self.widget.splitter2))
        
        
    def _onPipRootObjectEvent(self, rootObject):
        self.pipMapObject = rootObject.child('Map')
        if self.pipMapObject:
            self.pipMapObject.registerValueUpdatedListener(self._onPipMapReset)
            self._onPipMapReset(None, None, None)
                
    def _onPipMapReset(self, caller, value, pathObjs):
        self.pipMapWorldObject = self.pipMapObject.child('World')
        if self.pipMapWorldObject:
            self.pipWorldLocations = self.pipMapWorldObject.child('Locations')
            if self.pipWorldLocations:
                self.locationViewModel.setPipLocations(self.pipWorldLocations)
        
