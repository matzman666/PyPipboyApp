# -*- coding: utf-8 -*-


import os
import logging
from PyQt5 import QtWidgets, QtCore, QtGui, uic
from widgets import widgets
from widgets.shared import settings
from .marker import PipValueMarkerBase



class PlayerMarker(PipValueMarkerBase):
    signalPlayerPositionUpdate = QtCore.pyqtSignal(float, float, float)
    
    def __init__(self, widget, imageFactory, color, parent = None):
        super().__init__(widget.mapScene, widget.mapView, parent)
        self.widget = widget
        self.imageFactory = imageFactory
        self.imageFilePath = os.path.join('res', 'mapmarkerplayer.svg')
        self.pipValueListenerDepth = 1
        self.markerItem.setZValue(10)
        self.setColor(color,False)
        self.setLabelFont(QtGui.QFont("Times", 8, QtGui.QFont.Bold), False)
        self.setMapPos(480, 300, 0, False)
        self.setLabel('Player', False)
        self.doUpdate()
        
    def _getPixmap_(self):
        return self.imageFactory.getPixmap(self.imageFilePath, height=32, color=self.color)
    
    @QtCore.pyqtSlot()        
    def _slotPipValueUpdated(self):
        pr = self.pipValue.child('Rotation').value()
        self.setMapPos(self.mapPosX, self.mapPosY, pr)
        self.signalPlayerPositionUpdate.emit(self.mapPosX, self.mapPosY, pr)



class MapGraphicsItem(QtCore.QObject):
    
    class PixmapItem(QtWidgets.QGraphicsPixmapItem):
        def __init__(self, parent, qparent = None):
            super().__init__(qparent)
            self.parent = parent

    def __init__(self, lwidget, qparent = None):
        super().__init__(qparent)
        self.lwidget = lwidget
        self.mapItem = self.PixmapItem(self)
        self.lwidget.mapScene.addItem(self.mapItem)
        image = QtGui.QImage(960, 640, QtGui.QImage.Format_Indexed8)
        image.fill(QtGui.QColor.fromRgb(255,255,255))
        self._setMapPixmap(QtGui.QPixmap.fromImage(image))
        self.mapItem.setZValue(-10)
            
    def _setMapPixmap(self, pixmap):
        self.mapItem.setPixmap(pixmap)
        self.lwidget.mapScene.setSceneRect(self.mapItem.sceneBoundingRect())
    
    @QtCore.pyqtSlot(float, float, float)
    def setZoomLevel(self, zoom, mapposx, mapposy):
        self.mapItem.setTransform(QtGui.QTransform.fromScale(zoom, zoom))
        self.lwidget.mapScene.setSceneRect(self.mapItem.sceneBoundingRect())
        if mapposx >= 0 and mapposy >=0:
            self.lwidget.mapView.centerOn(mapposx * zoom, mapposy * zoom)
    
    @QtCore.pyqtSlot(QtGui.QColor)
    def setColor(self, color):
        pass


