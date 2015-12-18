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
        self.pipActiveEffects = None
        self.sortColumn = int(self.settings.value('effectswidget/sortColumn', 0))
        # Buggy QSettings Linux implementation forces us to convert to int and then to bool
        self.sortReversed = bool(int(self.settings.value('effectswidget/sortReversed', 0)))
        self.effectList = []
        self.showPermanent = bool(int(self.settings.value('effectswidget/showPermanent', False)))
        self.showEmptySources = bool(int(self.settings.value('effectswidget/showEmptySources', False)))
        self.showInactive = bool(int(self.settings.value('effectswidget/showInactive', False)))
        self._signalRadioUpdate.connect(self._slotEffectsUpdate)
        
    @QtCore.pyqtSlot(bool)
    def setShowPermanent(self, value, signal = True):
        self.showPermanent = value
        # Buggy QSettings Linux implementation forces us to save as int
        self.settings.setValue('effectswidget/showPermanent', int(value))
        if signal:
            self._signalRadioUpdate.emit()
        
    @QtCore.pyqtSlot(bool)
    def setShowEmptySources(self, value, signal = True):
        self.showEmptySources = value
        self.settings.setValue('effectswidget/showEmptySources', int(value))
        if signal:
            self._signalRadioUpdate.emit()
    
    @QtCore.pyqtSlot(bool)
    def setShowInactive(self, value, signal = True):
        self.showInactive = value
        self.settings.setValue('effectswidget/showInactive', int(value))
        if signal:
            self._signalRadioUpdate.emit()
        
    def setPipActiveEffects(self, pipValue):
        self.modelAboutToBeReset.emit()
        self.pipActiveEffects = pipValue
        self._createEffectList()
        self._sortEffectList()
        self.modelReset.emit()
        self.pipActiveEffects.registerValueUpdatedListener(self._onPipEffectsUpdate, 99)
    
    def _onPipEffectsUpdate(self, caller, value, pathObjs):
        self._signalRadioUpdate.emit()
    
    @QtCore.pyqtSlot()
    def _slotEffectsUpdate(self):
        self.layoutAboutToBeChanged.emit()
        self._createEffectList()
        self._sortEffectList()
        self.layoutChanged.emit()
    
    def _createEffectList(self):
        self.effectList = []
        if self.pipActiveEffects:
            for s in self.pipActiveEffects.value():
                for e in s.child('Effects').value():
                    if (self.showPermanent or self._data(e, 2) > 0.0) and (self.showEmptySources or self._data(e, 1)) and (self.showInactive or self._data(e, 7)):
                        self.effectList.append(e)
        
        
    def _sortEffectList(self):
        def _sortKey(pipValue):
            return self._data(pipValue, self.sortColumn)
        self.effectList.sort(key=_sortKey, reverse=self.sortReversed)
        
    def rowCount(self, parent = QtCore.QModelIndex()):
        return len(self.effectList)
        
    def columnCount(self, parent = QtCore.QModelIndex()):
        return 8
    
    def headerData(self, section, orientation, role = QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal:
            if role == QtCore.Qt.DisplayRole:
                if section == 0:
                    return 'Name'
                elif section == 1:
                    return 'Source'
                elif section == 2:
                    return 'Duration'
                elif section == 3:
                    return 'Value'
                elif section == 4:
                    return 'Type'
                elif section == 5:
                    return 'pipID'
                elif section == 6:
                    return 'showAsPercent'
                elif section == 7:
                    return 'IsActive'
        return None

    def data(self, index, role = QtCore.Qt.DisplayRole):
        effect = self.effectList[index.row()]
        return self._data(effect, index.column(), role)
        
    def _data(self, effect, column, role = QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if column == 0:
                customDesc = effect.child('CustomDesc')
                if customDesc and customDesc.value():
                    return effect.child('Name').value()
                else:
                    text = effect.child('Name').value()
                    value = effect.child('Value').value()
                    if value > 0:
                        text += ' +' + str(value)
                    elif value < 0:
                        text += ' ' + str(value)
                    return text
            elif column == 1:
                # Immediate parent is the enclosing array, therefore we need parent.parent
                return effect.pipParent.pipParent.child('Source').value()
            elif column == 2:
                duration = effect.child('duration')
                if duration:
                    return duration.value()
                return 0.0
            elif column == 3:
                value = effect.child('Value')
                if value:
                    return value.value()
                return 0.0
            elif column == 4:
                # Immediate parent is the enclosing array, therefore we need parent.parent
                return str(effect.pipParent.pipParent.child('type').value())
            elif column == 5:
                # Immediate parent is the enclosing array, therefore we need parent.parent
                return effect.pipId
            elif column == 6:
                sap = effect.child('showAsPercent')
                if sap:
                    return sap.value()
                return False
            elif column == 7:
                return effect.child('IsActive').value()
        elif role == QtCore.Qt.FontRole:
            if effect.child('IsActive').value():
                font = QtGui.QFont()
                font.setBold(True)
                return font
        #elif role == QtCore.Qt.ForegroundRole:
        #    if not effect.child('IsActive').value():
        #        return QtGui.QColor.fromRgb(150,150,150)
        return None
    
    def sort(self, column, order = QtCore.Qt.AscendingOrder):
        self.layoutAboutToBeChanged.emit()
        self.sortColumn = column
        if order == QtCore.Qt.DescendingOrder:
            self.sortReversed = True
        else:
            self.sortReversed = False
        self.settings.setValue('effectswidget/sortColumn', column)
        self.settings.setValue('effectswidget/sortReversed', int(self.sortReversed))
        self._sortEffectList()
        self.layoutChanged.emit()
        
    def getPipValue(self, row):
        if self.effectList and len(self.effectList) > row:
            return self.effectList[row]
        else:
            return None
    
        


class RadioWidget(widgets.WidgetBase):
    
    def __init__(self, mhandle, parent):
        super().__init__('Effects', parent)
        self.widget = uic.loadUi(os.path.join(mhandle.basepath, 'ui', 'effectwidget.ui'))
        self.setWidget(self.widget)
        
    def init(self, app, datamanager):
        super().init(app, datamanager)
        self.app = app
        self.effectsViewModel = RadioTableModel(self.app.settings)
        self.widget.effectsView.setModel(self.effectsViewModel)
        self.tableHeader = self.widget.effectsView.horizontalHeader()
        self.tableHeader.setSectionsMovable(True)
        self.tableHeader.setStretchLastSection(True)
        settings.setHeaderSectionSizes(self.tableHeader, self.app.settings.value('effectswidget/HeaderSectionSizes', []))
        settings.setHeaderSectionVisualIndices(self.tableHeader, self.app.settings.value('effectswidget/headerSectionVisualIndices', []))
        self.tableHeader.sectionResized.connect(self._slotTableSectionResized)
        self.tableHeader.sectionMoved.connect(self._slotTableSectionMoved)
        settings.setSplitterState(self.widget.splitter, self.app.settings.value('effectswidget/splitterState', None))
        self.widget.splitter.splitterMoved.connect(self._slotSplitterMoved)
        self.widget.showPermanentCheckBox.setChecked(bool(int(self.app.settings.value('effectswidget/showPermanent', 0))))
        self.widget.showEmptySourcesCheckBox.setChecked(bool(int(self.app.settings.value('effectswidget/showEmptySources', 0))))
        self.widget.showInactiveCheckBox.setChecked(bool(int(self.app.settings.value('effectswidget/showInactive', 0))))
        self.widget.showPermanentCheckBox.stateChanged.connect(self.effectsViewModel.setShowPermanent)
        self.widget.showEmptySourcesCheckBox.stateChanged.connect(self.effectsViewModel.setShowEmptySources)
        self.widget.showInactiveCheckBox.stateChanged.connect(self.effectsViewModel.setShowInactive)
        if self.effectsViewModel.sortReversed:
            self.widget.effectsView.sortByColumn(self.effectsViewModel.sortColumn, QtCore.Qt.DescendingOrder)
        else:
            self.widget.effectsView.sortByColumn(self.effectsViewModel.sortColumn, QtCore.Qt.AscendingOrder)
        self.dataManager = datamanager
        self.dataManager.registerRootObjectListener(self._onPipRootObjectEvent)
        
        
    def _onPipRootObjectEvent(self, rootObject):
        self.pipStats = rootObject.child('Stats')
        if self.pipStats:
            self.pipStats.registerValueUpdatedListener(self._onPipStatsUpdated)
            self.pipActiveEffects = self.pipStats.child('ActiveEffects')
            if self.pipActiveEffects:
                self.effectsViewModel.setPipActiveEffects(self.pipActiveEffects)
        
    def _onPipStatsUpdated(self, caller, value, pathObjs):
        self.pipActiveEffects = self.pipStats.child('ActiveEffects')
        if self.pipActiveEffects:
            self.effectsViewModel.setPipActiveEffects(self.pipActiveEffects)
            
    @QtCore.pyqtSlot(int, int, int)
    def _slotTableSectionResized(self, logicalIndex, oldSize, newSize):
        self.app.settings.setValue('effectswidget/HeaderSectionSizes', settings.getHeaderSectionSizes(self.tableHeader))
        
    @QtCore.pyqtSlot(int, int, int)
    def _slotTableSectionMoved(self, logicalIndex, oldVisualIndex, newVisualIndex):
        self.app.settings.setValue('effectswidget/headerSectionVisualIndices', settings.getHeaderSectionVisualIndices(self.tableHeader))
        
    @QtCore.pyqtSlot(int, int)
    def _slotSplitterMoved(self, pos, index):
        self.app.settings.setValue('effectswidget/splitterState', settings.getSplitterState(self.widget.splitter))
        
