# -*- coding: utf-8 -*-


import os
import json
import logging
import textwrap
import uuid
from collections import OrderedDict
from PyQt5 import QtWidgets, QtCore, QtGui, uic, QtMultimedia
from widgets.shared.graphics import ImageFactory
from widgets import widgets
from widgets.shared import settings
from widgets.shared.characterdatamanager import CharacterDataManager
from .marker import PipValueMarkerBase, MarkerBase
from .editpoidialog import EditPOIDialog
from .editnotedialog import EditNoteDialog

class PlayerMarker(PipValueMarkerBase):
    signalPlayerPositionUpdate = QtCore.pyqtSignal(float, float, float)
    
    def __init__(self, widget, imageFactory, color,  size, parent = None):
        super().__init__(widget.mapScene, widget.mapView, parent)
        self.markerType = 0
        self.uid = 'playermarker'
        self.widget = widget
        self.imageFactory = imageFactory
        self.imageFilePath = os.path.join('res', 'mapmarkerplayer.svg')
        self.pipValueListenerDepth = 1
        self.markerItem.setZValue(10)
        self.setColor(color,False)
        self.setSize(size, False)
        self.setLabelFont(QtGui.QFont("Times", 8, QtGui.QFont.Bold), False)
        self.setLabel('Player', False)
        self.doUpdate()

        
    def _getPixmap_(self):
        return self.imageFactory.getPixmap(self.imageFilePath, size=self.size, color=self.color)
    
    @QtCore.pyqtSlot()        
    def _slotPipValueUpdated(self):
        if self.pipValue:
            self.setVisible(True)
            rx = self.pipValue.child('X').value()
            ry = self.pipValue.child('Y').value()
            px = self.mapCoords.pip2map_x(rx)
            py = self.mapCoords.pip2map_y(ry)
            pr = self.pipValue.child('Rotation').value()
            self.markerItem.setToolTip( 'Pos: (' + str(rx) + ', ' + str(ry) + ')\n'
                                    + 'Rot: ' + str(pr))
            self.setMapPos(px, py, pr)
            self.signalPlayerPositionUpdate.emit(px, py, pr)

class CustomMarker(PipValueMarkerBase):
    def __init__(self, widget, imageFactory, color, size, parent = None):
        super().__init__(widget.mapScene, widget.mapView, parent)
        self.markerType = 1
        self.uid = 'pipcustommarker'
        self.widget = widget
        self.imageFactory = imageFactory
        self.imageFilePath = os.path.join('res', 'mapmarkercustom.svg')
        self.pipValueListenerDepth = 1
        self.markerItem.setZValue(0)
        self.setColor(color,False)
        self.setSize(size, False)
        self.setLabelFont(QtGui.QFont("Times", 8, QtGui.QFont.Bold), False)
        self.setLabel('Custom Marker', False)
        self.doUpdate()
        
    def _getPixmap_(self):
        return self.imageFactory.getPixmap(self.imageFilePath, size=self.size, color=self.color)
            
    def _updateMarkerOffset_(self):
        mb = self.markerItem.boundingRect()
        self.markerItem.setOffset(-mb.width()/2, -mb.height())
        
    @QtCore.pyqtSlot(int)
    def setSize(self, size, update = True):
        # We want it to be a little bit bigger than the other marker
        super().setSize(size * 1.4, update)
    
    @QtCore.pyqtSlot()        
    def _slotPipValueUpdated(self):
        if self.pipValue:
            isVisible = self.pipValue.child('Visible').value()
            if isVisible:
                self.setVisible(True)
                rx = self.pipValue.child('X').value()
                ry = self.pipValue.child('Y').value()
                px = self.mapCoords.pip2map_x(rx)
                py = self.mapCoords.pip2map_y(ry)
                height = self.pipValue.child('Height').value()
                self.markerItem.setToolTip( 'Pos: (' + str(rx) + ', ' + str(ry) + ')\n'
                                            + 'Visible: ' + str(isVisible) + '\n'
                                            + 'Height: ' +str(height) )
                self.setMapPos(px, py)
            else:
                self.setVisible(False)
        
    def _fillMarkerContextMenu_(self, event, menu):
        if self.pipValue:
            @QtCore.pyqtSlot()
            def _removeCustomMarker():
                self.datamanager.rpcRemoveCustomMarker()
            menu.addAction('Remove Marker', _removeCustomMarker)
    
class PowerArmorMarker(PipValueMarkerBase):
    def __init__(self, widget, imageFactory, color, size, parent = None):
        super().__init__(widget.mapScene, widget.mapView, parent)
        self.markerType = 2
        self.uid = 'powerarmormarker'
        self.widget = widget
        self.imageFactory = imageFactory
        self.imageFilePath = os.path.join('res', 'mapmarkerpowerarmor.svg')
        self.pipValueListenerDepth = 1
        self.markerItem.setZValue(0)
        self.setColor(color,False)
        self.setSize(size,False)
        self.setLabelFont(QtGui.QFont("Times", 8, QtGui.QFont.Bold), False)
        self.setLabel('Power Armor', False)
        self.filterVisibleFlag = True
        self.PipVisible = False
        self.doUpdate()
        
    def _getPixmap_(self):
        return self.imageFactory.getPixmap(self.imageFilePath, size=self.size, color=self.color)
    
    @QtCore.pyqtSlot(bool)
    def filterSetVisible(self, value):
        self.filterVisibleFlag = value
        if not value:
            self.setVisible(False)
        elif value and self.PipVisible:
            self.setVisible(True)
            self.doUpdate()
    
    @QtCore.pyqtSlot()        
    def _slotPipValueUpdated(self):
        if self.pipValue:
            self.PipVisible = self.pipValue.child('Visible').value()
            rx = self.pipValue.child('X').value()
            ry = self.pipValue.child('Y').value()
            px = self.mapCoords.pip2map_x(rx)
            py = self.mapCoords.pip2map_y(ry)
            height = self.pipValue.child('Height').value()
            self.markerItem.setToolTip( 'Pos: (' + str(rx) + ', ' + str(ry) + ')\n'
                                        + 'Visible: ' + str(self.PipVisible) + '\n'
                                        + 'Height: ' +str(height) )
            self.setMapPos(px, py, False)
            if self.PipVisible and self.filterVisibleFlag:
                self.setVisible(True)
                self.doUpdate()
            else:
                self.setVisible(False)

class QuestMarker(PipValueMarkerBase):
    def __init__(self, widget, imageFactory, color, size, parent = None):
        super().__init__(widget.mapScene, widget.mapView, parent)
        self.markerType = 3
        self.uid = 'questmarker'
        self.widget = widget
        self.imageFactory = imageFactory
        self.imageFilePath = os.path.join('res', 'mapmarkerquest.svg')
        self.pipValueListenerDepth = 1
        self.QuestFormIds = None
        self.markerItem.setZValue(0)
        self.setColor(color,False)
        self.setSize(size,False)
        self.setLabelFont(QtGui.QFont("Times", 8, QtGui.QFont.Bold), False)
        self.setLabel('Quest Marker', False)
        self.doUpdate()
        
    def _getPixmap_(self):
        return self.imageFactory.getPixmap(self.imageFilePath, size=self.size, color=self.color)
            
    def _updateMarkerOffset_(self):
        mb = self.markerItem.boundingRect()
        self.markerItem.setOffset(-mb.width()/2, -mb.height())
        
    @QtCore.pyqtSlot(int)
    def setSize(self, size, update = True):
        # We want it to be a little bit bigger than the other marker
        super().setSize(size * 1.2, update)
        
    @QtCore.pyqtSlot()        
    def _slotPipValueUpdated(self):
        if self.pipValue:
            self.setVisible(True)
            name = self.pipValue.child('Name').value()
            self.setLabel(name, False)
            rx = self.pipValue.child('X').value()
            ry = self.pipValue.child('Y').value()
            px = self.mapCoords.pip2map_x(rx)
            py = self.mapCoords.pip2map_y(ry)
            height = self.pipValue.child('Height').value()
            tttext =  'Pos: (' + str(rx) + ', ' + str(ry) + ')\n';
            tttext += 'Height: ' +str(height)
            onDoor = self.pipValue.child('OnDoor').value()
            if onDoor != None:
                tttext += '\nOnDoor: ' + str(onDoor)
            shared = self.pipValue.child('Shared').value()
            if shared != None:
                tttext += '\nShared: ' + str(shared)
            self.QuestFormIds = self.pipValue.child('QuestId').value()
            if self.QuestFormIds != None:
                tttext += '\nQuestIds: ['
                isFirst = True
                for q in self.QuestFormIds:
                    if isFirst:
                        isFirst = False
                    else:
                        tttext += ', '
                    tttext += str(q.value())
                tttext += ']'
            self.markerItem.setToolTip( tttext )
            self.setMapPos(px, py)
    
