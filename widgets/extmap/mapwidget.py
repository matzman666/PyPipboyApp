# -*- coding: utf-8 -*-


import os
import logging
from PyQt5 import QtWidgets, QtCore, QtGui, uic, QtSvg
from .. import widgets


class MapCoordsTranslator:
    # Simple Coordinate Translation
    # x2 = ax * x1 + bx
    # y2 = ay * y1 + by
    # The constants ax, ay, bx, by are calculated as follow:
    #  * We get North West (NWX, NWY), North East (NEX, NEY) and
    #       South West (SWX, SWY) coordinates from the game (/Map/World/Extents)
    #  * We state for each map we want to load NW, NE and SW coordinates 
    #  * We calculate the constants by simple equation solving
    # How to we get the coordinates for the map: by experimenting.
    def __init__(self):
        self._ax = 1
        self._bx = 0
        self._ay = 1
        self._by = 0
    def init(self, pnwx, pnwy, pnex, pney, pswx, pswy, mnwx, mnwy, mnex, mney, mswx, mswy):
        self._ax = float(mnex-mnwx)/float(pnex-pnwx)
        self._bx = mnwx - pnwx*self._ax 
        self._ay = float(mswy-mnwy)/float(pswy-pnwy)
        self._by = mnwy - pnwy*self._ay
    def pip2map_x(self, x):
        return self._ax*x + self._bx
    def pip2map_y(self, y):
        return self._ay*y + self._by
    def map2pip_x(self, x):
        return (1.0/self._ax)*(x-self._bx)
    def map2pip_y(self, x):
        return (1.0/self._ay)*(x-self._by)



