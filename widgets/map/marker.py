# -*- coding: utf-8 -*-


import os
import logging
from PyQt5 import QtWidgets, QtCore, QtGui, uic, QtSvg



class MarkerBase(QtCore.QObject):
    
    class MarkerItem(QtWidgets.QGraphicsPixmapItem):
        def __init__(self, parent, sparent = None):
            super().__init__(sparent)
            self.parent = parent
        def hoverEnterEvent(self, event):
            self.parent._markerHoverEnterEvent_(event)
        def hoverLeaveEvent(self, event):
            self.parent._markerHoverLeaveEvent_(event)
        def contextMenuEvent(self, event):
            self.parent._markerContextMenuEvent_(event)
        def mouseDoubleClickEvent(self, event):
            self.parent._markerDoubleClickEvent_(event)
    
    class LabelItem(QtWidgets.QGraphicsSimpleTextItem):
        def __init__(self, parent, text, sparent = None):
            super().__init__(text, sparent)
            self.parent = parent
        def hoverEnterEvent(self, event):
            self.parent._labelHoverEnterEvent_(event)
        def hoverLeaveEvent(self, event):
            self.parent._labelHoverLeaveEvent_(event)
        def contextMenuEvent(self, event):
            self.parent._labelContextMenuEvent_(event)
        def mouseDoubleClickEvent(self, event):
            self.parent._labelDoubleClickEvent_(event)
        def paint(self, painter, option, widget):
            self.setOpacity(0.6)
            brush = QtCore.Qt.black
            painter.setBrush(brush)
            painter.setPen(brush)
            painter.drawRect(self.boundingRect().adjusted(-3,-3,6,6))
            super().paint(painter, option, widget)
        
    signalDoUpdate = QtCore.pyqtSignal()
    signalMarkerDestroyed = QtCore.pyqtSignal(QtCore.QObject)
        
    def __init__(self, scene, view, parent = None):
        super().__init__(parent)
        self.scene = scene
        self.view = view
        self.isVisible = False
        self.color = None
        self.label = None
        self.labelFont = None
        self.labelAlwaysVisible = False
        self.stickyLabel = False
        self.labelDirty = False
        self.mapPosX = 0.0
        self.mapPosY = 0.0
        self.mapPosR = 0.0
        self.zoomLevel = 1.0
        self.positionDirty = False
        self.markerItem = MarkerBase.MarkerItem(self)
        self.markerItem.setVisible(False)
        self.markerItem.setAcceptHoverEvents(True)
        self.scene.addItem(self.markerItem)
        self.markerPixmapDirty = False
        self.labelItem = None
        self.markerHooverActive = False
        self.note =''
        self.uid = None
        self.size = None
        self.signalDoUpdate.connect(self.doUpdate)
        
    def updateZIndex(self):
        if hasattr(self.widget, 'mapMarkerZIndexes'):
            if (self.markerItem):
                self.markerItem.setZValue(self.widget.mapMarkerZIndexes.get(str(type(self)), 0))
            if (self.labelItem):
                self.labelItem.setZValue(self.widget.mapMarkerZIndexes.get(str(type(self)), 0)+1000)
        
    def _markerHoverEnterEvent_(self, event):
        if self.labelItem and not self.labelAlwaysVisible and not self.stickyLabel:
            self.markerHooverActive = True
            self.labelItem.setVisible(True)
    def _markerHoverLeaveEvent_(self, event):
        if self.labelItem and not self.labelAlwaysVisible and not self.stickyLabel:
            self.labelItem.setVisible(False)
            self.markerHooverActive = False
    def _markerDoubleClickEvent_(self, event):
        pass
    def _markerContextMenuEvent_(self, event):
        menu = QtWidgets.QMenu(self.view)
        self._fillMarkerContextMenu_(event, menu)
        if self.labelItem and not self.labelAlwaysVisible:
            @QtCore.pyqtSlot(bool)
            def _toggleStickyLabel(value):
                if self.uid != None:
                    settingPath = 'globalmapwidget/stickylabels2/'
                    if (value):
                        self.widget._app.settings.setValue(settingPath+self.uid, int(value))
                    else:
                        self.widget._app.settings.beginGroup(settingPath);
                        self.widget._app.settings.remove(self.uid); 
                        self.widget._app.settings.endGroup();
                self.setStickyLabel(value)
            ftaction = menu.addAction('Sticky Label')
            ftaction.toggled.connect(_toggleStickyLabel)
            ftaction.setCheckable(True)
            ftaction.setChecked(self.stickyLabel)
        menu.exec(event.screenPos())
        
    def _fillMarkerContextMenu_(self, event, menu):
        pass
        
        
    def _labelHoverEnterEvent_(self, event):
        pass
    def _labelHoverLeaveEvent_(self, event):
        pass
    def _labelContextMenuEvent_(self, event):
        pass
    def _labelDoubleClickEvent_(self, event):
        pass
            
    def _labelStr_(self):
        return self.label
            
    def _updateMarkerOffset_(self):
        mb = self.markerItem.boundingRect()
        self.markerItem.setOffset(-mb.width()/2, -mb.height()/2)
        
    def _getPixmap_(self):
        return QtGui.QPixmap()
    
    @QtCore.pyqtSlot()
    def doUpdate(self):
        if self.markerPixmapDirty:
            self.markerPixmapDirty = False
            self.markerItem.setPixmap(self._getPixmap_())
            self._updateMarkerOffset_()

        if self.labelDirty:
            self.labelDirty = False
            label = self._labelStr_()
            if label:
                if not self.labelItem:
                    self.labelItem = MarkerBase.LabelItem(self, label)
                    self.scene.addItem(self.labelItem)
                    self.labelItem.setAcceptHoverEvents(True)
                    if self.isVisible and (self.labelAlwaysVisible or self.stickyLabel):
                        self.labelItem.setVisible(True)
                    else:
                        self.labelItem.setVisible(False)
                else:
                    self.labelItem.setText(label)
                if not self.markerHooverActive:
                    if self.isVisible and (self.labelAlwaysVisible or self.stickyLabel):
                        self.labelItem.setVisible(True)
                    else:
                        self.labelItem.setVisible(False)
                if self.color:
                    self.labelItem.setBrush(QtGui.QBrush(self.color))
                if self.labelFont:
                    self.labelItem.setFont(self.labelFont)
            elif self.labelItem:
                self.scene.removeItem(self.labelItem)
                self.labelItem = None
        if self.positionDirty:
            self.positionDirty = False
            self.markerItem.setPos(self.mapPosX * self.zoomLevel, self.mapPosY * self.zoomLevel)
            self.markerItem.setRotation(self.mapPosR)
            if self.labelItem:
                mb = self.markerItem.sceneBoundingRect()
                lp = (mb.bottomRight() + mb.bottomLeft())/2.0
                lp += QtCore.QPointF(-self.labelItem.boundingRect().width()/2, 6)
                self.labelItem.setPos(lp)
        
        self.updateZIndex()

    @QtCore.pyqtSlot()
    def _rebuildOverlayIcons(self):
        pass
                
    @QtCore.pyqtSlot(QtGui.QColor)
    def setColor(self, color, update = True):
        self.color = color
        self.markerPixmapDirty = True
        self.labelDirty = True
        if update:
            self._rebuildOverlayIcons()
            self.doUpdate()
    
    @QtCore.pyqtSlot(str)
    def setLabel(self, label, update = True):
        self.label = label
        self.labelDirty = True
        self.positionDirty = True
        if update:
            self.doUpdate()
    
    @QtCore.pyqtSlot(QtGui.QFont)
    def setLabelFont(self, font, update = True):
        self.labelFont = font
        self.labelDirty = True
        if update:
            self.doUpdate()
    
    @QtCore.pyqtSlot(bool)
    def setLabelAlwaysVisible(self, visible, update = True):
        self.labelAlwaysVisible = visible
        self.labelDirty = True
        if update:
            self.doUpdate()
    
    @QtCore.pyqtSlot(bool)
    def setStickyLabel(self, sticky, update = True):
        self.stickyLabel = sticky
        self.labelDirty = True
        if update:
            self.doUpdate()
        
    @QtCore.pyqtSlot(bool)
    def setVisible(self, visible):
        self.isVisible = visible
        self.markerItem.setVisible(visible)
        if self.labelItem and (self.labelAlwaysVisible or self.stickyLabel):
            self.labelItem.setVisible(visible)
    
    @QtCore.pyqtSlot(float, float, float)
    def setZoomLevel(self, zoom, mapposx, mapposy, update = True):
        self.zoomLevel = zoom
        self.positionDirty = True
        if update:
            self.doUpdate()

    @QtCore.pyqtSlot(int)
    def setSize(self, size, update = True):
        self.size = size
        self.markerPixmapDirty = True
        self.positionDirty = True
        if update:
            self.doUpdate()

    @QtCore.pyqtSlot(float, float, float)
    def setMapPos(self, x, y, r = 0.0, update = True):
        self.mapPosX = x
        self.mapPosY = y
        self.mapPosR = r
        self.positionDirty = True
        if update:
            self.doUpdate()
            
    @QtCore.pyqtSlot()
    def invalidateMarkerPixmap(self, update = True):
        self.markerPixmapDirty = True
        if update:
            self.doUpdate()

    def destroy(self):
        if self.labelItem:
            self.scene.removeItem(self.labelItem)
            self.labelItem = None
        if self.markerItem:
            self.scene.removeItem(self.markerItem)
            self.markerItem = None
        self.signalMarkerDestroyed.emit(self)

    def setSavedSettings(self):
        if self.uid != None:
            settingPath = 'globalmapwidget/stickylabels2/'
            self.setStickyLabel(bool(self.widget._app.settings.value(settingPath+self.uid, 0)), True)
        return

    def mapCenterOn(self):
        self.view.centerOn(self.mapPosX * self.zoomLevel, self.mapPosY * self.zoomLevel)

    def isWithinRangeOf(self, target, distance):
        if (target.mapPosX - distance < self.mapPosX < target.mapPosX + distance
                and target.mapPosY - distance < self.mapPosY < target.mapPosY + distance):
            return True
        else:
            return False

class PipValueMarkerBase(MarkerBase):
    _signalPipValueUpdated = QtCore.pyqtSignal()
    
    def __init__(self, scene, view, parent = None):
        super().__init__(scene, view, parent)
        self.pipValue = None
        self.pipValueListenerDepth = 1
        self.mapCoords = None
        self._signalPipValueUpdated.connect(self._slotPipValueUpdated)
        
    def setPipValue(self, value, datamanager, mapCoords = None, signal = True):
        #self.setSavedSettings()
        self.datamanager = datamanager
        self.mapCoords = mapCoords
        if self.pipValue:
            self.pipValue.unregisterValueUpdatedListener(self._onPipValueUpdated)
        self.pipValue = value
        self.pipValue.registerValueUpdatedListener(self._onPipValueUpdated, self.pipValueListenerDepth)
        if signal:
            self._signalPipValueUpdated.emit()
    
    def _onPipValueUpdated(self, caller, value, pathObjs):
        self._signalPipValueUpdated.emit()
        
    @QtCore.pyqtSlot()        
    def _slotPipValueUpdated(self):
        pass