class LocationMarker(PipValueMarkerBase):
    artilleryRange = 97000
    noteOverlayIcon = None
    clearedOverlayIcon = None
    workshopOverlayIcon = None
    
    def __init__(self, widget, imageFactory, imageFactory2, color, size, parent = None):
        super().__init__(widget.mapScene, widget.mapView, parent)
        self.markerType = 4
        self.widget = widget
        self.imageFactory = imageFactory
        self.imageFactory2 = imageFactory2
        self.pipValueListenerDepth = 1
        self.markerItem.setZValue(0)
        self.setColor(color,False)
        self.setSize(size,False)
        self.setLabelFont(QtGui.QFont("Times", 8, QtGui.QFont.Bold), False)
        self.setLabel('Location', False)
        self.locType = -1
        self.noTypePixmapFound = False
        self.discovered = False
        self.lastKnownDiscovered = False
        self.visible = False
        self.cleared = False
        self.filterVisibleFlag = True
        self.filterVisibilityCheatFlag = False
        self.artilleryRangeCircle = None
        self.isOwnedWorkshop = False

        if LocationMarker.noteOverlayIcon is None:
            self._rebuildOverlayIcons()


        self.doUpdate()

    @QtCore.pyqtSlot()
    def _rebuildOverlayIcons(self):
        self.widget._logger.info('LocationMarker: rebuilding overlay icons')
        LocationMarker.noteOverlayIcon = self.imageFactory2.getImage('note8.png')
        ImageFactory.colorizeImage(LocationMarker.noteOverlayIcon, self.color)
        LocationMarker.clearedOverlayIcon = self.imageFactory2.getImage('tick8.png')
        ImageFactory.colorizeImage(LocationMarker.clearedOverlayIcon, self.color)
        LocationMarker.workshopOverlayIcon = self.imageFactory2.getImage('hammer8.png')
        ImageFactory.colorizeImage(LocationMarker.workshopOverlayIcon, self.color)
        super()._rebuildOverlayIcons()


    def updateZIndex(self):
        if hasattr(self.widget, 'mapMarkerZIndexes'):
            if (self.note and len(self.note) > 0):
                if (self.markerItem):
                    self.markerItem.setZValue(self.widget.mapMarkerZIndexes.get('LabelledLocationMarker', 0))
                if (self.labelItem):
                    self.labelItem.setZValue(self.widget.mapMarkerZIndexes.get('LabelledLocationMarker', 0)+1000)
            else:
                super().updateZIndex()
        
        
    def showArtilleryRange(self, value, updateSignal = True):
        idList = self.widget._app.settings.value('globalmapwidget/showArtilleryFormIDs', [])
        if idList == None: # Yes, this happens (because of buggy Linux QSettings implementation)
            idList = []
        if value:
            if self.pipValue and self.pipValue.child('LocationMarkerFormId'):
                id = hex(self.pipValue.child('LocationMarkerFormId').value()).lower()
                if not id in idList:
                    idList.append(id)
            self.artilleryRangeCircle = self.scene.addEllipse(0, 0, 0, 0)
            self.artilleryRangeCircle.setPen(QtGui.QPen(self.color, 2))
            self.positionDirty = True
        else:
            if self.pipValue and self.pipValue.child('LocationMarkerFormId'):
                id = hex(self.pipValue.child('LocationMarkerFormId').value()).lower()
                if id in idList:
                    idList.remove(id)
            if self.artilleryRangeCircle:
                self.scene.removeItem(self.artilleryRangeCircle)
            self.artilleryRangeCircle = None
            self.positionDirty = True
        self.widget._app.settings.setValue('globalmapwidget/showArtilleryFormIDs', idList)
        if updateSignal:
            self.doUpdate()
        
    @QtCore.pyqtSlot()
    def doUpdate(self):
        if self.artilleryRangeCircle:
            if self.isVisible:
                self.artilleryRangeCircle.setVisible(True)
                if self.markerPixmapDirty:
                    self.artilleryRangeCircle.setPen(QtGui.QPen(self.color, 2))
                if self.positionDirty and self.mapCoords:
                    rangeX = self.artilleryRange * self.mapCoords._ax * self.zoomLevel
                    rangeY = self.artilleryRange * self.mapCoords._ay * self.zoomLevel
                    self.artilleryRangeCircle.setRect(self.mapPosX * self.zoomLevel - rangeX/2,
                                                         self.mapPosY * self.zoomLevel - rangeY/2,
                                                         rangeX, rangeY)
            else:
                self.artilleryRangeCircle.setVisible(False)
        super().doUpdate()
            
    def destroy(self):
        if self.artilleryRangeCircle:
            self.scene.removeItem(self.artilleryRangeCircle)
            self.artilleryRangeCircle = None
        super().destroy()
            

    def _getPixmap_(self):
        def _getDefaultPixmap():
            if self.discovered:
                self.imageFilePath = os.path.join('res', 'mapmarkerloctype_default_d.svg')
            else:
                self.imageFilePath = os.path.join('res', 'mapmarkerloctype_default_u.svg')
            return self.imageFactory.getPixmap(self.imageFilePath, size=self.size, color=self.color)
        if not self.locType < 0:
            filepath = 'mapmarkerloctype_' + str(self.locType)
            if self.discovered:
                self.imageFilePath = os.path.join('res', filepath + '_d.svg')
            else:
                self.imageFilePath = os.path.join('res', filepath + '_u.svg')
            p = self.imageFactory.getPixmap(self.imageFilePath, size=self.size, color=self.color)
            if not p:
                self.noTypePixmapFound = True
                p = _getDefaultPixmap()
        else:
            p = _getDefaultPixmap()
        px = QtGui.QPixmap(p.width() + 10, p.height())
        px.fill(QtCore.Qt.transparent)
        pn = QtGui.QPainter(px)
        pn.drawPixmap(QtCore.QRect(0,0,p.width(),p.height()), p)
        overlayXOffset = p.width() + 2
        overlayYOffset = 0
        if (len(self.note) > 0):
            pn.drawImage(QtCore.QRect(overlayXOffset, overlayYOffset, 8, 8), LocationMarker.noteOverlayIcon)
            overlayYOffset += 8+2
        if (self.isOwnedWorkshop):
            pn.drawImage(QtCore.QRect(overlayXOffset, overlayYOffset, 8, 8), LocationMarker.workshopOverlayIcon)
            overlayYOffset += 8+2
        if (self.cleared):
            pn.drawImage(QtCore.QRect(overlayXOffset, overlayYOffset, 8, 8), LocationMarker.clearedOverlayIcon)
            overlayYOffset += 8+2
        pn.end()
        return px
            
    def _updateMarkerOffset_(self):
        mb = self.markerItem.boundingRect()
        self.markerItem.setOffset(-(mb.width()-10)/2, -mb.height()/2)


    @QtCore.pyqtSlot(bool)
    def filterSetVisible(self, value, update = True):
        self.filterVisibleFlag = value
        if not value:
            self.setVisible(False)
        elif value and self.visible:
            self.setVisible(True)
            if update:
                self.doUpdate()
    
    @QtCore.pyqtSlot(bool)
    def filterVisibilityCheat(self, value, update = True):
        self.filterVisibilityCheatFlag = value
        if not self.visible:
            if value:
                self.setVisible(True)
                if update:
                    self.doUpdate()
            else:
                self.setVisible(False)
    
    def setPipValue(self, value, datamanager, mapCoords = None, signal = True):
        super().setPipValue(value, datamanager, mapCoords, signal)
        if self.uid == None and self.pipValue and self.pipValue.child('LocationMarkerFormId'):
            self.uid = hex(self.pipValue.child('LocationMarkerFormId').value()).lower()
        if self.pipValue and self.pipValue.child('LocationMarkerFormId'):
            idList = self.widget._app.settings.value('globalmapwidget/showArtilleryFormIDs', [])
            if idList:
                if hex(self.pipValue.child('LocationMarkerFormId').value()).lower() in idList:
                    self.showArtilleryRange(True, False)
        self.invalidateMarkerPixmap(signal)
        
    @QtCore.pyqtSlot()        
    def _slotPipValueUpdated(self):
        if self.pipValue:
            self.visible = self.pipValue.child('Visible').value()
            name = self.pipValue.child('Name')
            if name:
                self.setLabel(name.value(), False)
            else:
                self.setLabel('<Location>', False)
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
            if self.discovered != self.lastKnownDiscovered:
                self.invalidateMarkerPixmap(False)
            self.lastKnownDiscovered = self.discovered
            rx = self.pipValue.child('X').value()
            ry = self.pipValue.child('Y').value()
            px = self.mapCoords.pip2map_x(rx)
            py = self.mapCoords.pip2map_y(ry)
            tttext = 'Pos: (' + str(rx) + ', ' + str(ry) + ')'
            props = self.pipValue.value()
            for propkey in props:
                if propkey != 'x' and propkey !='y':
                    prop = props[propkey]
                    tttext += '\n' + prop.pipParentKey + ': ' + str(prop.value())
            self.markerItem.setToolTip( tttext )
            if (self.visible or self.filterVisibilityCheatFlag) and self.filterVisibleFlag:
                self.setVisible(True)
                self.markerPixmapDirty = True
                self.setMapPos(px, py)
            else:
                self.setMapPos(px, py, False)
            if (self.pipValue.child('WorkshopOwned')):
                self.isOwnedWorkshop = self.pipValue.child('WorkshopOwned').value()

            
    def _labelStr_(self):
        tmp = self.label
        if self.pipValue:
            workshopOwned = self.pipValue.child('WorkshopOwned')
            if  workshopOwned and workshopOwned.value():
                tmp = textwrap.fill(tmp, 25)
                tmp += '\nPop: ' + str(self.pipValue.child('WorkshopPopulation').value())
                tmp += '   Happ: ' + str(int(self.pipValue.child('WorkshopHappinessPct').value())) + '%'
            elif self.cleared:
                tmp += ' [CLEARED]'
                tmp = textwrap.fill(tmp, 25)
        if self.pipValue:
            if len(self.note) > 0:
                tmp +='\n' + textwrap.fill(self.note, 25)
        return tmp
        
    def _fillMarkerContextMenu_(self, event, menu):
        if self.pipValue:
            @QtCore.pyqtSlot()
            def _fastTravel():
                if QtWidgets.QMessageBox.question(self.view, 'Fast Travel', 
                        'Do you want to travel to ' + self.label + '?') == QtWidgets.QMessageBox.Yes:
                    self.datamanager.rpcFastTravel(self.pipValue)
            menu.addAction('Fast Travel', _fastTravel)
            
            @QtCore.pyqtSlot()
            def _addMarkerNote():
                if(self.uid == None):
                    self.widget._logger.warn('marker has no uid, cannot create note')
                    return
                    
                notestr = self.note
                noteDlg = EditNoteDialog()
                noteDlg.txtNote.setText(notestr)
                noteDlg.lblLocation.setText(self.pipValue.child('Name').value())
                noteDlg.chkCharacterOnly.setText(noteDlg.chkCharacterOnly.text() + '(' +self.widget.characterDataManager.pipPlayerName +')')
                ok = noteDlg.exec_()
                notestr = noteDlg.txtNote.text()
                thisCharOnly = noteDlg.chkCharacterOnly.isChecked()
                noteDlg.show()
            
                if (ok != 0):
                    noteSettingPath = 'globalmapwidget/locationmarkernotes/'
                    if thisCharOnly:
                        noteSettingPath = self.widget.characterDataManager.playerDataPath + '/locationmarkernotes/'

                    if (len(notestr) > 0):
                        self.widget._app.settings.setValue(noteSettingPath+self.uid, notestr)
                        self.setNote(notestr, True)

                        self.widget._app.settings.setValue('globalmapwidget/stickylabels2/'+self.uid, int(True))
                        self.setStickyLabel(True, True)
                    else:
                        self.widget._app.settings.beginGroup(noteSettingPath);
                        self.widget._app.settings.remove(self.uid);
                        self.widget._app.settings.endGroup();
                        self.setNote(notestr, True)

                        self.widget._app.settings.beginGroup('globalmapwidget/stickylabels2/');
                        self.widget._app.settings.remove(self.uid); 
                        self.widget._app.settings.endGroup();
                        self.setStickyLabel(False, True)

            menu.addAction('Add\Edit Note', _addMarkerNote)
            
            if self.pipValue.child('WorkshopOwned'):
                @QtCore.pyqtSlot()
                def _showArtilleryRange():
                    self.showArtilleryRange(self.artilleryRangeCircle == None)
                action = menu.addAction('Artillery Range', _showArtilleryRange)
                action.setCheckable(True)
                action.setChecked(self.artilleryRangeCircle != None)
            
    def _markerDoubleClickEvent_(self, event):
        if self.pipValue:
            if QtWidgets.QMessageBox.question(self.view, 'Fast Travel', 
                    'Do you want to travel to ' + self.label + '?') == QtWidgets.QMessageBox.Yes:
                self.datamanager.rpcFastTravel(self.pipValue)

    @QtCore.pyqtSlot(str)
    def setNote(self, note, update = True):
        self.note = note
        self.labelDirty = True
        self.markerPixmapDirty = True
        self.doUpdate()
        
    def setSavedSettings(self):
        super().setSavedSettings()
        if self.uid != None and self.widget.characterDataManager.playerDataPath != None:

            self.setNote (self.widget._app.settings.value(self.widget.characterDataManager.playerDataPath + '/locationmarkernotes/' + self.uid, ''))
        if self.uid != None and len(self.note) == 0:
            self.setNote (self.widget._app.settings.value('globalmapwidget/locationmarkernotes/'+self.uid, ''))