class MapPixmapFactory:
    def __init__(self, basepath):
        self.basepath = basepath
        self._playerMarkerRenderer = None
        self._customMarkerRenderer = None
        self._powerMarkerRenderer = None
        self._questMarkerRenderer = None
        self._locationDefaultMarkerDRenderer = None
        self._locationDefaultMarkerURenderer = None
        self._locationDRendererMap = dict()
        self._locationURendererMap = dict()
        self._mapGreyImage = None
        self._mapColorImage = None
        
        
    def colorizeImage(self, image, color, painter = None):
        if not painter:
            endPainter = True
            painter = painter = QtGui.QPainter(image)
        else:
            endPainter = False
        maskImage = QtGui.QImage(image)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_Multiply)
        painter.fillRect( image.rect(), color)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_DestinationIn)
        painter.drawImage(0, 0, maskImage)
        if endPainter:
            painter.end()
            
    
    # maptype: 0 .. grey (default), 1 .. color
    def getMapPixmap(self, maptype, scale = 1.0, color = None):
        if maptype == 1:
            if not self._mapColorImage:
                self._mapColorImage = QtGui.QImage(os.path.join(self.basepath, 'res', 'mapcolor.png'))
            mapImage = self._mapColorImage
        else:
            if not self._mapGreyImage:
                self._mapGreyImage = QtGui.QImage(os.path.join(self.basepath, 'res', 'mapgreyscale.png'))
            mapImage = self._mapGreyImage
        outImage = QtGui.QImage(mapImage)
        if color:
            self.colorizeImage(outImage, color)
        outImage = outImage.scaled(mapImage.width() * scale, mapImage.height() * scale)
        return QtGui.QPixmap.fromImage(outImage)


    def _createIconPixmapFromSvg(self, svgRenderer, scaledTo = None, color = None):
        vb = svgRenderer.viewBox()
        owidth = vb.width()
        oheight = vb.height()
        if scaledTo != None:
            if owidth == oheight:
                owidth = scaledTo
                oheight = scaledTo
            elif owidth > oheight:
                oheight = int(scaledTo * float(oheight)/float(owidth))
                owidth = scaledTo
            else:
                owidth = int(scaledTo * float(owidth)/float(oheight))
                oheight = scaledTo
        markerImage = QtGui.QImage(owidth, oheight, QtGui.QImage.Format_ARGB32_Premultiplied)
        markerImage.fill(QtGui.QColor.fromRgb(0,0,0,0))
        painter = QtGui.QPainter(markerImage)
        svgRenderer.render(painter)
        if color:
            self.colorizeImage(markerImage, color, painter)
        painter.end()
        return QtGui.QPixmap.fromImage(markerImage)
        
        
        
    def getPlayerMarkerPixmap(self, scaledTo = None, color = None):
        if not self._playerMarkerRenderer:
            self._playerMarkerRenderer = QtSvg.QSvgRenderer(os.path.join(self.basepath, 'res', 'mapmarkerplayer.svg'))
        return self._createIconPixmapFromSvg(self._playerMarkerRenderer, scaledTo, color)
        
        
    def getCustomMarkerPixmap(self, scaledTo = None, color = None):
        if not self._customMarkerRenderer:
            self._customMarkerRenderer = QtSvg.QSvgRenderer(os.path.join(self.basepath, 'res', 'mapmarkercustom.svg'))
        return self._createIconPixmapFromSvg(self._customMarkerRenderer, scaledTo, color)
        
        
    def getPowerArmorMarkerPixmap(self, scaledTo = None, color = None):
        if not self._powerMarkerRenderer:
            self._powerMarkerRenderer = QtSvg.QSvgRenderer(os.path.join(self.basepath, 'res', 'mapmarkerpowerarmor.svg'))
        return self._createIconPixmapFromSvg(self._powerMarkerRenderer, scaledTo, color)
        
        
    def getQuestMarkerPixmap(self, scaledTo = None, color = None):
        if not self._questMarkerRenderer:
            self._questMarkerRenderer = QtSvg.QSvgRenderer(os.path.join(self.basepath, 'res', 'mapmarkerquest.svg'))
        return self._createIconPixmapFromSvg(self._questMarkerRenderer, scaledTo, color)
        
    def getLocationMarkerDefaultPixmap(self, discovered, scaledTo = None, color = None):
        if discovered:
            if not self._locationDefaultMarkerDRenderer:
                self._locationDefaultMarkerDRenderer = QtSvg.QSvgRenderer(os.path.join(self.basepath, 'res', 'mapmarkerloctype_default_d.svg'))
            return self._createIconPixmapFromSvg(self._locationDefaultMarkerDRenderer, scaledTo, color)
        else:
            if not self._locationDefaultMarkerURenderer:
                self._locationDefaultMarkerURenderer = QtSvg.QSvgRenderer(os.path.join(self.basepath, 'res', 'mapmarkerloctype_default_u.svg'))
            return self._createIconPixmapFromSvg(self._locationDefaultMarkerURenderer, scaledTo, color)
        
    def getLocationMarkerPixmap(self, loctype, discovered, scaledTo = None, color = None):
        if discovered:
            if not loctype in self._locationDRendererMap:
                fpath = os.path.join(self.basepath, 'res', 'mapmarkerloctype_' + str(loctype) + '_d.svg')
                if not os.path.isfile(fpath):
                    return None
                renderer = QtSvg.QSvgRenderer(fpath)
                self._locationDRendererMap[loctype] = renderer
            else:
                renderer = self._locationDRendererMap[loctype]
            return self._createIconPixmapFromSvg(renderer, scaledTo, color)
        else:
            if not loctype in self._locationURendererMap:
                fpath = os.path.join(self.basepath, 'res', 'mapmarkerloctype_' + str(loctype) + '_u.svg')
                if not os.path.isfile(fpath):
                    raise Exception('Error')
                    return None
                renderer = QtSvg.QSvgRenderer(fpath)
                self._locationURendererMap[loctype] = renderer
            else:
                renderer = self._locationURendererMap[loctype]
            return self._createIconPixmapFromSvg(renderer, scaledTo, color)
            
        
        
        