class LocalMapWidget(widgets.WidgetBase):
    MAPZOOM_SCALE_MAX = 4.0
    MAPZOOM_SCALE_MIN = 0.1
    
    signalSetZoomLevel = QtCore.pyqtSignal(float, float, float)
    signalSetColor = QtCore.pyqtSignal(QtGui.QColor)
    signalSetStickyLabel= QtCore.pyqtSignal(bool)
    
    _signalMapUpdate = QtCore.pyqtSignal()
    
    def __init__(self, handle, controller, parent):
        super().__init__('Local Map', parent)
        self.basepath = handle.basepath
        self.controller = controller
        self.widget = uic.loadUi(os.path.join(self.basepath, 'ui', 'localmapwidget.ui'))
        self.setWidget(self.widget)
        self._logger = logging.getLogger('pypipboyapp.map.localmap')
        self.mapZoomLevel = 1.0
        self.mapReqTimer = QtCore.QTimer()
        
    def init(self, app, datamanager):
        super().init(app, datamanager)
        self._app = app
        self.mapScene = QtWidgets.QGraphicsScene()
        self.mapScene.setBackgroundBrush(QtGui.QBrush(QtGui.QColor.fromRgb(0,0,0)))
        self.mapColor = QtGui.QColor.fromRgb(20,255,23)
        # Init graphics view
        self.COLORTABLE=[]
        for i in range(256): self.COLORTABLE.append(QtGui.qRgb(i/4,i,i/2))
        self.mapView = self.widget.graphicsView
        self.mapView.setScene(self.mapScene)
        self.mapView.setMouseTracking(True)
        self.mapView.centerOn(0, 0)
        self.mapView.viewport().installEventFilter(self)
        self.dataManager = datamanager
        # Add map graphics
        self.mapItem = MapGraphicsItem(self)
        self.signalSetZoomLevel.connect(self.mapItem.setZoomLevel)
        self.signalSetColor.connect(self.mapItem.setColor)
        self.mapEnabledFlag = False
        # Add player marker
        self.playerMarker = PlayerMarker(self,self.controller.imageFactory, self.mapColor)
        self._connectMarker(self.playerMarker)
        # Init zoom slider
        self.widget.mapZoomSlider.setMinimum(-100)
        self.widget.mapZoomSlider.setMaximum(100)
        self.widget.mapZoomSlider.setValue(0)
        self.widget.mapZoomSlider.setSingleStep(5)
        self.widget.mapZoomSlider.valueChanged.connect(self._slotZoomSliderTriggered)
        # Init zoom Spinbox
        self.widget.mapZoomSpinbox.setMinimum(self.MAPZOOM_SCALE_MIN*100.0)
        self.widget.mapZoomSpinbox.setMaximum(self.MAPZOOM_SCALE_MAX*100.0)
        self.widget.mapZoomSpinbox.setValue(100.0)
        self.widget.mapZoomSpinbox.setSingleStep(10.0)
        self.widget.mapZoomSpinbox.valueChanged.connect(self._slotZoomSpinTriggered)
        self.signalSetZoomLevel.connect(self.saveZoom)
        if self._app.settings.value('localmapwidget/zoom'):
            self.mapZoomLevel = float(self._app.settings.value('localmapwidget/zoom'))
            if self.mapZoomLevel == 1.0:
                sliderValue = 0
            elif self.mapZoomLevel > 1.0:
                sliderValue = (self.mapZoomLevel/self.MAPZOOM_SCALE_MAX)*100.0
            else:
                sliderValue = -(self.MAPZOOM_SCALE_MIN/self.mapZoomLevel)*100.0
            self.widget.mapZoomSlider.blockSignals(True)
            self.widget.mapZoomSlider.setValue(sliderValue)
            self.widget.mapZoomSlider.blockSignals(False)
            self.widget.mapZoomSpinbox.blockSignals(True)
            self.widget.mapZoomSpinbox.setValue(self.mapZoomLevel*100.0)
            self.widget.mapZoomSpinbox.blockSignals(False)        
            self.signalSetZoomLevel.emit(self.mapZoomLevel, 0, 0)
        # Init Enable Checkbox
        self.widget.enableCheckbox.stateChanged.connect(self._slotEnableMapTriggered)
        self.widget.enableCheckbox.setChecked(bool(int(self._app.settings.value('localmapwidget/enabled', 0))))
        # Init SaveTo Button
        self.widget.saveToButton.clicked.connect(self._slotSaveToTriggered)
        # Init fps spinner
        self.mapFPS = int(self._app.settings.value('localmapwidget/fps', 5))
        self.widget.fpsSpinBox.setValue(self.mapFPS)
        self.mapReqTimer.setInterval(int(1000/self.mapFPS))
        self.mapReqTimer.timeout.connect(self._slotSendMapReq)
        self.widget.fpsSpinBox.valueChanged.connect(self._slotFpsSpinnerTriggered)
        # Init Splitter
        settings.setSplitterState(self.widget.splitter, self._app.settings.value('localmapwidget/splitterState', None))
        self.widget.splitter.splitterMoved.connect(self._slotSplitterMoved)
        # Init PyPipboy stuff
        from .controller import MapCoordinates
        self.mapCoords = MapCoordinates()
        self.datamanager = datamanager
        self.pipMapObject = None
        self.pipMapWorldObject = None
        self.pipColor = None
        self.pipWorldQuests = None
        self.pipMapQuestsItems = dict()
        #self._signalPipWorldQuestsUpdated.connect(self._slotPipWorldQuestsUpdated)
        #self._signalPipWorldLocationsUpdated.connect(self._slotPipWorldLocationsUpdated)
        self.datamanager.registerRootObjectListener(self._onRootObjectEvent)
        self.dataManager.registerLocalMapListener(self._onLocalMapUpdate)
        self._signalMapUpdate.connect(self._slotMapUpdate)
        
    def getMenuCategory(self):
        return 'Map && Locations'

    @QtCore.pyqtSlot(float, float, float)
    def saveZoom(self, zoom, mapposx, mapposy):
        self._app.settings.setValue('localmapwidget/zoom', zoom)
        
    @QtCore.pyqtSlot(int, int)
    def _slotSplitterMoved(self, pos, index):
        self._app.settings.setValue('localmapwidget/splitterState', settings.getSplitterState(self.widget.splitter))

    def _connectMarker(self, marker):
        self.signalSetZoomLevel.connect(marker.setZoomLevel)
        #self.signalSetColor.connect(marker.setColor)
        #self.signalSetStickyLabel.connect(marker.setStickyLabel)
        #marker.signalMarkerDestroyed.connect(self._disconnectMarker)
    
    def _onRootObjectEvent(self, rootObject):
        self.pipMapObject = rootObject.child('Map')
        if self.pipMapObject:
            self.pipMapObject.registerValueUpdatedListener(self._onPipMapReset)
            self._onPipMapReset(None, None, None)
                
    def _onPipMapReset(self, caller, value, pathObjs):
        self.pipMapWorldObject = self.pipMapObject.child('Local')
        if self.pipMapWorldObject:
            pipWorldPlayer = self.pipMapWorldObject.child('Player')
            if pipWorldPlayer:
                self.playerMarker.setPipValue(pipWorldPlayer, self.datamanager, self.mapCoords)
                self.playerMarker.setVisible(False)
            else:
                self.widget.enableCheckbox.setChecked(False)
        else:
            self.widget.enableCheckbox.setChecked(False)
    
    
    @QtCore.pyqtSlot(bool)
    def _slotEnableMapTriggered(self, value):
        self._app.settings.setValue('localmapwidget/enabled', int(value))
        self.mapEnabledFlag = value
        if value:
            self.mapReqTimer.start()
        else:
            self.mapReqTimer.stop()
    
    @QtCore.pyqtSlot(int)
    def _slotFpsSpinnerTriggered(self, value):
        self.mapFPS = value
        self.mapReqTimer.setInterval(int(1000/self.mapFPS))
        self._app.settings.setValue('localmapwidget/fps', self.mapFPS)
        
    def _onLocalMapUpdate(self, lmap):
        self._mapUpdate = lmap
        self._signalMapUpdate.emit()
        
    @QtCore.pyqtSlot()
    def _slotSaveToTriggered(self):
        fileName = QtWidgets.QFileDialog.getSaveFileName(self, '', '', 'Images (*.png *.jpg *.gif)')
        if fileName:
            self.mapItem.mapItem.pixmap().save(fileName[0])
            #pixmap = self.mapView.grab()
            #pixmap.save(fileName[0])
            
    @QtCore.pyqtSlot()
    def _slotMapUpdate(self):
        #self.mapCoords.init( 
        #        self._mapUpdate.nw[0], self._mapUpdate.nw[1],
        #        self._mapUpdate.ne[0], self._mapUpdate.ne[1],
        #        self._mapUpdate.sw[0], self._mapUpdate.sw[1],
        #        self.mapItem.MAP_NWX, self.mapItem.MAP_NWY, 
        #        self.mapItem.MAP_NEX, self.mapItem.MAP_NEY, 
        #        self.mapItem.MAP_SWX, self.mapItem.MAP_SWY )
        image = QtGui.QImage(self._mapUpdate.pixels, self._mapUpdate.width, self._mapUpdate.height, QtGui.QImage.Format_Indexed8)
        image.setColorTable(self.COLORTABLE)
        self.playerMarker.setMapPos(self._mapUpdate.width/2, self._mapUpdate.height/2, self.playerMarker.mapPosR, False)
        if self.mapItem:
            self.mapItem._setMapPixmap(QtGui.QPixmap.fromImage(image))
        if self.mapEnabledFlag:
            self.playerMarker.setVisible(True)
        else:
            self.playerMarker.setVisible(False)
            
    @QtCore.pyqtSlot()
    def _slotSendMapReq(self):
        if self.mapEnabledFlag:
            self.dataManager.rpcRequestLocalMapSnapshot()
        
        
    @QtCore.pyqtSlot(int)        
    def _slotZoomSliderTriggered(self, zoom):
        if zoom == 0:
            mod = 0.0
        elif zoom > 0:
            mod = (self.MAPZOOM_SCALE_MAX - 1) * float(zoom)/100.0
        else:
            mod = (1 -self.MAPZOOM_SCALE_MIN) * float(zoom)/100.0
        viewport = self.mapView.mapToScene(self.mapView.rect())
        centerpos = (viewport.at(2) + viewport.at(0))/2 # (SE + NW)/2
        mcenterpos = centerpos / self.mapZoomLevel # account for previous zoom 
        self.mapZoomLevel = 1+mod
        self.widget.mapZoomSpinbox.blockSignals(True)
        self.widget.mapZoomSpinbox.setValue(self.mapZoomLevel*100.0)
        self.widget.mapZoomSpinbox.blockSignals(False)
        self.signalSetZoomLevel.emit(self.mapZoomLevel, mcenterpos.x(), mcenterpos.y())
        
        
    @QtCore.pyqtSlot(float)        
    def _slotZoomSpinTriggered(self, zoom):
        viewport = self.mapView.mapToScene(self.mapView.rect())
        centerpos = (viewport.at(2) + viewport.at(0))/2 # (SE + NW)/2
        mcenterpos = centerpos / self.mapZoomLevel # account for previous zoom 
        self.mapZoomLevel = zoom/100.0
        if self.mapZoomLevel == 1.0:
            sliderValue = 0
        elif self.mapZoomLevel > 1.0:
            sliderValue = (self.mapZoomLevel/self.MAPZOOM_SCALE_MAX)*100.0
        else:
            sliderValue = -(self.MAPZOOM_SCALE_MIN/self.mapZoomLevel)*100.0
        self.widget.mapZoomSlider.blockSignals(True)
        self.widget.mapZoomSlider.setValue(sliderValue)
        self.widget.mapZoomSlider.blockSignals(False)
        self.signalSetZoomLevel.emit(self.mapZoomLevel, mcenterpos.x(), mcenterpos.y())

    def eventFilter(self, watched, event):
        if watched == self.mapView.viewport():
            if event.type() == QtCore.QEvent.Wheel:
                # Zoom to center
                viewport = self.mapView.mapToScene(self.mapView.rect())
                centerpos = (viewport.at(2) + viewport.at(0))/2 # (SE + NW)/2
                vcenterpos = centerpos / self.mapZoomLevel # account for previous zoom 
                # Sometimes I get strange angle readings (especially after mouse move)
                #zoom = self.mapZoomLevel + event.angleDelta().y()/120 * 0.1
                if event.angleDelta().y() > 0:
                    zoom = self.mapZoomLevel * 1.1
                else:
                    zoom = self.mapZoomLevel * 0.9
                if zoom < self.MAPZOOM_SCALE_MIN:
                    zoom = self.MAPZOOM_SCALE_MIN
                elif zoom > self.MAPZOOM_SCALE_MAX:
                    zoom = self.MAPZOOM_SCALE_MAX
                if self.mapZoomLevel != zoom:
                    self.mapZoomLevel = zoom
                    if self.mapZoomLevel == 1.0:
                        sliderValue = 0
                    elif self.mapZoomLevel > 1.0:
                        sliderValue = (self.mapZoomLevel/self.MAPZOOM_SCALE_MAX)*100.0
                    else:
                        sliderValue = -(self.MAPZOOM_SCALE_MIN/self.mapZoomLevel)*100.0
                    self.widget.mapZoomSlider.blockSignals(True)
                    self.widget.mapZoomSlider.setValue(sliderValue)
                    self.widget.mapZoomSlider.blockSignals(False)
                    self.widget.mapZoomSpinbox.blockSignals(True)
                    self.widget.mapZoomSpinbox.setValue(self.mapZoomLevel*100.0)
                    self.widget.mapZoomSpinbox.blockSignals(False)
                    self.signalSetZoomLevel.emit(self.mapZoomLevel, vcenterpos.x(), vcenterpos.y())
                return True
        return False
    