class PointofInterestMarker(MarkerBase):
    def __init__(self, uid, widget, imageFactory, color, size, iconfile='mapmarkerpoi_1.svg', parent = None):
        super().__init__(widget.mapScene, widget.mapView, parent)
        self.markerType = 5
        self.widget = widget
        self.imageFactory = imageFactory
        self.imageFilePath = iconfile
        self.pipValueListenerDepth = 1
        self.markerItem.setZValue(0)
        self.setColor(color,False)
        self.setSize(size,False)
        self.setLabelFont(QtGui.QFont("Times", 8, QtGui.QFont.Bold), False)
        self.setLabel('Point of Interest Marker', False)
        self.filterVisibleFlag = True
        self.uid = str(uid)
        self.thisCharOnly = True

        self.doUpdate()

    def _labelStr_(self):
        return textwrap.fill(self.label, 25)
        
    def _getPixmap_(self):
        return self.imageFactory.getPixmap(self.imageFilePath, size=self.size, color=self.color)

    def _updateMarkerOffset_(self):
        mb = self.markerItem.boundingRect()
        self.markerItem.setOffset(-mb.width()/2, -mb.height())
        
    @QtCore.pyqtSlot(bool)
    def filterSetVisible(self, value):
        self.filterVisibleFlag = value
        if not value:
            self.setVisible(False)
        elif value :
            self.setVisible(value)
            self.doUpdate()
    
    @QtCore.pyqtSlot()        
    def _slotPipValueUpdated(self):
        self.setSavedSettings()
        return
                
    def _fillMarkerContextMenu_(self, event, menu):
        @QtCore.pyqtSlot()
        def _deletePOIMarker(): 
            self.widget._logger.info ('markertodelete: ' +self.uid)
            poiSettingPath = 'globalmapwidget/pointsofinterest/' 
            if self.thisCharOnly:
                poiSettingPath = self.widget.characterDataManager.playerDataPath + '/pointsofinterest/'

            self.widget._app.settings.beginGroup(poiSettingPath);
            self.widget._app.settings.remove(self.uid); 
            self.widget._app.settings.endGroup();

            index = self.widget._app.settings.value(poiSettingPath+'index', None)
            if index == None: # Yes, this happens (because of buggy Linux QSettings implementation)
                index = []
            if index and len(index) > 0:
                if self.uid in index:
                    index.remove(self.uid)
                    self.widget._app.settings.setValue(poiSettingPath+'index', index)
                    
                    self.widget._app.settings.beginGroup(poiSettingPath+self.uid);
                    self.widget._app.settings.remove(""); 
                    self.widget._app.settings.endGroup();
            
            self.destroy()

        @QtCore.pyqtSlot()
        def _editPOIMarker():
            labelstr = ''
            
            editpoiDialog = EditPOIDialog(self.widget, color=self.color)
            editpoiDialog.txtPOILabel.setText(self.label)
            editpoiDialog.setSelectedIcon(self.imageFilePath)
            editpoiDialog.chkCharacterOnly.setText(editpoiDialog.chkCharacterOnly.text() + '(' +self.widget.characterDataManager.pipPlayerName +')')
            editpoiDialog.chkCharacterOnly.setChecked(self.thisCharOnly)
            editpoiDialog.chkCharacterOnly.setEnabled(False)
            ok = editpoiDialog.exec_()
            labelstr = editpoiDialog.txtPOILabel.text()
            thisCharOnly = editpoiDialog.chkCharacterOnly.isChecked()
            
            editpoiDialog.show()
            
            if (ok != 0):
                poiSettingPath = 'globalmapwidget/pointsofinterest/' 
                if thisCharOnly:
                    poiSettingPath = self.widget.characterDataManager.playerDataPath + '/pointsofinterest/'

                markerKey = self.uid

                self.widget._app.settings.setValue(poiSettingPath+str(markerKey)+'/label', labelstr)
                self.widget._app.settings.setValue(poiSettingPath+str(markerKey)+'/color', editpoiDialog.selectedColor)
                self.widget._app.settings.setValue(poiSettingPath+str(markerKey)+'/icon', editpoiDialog.IconFile)
                self.widget._app.settings.sync()
                self.setSavedSettings()
                    
        
        menu.addAction('Edit POI Marker', _editPOIMarker)
        menu.addAction('Delete POI Marker', _deletePOIMarker)
        
    def setSavedSettings(self):
        poiSettingPath = 'globalmapwidget/pointsofinterest/'
        if self.thisCharOnly:
            poiSettingPath = self.widget.characterDataManager.playerDataPath + '/pointsofinterest/'

        label = self.widget._app.settings.value(poiSettingPath+str(self.uid)+'/label', '')
        self.imageFilePath = self.widget._app.settings.value(poiSettingPath+str(self.uid)+'/icon', 'mapmarkerpoi_1.svg')
        worldx = float(self.widget._app.settings.value(poiSettingPath+str(self.uid)+'/worldx', 0.0))
        worldy = float(self.widget._app.settings.value(poiSettingPath+str(self.uid)+'/worldy', 0.0))
        color = self.widget._app.settings.value(poiSettingPath+str(self.uid)+'/color', None)
        if (color != None):
            self.setColor(color, True)

        self.setMapPos(self.widget.mapCoords.pip2map_x(worldx), self.widget.mapCoords.pip2map_y(worldy))
        self.setLabel(label)
        self.invalidateMarkerPixmap()
        super().setSavedSettings()

class CollectableMarker(MarkerBase):
    def __init__(self, uid, widget, imageFactory, color, size, parent = None, icon='StarFilled.svg'):
        super().__init__(widget.mapScene, widget.mapView, parent)
        self.markerType = 6
        self.widget = widget
        self.imageFactory = imageFactory
        self.imageFilePath = os.path.join(icon)
        self.markerItem.setZValue(0)
        self.setColor(color,False)
        self.setSize(size, False)
        if self.color is not None:
            self.uncollectedColor = QtGui.QColor.fromRgb(self.color.red(), self.color.green(), self.color.blue())
            self.collectedColor = self.color.darker(200)
        self.setLabelFont(QtGui.QFont("Times", 8, QtGui.QFont.Bold), False)
        self.setLabel('Collectable Marker', False)
        self.filterVisibleFlag = True
        self.uid = uid
        self.collected = False
        self.itemFormID = None
        self.collectedOverlayIcon = None
        self._rebuildOverlayIcons()
        self.doUpdate()

    @QtCore.pyqtSlot()
    def _rebuildOverlayIcons(self):
        #self.widget._logger.info('CollectableMarker: rebuilding overlay icons')
        self.collectedOverlayIcon = self.imageFactory.getImage('tick8.png')
        ImageFactory.colorizeImage(self.collectedOverlayIcon, self.collectedColor)
        super()._rebuildOverlayIcons()

    def _labelStr_(self):
        if(self.collected):
            return self.label + '\n[Collected]'
        else:
            return self.label

    def updateZIndex(self):
        if hasattr(self.widget, 'mapMarkerZIndexes'):
            if (self.collected):
                if (self.markerItem):
                    self.markerItem.setZValue(self.widget.mapMarkerZIndexes.get('CollectedCollectableMarker', 0))
                if (self.labelItem):
                    self.labelItem.setZValue(self.widget.mapMarkerZIndexes.get('CollectedCollectableMarker', 0)+1000)
            else:
                super().updateZIndex()

    def _getPixmap_(self):
        p = self.imageFactory.getPixmap(self.imageFilePath, size=self.size, color=self.color)

        px = QtGui.QPixmap(p.width() + 10, p.height())
        px.fill(QtCore.Qt.transparent)
        pn = QtGui.QPainter(px)
        pn.drawPixmap(QtCore.QRect(0,0,p.width(),p.height()), p)
        overlayXOffset = p.width() + 2
        overlayYOffset = 0
        if (self.collected):
            pn.drawImage(QtCore.QRect(overlayXOffset, overlayYOffset, 8, 8), self.collectedOverlayIcon)
            overlayYOffset += 8+2
        pn.end()
        return px
        
    @QtCore.pyqtSlot(int)
    def setSize(self, size, update = True):
        # We want it to be a little bit smaller than the other marker
        super().setSize(size * 0.8, update)

        
    @QtCore.pyqtSlot(bool)
    def setCollected(self, value):
        if self.collected != value:
            self.collected = value
            if value:
                if self.collectedColor is not None:
                    self.color = self.collectedColor
            else:
                if self.uncollectedColor is not None:
                    self.color = self.uncollectedColor
            self.markerPixmapDirty = True
            self.labelDirty = True
            self.doUpdate()

    @QtCore.pyqtSlot(bool)
    def filterSetVisible(self, value):
        self.filterVisibleFlag = value
        if not value:
            self.setVisible(False)
        elif value :
            self.setVisible(value)
            self.doUpdate()        
    @QtCore.pyqtSlot()        
    def _slotPipValueUpdated(self):
        return

    def _fillMarkerContextMenu_(self, event, menu):
        @QtCore.pyqtSlot(bool)
        def _markAsCollected(value):
            if self.itemFormID != None:
                collectedcollectablesSettingsPath =\
                    self.widget.characterDataManager.playerDataPath + self.widget.characterDataManager.collectedcollectablesuffix
                index = self.widget._app.settings.value(collectedcollectablesSettingsPath, None)
                if index == None:
                    index = []
                tmp = str(int(self.itemFormID,16))
                if (value):
                    if tmp not in index:
                        index = list(set(index)) # remove duplicates
                        index.append(tmp)
                        self.widget._app.settings.setValue(collectedcollectablesSettingsPath, index)
                else:
                    if tmp in index:
                        index = list(set(index)) # remove duplicates
                        index.remove(tmp)
                        self.widget._app.settings.setValue(collectedcollectablesSettingsPath, index)
            self.setCollected(value)
        ftaction = menu.addAction('Mark as Collected')
        ftaction.triggered.connect(_markAsCollected)
        ftaction.setCheckable(True)
        ftaction.setChecked(self.collected)

    def setSavedSettings(self):
        if self.widget.characterDataManager.playerDataPath and self.widget.characterDataManager.collectedcollectablesuffix:
            collectedcollectablesSettingsPath =\
                self.widget.characterDataManager.playerDataPath + self.widget.characterDataManager.collectedcollectablesuffix
            index = self.widget._app.settings.value(collectedcollectablesSettingsPath, None)
            if index == None:
                index = []
    
            if index and len(index) > 0:
                if str(int(self.itemFormID,16)) in index:
                    self.setCollected(True)

        super().setSavedSettings()