class MapMarkerItemBase(QtCore.QObject):
    _signalUpdatePosition = QtCore.pyqtSignal()
    signalMarkerDestroyed = QtCore.pyqtSignal(QtCore.QObject)
    
    class PixmapItem(QtWidgets.QGraphicsPixmapItem):
        def __init__(self, parent, sparent = None):
            super().__init__(sparent)
            self.parent = parent
        def hoverEnterEvent(self, event):
            self.parent.markerHoverEnterEvent(event)
        def hoverLeaveEvent(self, event):
            self.parent.markerHoverLeaveEvent(event)
        
    def __init__(self, scene, color = None, label = None, labelFont = None, permantentLabel = False, tempPermanentLabel = False, zoomLevel = 1.0, parent = None):
        super().__init__(parent)
        self.scene = scene
        self.color = color
        self.label = label
        self.labelFont = labelFont
        self.permanentLabel = permantentLabel
        self.tempPermanentLabel = tempPermanentLabel
        self.zoomLevel = zoomLevel
        self.mapPosX = 0
        self.mapPosY = 0
        self.markerItem = self.PixmapItem(self)
        self.isVisible = False
        self.markerItem.setVisible(False)
        scene.addItem(self.markerItem)
        if label:
            self.labelItem = scene.addSimpleText(label)
            self.labelItem.setVisible(False)
            self.markerItem.setAcceptHoverEvents(True)
            if color:
                self.labelItem.setBrush(QtGui.QBrush(color))
            if labelFont:
                self.labelItem.setFont(labelFont)
        else:
            self.labelItem = None
        self._signalUpdatePosition.connect(self._slotUpdatePosition)
        
    def markerHoverEnterEvent(self, event):
        if self.isVisible and not self.permanentLabel and not self.tempPermanentLabel and self.labelItem:
            self.labelItem.setVisible(True)
            
    def markerHoverLeaveEvent(self, event):
        if self.isVisible and not self.permanentLabel and not self.tempPermanentLabel and self.labelItem:
            self.labelItem.setVisible(False)
            
    def setVisible(self, visible):
        self.isVisible = visible
        self.markerItem.setVisible(visible)
        if self.labelItem and (self.permanentLabel or self.tempPermanentLabel):
            self.labelItem.setVisible(visible)
            
    def updateMapPos(self, x, y, signal = True):
        self.mapPosX = x
        self.mapPosY = y
        if signal:
            self._signalUpdatePosition.emit()
            
    def setMarkerPixmap(self, pixmap):
        self.markerItem.setPixmap(pixmap)
        self._updateMarkerOffset()
            
    def _updateMarkerOffset(self):
        mb = self.markerItem.boundingRect()
        self.markerItem.setOffset(-mb.width()/2, -mb.height()/2)
        
    def setLabel(self, label, signal = True):
        self.label = label
        if label:
            if not self.labelItem:
                self.labelItem = self.scene.addSimpleText(label)
                self.markerItem.setAcceptHoverEvents(True)
                if not self.permantentLabel:
                    self.labelItem.setVisible(False)
                if self.color:
                    self.labelItem.setBrush(QtGui.QBrush(self.color))
                if self.labelFont:
                    self.labelItem.setFont(self.labelFont)
            else:
                self.labelItem.setText(label)
            if signal:
                self._signalUpdatePosition.emit()
            
    @QtCore.pyqtSlot()        
    def _slotUpdatePosition(self):
        self.markerItem.setPos(self.mapPosX * self.zoomLevel, self.mapPosY * self.zoomLevel)
        if self.labelItem:
            mb = self.markerItem.sceneBoundingRect()
            lp = (mb.bottomRight() + mb.bottomLeft())/2.0
            lp += QtCore.QPointF(-self.labelItem.boundingRect().width()/2, 0)
            self.labelItem.setPos(lp)
    
    @QtCore.pyqtSlot(float)
    def slotSetZoomLevel(self, zoom, signal = True):
        self.zoomLevel = zoom
        if signal:
            self._signalUpdatePosition.emit()
    
    @QtCore.pyqtSlot(QtGui.QColor)
    def slotSetColor(self, color):
        self.color = color
        if self.labelItem:
            self.labelItem.setBrush(QtGui.QBrush(color))
    
    @QtCore.pyqtSlot(bool)
    def slotSetTemporaryPermanentLabels(self, value):
        self.tempPermanentLabel = value
        if self.labelItem and self.isVisible:
            self.labelItem.setVisible(value)
            
    def destroy(self):
        if self.labelItem:
            self.scene.removeItem(self.labelItem)
            self.labelItem = None
        if self.markerItem:
            self.scene.removeItem(self.markerItem)
            self.markerItem = None
        self.signalMarkerDestroyed.emit(self)
    


class MapPipValueMarkerItem(MapMarkerItemBase):
    _signalPipValueUpdated = QtCore.pyqtSignal()
    
    def __init__(self, scene, markerFactory, color = None, label = None, labelFont = None, permantentLabel = False, tempPermanentLabel = False, zoomLevel = 1.0, parent = None):
        super().__init__(scene, color, label, labelFont, permantentLabel, tempPermanentLabel, zoomLevel, parent)
        self.markerFactory = markerFactory
        self.coordTranslator = None
        self.pipValue = None
        self._pipValueListenerDepth = 1
        self.setMarkerPixmap(self._getPixmap())
        self.setVisible(False)
        self._signalPipValueUpdated.connect(self._slotPipValueUpdated)
        
    def _getPixmap(self):
        return None
        
    def setPipValue(self, value, coordTranslator, signal = True):
        self.coordTranslator = coordTranslator
        if self.pipValue:
            self.pipValue.unregisterValueUpdatedListener(self._onPipValueUpdated)
        self.pipValue = value
        self.pipValue.registerValueUpdatedListener(self._onPipValueUpdated, self._pipValueListenerDepth)
        if signal:
            self._signalPipValueUpdated.emit()
    
    def _onPipValueUpdated(self, caller, value, pathObjs):
        self._signalPipValueUpdated.emit()
        
    @QtCore.pyqtSlot()        
    def _slotPipValueUpdated(self):
        pass
        
    @QtCore.pyqtSlot(QtGui.QColor)
    def slotSetColor(self, color):
        super().slotSetColor(color)
        self.setMarkerPixmap(self._getPixmap())
    
    


class MapPlayerMarkerItem(MapPipValueMarkerItem):
    signalMapPositionUpdate = QtCore.pyqtSignal(float, float, float)
    
    def __init__(self, scene, markerFactory, color = None, tempPermanentLabel = False, parent = None):
        super().__init__(scene, markerFactory, color, None, QtGui.QFont("Times", 8, QtGui.QFont.Bold), False, tempPermanentLabel, 1.0, parent)
        self._pipValueListenerDepth = 1
        self.markerItem.setZValue(10)
        self.setVisible(True)
        
    def _getPixmap(self):
        return self.markerFactory.getPlayerMarkerPixmap(32, self.color)
    
    @QtCore.pyqtSlot()        
    def _slotPipValueUpdated(self):
        self.setVisible(True)
        px = self.coordTranslator.pip2map_x(self.pipValue.child('X').value())
        py = self.coordTranslator.pip2map_y(self.pipValue.child('Y').value())
        pr = self.pipValue.child('Rotation').value()
        self.updateMapPos(px, py)
        self.markerItem.setRotation(pr)
        self.signalMapPositionUpdate.emit(px, py, pr)
    


class MapCustomMarkerItem(MapPipValueMarkerItem):
    def __init__(self, scene, markerFactory, color = None, tempPermanentLabel = False, parent = None):
        super().__init__(scene,markerFactory, color, 'Custom Marker', QtGui.QFont("Times", 8, QtGui.QFont.Bold), False, tempPermanentLabel, 1.0, parent)
        self._pipValueListenerDepth = 1
        self.markerItem.setZValue(0)
        
    def _getPixmap(self):
        return self.markerFactory.getCustomMarkerPixmap(48, self.color)
            
    def _updateMarkerOffset(self):
        mb = self.markerItem.boundingRect()
        self.markerItem.setOffset(-mb.width()/2, -mb.height())
    
    @QtCore.pyqtSlot()        
    def _slotPipValueUpdated(self):
        isVisible = self.pipValue.child('Visible').value()
        if isVisible:
            self.setVisible(True)
            px = self.coordTranslator.pip2map_x(self.pipValue.child('X').value())
            py = self.coordTranslator.pip2map_y(self.pipValue.child('Y').value())
            self.updateMapPos(px, py)
            #if self.labelItem:
            #    height = self.pipValue.child('Height').value()
            #    self.labelItem.setText(self.label + '\n(Height ' + str(height) + ')')
        else:
            self.setVisible(False)
    


class MapPowerArmorMarkerItem(MapPipValueMarkerItem):
    def __init__(self, scene, markerFactory, color = None, tempPermanentLabel = False, parent = None):
        super().__init__(scene, markerFactory, color, 'Power Armor', QtGui.QFont("Times", 8, QtGui.QFont.Bold), False, tempPermanentLabel, 1.0, parent)
        self._pipValueListenerDepth = 1
        self.markerItem.setZValue(0)
        
    def _getPixmap(self):
        return self.markerFactory.getPowerArmorMarkerPixmap(32, self.color)
    
    @QtCore.pyqtSlot()        
    def _slotPipValueUpdated(self):
        isVisible = self.pipValue.child('Visible').value()
        if isVisible:
            self.setVisible(True)
            px = self.coordTranslator.pip2map_x(self.pipValue.child('X').value())
            py = self.coordTranslator.pip2map_y(self.pipValue.child('Y').value())
            self.updateMapPos(px, py)
            #if self.labelItem:
            #    height = self.pipValue.child('Height').value()
            #    self.labelItem.setText(self.label + '\n(Height ' + str(height) + ')')
        else:
            self.setVisible(False)
    