class MapGraphicsItem(QtCore.QObject):
    
    class PixmapItem(QtWidgets.QGraphicsPixmapItem):
        def __init__(self, parent, qparent = None):
            super().__init__(qparent)
            self.parent = parent

    def __init__(self, gwidget, imageFactory, color = None, qparent = None):
        super().__init__(qparent)
        self.gwidget = gwidget
        self.imageFactory = imageFactory
        self.mapfile = None
        self.color = color
        self.colorable = True
        self.nw = None
        self.ne = None
        self.sw = None
        self.mapItem = self.PixmapItem(self)
        self.gwidget.mapScene.addItem(self.mapItem)
        self.mapItem.setZValue(-10)
    
    def setMapFile(self, mapfile, colorable = True, nw = [52, 52], ne = [1990, 52], sw = [52, 1990]):
        self.mapfile = mapfile
        self.colorable = colorable
        self.nw = nw
        self.ne = ne
        self.sw = sw
        if colorable:
            self._setMapPixmap(self.imageFactory.getPixmap(self.mapfile, color = self.color))
        else:
            self._setMapPixmap(self.imageFactory.getPixmap(self.mapfile, color = None))
        
    
    def _setMapPixmap(self, pixmap):
        self.mapItem.setPixmap(pixmap)
        self.gwidget.mapScene.setSceneRect(self.mapItem.sceneBoundingRect())
    
    @QtCore.pyqtSlot(float, float, float)
    def setZoomLevel(self, zoom, mapposx, mapposy):
        self.mapItem.setTransform(QtGui.QTransform.fromScale(zoom, zoom))
        self.gwidget.mapScene.setSceneRect(self.mapItem.sceneBoundingRect())
        if mapposx >= 0 and mapposy >=0:
            self.gwidget.mapView.centerOn(mapposx * zoom, mapposy * zoom)
    
    @QtCore.pyqtSlot(QtGui.QColor)
    def setColor(self, color):
        self.color = color
        if self.colorable:
            self._setMapPixmap(self.imageFactory.getPixmap(self.mapfile, color = color))