class MapQuestMarkerItem(MapPipValueMarkerItem):
    def __init__(self, scene, markerFactory, color = None, tempPermanentLabel = False, zoomLevel = 1.0, parent = None):
        super().__init__(scene, markerFactory, color, 'Quest Marker', QtGui.QFont("Times", 8, QtGui.QFont.Bold), False, tempPermanentLabel, zoomLevel, parent)
        self._pipValueListenerDepth = 1
        self.markerItem.setZValue(0)
        
    def _getPixmap(self):
        return self.markerFactory.getQuestMarkerPixmap(48, self.color)
            
    def _updateMarkerOffset(self):
        mb = self.markerItem.boundingRect()
        self.markerItem.setOffset(-mb.width()/2, -mb.height())
        
    @QtCore.pyqtSlot()        
    def _slotPipValueUpdated(self):
        self.setVisible(True)
        name = self.pipValue.child('Name').value()
        self.setLabel(name, False)
        px = self.coordTranslator.pip2map_x(self.pipValue.child('X').value())
        py = self.coordTranslator.pip2map_y(self.pipValue.child('Y').value())
        self.updateMapPos(px, py)
        #if self.labelItem:
        #    height = self.pipValue.child('Height').value()
        #    self.labelItem.setText(self.label + '\n(Height ' + str(height) + ')')
        
    


class MapLocationMarkerItem(MapPipValueMarkerItem):
    def __init__(self, scene, markerFactory, color = None, tempPermanentLabel = False, zoomLevel = 1.0, parent = None):
        self.locType = -1
        self.noTypePixmapFound = False
        self.discovered = False
        self.lastKnownDiscovered = False
        self.visible = False
        self.cleared = False
        self.initialSetupFlag = False
        super().__init__(scene, markerFactory, color, 'Location', QtGui.QFont("Times", 8, QtGui.QFont.Bold), False, tempPermanentLabel, zoomLevel, parent)
        self._pipValueListenerDepth = 1
        self.markerItem.setZValue(0)
        
    def _getPixmap(self):
        if self.locType < 0:
            return self.markerFactory.getLocationMarkerDefaultPixmap(self.discovered, 32, self.color)
        else:
            p = self.markerFactory.getLocationMarkerPixmap(self.locType, self.discovered, 32, self.color)
            if not p:
                self.noTypePixmapFound = True
                p = self.markerFactory.getLocationMarkerDefaultPixmap(self.discovered, 32, self.color)
            return p
        
    @QtCore.pyqtSlot()        
    def _slotPipValueUpdated(self):
        self.visible = self.pipValue.child('Visible').value()
        if self.visible:
            name = self.pipValue.child('Name')
            if name:
                self.setLabel(name.value(), False)
            else:
                self.setLabel('<Location>')
            loctype = self.pipValue.child('type')
            if loctype:
                self.locType = loctype.value()
            else:
                self.locType = -1
            discovered = self.pipValue.child('Discovered')
            if discovered:
                self.discovered = discovered.value()
            cleared = self.pipValue.child('ClearedStatus')
            if cleared:
                self.cleared = cleared.value()
            px = self.coordTranslator.pip2map_x(self.pipValue.child('X').value())
            py = self.coordTranslator.pip2map_y(self.pipValue.child('Y').value())
            self.updateMapPos(px, py)
            if not self.initialSetupFlag or self.discovered != self.lastKnownDiscovered:
                self.setMarkerPixmap(self._getPixmap())
                self.initialSetupFlag = True
            self.lastKnownDiscovered = self.discovered
            self.setVisible(True)
            if self.labelItem:
                mlabel = self.label
                mlabelchanged = False
                if self.cleared:
                    mlabel += '\n[CLEARED]'
                    mlabelchanged = True
                if self.noTypePixmapFound:
                    mlabel += '\n(LocType: ' + str(self.locType) + ')'
                    mlabelchanged = True
                if mlabelchanged:
                    self.labelItem.setText(mlabel)
        


class MapItem(QtCore.QObject):
    
    MAP_NWX = 36
    MAP_NWY = 50
    MAP_NEX = 2000
    MAP_NEY = 50
    MAP_SWX = 36
    MAP_SWY = 1978
    
    class PixmapItem(QtWidgets.QGraphicsPixmapItem):
        def __init__(self, parent, sparent = None):
            super().__init__(sparent)
            self.parent = parent
            
    def __init__(self, scene, pixmapFactory, maptype = 0, color = None, parent = None):
        super().__init__(parent)
        self.color = color
        self.scene = scene
        self.mapType = maptype
        self.pixmapFactory = pixmapFactory
        self.mapItem = self.PixmapItem(self)
        scene.addItem(self.mapItem)
        self.setMapPixmap(pixmapFactory.getMapPixmap(maptype, 1.0, color))
        self.mapItem.setZValue(-10)
            
    def setMapPixmap(self, pixmap):
        self.mapItem.setPixmap(pixmap)
        self.scene.setSceneRect(self.mapItem.sceneBoundingRect())
    
    @QtCore.pyqtSlot(float)
    def slotSetZoomLevel(self, zoom):
        self.mapItem.setTransform(QtGui.QTransform.fromScale(zoom, zoom))
        self.scene.setSceneRect(self.mapItem.sceneBoundingRect())
    
    @QtCore.pyqtSlot(QtGui.QColor)
    def slotSetColor(self, color):
        self.color = color
        self.setMapPixmap(self.pixmapFactory.getMapPixmap(self.mapType, 1.0, color))
        
            
            