class GlobalMapWidget(widgets.WidgetBase):
    
    signalSetZoomLevel = QtCore.pyqtSignal(float, float, float)
    signalSetColor = QtCore.pyqtSignal(QtGui.QColor)
    signalSetMarkerSize = QtCore.pyqtSignal(int)
    signalSetStickyLabel = QtCore.pyqtSignal(bool)
    signalLocationFilterSetVisible = QtCore.pyqtSignal(bool)
    signalLocationFilterVisibilityCheat = QtCore.pyqtSignal(bool)
    signalMarkerForcePipValueUpdate = QtCore.pyqtSignal()

    
    _signalPipWorldQuestsUpdated = QtCore.pyqtSignal()
    _signalPipWorldLocationsUpdated = QtCore.pyqtSignal()
    
    MAPZOOM_SCALE_MAX = 4.0
    MAPZOOM_SCALE_MIN = 0.05
    
    MAP_NWX = -135168
    MAP_NWY = 102400
    MAP_NEX = 114688
    MAP_NEY = 102400
    MAP_SWX = -135168
    MAP_SWY = -147456
  
    def __init__(self, handle, controller, parent):
        super().__init__('Global Map', parent)
        self.basepath = handle.basepath
        self.controller = controller
        self.widget = uic.loadUi(os.path.join(self.basepath, 'ui', 'globalmapwidget.ui'))
        self.setWidget(self.widget)
        self._logger = logging.getLogger('pypipboyapp.map.globalmap')
        self.mapZoomLevel = 1.0
        self.characterDataManager = None
        self.collectablesNearPlayer = []
        self.collectableNearSoundEffects = {}
        self.collectableNearUpdateTimer = QtCore.QTimer()


    def iwcSetup(self, app):
        app.iwcRegisterEndpoint('globalmapwidget', self)
    
    def init(self, app, datamanager):
        super().init(app, datamanager)
        self._app = app

        # Init Collectables
        self.showCollectables = {}
        self.collectableBtnGroups = []
        self.collectableLocationMarkers = dict()
        self.collectableDefs = self._loadCollectablesDefinitionsFromJson()
        self.characterDataManager = CharacterDataManager()
        self.characterDataManager.init(app, datamanager, self.collectableDefs)
        self._addCollectablesControls(self.collectableDefs)

        self.collectableNearUpdateFPS = 1
        self.collectableNearUpdateTimer.setInterval(int(1000/self.collectableNearUpdateFPS))
        self.collectableNearUpdateTimer.timeout.connect(self.updateCollectableVisibility)
        self.collectableNearUpdateTimer.start()

        # Read maps config file
        try:
            configFile = open(os.path.join(self.basepath, 'res', 'globalmapsconfig.json'))
            self.mapFiles = json.load(configFile)
        except Exception as e:
            self._logger.error('Could not load map-files: ' + str(e))
        self.mapMarkerSize = int(self._app.settings.value('globalmapwidget/mapMarkerSize', 28))
        self.selectedMapFile = self._app.settings.value('globalmapwidget/selectedMapFile', 'default')
        # Init graphics view
        self.mapColor = QtGui.QColor.fromRgb(20,255,23)
        self.mapScene = QtWidgets.QGraphicsScene()
        self.mapScene.setBackgroundBrush(QtGui.QBrush(QtGui.QColor.fromRgb(0,0,0)))
        self.mapView = self.widget.mapGraphicsView
        self.mapView.viewport().installEventFilter(self)
        self.mapView.setScene(self.mapScene)
        self.mapView.setMouseTracking(True)
        self.mapView.centerOn(0, 0)
        # Add map graphics
        if self._app.settings.value('globalmapwidget/colour'):
            self.mapColor = self._app.settings.value('globalmapwidget/colour')
        self.mapItem = MapGraphicsItem(self, self.controller.imageFactory, self.mapColor)
        try:
            mapfile = self.mapFiles[self.selectedMapFile]
        except Exception as e:
            self._logger.error('Could not find map "' + self.selectedMapFile + '": ' + str(e))
            self.selectedMapFile = 'default'
            self._app.settings.setValue('globalmapwidget/selectedMapFile', self.selectedMapFile)
            mapfile = self.mapFiles[self.selectedMapFile]
        file = os.path.join('res', mapfile['file'])
        self.mapItem.setMapFile(file, mapfile['colorable'], mapfile['nw'], mapfile['ne'], mapfile['sw'])
        self.signalSetZoomLevel.connect(self.mapItem.setZoomLevel)
        self.signalSetColor.connect(self.mapItem.setColor)
        #Define ZOrder of different types of marker
        self.mapMarkerZIndexes = {}
        self.mapMarkerZIndexes[str(PlayerMarker)] = 100
        self.mapMarkerZIndexes[str(CustomMarker)] = 90
        self.mapMarkerZIndexes[str(QuestMarker)] = 80
        self.mapMarkerZIndexes[str(PowerArmorMarker)] = 70
        self.mapMarkerZIndexes[str(PointofInterestMarker)] = 60
        self.mapMarkerZIndexes['LabelledLocationMarker'] = 50
        self.mapMarkerZIndexes[str(CollectableMarker)] = 40
        self.mapMarkerZIndexes[str(LocationMarker)] = 30
        self.mapMarkerZIndexes[str(MarkerBase)] = 10
        self.mapMarkerZIndexes['CollectedCollectableMarker'] = 0

        # Add player marker
        self.playerMarker = PlayerMarker(self,self.controller.imageFactory, self.mapColor, self.mapMarkerSize)
        self._connectMarker(self.playerMarker)
        self.playerMarker.signalPlayerPositionUpdate.connect(self._slotPlayerMarkerPositionUpdated)
        # Add custom marker
        self.customMarker = CustomMarker(self,self.controller.imageFactory, self.mapColor, self.mapMarkerSize)
        self._connectMarker(self.customMarker)
        # Add powerarmor marker
        self.powerArmorMarker = PowerArmorMarker(self,self.controller.imageFactory, self.mapColor, self.mapMarkerSize)
        self._connectMarker(self.powerArmorMarker)
        # Init zoom slider
        self.widget.mapZoomSlider.setMinimum(-100)
        self.widget.mapZoomSlider.setMaximum(100)
        self.widget.mapZoomSlider.setValue(0)
        self.widget.mapZoomSlider.setSingleStep(5)
        self.widget.mapZoomSlider.valueChanged.connect(self._slotZoomSliderTriggered)
        self.widget.markerSizeSlider.valueChanged.connect(self._slotMarkerSizeSliderTriggered)
        self.widget.markerSizeSpinbox.valueChanged.connect(self._slotMarkerSizeSpinboxTriggered)
        # Init zoom Spinbox
        self.widget.mapZoomSpinbox.setMinimum(self.MAPZOOM_SCALE_MIN*100.0)
        self.widget.mapZoomSpinbox.setMaximum(self.MAPZOOM_SCALE_MAX*100.0)
        self.widget.mapZoomSpinbox.setValue(100.0)
        self.widget.mapZoomSpinbox.setSingleStep(10.0)
        self.widget.mapZoomSpinbox.valueChanged.connect(self._slotZoomSpinTriggered)
        self.signalSetZoomLevel.connect(self.saveZoom)
        if (self._app.settings.value('globalmapwidget/zoom')):
            self.mapZoomLevel = float(self._app.settings.value('globalmapwidget/zoom'))
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
        #Init Location MArker size spinbox and slider
        self.widget.markerSizeSlider.setValue(self.mapMarkerSize)
        self.widget.markerSizeSpinbox.setValue(self.mapMarkerSize)
        # Init map file combo box
        i = 0
        self.mapFileComboItems = []
        for mf in self.mapFiles:
            self.widget.mapFileComboBox.addItem(self.mapFiles[mf]['label'])
            if mf == self.selectedMapFile:
                self.widget.mapFileComboBox.setCurrentIndex(i)
            i += 1
            self.mapFileComboItems.append(mf)
        self.widget.mapFileComboBox.currentIndexChanged.connect(self._slotMapFileComboTriggered)
        # Init color controls
        self.widget.mapColorButton.clicked.connect(self._slotMapColorSelectionTriggered)
        try:
            self.widget.mapColorAutoToggle.setChecked(bool(int(self._app.settings.value('globalmapwidget/autoColour', 0))))
        except ValueError:
            self.widget.mapColorAutoToggle.setChecked(bool(self._app.settings.value('globalmapwidget/autoColour', False)))
        #self.widget.mapColorAutoToggle.setChecked(False)
        
        self.widget.mapColorAutoToggle.stateChanged.connect(self._slotMapColorAutoModeTriggered)
        # Init stickyLabels Checkbox
        self.stickyLabelsEnabled = False
        self.widget.stickyLabelsCheckbox.stateChanged.connect(self._slotStickyLabelsTriggered)
        self.widget.stickyLabelsCheckbox.setChecked(bool(int(self._app.settings.value('globalmapwidget/stickyLabels', 0))))
        # Init PowerMarker Enable Checkbox
        self.widget.powerMarkerEnableCheckbox.stateChanged.connect(self._slotPowerMarkerEnableTriggered)
        self.widget.powerMarkerEnableCheckbox.setChecked(bool(int(self._app.settings.value('globalmapwidget/powerArmourMarker', 1))))
        # Init Location Enable Checkbox
        self.locationFilterEnableFlag = True
        self.widget.locationMarkerEnableCheckbox.stateChanged.connect(self._slotLocationEnableTriggered)
        self.widget.locationMarkerEnableCheckbox.setChecked(bool(int(self._app.settings.value('globalmapwidget/locationMarker', 1))))
        # Init Location Visibility Cheat Checkbox
        self.locationVisibilityCheatFlag = False
        self.widget.locationVisibilityCheatCheckbox.stateChanged.connect(self._slotLocationVisibilityCheatTriggered)
        self.widget.locationVisibilityCheatCheckbox.setChecked(bool(int(self._app.settings.value('globalmapwidget/locationVisibilityCheat', 0))))
        # Init CenterOnPlayer checkbox
        self.centerOnPlayerEnabled = False
        self.widget.centerPlayerCheckbox.stateChanged.connect(self._slotCenterOnPlayerCheckToggled)
        self.widget.centerPlayerCheckbox.setChecked(bool(int(self._app.settings.value('globalmapwidget/centerPlayer', 0))))
        # Init SaveTo Button
        self.widget.saveToButton.clicked.connect(self._slotSaveToTriggered)
        # Init Splitter
        settings.setSplitterState(self.widget.splitter, self._app.settings.value('globalmapwidget/splitterState', None))
        self.widget.splitter.splitterMoved.connect(self._slotSplitterMoved)
        # Init Toolbox
        tbCurrent = self._app.settings.value('globalmapwidget/toolboxCurrentIndex', None)
        if tbCurrent:
            self.widget.toolBox.setCurrentIndex(int(tbCurrent))
        self.widget.toolBox.currentChanged.connect(self._slotToolboxCurrentChanged)
        # Init PyPipboy stuff
        from .controller import MapCoordinates
        self.mapCoords = MapCoordinates()
        self.datamanager = datamanager
        self.pipMapObject = None
        self.pipMapWorldObject = None
        self.pipColor = None
        self.pipWorldQuests = None
        self.pipMapQuestsItems = dict()
        self.pipWorldLocations = None
        self.pipMapLocationItems = dict()
        self.poiLocationItems = dict()

        self._signalPipWorldQuestsUpdated.connect(self._slotPipWorldQuestsUpdated)
        self._signalPipWorldLocationsUpdated.connect(self._slotPipWorldLocationsUpdated)
        self.datamanager.registerRootObjectListener(self._onRootObjectEvent)
        
    def getMenuCategory(self):
        return 'Map && Locations'

    def _loadCollectablesDefinitionsFromJson(self):
        self._logger.info('Loading CollectableMarkers from JSON')
        inputFile = open(os.path.join('widgets', 'shared', 'res', 'collectables-processed.json'))
        collectables = json.load(inputFile, object_pairs_hook=OrderedDict)

        for k in collectables.keys():
            self.collectableNearSoundEffects[k] = QtMultimedia.QSoundEffect()
            self.collectableNearSoundEffects[k].setSource(QtCore.QUrl.fromLocalFile(os.path.join(self.basepath, 'res', k+'.wav')))
            self.collectableNearSoundEffects[k].setVolume(0.25)
            self.collectableNearSoundEffects[k].setLoopCount(1)


        return collectables

    @QtCore.pyqtSlot(float, float, float)
    def saveZoom(self, zoom, mapposx, mapposy):
        self._app.settings.setValue('globalmapwidget/zoom', zoom)

    
    @QtCore.pyqtSlot(int, int)
    def _slotSplitterMoved(self, pos, index):
        self._app.settings.setValue('globalmapwidget/splitterState', settings.getSplitterState(self.widget.splitter))
    
    @QtCore.pyqtSlot(int)
    def _slotToolboxCurrentChanged(self, index):
        self._app.settings.setValue('globalmapwidget/toolboxCurrentIndex', index)
        
    def _connectMarker(self, marker):
        self.signalSetZoomLevel.connect(marker.setZoomLevel)
        if marker.markerType != 5 and marker.markerType != 6: # POIs and Collectables
            self.signalSetColor.connect(marker.setColor)
        self.signalSetStickyLabel.connect(marker.setStickyLabel)
        self.signalMarkerForcePipValueUpdate.connect(marker._slotPipValueUpdated)
        marker.signalMarkerDestroyed.connect(self._disconnectMarker)
        self.signalSetMarkerSize.connect(marker.setSize)
        if marker.markerType == 4: # Locations
            self.signalLocationFilterSetVisible.connect(marker.filterSetVisible)
            self.signalLocationFilterVisibilityCheat.connect(marker.filterVisibilityCheat)
        
    @QtCore.pyqtSlot(QtCore.QObject)
    def _disconnectMarker(self, marker):
        marker.signalMarkerDestroyed.disconnect(self._disconnectMarker)
        self.signalSetZoomLevel.disconnect(marker.setZoomLevel)
        self.signalSetStickyLabel.disconnect(marker.setStickyLabel)
        if marker.markerType != 5 and marker.markerType != 6: # POIs and Collectables
            self.signalSetColor.disconnect(marker.setColor)
        self.signalMarkerForcePipValueUpdate.disconnect(marker._slotPipValueUpdated)
        self.signalSetMarkerSize.disconnect(marker.setSize)
        if marker.markerType == 4: # Locations
            self.signalLocationFilterSetVisible.disconnect(marker.filterSetVisible)
            self.signalLocationFilterVisibilityCheat.disconnect(marker.filterVisibilityCheat)

    def _onRootObjectEvent(self, rootObject):
        self.pipMapObject = rootObject.child('Map')
        if self.pipMapObject:
            self.pipMapObject.registerValueUpdatedListener(self._onPipMapReset)
            self._onPipMapReset(None, None, None)

    def _onPipMapReset(self, caller, value, pathObjs):
        self.pipMapWorldObject = self.pipMapObject.child('World')
        if self.pipMapWorldObject:
            self.mapCoords.init( 
                    self.MAP_NWX, self.MAP_NWY, 
                    self.MAP_NEX,  self.MAP_NEY, 
                    self.MAP_SWX, self.MAP_SWY, 
                    self.mapItem.nw[0], self.mapItem.nw[1], 
                    self.mapItem.ne[0], self.mapItem.ne[1], 
                    self.mapItem.sw[0], self.mapItem.sw[1] )
            if self.widget.mapColorAutoToggle.isChecked():
                self._slotMapColorAutoModeTriggered(True)
            pipWorldPlayer = self.pipMapWorldObject.child('Player')
            if pipWorldPlayer:
                self.playerMarker.setPipValue(pipWorldPlayer, self.datamanager, self.mapCoords)
                self.playerMarker.setSavedSettings()
            pipWorldCustom = self.pipMapWorldObject.child('Custom')
            if pipWorldCustom:
                self.customMarker.setPipValue(pipWorldCustom, self.datamanager, self.mapCoords)
                self.customMarker.setSavedSettings()
            pipWorldPower = self.pipMapWorldObject.child('PowerArmor')
            if pipWorldPower:
                self.powerArmorMarker.setPipValue(pipWorldPower, self.datamanager, self.mapCoords)
                self.powerArmorMarker.setSavedSettings()
            self.pipWorldQuests = self.pipMapWorldObject.child('Quests')
            if self.pipWorldQuests:
                self.pipWorldQuests.registerValueUpdatedListener(self._onPipWorldQuestsUpdated, 0)
                self._signalPipWorldQuestsUpdated.emit()
            self.pipWorldLocations = self.pipMapWorldObject.child('Locations')
            if self.pipWorldLocations:
                self.pipWorldLocations.registerValueUpdatedListener(self._onPipWorldLocationsUpdated, 0)
                self._signalPipWorldLocationsUpdated.emit()

    def _addCollectablesControls(self, collectabledefs):
        for k, v in collectabledefs.items():
            btngrp = self._findCollectableButtonGroup('collectable_showcollected_' + k )

            showCollected = int(self._app.settings.value('globalmapwidget/collectable_showcollected_' + k, 0))
            showUncollected = int(self._app.settings.value('globalmapwidget/collectable_showuncollected_' + k, 0))
            alertUncollected = bool(int(self._app.settings.value('globalmapwidget/collectable_alertuncollected_' + k, 0)))
            collectableVRange = int(self._app.settings.value('globalmapwidget/collectable_vrange_' + k, 100))
            collectableARange = int(self._app.settings.value('globalmapwidget/collectable_arange_' + k, 50))

            if btngrp is None:
                groupBox = QtWidgets.QGroupBox()
                groupBox.setTitle(v.get('friendlyname', k))

                collectedLbl = QtWidgets.QLabel('Collected')
                alwaysShowCollected = QtWidgets.QRadioButton('Always')
                neverShowCollected = QtWidgets.QRadioButton('Never')
                nearShowCollected = QtWidgets.QRadioButton('Nearby')

                collectedLayout = QtWidgets.QVBoxLayout()
                collectedLayout.addWidget(collectedLbl)
                collectedLayout.addWidget(alwaysShowCollected)
                collectedLayout.addWidget(neverShowCollected)
                collectedLayout.addWidget(nearShowCollected)
                collectedLayout.addStretch()

                collectedBtnGroup = QtWidgets.QButtonGroup(self)
                collectedBtnGroup.setObjectName('collectable_showcollected_' + k)
                collectedBtnGroup.addButton(alwaysShowCollected,1)
                collectedBtnGroup.addButton(neverShowCollected,0)
                collectedBtnGroup.addButton(nearShowCollected,2)
                self.collectableBtnGroups.append(collectedBtnGroup)
                collectedBtnGroup.buttonClicked[int].connect(self._showCollectableBtnGroupClicked)
                collectedBtnGroup.button(showCollected).setChecked(True)


                uncollectedLbl = QtWidgets.QLabel('Uncollected')
                alwaysShowUncollected = QtWidgets.QRadioButton('Always')
                neverShowUncollected = QtWidgets.QRadioButton('Never')
                nearShowUncollected = QtWidgets.QRadioButton('Nearby')
                uncollectedLayout = QtWidgets.QVBoxLayout()
                uncollectedLayout.addWidget(uncollectedLbl)
                uncollectedLayout.addWidget(alwaysShowUncollected)
                uncollectedLayout.addWidget(neverShowUncollected)
                uncollectedLayout.addWidget(nearShowUncollected)
                uncollectedLayout.addStretch()

                uncollectedBtnGroup = QtWidgets.QButtonGroup(self)
                uncollectedBtnGroup.setObjectName('collectable_showuncollected_' + k)
                uncollectedBtnGroup.addButton(alwaysShowUncollected,1)
                uncollectedBtnGroup.addButton(neverShowUncollected,0)
                uncollectedBtnGroup.addButton(nearShowUncollected,2)
                self.collectableBtnGroups.append(uncollectedBtnGroup)
                uncollectedBtnGroup.buttonClicked[int].connect(self._showCollectableBtnGroupClicked)
                uncollectedBtnGroup.button(showUncollected).setChecked(True)

                uncollectedVisualRange = QtWidgets.QSpinBox()
                uncollectedVisualRange.setPrefix('Visual Range ')
                uncollectedVisualRange.setObjectName('collectable_vrange_' + k)
                uncollectedVisualRange.setRange(0, 500)
                uncollectedVisualRange.setSingleStep(10)
                uncollectedVisualRange.setValue(collectableVRange)
                uncollectedVisualRange.valueChanged[int].connect(self._vrangeCollectableUpdated)


                uncollectedAubiblealert = QtWidgets.QCheckBox('Audible alert near uncollected')
                uncollectedAubiblealert.setObjectName('collectable_alertuncollected_' + k)
                uncollectedAubiblealert.setChecked(alertUncollected)
                uncollectedAubiblealert.stateChanged.connect(self._audibleAlertCollectableStateChanged)

                uncollectedAudibleRange = QtWidgets.QSpinBox()
                uncollectedAudibleRange.setPrefix('Audible Range ')
                uncollectedAudibleRange.setObjectName('collectable_arange_' + k)
                uncollectedAudibleRange.setRange(0, 500)
                uncollectedAudibleRange.setSingleStep(10)
                uncollectedAudibleRange.setValue(collectableARange)
                uncollectedAudibleRange.valueChanged[int].connect(self._arangeCollectableUpdated)



                groupBoxLayout = QtWidgets.QVBoxLayout()
                groupBoxHLayout = QtWidgets.QHBoxLayout()
                groupBoxHLayout.addLayout(uncollectedLayout)
                groupBoxHLayout.addLayout(collectedLayout)
                groupBoxLayout.addLayout(groupBoxHLayout)
                groupBoxLayout.addWidget(uncollectedVisualRange)
                groupBoxLayout.addWidget(uncollectedAubiblealert)
                groupBoxLayout.addWidget(uncollectedAudibleRange)
                groupBox.setLayout(groupBoxLayout)
                self.widget.CollectablesLayout.addWidget(groupBox)

    def _findCollectableButtonGroup(self, objectname):
        for i in self.collectableBtnGroups:
            if i.objectName() == objectname:
                return i
        return None

    @QtCore.pyqtSlot(int)
    def _arangeCollectableUpdated(self, val):
        sender = self.sender()
        sendername = str(sender.objectName())
        self._logger.info(sendername + str(val))
        self._app.settings.setValue('globalmapwidget/' + sendername, val)
        self.updateCollectableVisibility()

    @QtCore.pyqtSlot(int)
    def _vrangeCollectableUpdated(self, val):
        sender = self.sender()
        sendername = str(sender.objectName())
        self._logger.info(sendername + str(val))
        self._app.settings.setValue('globalmapwidget/' + sendername, val)
        self.updateCollectableVisibility(playAudibleAlerts=False)

    @QtCore.pyqtSlot(int)
    def _audibleAlertCollectableStateChanged(self, val):
        sender = self.sender()
        sendername = str(sender.objectName())
        self._logger.info(sendername + str(val))
        self._app.settings.setValue('globalmapwidget/' + sendername, val)
        self.updateCollectableVisibility()

    @QtCore.pyqtSlot(int)
    def _showCollectableBtnGroupClicked(self, val):
        sender = self.sender()
        sendername = str(sender.objectName())
        self._logger.info(sendername + str(val))
        self._app.settings.setValue('globalmapwidget/' + sendername, val)
        self.updateCollectableVisibility(playAudibleAlerts=False)

    def _onPipWorldQuestsUpdated(self, caller, value, pathObjs):
        self._signalPipWorldQuestsUpdated.emit()
        
    @QtCore.pyqtSlot() 
    def _slotPipWorldQuestsUpdated(self):
        newDict = dict()
        for q in self.pipWorldQuests.value():
            if q.pipId in self.pipMapQuestsItems:
                marker = self.pipMapQuestsItems[q.pipId]
                newDict[q.pipId] = marker
                del self.pipMapQuestsItems[q.pipId]
            else:
                marker = QuestMarker(self,self.controller.imageFactory, self.mapColor, self.mapMarkerSize)
                self._connectMarker(marker)
                marker.setStickyLabel(self.stickyLabelsEnabled, False)
                marker.setZoomLevel(self.mapZoomLevel, 0.0, 0.0, False)
                marker.setPipValue(q, self.datamanager, self.mapCoords)
                marker.setSavedSettings()
                newDict[q.pipId] = marker
        for i in self.pipMapQuestsItems:
            self.pipMapQuestsItems[i].destroy()
        self.pipMapQuestsItems = newDict
                    
    def _onPipWorldLocationsUpdated(self, caller, value, pathObjs):
        self._signalPipWorldLocationsUpdated.emit()

    @QtCore.pyqtSlot() 
    def _slotPipWorldLocationsUpdated(self):
        self._createLocationMarkers()
        self._createPOIMarkers()
        self._createCollectablesMarkers(self.collectableDefs)

        self._signalPipWorldQuestsUpdated.emit()

    def _createCollectablesMarkers(self, collectableDefs, reset=False):
        self._logger.info('creating CollectableMarkers')
        if reset:
            self.collectablesNearPlayer = []


        for catKey, catData in collectableDefs.items():
            if catKey not in self.collectableLocationMarkers.keys():
                self.collectableLocationMarkers[catKey] = {}

            iconcolor = self.mapColor
            color = catData.get('color', None)
            if color is not None and len(color) == 3:
                iconcolor = QtGui.QColor(int(color[0]), int(color[1]), int(color[2]))

            newDict = dict()

            for collectable in catData.get('items'):
                if collectable.get('instanceid', None) in self.collectableLocationMarkers[catKey].keys() and not reset:
                    marker = self.collectableLocationMarkers[catKey][collectable.get('instanceid', None)]
                    self._logger.info ('reused marker '+ str(collectable.get('instanceid', None)))
                    newDict[collectable.get('instanceid', None)] = marker
                    del self.collectableLocationMarkers[catKey][collectable.get('instanceid', None)]
                else:
                    cmx = collectable.get('commonwealthx', None)
                    cmy = collectable.get('commonwealthy', None)
                    if cmx is not None and cmy is not None:
                        marker = CollectableMarker(collectable.get('instanceid', None), self, self.controller.sharedResImageFactory, iconcolor, self.mapMarkerSize, icon=catData.get('icon', 'Starfilled.svg'))
                        marker.setLabel(textwrap.fill(collectable.get('name', ''), 30) + '\n' + textwrap.fill(collectable.get('description', ''), 30))
                        marker.itemFormID = collectable.get('formid')
                        marker.setMapPos(self.mapCoords.pip2map_x(float(cmx)), self.mapCoords.pip2map_y(float(cmy)))
                        marker.setZoomLevel(self.mapZoomLevel, 0.0, 0.0, True)
                        marker.setSavedSettings()
                        self._connectMarker(marker)

                        newDict[collectable.get('instanceid', None)] = marker

            for instanceID, marker in self.collectableLocationMarkers[catKey].items():
                marker.destroy()
            self.collectableLocationMarkers[catKey] = newDict
            self.updateCollectableVisibility(playAudibleAlerts=False)

        return

    def _createPOIMarkers(self):
        poiLocDict = dict()

        globalPoisettingPath = 'globalmapwidget/pointsofinterest/'
        index = self._app.settings.value(globalPoisettingPath+'index', None)
        if index and len(index) > 0:
            for i in index:
                if str(i) in self.poiLocationItems.keys():
                    marker = self.poiLocationItems[str(i)]
                    poiLocDict[str(i)] = marker
                    del self.poiLocationItems[str(i)]
                else:
                    marker = PointofInterestMarker(i,self,self.controller.sharedResImageFactory, self.mapColor, self.mapMarkerSize)
                    marker.thisCharOnly = False
                    marker.setSavedSettings()
                    marker.filterSetVisible(True)
                    marker.setZoomLevel(self.mapZoomLevel, 0.0, 0.0, True)
                    self._connectMarker(marker)
                    poiLocDict[str(i)] = marker

        if self.characterDataManager.playerDataPath is not None:
            playerPoiSettingPath = self.characterDataManager.playerDataPath + '/pointsofinterest/'
        else:
            playerPoiSettingPath = None # To avoid reference before assignment
        if playerPoiSettingPath:
            index = self._app.settings.value(playerPoiSettingPath + 'index', None)
            if index and len(index) > 0:
                for i in index:
                    if str(i) in self.poiLocationItems.keys():
                        marker = self.poiLocationItems[str(i)]
                        poiLocDict[str(i)] = marker
                        del self.poiLocationItems[str(i)]
                    else:
                        marker = PointofInterestMarker(i,self,self.controller.sharedResImageFactory, self.mapColor, self.mapMarkerSize)
                        marker.thisCharOnly = True
                        marker.setSavedSettings()
                        marker.filterSetVisible(True)
                        marker.setZoomLevel(self.mapZoomLevel, 0.0, 0.0, True)
                        self._connectMarker(marker)
                        poiLocDict[str(i)] = marker

        for i in self.poiLocationItems:
            self.poiLocationItems[i].destroy()
        self.poiLocationItems = poiLocDict

    def _createLocationMarkers(self):
        newDict = dict()
        for l in self.pipWorldLocations.value():
            if l.pipId in self.pipMapLocationItems:
                marker = self.pipMapLocationItems[l.pipId]
                newDict[l.pipId] = marker
                del self.pipMapLocationItems[l.pipId]
            else:
                marker = LocationMarker(self, self.controller.imageFactory, self.controller.sharedResImageFactory,
                                        self.mapColor, self.mapMarkerSize)
                self._connectMarker(marker)
                marker.setZoomLevel(self.mapZoomLevel, 0.0, 0.0, False)
                marker.filterSetVisible(self.locationFilterEnableFlag, False)
                marker.filterVisibilityCheat(self.locationVisibilityCheatFlag, False)
                marker.setPipValue(l, self.datamanager, self.mapCoords)
                marker.setStickyLabel(self.stickyLabelsEnabled, False)
                marker.setSize(self.mapMarkerSize, False)
                marker.setSavedSettings()

                # convert old coord indexed notes and stickies to new uid indexed from
                # and remove old entries - remove this block in vNext (0.9?)
                if (marker.uid != None):
                    rx = l.child('X').value()
                    ry = l.child('Y').value()

                    if not marker.stickyLabel:
                        oldsavedsticky = bool(
                            int(self._app.settings.value('globalmapwidget/stickylabels/' + str(rx) + ',' + str(ry), 0)))
                        if oldsavedsticky:
                            marker.setStickyLabel(oldsavedsticky, True)
                            self._app.settings.setValue('globalmapwidget/stickylabels2/' + marker.uid, 1)
                            self._app.settings.remove('globalmapwidget/stickylabels/' + str(rx) + ',' + str(ry))

                    if (len(marker.note) == 0):
                        marker.setNote(
                            self._app.settings.value('globalmapwidget/locationnotes/' + str(rx) + ',' + str(ry), ''))
                        if (len(marker.note) > 0):
                            self._app.settings.setValue('globalmapwidget/locationmarkernotes/' + marker.uid,
                                                        marker.note)
                            self._app.settings.remove('globalmapwidget/locationnotes/' + str(rx) + ',' + str(ry))

                self._app.settings.beginGroup("globalmapwidget/locationnotes");
                if len(self._app.settings.childKeys()) == 0:
                    self._app.settings.remove('');
                self._app.settings.endGroup();

                self._app.settings.beginGroup("globalmapwidget/stickylabels");
                if len(self._app.settings.childKeys()) == 0:
                    self._app.settings.remove('');
                self._app.settings.endGroup();
                # end convert and clean up - remove this block in vNext (0.9?)

                newDict[l.pipId] = marker
        for i in self.pipMapLocationItems:
            self.pipMapLocationItems[i].destroy()
        self.pipMapLocationItems = newDict

    @QtCore.pyqtSlot()        
    def _slotMapColorSelectionTriggered(self):
        color = QtWidgets.QColorDialog.getColor(self.mapColor, self)
        if color.isValid and color.value() != QtGui.QColor.fromRgb(0,0,0).value():
            self.mapColor = color
            self._app.settings.setValue('globalmapwidget/colour', color)
            self.widget.mapColorAutoToggle.setChecked(False)
            self.signalSetColor.emit(color)
    
    
    @QtCore.pyqtSlot(int)
    def _slotMapFileComboTriggered(self, index):
        mapfile = self.mapFiles[self.mapFileComboItems[index]]
        if not mapfile:
            self._logger.error('Could not find map "' + self.selectedMapFile + '".')
        else:
            self.selectedMapFile = self.mapFileComboItems[index]
            file = os.path.join('res', mapfile['file'])
            self.mapItem.setMapFile(file, mapfile['colorable'], mapfile['nw'], mapfile['ne'], mapfile['sw'])
            self.mapCoords.init( 
                    self.MAP_NWX, self.MAP_NWY, 
                    self.MAP_NEX,  self.MAP_NEY, 
                    self.MAP_SWX, self.MAP_SWY,
                    self.mapItem.nw[0], self.mapItem.nw[1], 
                    self.mapItem.ne[0], self.mapItem.ne[1], 
                    self.mapItem.sw[0], self.mapItem.sw[1] )
            self.signalMarkerForcePipValueUpdate.emit()

            self._app.settings.setValue('globalmapwidget/selectedMapFile', self.selectedMapFile)
            # Only create collectables markers when we have a map object
            if self.pipMapObject:
                self._createCollectablesMarkers(self.collectableDefs, reset=True)


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
        
    @QtCore.pyqtSlot(int)
    def _slotMarkerSizeSliderTriggered (self,size):
        self.widget.markerSizeSpinbox.blockSignals(True)
        self.widget.markerSizeSpinbox.setValue(size)
        self.widget.markerSizeSpinbox.blockSignals(False)
        self._app.settings.setValue('globalmapwidget/mapMarkerSize', size)
        self.mapMarkerSize = size
        self.signalSetMarkerSize.emit(size)

    @QtCore.pyqtSlot(int)
    def _slotMarkerSizeSpinboxTriggered (self,size):
        self.widget.markerSizeSlider.blockSignals(True)
        self.widget.markerSizeSlider.setValue(size)
        self.widget.markerSizeSlider.blockSignals(False)
        self.mapMarkerSize = size
        self._app.settings.setValue('globalmapwidget/mapMarkerSize', size)
        self.signalSetMarkerSize.emit(size)

    @QtCore.pyqtSlot(bool)
    def _slotStickyLabelsTriggered(self, value):
        self.stickyLabelsEnabled = value
        self._app.settings.setValue('globalmapwidget/stickyLabels', int(value))
        self.signalSetStickyLabel.emit(value)
        
    @QtCore.pyqtSlot(bool)        
    def _slotPowerMarkerEnableTriggered(self, value):
        self.powerArmorMarker.filterSetVisible(value)
        self._app.settings.setValue('globalmapwidget/powerArmourMarker', int(value))
        
    @QtCore.pyqtSlot(bool)        
    def _slotLocationEnableTriggered(self, value):
        self.locationFilterEnableFlag = value
        self._app.settings.setValue('globalmapwidget/locationMarker', int(value))
        self.signalLocationFilterSetVisible.emit(value)
        
    @QtCore.pyqtSlot(bool)        
    def _slotLocationVisibilityCheatTriggered(self, value):
        self.locationVisibilityCheatFlag = value
        self._app.settings.setValue('globalmapwidget/locationVisibilityCheat', int(value))
        self.signalLocationFilterVisibilityCheat.emit(value)
        
    @QtCore.pyqtSlot(bool)        
    def _slotCenterOnPlayerCheckToggled(self, value):
        self.centerOnPlayerEnabled = value
        self._app.settings.setValue('globalmapwidget/centerPlayer', int(value))
        if value and self.playerMarker.markerItem.isVisible():
            self.playerMarker.mapCenterOn()
            
    @QtCore.pyqtSlot(float, float, float)        
    def _slotPlayerMarkerPositionUpdated(self, x, y, r):
        if self.centerOnPlayerEnabled:
            self.playerMarker.mapCenterOn()

    def updateCollectableVisibility(self, playAudibleAlerts=True):
        for catKey in self.collectableLocationMarkers.keys():
            showAlwaysCollected = bool(int(self._app.settings.value('globalmapwidget/collectable_showcollected_' + catKey, 0)) == 1)
            showNeverCollected = bool(int(self._app.settings.value('globalmapwidget/collectable_showcollected_' + catKey, 0)) == 0)

            showAlwaysUncollected = bool(int(self._app.settings.value('globalmapwidget/collectable_showuncollected_' + catKey, 0)) == 1)
            showNeverUncollected = bool(int(self._app.settings.value('globalmapwidget/collectable_showuncollected_' + catKey, 0)) == 0)

            showNearCollected = bool(int(self._app.settings.value('globalmapwidget/collectable_showcollected_' + catKey, 0)) == 2)
            showNearUncollected = bool(int(self._app.settings.value('globalmapwidget/collectable_showuncollected_' + catKey, 0)) == 2)
            alertnearuncollected = bool(int(self._app.settings.value('globalmapwidget/collectable_alertuncollected_' + catKey, 0)))
            collectableVRange = int(self._app.settings.value('globalmapwidget/collectable_vrange_' + catKey, 100))
            collectableARange = int(self._app.settings.value('globalmapwidget/collectable_arange_' + catKey, 50))

            # Multiplying with the map coordinate's scale factor will make the distance 
            # independent from the map resolution
            collectableVRange = self.mapCoords._ax * collectableVRange * 100
            collectableARange = self.mapCoords._ax * collectableARange * 100

            for k, marker in self.collectableLocationMarkers[catKey].items():
                if marker.collected:
                    if showAlwaysCollected:
                        marker.filterSetVisible(True)
                    if showNeverCollected:
                        marker.filterSetVisible(False)
                    if showNearCollected:
                        if self.playerMarker.isWithinRangeOf(marker, collectableVRange):
                            marker.filterSetVisible(True)
                        else:
                            marker.filterSetVisible(False)
                else:
                    if showAlwaysUncollected:
                        marker.filterSetVisible(True)
                    if showNeverUncollected:
                        marker.filterSetVisible(False)
                    if showNearUncollected:
                        if self.playerMarker.isWithinRangeOf(marker, collectableVRange):
                            marker.filterSetVisible(True)
                        else:
                            marker.filterSetVisible(False)
                    if alertnearuncollected:
                        if self.playerMarker.isWithinRangeOf(marker, collectableARange):
                            if marker.uid not in self.collectablesNearPlayer:
                                self.collectablesNearPlayer.append(marker.uid)
                                if playAudibleAlerts and catKey in self.collectableNearSoundEffects.keys() and not self.collectableNearSoundEffects[catKey].isPlaying():
                                    self.collectableNearSoundEffects[catKey].play()
                        else:
                            if marker.uid in self.collectablesNearPlayer:
                                self.collectablesNearPlayer.remove(marker.uid)


    @QtCore.pyqtSlot(bool)
    def _slotMapColorAutoModeTriggered(self, value):
        self._app.settings.setValue('globalmapwidget/autoColour', int(value))
        if self.pipMapObject:
            if value:
                self.pipColor = self.pipMapObject.pipParent.child('Status').child('EffectColor')
                self.pipColor.registerValueUpdatedListener(self._onPipColorChanged, 1)
                self._onPipColorChanged(None, None, None)
            elif self.pipColor:
                self.pipColor.unregisterValueUpdatedListener(self._onPipColorChanged)
                r = self.pipColor.child(0).value() * 255
                g = self.pipColor.child(1).value() * 255
                b = self.pipColor.child(2).value() * 255
                pipColor = QtGui.QColor.fromRgb(r,g,b)
                self.signalSetColor.emit(pipColor)

        
    @QtCore.pyqtSlot()
    def _slotSaveToTriggered(self):
        fileName = QtWidgets.QFileDialog.getSaveFileName(self, '', '', 'Images (*.png *.jpg *.gif)')
        if fileName:
            pixmap = self.mapView.grab()
            pixmap.save(fileName[0])
            
    def _onPipColorChanged(self, caller, value, pathObjs):
        if self.pipColor:
            r = self.pipColor.child(0).value() * 255
            g = self.pipColor.child(1).value() * 255
            b = self.pipColor.child(2).value() * 255
            self.mapColor = QtGui.QColor.fromRgb(r,g,b)
            self.signalSetColor.emit(self.mapColor)

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
            elif event.type() == QtCore.QEvent.ContextMenu:
                if self.mapCoords.isValid:
                    menu = QtWidgets.QMenu(self.mapView)
                    markerPos = self.mapView.mapToScene(event.pos())
                    # Check whether we clicked on a marker
                    if self.mapScene.itemAt(markerPos, QtGui.QTransform()) != self.mapItem.mapItem:
                        return False
                    markerPos = markerPos/self.mapZoomLevel # Account for zoom
                    @QtCore.pyqtSlot()
                    def _setCustomMarker():
                        self.datamanager.rpcSetCustomMarker(self.mapCoords.map2pip_x(markerPos.x()), self.mapCoords.map2pip_y(markerPos.y()))
                    action = menu.addAction('Set Custom Marker')
                    action.triggered.connect(_setCustomMarker)

                    @QtCore.pyqtSlot()
                    def _setPoiLocationMarker():
                        rx = self.mapCoords.map2pip_x(markerPos.x())
                        ry = self.mapCoords.map2pip_y(markerPos.y())
                        labelstr = ''
                        


                        editpoiDialog = EditPOIDialog(self, color=self.mapColor)
                        editpoiDialog.txtPOILabel.setText(labelstr)
                        editpoiDialog.chkCharacterOnly.setText(editpoiDialog.chkCharacterOnly.text() + '(' +self.characterDataManager.pipPlayerName +')')
                        ok = editpoiDialog.exec_()
                        labelstr = editpoiDialog.txtPOILabel.text()
                        editpoiDialog.show()
                        thisCharOnly = editpoiDialog.chkCharacterOnly.isChecked()
                        if (ok != 0):
                            poimarker = PointofInterestMarker(uuid.uuid4(), self,self.controller.sharedResImageFactory, editpoiDialog.selectedColor, self.mapMarkerSize, iconfile=editpoiDialog.IconFile)
                            poimarker.setLabel(labelstr)
                            self._connectMarker(poimarker)
                            poimarker.setMapPos(self.mapCoords.pip2map_x(rx), self.mapCoords.pip2map_y(ry))
                            poimarker.setZoomLevel(self.mapZoomLevel, 0.0, 0.0, False)
                            poimarker.filterSetVisible(True)
                            poimarker.setStickyLabel(True, True)
                            poimarker.thisCharOnly = thisCharOnly
                            
                            markerKey = poimarker.uid
                            self.poiLocationItems[markerKey] = poimarker
                        
                            poiSettingPath = 'globalmapwidget/pointsofinterest/' 
                            if thisCharOnly:
                                poiSettingPath = self.characterDataManager.playerDataPath + '/pointsofinterest/'

                            index = self._app.settings.value(poiSettingPath+'index', None)
                            if index == None: 
                                index = []
                            
                            index.append(str(markerKey))
                                
                            self._app.settings.setValue(poiSettingPath+'index', index)
                            
                            self._app.settings.setValue(poiSettingPath+str(markerKey)+'/worldx', rx)
                            self._app.settings.setValue(poiSettingPath+str(markerKey)+'/worldy', ry)
                            self._app.settings.setValue(poiSettingPath+str(markerKey)+'/label', labelstr)
                            self._app.settings.setValue(poiSettingPath+str(markerKey)+'/color', editpoiDialog.selectedColor)
                            self._app.settings.setValue(poiSettingPath+str(markerKey)+'/icon', editpoiDialog.IconFile)

                            settingPath = 'globalmapwidget/stickylabels2/'
                            self._app.settings.setValue(settingPath+markerKey, int(True))                                
                        return

                    menu.addAction('Add Point of Interest', _setPoiLocationMarker)


                    menu.exec(event.globalPos())
                return True
            elif event.type() == QtCore.QEvent.MouseButtonDblClick:
                
                if self.mapCoords.isValid:
                    markerPos = self.mapView.mapToScene(event.pos())
                    # Check whether we clicked on a marker
                    if self.mapScene.itemAt(markerPos, QtGui.QTransform()) != self.mapItem.mapItem:
                        return False
                    markerPos = markerPos/self.mapZoomLevel # Account for zoom
                    self.datamanager.rpcSetCustomMarker(self.mapCoords.map2pip_x(markerPos.x()), self.mapCoords.map2pip_y(markerPos.y()))
                return True
        return False

    def iwcSetCollectablesCollectedState(self, listFormids, fullUpdate = True):
        if fullUpdate:
            for catKey in self.collectableLocationMarkers.keys():
                for instanceID, marker in self.collectableLocationMarkers[catKey].items():
                    if str(int(marker.itemFormID,16)) in listFormids:
                        marker.setCollected(True)
                    else:
                        marker.setCollected(False)
        else:
            # Python does not allow to break out of several nested loop, 
            # but we can use "return" as a workaround
            def _idSetCollected(id):
                for catKey in self.collectableLocationMarkers.keys():
                    for instanceID, marker in self.collectableLocationMarkers[catKey].items():
                        if str(int(marker.itemFormID,16)) == id:
                            marker.setCollected(True)
                            return
            for id in listFormids:
                _idSetCollected(id)
        self.updateCollectableVisibility(playAudibleAlerts=False)



    def iwcCenterOnLocation(self, pipId):
        try:
            loc = self.pipMapLocationItems[pipId]
            loc.mapCenterOn()
        except:
            pass
    
    # CENTER MAP ON QUEST MARKER
    # formId - int - Quest formID value
    def iwcCenterOnQuest(self, formId):
        Quest = None
        
        if self.pipMapQuestsItems:
            def _searchForQuest():
                for QuestItem in self.pipMapQuestsItems:
                    for QuestFormId in self.pipMapQuestsItems[QuestItem].QuestFormIds:
                        if QuestFormId.value() == formId:
                            return self.pipMapQuestsItems[QuestItem]
            Quest = _searchForQuest()
        
        if Quest:
            Quest.mapCenterOn()