class MapWidget(widgets.WidgetBase):
    
    signalSetZoomLevel = QtCore.pyqtSignal(float)
    signalSetColor = QtCore.pyqtSignal(QtGui.QColor)
    signalSetTemporaryPermanentLabels = QtCore.pyqtSignal(bool)
    _signalPipWorldQuestsUpdated = QtCore.pyqtSignal()
    _signalPipWorldLocationsUpdated = QtCore.pyqtSignal()
    
    MAPZOOM_SCALE_MAX = 3.0
    MAPZOOM_SCALE_MIN = 0.2
  
    def __init__(self, mhandle, parent):
        super().__init__('Map', parent)
        self.basepath = mhandle.basepath
        self.widget = uic.loadUi(os.path.join(self.basepath, 'ui', 'mapwidget.ui'))
        self.setWidget(self.widget)
        self.mapCenterOnPlayerEnabled = False
        self.mapZoomLevel = 1.0
        self._logger = logging.getLogger('pypipboyapp.mapwidget')
        self._signalPipWorldQuestsUpdated.connect(self._slotPipWorldQuestsUpdated)
        self._signalPipWorldLocationsUpdated.connect(self._slotPipWorldLocationsUpdated)
        
    def init(self, app, datamanager):
        super().init(app, datamanager)
        self.mapGraphicsScene = QtWidgets.QGraphicsScene()
        self.pixmapFactory = MapPixmapFactory(self.basepath)
        self.mapCoordTranslator = MapCoordsTranslator()
        self.mapColor = QtGui.QColor.fromRgb(20,255,23)
        
        # Add map graphics
        self.mapItem = MapItem(self.mapGraphicsScene, self.pixmapFactory, 0, self.mapColor)
        self.signalSetZoomLevel.connect(self.mapItem.slotSetZoomLevel)
        self.signalSetColor.connect(self.mapItem.slotSetColor)
        
        # Add player marker
        self.mapPlayerMarkerItem = MapPlayerMarkerItem(self.mapGraphicsScene, self.pixmapFactory, self.mapColor)
        self._connectMarkerItem(self.mapPlayerMarkerItem)
        self.mapPlayerMarkerItem.updateMapPos(500, 150)
        self.mapPlayerMarkerItem.signalMapPositionUpdate.connect(self._slotPlayerMapPositionUpdated)
        
        # Add custom marker
        self.mapCustomMarkerItem = MapCustomMarkerItem(self.mapGraphicsScene, self.pixmapFactory, self.mapColor)
        self._connectMarkerItem(self.mapCustomMarkerItem)
        
        # Add powerarmor marker
        self.mapPowerArmorMarkerItem = MapPowerArmorMarkerItem(self.mapGraphicsScene, self.pixmapFactory, self.mapColor)
        self._connectMarkerItem(self.mapPowerArmorMarkerItem)
        
        # Init graphics view
        self.widget.mapGraphicsView.setScene(self.mapGraphicsScene)
        self.widget.mapGraphicsView.setMouseTracking(True)
        self.widget.mapGraphicsView.centerOn(0, 0)
        
        # Init zoom slider
        self.widget.mapZoomSlider.setMinimum(-100)
        self.widget.mapZoomSlider.setMaximum(100)
        self.widget.mapZoomSlider.setValue(0)
        self.widget.mapZoomSlider.setSingleStep(5)
        self.widget.mapZoomSlider.valueChanged.connect(self._slotZoomSliderTriggered)
        
        # Init CenterOnPlayer checkbox
        self.widget.centerPlayerCheckbox.setChecked(False)
        self.widget.centerPlayerCheckbox.stateChanged.connect(self._slotCenterOnPlayerCheckToggled)
        
        # Init map color elements
        self.widget.mapColorButton.clicked.connect(self._slotMapColorSelectionTriggered)
        self.widget.mapColorAutoToggle.stateChanged.connect(self._slotMapColorAutoModeTriggered)
        
        # Init permanentLabelsCheckbox
        self.permanentLabelsEnabled = False
        self.widget.permanentLabelsCheckbox.stateChanged.connect(self._slotPermanentLabelsTriggered)
        
        # Init PyPipboy stuff
        self.datamanager = datamanager
        self.pipMapObject = None
        self.pipMapWorldObject = None
        self.pipColor = None
        self.pipWorldQuests = None
        self.pipMapQuestsItems = dict()
        self.pipWorldLocations = None
        self.pipMapLocationItems = dict()
        self.datamanager.registerRootObjectListener(self._onRootObjectEvent)
        
    def _connectMarkerItem(self, marker):
        self.signalSetZoomLevel.connect(marker.slotSetZoomLevel)
        self.signalSetColor.connect(marker.slotSetColor)
        self.signalSetTemporaryPermanentLabels.connect(marker.slotSetTemporaryPermanentLabels)
        marker.signalMarkerDestroyed.connect(self._slotMarkerDestroyed)
        
        
    @QtCore.pyqtSlot(QtCore.QObject)
    def _slotMarkerDestroyed(self, marker):
        self.signalSetZoomLevel.disconnect(marker.slotSetZoomLevel)
        self.signalSetColor.disconnect(marker.slotSetColor)
        self.signalSetTemporaryPermanentLabels.disconnect(marker.slotSetTemporaryPermanentLabels)
        marker.signalMarkerDestroyed.disconnect(self._slotMarkerDestroyed)
        
        
        
        
    def _onRootObjectEvent(self, rootObject):
        self.pipMapObject = rootObject.child('Map')
        if self.pipMapObject:
            self.pipMapObject.registerValueUpdatedListener(self._onPipMapReset)
            self._onPipMapReset(None, self.pipMapObject, None)
                
        
    def _onPipMapReset(self, caller, value, pathObjs):
        self.pipMapWorldObject = self.pipMapObject.child('World')
        if self.pipMapWorldObject:
            extents = self.pipMapWorldObject.child('Extents')
            if extents:
                self.mapCoordTranslator.init( 
                        extents.child('NWX').value(), extents.child('NWY').value(), 
                        extents.child('NEX').value(),  extents.child('NEY').value(), 
                        extents.child('SWX').value(), extents.child('SWY').value(), 
                        self.mapItem.MAP_NWX, self.mapItem.MAP_NWY, 
                        self.mapItem.MAP_NEX, self.mapItem.MAP_NEY, 
                        self.mapItem.MAP_SWX, self.mapItem.MAP_SWY )
            else:
                self._logger.warn('No "Extents" record found. Map coordinates may be off')
            if self.widget.mapColorAutoToggle.isChecked():
                self._slotMapColorAutoModeTriggered(True)
            pipWorldPlayer = self.pipMapWorldObject.child('Player')
            if pipWorldPlayer:
                self.mapPlayerMarkerItem.setPipValue(pipWorldPlayer, self.mapCoordTranslator)
            pipWorldCustom = self.pipMapWorldObject.child('Custom')
            if pipWorldCustom:
                self.mapCustomMarkerItem.setPipValue(pipWorldCustom, self.mapCoordTranslator)
            pipWorldPower = self.pipMapWorldObject.child('PowerArmor')
            if pipWorldPower:
                self.mapPowerArmorMarkerItem.setPipValue(pipWorldPower, self.mapCoordTranslator)
            self.pipWorldQuests = self.pipMapWorldObject.child('Quests')
            if self.pipWorldQuests:
                self.pipWorldQuests.registerValueUpdatedListener(self._onPipWorldQuestsUpdated, 0)
                self._signalPipWorldQuestsUpdated.emit()
            self.pipWorldLocations = self.pipMapWorldObject.child('Locations')
            if self.pipWorldLocations:
                self.pipWorldLocations.registerValueUpdatedListener(self._onPipWorldLocationsUpdated, 0)
                self._signalPipWorldLocationsUpdated.emit()
                    
                    
    def _onPipWorldQuestsUpdated(self, caller, value, pathObjs):
        self._signalPipWorldQuestsUpdated.emit()

    @QtCore.pyqtSlot() 
    def _slotPipWorldQuestsUpdated(self):
        newDict = dict()
        for q in self.pipWorldQuests.value():
            if q.pipId in self.pipMapQuestsItems:
                item = self.pipMapQuestsItems[q.pipId]
                newDict[q.pipId] = item
                del self.pipMapQuestsItems[q.pipId]
            else:
                item = MapQuestMarkerItem(self.mapGraphicsScene, self.pixmapFactory, self.mapColor, self.permanentLabelsEnabled, self.mapZoomLevel)
                self._connectMarkerItem(item)
                item.setPipValue(q, self.mapCoordTranslator)
                newDict[q.pipId] = item
        for i in self.pipMapQuestsItems:
            self.pipMapQuestsItems[i].destroy()
        self.pipMapQuestsItems = newDict
                    
                    
    def _onPipWorldLocationsUpdated(self, caller, value, pathObjs):
        self._signalPipWorldLocationsUpdated.emit()

    @QtCore.pyqtSlot() 
    def _slotPipWorldLocationsUpdated(self):
        newDict = dict()
        for l in self.pipWorldLocations.value():
            if l.pipId in self.pipMapLocationItems:
                item = self.pipMapLocationItems[l.pipId]
                newDict[l.pipId] = item
                del self.pipMapLocationItems[l.pipId]
            else:
                item = MapLocationMarkerItem(self.mapGraphicsScene, self.pixmapFactory, self.mapColor, self.permanentLabelsEnabled, self.mapZoomLevel)
                self._connectMarkerItem(item)
                item.setPipValue(l, self.mapCoordTranslator)
                newDict[l.pipId] = item
        for i in self.pipMapLocationItems:
            self.pipMapLocationItems[i].destroy()
        self.pipMapLocationItems = newDict
        
        
        
    @QtCore.pyqtSlot(float, float, float)        
    def _slotPlayerMapPositionUpdated(self, x, y, r):
        if self.mapCenterOnPlayerEnabled:
            self.widget.mapGraphicsView.centerOn(self.mapPlayerMarkerItem.markerItem.pos())
        
        
        
    @QtCore.pyqtSlot(int)        
    def _slotZoomSliderTriggered(self, zoom):
        if zoom == 0:
            mod = 0.0
        elif zoom > 0:
            mod = (self.MAPZOOM_SCALE_MAX - 1) * float(zoom)/100.0
        else:
            mod = (1 -self.MAPZOOM_SCALE_MIN) * float(zoom)/100.0
        self.mapZoomLevel = 1+mod
        self.signalSetZoomLevel.emit(1+mod)
        
    @QtCore.pyqtSlot(bool)        
    def _slotCenterOnPlayerCheckToggled(self, value):
        self.mapCenterOnPlayerEnabled = value
        if value and self.mapPlayerMarkerItem.markerItem.isVisible():
            self.widget.mapGraphicsView.centerOn(self.mapPlayerMarkerItem.markerItem.pos())
        
        
    @QtCore.pyqtSlot()        
    def _slotMapColorSelectionTriggered(self):
        color = QtWidgets.QColorDialog.getColor(self.mapColor, self)
        if color.isValid:
            self.signalSetColor.emit(color)
        
    @QtCore.pyqtSlot(bool)        
    def _slotMapColorAutoModeTriggered(self, value):
        if self.pipMapObject:
            if value:
                self.pipColor = self.pipMapObject.pipParent.child('Status').child('EffectColor')
                self.pipColor.registerValueUpdatedListener(self._onPipColorChanged, 1)
                self._onPipColorChanged(None, None, None)
            elif self.pipColor:
                self.pipColor.unregisterValueUpdatedListener(self._onPipColorChanged)
            
    def _onPipColorChanged(self, caller, value, pathObjs):
        if self.pipColor:
            r = self.pipColor.child(0).value() * 255
            g = self.pipColor.child(1).value() * 255
            b = self.pipColor.child(2).value() * 255
            self.mapColor = QtGui.QColor.fromRgb(r,g,b)
            self.signalSetColor.emit(self.mapColor)
        
    @QtCore.pyqtSlot(bool)        
    def _slotPermanentLabelsTriggered(self, value):
        self.permanentLabelsEnabled = value
        self.signalSetTemporaryPermanentLabels.emit(value)
        
 
