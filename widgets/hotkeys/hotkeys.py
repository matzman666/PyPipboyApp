# -*- coding: utf-8 -*-
import datetime
import time
import os
import traceback, sys
from PyQt5 import QtWidgets, QtCore, uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from pypipboy.types import eValueType
from widgets import widgets
from widgets.shared import settings
from collections import namedtuple
from collections import OrderedDict
from pypipboy import inventoryutils

import logging

Action=namedtuple("Action", (['name', 'description', 'action', 'numParams']))
Actions = OrderedDict()

class HotkeyWidget(widgets.WidgetBase):
    _signalInfoUpdated = QtCore.pyqtSignal()
    
    def __init__(self, mhandle, parent):
        super().__init__('HotkeyWidget', parent)
        self.widget = uic.loadUi(os.path.join(mhandle.basepath, 'ui', 'hotkeys.ui'))
        self.widget.textBrowser.setSource(QtCore.QUrl.fromLocalFile(os.path.join(mhandle.basepath, 'ui', 'hotkeys.html')))
        self._logger = logging.getLogger('pypipboyapp.llhookey')
        self.setWidget(self.widget)
        self.pipInventoryInfo = None
        self.pipRadioInfo = None
        
        self._signalInfoUpdated.connect(self._slotInfoUpdated)
        
    def init(self, app, datamanager):
        super().init(app, datamanager)
        self.dataManager = datamanager
        self.dataManager.registerRootObjectListener(self._onPipRootObjectEvent)
        self._app = app
        self.llh = LLHookey()
        
        self.widget.btnLoad.clicked.connect(self._loadButtonHandler)
        self.widget.btnSave.clicked.connect(self._saveButtonHandler)
        self.widget.btnDelete.clicked.connect(self._deleteButtonHandler)
        self.widget.btnAdd.clicked.connect(self._addButtonHandler)

        forcedInstructionsCounter = 1
        forceInstructions = int(self._app.settings.value('hotkeyswidget/forcedInstructionsCounter', 0)) < forcedInstructionsCounter
        if not forceInstructions:
            settings.setSplitterState(self.widget.splitter, self._app.settings.value('hotkeyswidget/splitterState', None))

        self._app.settings.setValue('hotkeyswidget/forcedInstructionsCounter', forcedInstructionsCounter)
        self.widget.splitter.splitterMoved.connect(self._slotSplitterMoved)

        Actions['testHotkeyHook'] =Action('Test Hotkey Hook', '', self.testHotkeyHook, 0 ) 
        Actions['toggleAllHotkeys'] =Action('Toggle Hotkeys On/Off', '', self.llh.toggleAllHotkeys, 0 ) 
        Actions['equipNextGrenade'] =Action('Cycle Equipped Grenade', '', self.equipNextGrendae, 0 ) 
        Actions['toggleEquippedGrenades'] =Action('Unequip\Equip Current Grenade', '', self.toggleEquippedGrenades, 0 ) 
        Actions['saveEquippedApparelToSlot'] =Action('Save all currently equipped apparel to slot ', '(param1: Slot Number [1-99])', self.saveEquippedApparelToSlot, 1 ) 
        Actions['equipApparelFromSlot'] =Action('Equip apparel from saved slot', '(param1: Slot Number [1-99])', self.equipApparelFromSlot, 1 ) 
        Actions['unequipAllApparel'] =Action('Unequip all items of apparel', '', self.unequipAllApparel, 0 ) 
        Actions['toggleRadio'] =Action('Toggle Radio On\Off', '', self.toggleRadio, 0 ) 
        Actions['nextRadio'] =Action('Tune to next radio station', '', self.nextRadio, 0 ) 
        Actions['useStimpak'] =Action('Use Stimpak', '', self.useStimpak, 0 ) 
        Actions['useRadaway'] =Action('Use Radaway', '', self.useRadAway, 0 ) 
        Actions['useJet'] = Action('Use Jet', '', self.useJet, 0 ) 
        Actions['useNamedItem'] =Action('Use Named Item' , '(param1: Inventory Section [ie:48], param2: ItemName [ie: psycho])', self.useItemByName, 2 ) 
        Actions['cycleWidgets'] = Action('Cycle Tabbed Widgets', '(param1: Comma seperated list of widget titles to cycle through)', self.cycleWidgets, 1 ) 
        
        for k, v in VK_CODE.items():    
            self.widget.keyComboBox.addItem(k, v)

        for k, v in Actions.items():
            self.widget.actionComboBox.addItem(v.name + v.description, k)

        self.widget.actionComboBox.currentIndexChanged.connect(self._actionComboBoxCurrentIndexChanged)
        self.widget.param1Label.setVisible(False)
        self.widget.param1LineEdit.setVisible(False)
        self.widget.param2Label.setVisible(False)
        self.widget.param2LineEdit.setVisible(False)
        self.widget.param3Label.setVisible(False)
        self.widget.param3LineEdit.setVisible(False)
        self.widget.btnLoad.setVisible(False)
        
        self.loadHotkeys()
        if(len(self.llh.Hotkeys) == 0):
            self.llh.addHotkey( Hotkey(keycode=VK_CODE.get('home'), actionkey='testHotkeyHook') )
            self.llh.addHotkey( Hotkey(keycode=VK_CODE.get('pause'), shift=True, actionkey='toggleAllHotkeys') )
            self.llh.addHotkey( Hotkey(keycode=VK_CODE.get('y'), actionkey='useStimpak'))
            self.llh.addHotkey( Hotkey(keycode=VK_CODE.get('u'), actionkey='useRadaway'))
            self.llh.addHotkey( Hotkey(keycode=VK_CODE.get('`'), actionkey='useJet') )
            self.llh.addHotkey( Hotkey(keycode=VK_CODE.get('g'), actionkey='equipNextGrenade') )
            self.llh.addHotkey( Hotkey(keycode=VK_CODE.get('h'), actionkey='useNamedItem', params=["48", "psycho"]) )
            self.llh.addHotkey( Hotkey(keycode=VK_CODE.get('page_up'), actionkey='toggleRadio'))
            self.llh.addHotkey( Hotkey(keycode=VK_CODE.get('page_down'), actionkey='nextRadio'))
            self.llh.addHotkey( Hotkey(keycode=VK_CODE.get('numpad_1'), control=True, actionkey='saveEquippedApparelToSlot', params=["1"] ))
            self.llh.addHotkey( Hotkey(keycode=VK_CODE.get('numpad_1'), control=False, actionkey='equipApparelFromSlot', params=["1"] ))
            self.llh.addHotkey( Hotkey(keycode=VK_CODE.get('numpad_2'), control=True, actionkey='saveEquippedApparelToSlot', params=["2"] ))
            self.llh.addHotkey( Hotkey(keycode=VK_CODE.get('numpad_2'), control=False, actionkey='equipApparelFromSlot', params=["2"] ))
            self.llh.addHotkey( Hotkey(keycode=VK_CODE.get('numpad_3'), control=True, actionkey='saveEquippedApparelToSlot', params=["3"] ))
            self.llh.addHotkey( Hotkey(keycode=VK_CODE.get('numpad_3'), control=False, actionkey='equipApparelFromSlot', params=["3"] ))
            self.llh.addHotkey( Hotkey(keycode=VK_CODE.get('numpad_9'), actionkey='unequipAllApparel')) 
            self.llh.addHotkey( Hotkey(keycode=VK_CODE.get('backspace'), actionkey='cycleWidgets', params=["Global Map, HotkeyWidget"])) 
        
        #self.llh.addHotkey( Hotkey(keycode=VK_CODE.get('home'), control=True , alt=True, shift=True, actionkey='useNamedItem', params=("48", "psycho")))

        #h1 = Hotkey(keycode=VK_CODE.get(','), action=self.useItemByName, params=("29", "formal hat"))
        #h2 = Hotkey(keycode=VK_CODE.get('/'), action=self.llh.removeHotkey, params=(h1))
        #h3 = Hotkey(keycode=VK_CODE.get('/'), action=self.llh.disableHotkey, params=(h1))
        #self.llh.addHotkey( h1 )
        #self.llh.addHotkey( h2 )
        #self.llh.addHotkey( h3 )
        
        self.updateTable()

        self.availableGrenades = []
        self.availableRadioStations = []
        self.currentRadioStation = None
        self.lastEquippedGrenade = None

        self.savedApparelSlots = {}
        for index in range (0,100):
            settingPath = 'hotkeyswidget/apparelslots/'
            self.savedApparelSlots[str(index)] = self._app.settings.value(settingPath+str(index), None)

        return

    def cycleWidgets(self, widgetnames):
        widgetNameList = [ w.strip().lower() for w in widgetnames.split(',')]
        self._app.cycleWidgets(widgetNameList)
        return
        
    def toggleEquippedGrenades(self):
        if (self.lastEquippedGrenade):
            self.useItemByName('43', self.lastEquippedGrenade)
        else:
            self.equipNextGrendae()
        return
        
    def testHotkeyHook(self):
        msg = time.strftime("%H:%M:%S")
        msg += " - Success!!"

        self._logger.debug(msg)
        self.widget.testMessage.setText(msg)
        return
    
    def unequipAllApparel(self):
        if (self.pipInventoryInfo):
            def _filterFunc(item):
                return inventoryutils.itemHasAnyFilterCategory(item, inventoryutils.eItemFilterCategory.Apparel)
            apparels = inventoryutils.inventoryGetItems(self.pipInventoryInfo, _filterFunc)
            if(not apparels):
                return
            for apparel in apparels:        
                if (apparel.child('equipState').value() > 0):
                    try:
                        self.dataManager.rpcUseItem(apparel)
                    except Exception as e:
                        self._logger.error('unequipAllApparel Exception in rpc call: ' + str(e))
                    ### This is a vile hack to allow each rpc call to complete
                    ### before sending the next 
                    ### It'll do for now, but should really find a better way 
                    ### of handling this, queue action method on datamanager.py 
                    ### perhaps?
                    time.sleep(0.1)             
        return
            
    def saveEquippedApparelToSlot(self, slotIndex):
        slotIndex = str(slotIndex)
        self._logger.debug('saveEquippedApparelToSlot: slot ' + str(slotIndex))
        self.savedApparelSlots[slotIndex] = []
        selectedSlot = self.savedApparelSlots[slotIndex]
        
        if (self.pipInventoryInfo):
            def _filterFunc(item):
                return inventoryutils.itemHasAnyFilterCategory(item, inventoryutils.eItemFilterCategory.Apparel)
            apparels = inventoryutils.inventoryGetItems(self.pipInventoryInfo, _filterFunc)
            if(not apparels):
                return
            for apparel in apparels:        
                if (apparel.child('equipState').value() > 0):
                    selectedSlot.append(apparel.child('text').value())
                    
            self._logger.debug('saveEquippedApparelToSlot: saving: ' + str(selectedSlot))
            settingPath = 'hotkeyswidget/apparelslots/'
            self._app.settings.setValue(settingPath+str(slotIndex), selectedSlot)

        return
        
    def equipApparelFromSlot(self, slotIndex):
        str(slotIndex)
        selectedSlot = self.savedApparelSlots.get(slotIndex, None)
        
        if (not selectedSlot):
            self._logger.debug('equipApparelFromSlot: no such slot')
            return

        for i in range(0, len(selectedSlot)):
            self.useItemByName('29', selectedSlot[i])
            self._logger.debug('equipApparelFromSlot: equipping: ' + selectedSlot[i])
            ### This is a vile hack to allow each rpc call to complete
            ### before sending the next 
            ### It'll do for now, but should really find a better way 
            ### of handling this, queue action method on datamanager.py 
            ### perhaps?
            time.sleep(0.1)
            
        return
        
    def toggleRadio(self):
        
        if (self.currentRadioStation):
            self._logger.debug('toggleRadio: currentstation: ' + self.currentRadioStation.child('text').value())
            try:
                self.dataManager.rpcToggleRadioStation(self.currentRadioStation)
            except Exception as e:
                self._logger.error('toggleRadio Exception in rpc call: ' + str(e))
        else:
            self._logger.debug('toggleRadio: no current, trying station 0')
            numStations = len(self.availableRadioStations)
            if numStations > 0:
                try:
                    self.dataManager.rpcToggleRadioStation(self.availableRadioStations[0])
                except Exception as e:
                    self._logger.error('toggleRadio Exception in rpc call: ' + str(e))
                
        return
        
    def nextRadio(self):
        getIndex = 0
        numStations = len(self.availableRadioStations)

        if self.currentRadioStation:
            self._logger.debug('nextRadio: currentstation: ' + self.currentRadioStation.child('text').value())
            for i in range (0, numStations):
                if self.availableRadioStations[i].child('text').value() == self.currentRadioStation.child('text').value():
                    getIndex = i + 1
                    break
            
        if (getIndex >= numStations):
            getIndex = 0
            
        if (getIndex <= numStations):
            self._logger.debug('nextRadio: tuning radio to: ' + self.availableRadioStations[getIndex].child('text').value())
            try:
                self.dataManager.rpcToggleRadioStation(self.availableRadioStations[getIndex])
            except Exception as e:
                self._logger.error('nextRadio Exception in rpc call: ' + str(e))
        
        return        
        
    def equipNextGrendae(self):
        nextIndex = -1
        lastIndex = -1 
        self.availableGrenades.sort()
        numGrenades = len(self.availableGrenades)
        if (numGrenades > 0):
            for i in range(0, numGrenades):
                if (self.availableGrenades[i][1]):
                    nextIndex = i + 1
                    break
                if (self.availableGrenades[i][0] == self.lastEquippedGrenade):
                    lastIndex = i
                    
            if (nextIndex == numGrenades):
                nextIndex = 0
            
            if (nextIndex < 0 and lastIndex >= 0): 
                nextIndex = lastIndex
            
            if(nextIndex < 0):
                nextIndex = 0
            
            self.useItemByName("43", self.availableGrenades[nextIndex][0])
        
        return
                
    def useJet(self):   
        self.useItemByName("48", "jet")
        return
        
    def useStimpak(self):
        try:
            self.dataManager.rpcUseStimpak()
        except Exception as e:
            self._logger.error('useStimpak Exception in rpc call: ' + str(e))
        return
        
    def useRadAway(self):
        try:
            self.dataManager.rpcUseRadAway()
        except Exception as e:
            self._logger.error('useRadAway Exception in rpc call: ' + str(e))
        return

    def _useItemByName(self,filterCategory, itemName):
        def _filterFunc(item):
            if inventoryutils.itemHasAnyFilterCategory(item, filterCategory):
                if item.child('text').value().lower() == itemName.lower():
                    return True
            return False

        item = inventoryutils.inventoryGetItem(self.pipInventoryInfo, _filterFunc)
        try:
            self.dataManager.rpcUseItem(item)
        except Exception as e:
            self._logger.error('useItemByName Exception in rpc call: ' + str(e))
        return
    
    def useItemByName(self,inventorySection, itemName):
        filtercat = None
        if inventorySection == '29':
            filtercat = inventoryutils.eItemFilterCategory.Apparel
        if inventorySection == '35':
            filtercat = inventoryutils.eItemFilterCategory.Misc
        if inventorySection == '43':
            filtercat = inventoryutils.eItemFilterCategory.Weapon
        if inventorySection == '44':
            filtercat = inventoryutils.eItemFilterCategory.Ammo
        if inventorySection == '48':
            filtercat = inventoryutils.eItemFilterCategory.Aid
    
        if filtercat != None:
            self._useItemByName(filtercat, itemName)

        return

    def _onPipRootObjectEvent(self, rootObject):
        self.pipInventoryInfo = rootObject.child('Inventory')
        if self.pipInventoryInfo:
            self.pipInventoryInfo.registerValueUpdatedListener(self._onPipPlayerInfoUpdate, 1)
            
        self.pipRadioInfo = rootObject.child('Radio')
        if self.pipRadioInfo:
            self.pipRadioInfo.registerValueUpdatedListener(self._onPipPlayerInfoUpdate, 2)

        self._signalInfoUpdated.emit()
        pass

    def _onPipPlayerInfoUpdate(self, caller, value, pathObjs):
        self._signalInfoUpdated.emit()
        
    @QtCore.pyqtSlot()
    def _slotInfoUpdated(self):
        self.availableGrenades = []
        if (self.pipInventoryInfo):
            def _filterFunc(item):
                return inventoryutils.itemHasAnyFilterCategory(item, inventoryutils.eItemFilterCategory.Weapon)
            weapons = inventoryutils.inventoryGetItems(self.pipInventoryInfo, _filterFunc)
            if(not weapons):
                return
            for weapon in weapons:        
                equipped = False
                if inventoryutils.itemIsWeaponThrowable(weapon):        
                    count = str(weapon.child('count').value())
                    name = str(weapon.child('text').value())
                    if (weapon.child('equipState').value() == 3):
                        equipped = True
                        self.lastEquippedGrenade = name.lower()
                    
                    self.availableGrenades.append([name.lower(), equipped])
                    
        self.availableRadioStations = []
        if(self.pipRadioInfo):
            for i in range(0, self.pipRadioInfo.childCount()):
                station = self.pipRadioInfo.child(i)
                if station.child('inRange').value():
                    self.availableRadioStations.append(station)
                if station.child('active').value():
                    self.currentRadioStation = station
        
                    
    @QtCore.pyqtSlot(int, int)
    def _slotSplitterMoved(self, pos, index):
        self._app.settings.setValue('hotkeyswidget/splitterState', settings.getSplitterState(self.widget.splitter))
                    
    @QtCore.pyqtSlot()
    def _loadButtonHandler(self):
        self.loadHotkeys()
        
    def loadHotkeys(self):
        self.llh.Hotkeys.clear()
    
        for index in range (0,100):
            settingPath = 'hotkeyswidget/keys/'+str(index)+'/'
            keycode = int(self._app.settings.value(settingPath+'keycode', 0))
            if(keycode == 0):
                break
            
            control = bool(int(self._app.settings.value(settingPath+'control', 0)))
            alt = bool(int(self._app.settings.value(settingPath+'alt', 0)))
            shift = bool(int(self._app.settings.value(settingPath+'shift', 0)))
            params = self._app.settings.value(settingPath+'params', None)
            actionkey = self._app.settings.value(settingPath+'action', None)
            
            action = Actions.get(actionkey, None)
            
            if (action):
                hk = Hotkey(keycode=keycode, control=control, alt=alt, shift=shift, params=params, actionkey=actionkey)
                self.llh.addHotkey(hk)
        
        self.updateTable()

    @QtCore.pyqtSlot()
    def _saveButtonHandler(self):
        self.saveHotkeys()

    def saveHotkeys(self):
    
        self._app.settings.beginGroup("hotkeyswidget/keys/");
        self._app.settings.remove(""); 
        self._app.settings.endGroup();
    
        for index, hk in enumerate(self.llh.Hotkeys):
            settingPath = 'hotkeyswidget/keys/'+str(index)+'/'
            self._app.settings.setValue(settingPath+'keycode', int(hk.keycode))
            self._app.settings.setValue(settingPath+'control', int(hk.control))
            self._app.settings.setValue(settingPath+'alt', int(hk.alt))
            self._app.settings.setValue(settingPath+'shift', int(hk.shift))
            if(hk.params):
                self._app.settings.setValue(settingPath+'params', hk.params)
            if(hk.actionkey):
                self._app.settings.setValue(settingPath+'action', hk.actionkey)

    @QtCore.pyqtSlot()
    def _addButtonHandler(self):
        kc = self.widget.keyComboBox.currentData(QtCore.Qt.UserRole)
        actionkey = self.widget.actionComboBox.currentData(QtCore.Qt.UserRole)

        if (kc):
            hk = Hotkey( 
                keycode=kc, 
                control=self.widget.cbxControl.isChecked(),
                alt=self.widget.cbxAlt.isChecked(),
                shift=self.widget.cbxShift.isChecked(),
                actionkey=actionkey)
                
            params = None
            if (Actions[actionkey].numParams > 0):
                params = []
                params.append(self.widget.param1LineEdit.text())
            if (Actions[actionkey].numParams > 1):
                params.append(self.widget.param2LineEdit.text())
            if (Actions[actionkey].numParams > 2):
                params.append(self.widget.param3LineEdit.text())
                
            hk.params = params

                
            self.llh.addHotkey(hk)
        self.updateTable()

        self.widget.param1LineEdit.setText("")
        self.widget.param2LineEdit.setText("")
        self.widget.param3LineEdit.setText("")

        self.widget.cbxControl.setChecked(False)
        self.widget.cbxAlt.setChecked(False)
        self.widget.cbxShift.setChecked(False)
        

    @QtCore.pyqtSlot(int)
    def _actionComboBoxCurrentIndexChanged(self, index):
        data = self.widget.actionComboBox.currentData(QtCore.Qt.UserRole)
    
        self.widget.param1Label.setVisible(False)
        self.widget.param1LineEdit.setVisible(False)
        self.widget.param2Label.setVisible(False)
        self.widget.param2LineEdit.setVisible(False)
        self.widget.param3Label.setVisible(False)
        self.widget.param3LineEdit.setVisible(False)

        if (Actions[data].numParams > 0):
            self.widget.param1Label.setVisible(True)
            self.widget.param1LineEdit.setVisible(True)
        if (Actions[data].numParams > 1):
            self.widget.param2Label.setVisible(True)
            self.widget.param2LineEdit.setVisible(True)
        if (Actions[data].numParams > 2):
            self.widget.param3Label.setVisible(True)
            self.widget.param3LineEdit.setVisible(True)
        
    @QtCore.pyqtSlot()
    def _deleteButtonHandler(self):
        table = self.widget.tableWidget
        curIndex = table.currentIndex().row()
        
        self._logger.debug("_deleteButtonHandler: curIndex:" + str(curIndex))
        if(curIndex >= 0):
            item = table.item(curIndex, 0)
            self._logger.debug("_deleteButtonHandler: item:" + str(item))
            hkid = item.data(QtCore.Qt.UserRole)
            if(hkid):
                self._logger.debug("_deleteButtonHandler: hkid:" + str(hkid))
                hk = self.llh.getHotkeyById(hkid)
                self._logger.debug("_deleteButtonHandler: hk: " + str(hk))
                if (hk):
                    self.llh.removeHotkey(hk)
                    self.updateTable()
        
        
    def updateTable(self, current=None):
        table = self.widget.tableWidget
        table.clear()
        table.setRowCount(len(self.llh.Hotkeys))
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["key", "keycode", "modifiers" ,"action", "params", "enabled"])
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setColumnHidden(1, True)
        table.setColumnHidden(5, True)

        
        selected = None        
        
        for row, hk in enumerate(self.llh.Hotkeys):
            item = QTableWidgetItem(VK_KEY.get(hk.keycode))
            table.setItem(row, 0, item)
            if current is not None and current == id(hk):
                selected = item
            item.setData(QtCore.Qt.UserRole, QtCore.QVariant(id(hk)))
            
            item = QTableWidgetItem(str(hk.keycode))
            table.setItem(row, 1, item)

            item = QTableWidgetItem(hk.getModifierString())
            table.setItem(row, 2, item)

            action = Actions.get(hk.actionkey, None)
            if (action):
                item = QTableWidgetItem(action.name)
                
            table.setItem(row, 3, item)

            item = QTableWidgetItem(str(hk.params))
            table.setItem(row, 4, item)
            item = QTableWidgetItem(str(hk.enabled))
            table.setItem(row, 5, item)
            
            table.resizeColumnsToContents()
            if selected is not None:
                selected.setSelected(True)
                table.setCurrentItem(selected)
                table.scrollToItem(selected)


    

import ctypes
from ctypes import wintypes
from ctypes import windll
from win32gui import GetWindowText, GetForegroundWindow
import threading
import time

KeyEvent=namedtuple("KeyEvent",(['event_type', 'key_code',
                                             'scan_code', 'alt_pressed',
                                             'time']))
handlers=[]

class Hotkey():
    def __init__(self, keycode=None, actionkey=None, control=False, alt=False, shift=False, enabled=True, params=None):
        self.keycode = keycode
        self.actionkey = actionkey
        self.control = control
        self.alt = alt
        self.shift = shift
        self.enabled = enabled
        self.params = params
     
    def getModifierString(self):
        seperator = " "
        modifiers = []
        if self.control:
            modifiers.append("ctrl")
        if self.alt:
            modifiers.append("alt")
        if self.shift:
            modifiers.append("shift")
            
        retstr = seperator.join(modifiers)
        return retstr


class LLHookey(QtCore.QObject):
    Hotkeys=[]
    _signalKeyEvent = QtCore.pyqtSignal(KeyEvent)
  
    def __init__(self):
        super().__init__()
        self.ctrldown = False
        self.windown = False
        self.shiftdown = False
        self.altdown = False
        
        self.allKeysDisabled = False
        
        self._signalKeyEvent.connect(self._onKeyEvent)
        handlers.append(self._handleKeyHookEvent)
        
        t = threading.Thread(target=listener)
        t.daemon = True
        t.start()

        
    def _handleKeyHookEvent(self, event):
        self._signalKeyEvent.emit(event)        
        
    @QtCore.pyqtSlot(KeyEvent)
    def _onKeyEvent(self, event):
        #print("_onKeyEvent: " + event);
        self.altdown = event.alt_pressed
        
        if(event.event_type == 'key up'):
            if(event.key_code == 160 or event.key_code == 161):
                self.shiftdown = False
            if(event.key_code == 162 or event.key_code == 163):
                self.ctrldown = False
            if(event.key_code == 164 or event.key_code == 165 or event.key_code == 18):
                self.altdown = False
            if(event.key_code == 91):
                self.windown = False
        if(event.event_type == 'key down'):
            if(event.key_code == 160 or event.key_code == 161):
                self.shiftdown = True
            if(event.key_code == 162 or event.key_code == 163):
                self.ctrldown = True
            if(event.key_code == 164 or event.key_code == 165 or event.key_code == 18):
                self.altdown = True
            if(event.key_code == 91):
                self.windown = True

            activeWin = GetWindowText(GetForegroundWindow())
            if (activeWin != "Fallout4"):
                return
                
            for hk in self.Hotkeys:
                if (hk.keycode == event.key_code
                and hk.control == self.ctrldown
                and hk.shift == self.shiftdown
                and hk.alt == self.altdown):

                    action = Actions.get(hk.actionkey, None)
                    if ( (action and hk.enabled) 
                    and ( not self.allKeysDisabled or hk.actionkey == 'toggleAllHotkeys') ):
                        if(hk.params):
                            args = hk.params
                            try:
                                action.action(*args)
                            except:
                                action.action(hk.params)
                        else:
                            action.action()
                        
                        ### This is a vile hack to allow each rpc call to complete
                        ### before sending the next in cases where a single hotkey
                        ### is bound to multiple actions
                        ### It'll do for now, but should really find a better way 
                        ### of handling this, queue action method on datamanager.py 
                        ### perhaps?
                        time.sleep(0.1)

    def addHotkey(self, hotkey):
        self.Hotkeys.append( hotkey )

    def removeHotkey(self, hotkey):
        self.Hotkeys.remove(hotkey)
        
    def removeAllHotkeys(self):
        self.Hotkeys.clear()

    def toggleAllHotkeys(self):
        self.allKeysDisabled = not self.allKeysDisabled
        
    def toggleHotkey(self, hotkey):
        hotkey.enabled = not hotkey.enabled
        
    def disableHotkey(self, hotkey):
        hotkey.enabled = False

    def enableHotkey(self, hotkey):
        hotkey.enabled = True
                
    def getHotkeys(self):
        return self.Hotkeys
        
    def getHotkeyById(self, hkid):
        for hk in self.Hotkeys:
            if (id(hk) == hkid):
                return hk

        return None
    
        
def listener():
    try:
        #print("LLHookey: in listener")
        from ctypes import windll, CFUNCTYPE, POINTER, c_int, c_void_p, byref
        import atexit
        event_types = {0x100: 'key down', #WM_KeyDown for normal keys
           0x101: 'key up', #WM_KeyUp for normal keys
           0x104: 'key down', # WM_SYSKEYDOWN, used for Alt key.
           0x105: 'key up', # WM_SYSKEYUP, used for Alt key.
          }
        def low_level_handler(nCode, wParam, lParam):
            
            event = KeyEvent(event_types[wParam], lParam[0], lParam[1],
                              lParam[2] == 32, lParam[3])
            for h in handlers:
                h(event)
            #Be nice, return next hook
            return windll.user32.CallNextHookEx(hook_id, nCode, wParam, lParam)
    
        
        # Our low level handler signature.
        CMPFUNC = CFUNCTYPE(c_int, c_int, c_int, POINTER(c_void_p))
        # Convert the Python handler into C pointer.
        pointer = CMPFUNC(low_level_handler)
        #Added 4-18-15 for move to ctypes:
        windll.kernel32.GetModuleHandleW.restype = wintypes.HMODULE
        windll.kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
        # Hook both key up and key down events for common keys (non-system).
        hook_id = windll.user32.SetWindowsHookExA(0x00D, pointer,
                                                 windll.kernel32.GetModuleHandleW(None), 0)
    
        # Register to remove the hook when the interpreter exits.
        atexit.register(windll.user32.UnhookWindowsHookEx, hook_id)
        msg = windll.user32.GetMessageW(None, 0, 0,0)
        windll.user32.TranslateMessage(byref(msg))
        windll.user32.DispatchMessageW(byref(msg))
    except:
        traceback.print_exc(file=sys.stdout)
    

VK_CODE = OrderedDict()
    
VK_CODE['backspace'] = 0x08
VK_CODE['tab'] = 0x09
VK_CODE['clear'] = 0x0C
VK_CODE['enter'] = 0x0D
VK_CODE['shift'] = 0x10
VK_CODE['ctrl'] = 0x11
VK_CODE['alt'] = 0x12
VK_CODE['pause'] = 0x13
VK_CODE['caps_lock'] = 0x14
VK_CODE['esc'] = 0x1B
VK_CODE['spacebar'] = 0x20
VK_CODE['page_up'] = 0x21
VK_CODE['page_down'] = 0x22
VK_CODE['end'] = 0x23
VK_CODE['home'] = 0x24
VK_CODE['left_arrow'] = 0x25
VK_CODE['up_arrow'] = 0x26
VK_CODE['right_arrow'] = 0x27
VK_CODE['down_arrow'] = 0x28
VK_CODE['select'] = 0x29
VK_CODE['print'] = 0x2A
VK_CODE['execute'] = 0x2B
VK_CODE['print_screen'] = 0x2C
VK_CODE['ins'] = 0x2D
VK_CODE['del'] = 0x2E
VK_CODE['help'] = 0x2F
VK_CODE['0'] = 0x30
VK_CODE['1'] = 0x31
VK_CODE['2'] = 0x32
VK_CODE['3'] = 0x33
VK_CODE['4'] = 0x34
VK_CODE['5'] = 0x35
VK_CODE['6'] = 0x36
VK_CODE['7'] = 0x37
VK_CODE['8'] = 0x38
VK_CODE['9'] = 0x39
VK_CODE['a'] = 0x41
VK_CODE['b'] = 0x42
VK_CODE['c'] = 0x43
VK_CODE['d'] = 0x44
VK_CODE['e'] = 0x45
VK_CODE['f'] = 0x46
VK_CODE['g'] = 0x47
VK_CODE['h'] = 0x48
VK_CODE['i'] = 0x49
VK_CODE['j'] = 0x4A
VK_CODE['k'] = 0x4B
VK_CODE['l'] = 0x4C
VK_CODE['m'] = 0x4D
VK_CODE['n'] = 0x4E
VK_CODE['o'] = 0x4F
VK_CODE['p'] = 0x50
VK_CODE['q'] = 0x51
VK_CODE['r'] = 0x52
VK_CODE['s'] = 0x53
VK_CODE['t'] = 0x54
VK_CODE['u'] = 0x55
VK_CODE['v'] = 0x56
VK_CODE['w'] = 0x57
VK_CODE['x'] = 0x58
VK_CODE['y'] = 0x59
VK_CODE['z'] = 0x5A
VK_CODE['numpad_0'] = 0x60
VK_CODE['numpad_1'] = 0x61
VK_CODE['numpad_2'] = 0x62
VK_CODE['numpad_3'] = 0x63
VK_CODE['numpad_4'] = 0x64
VK_CODE['numpad_5'] = 0x65
VK_CODE['numpad_6'] = 0x66
VK_CODE['numpad_7'] = 0x67
VK_CODE['numpad_8'] = 0x68
VK_CODE['numpad_9'] = 0x69
VK_CODE['multiply_key'] = 0x6A
VK_CODE['add_key'] = 0x6B
VK_CODE['separator_key'] = 0x6C
VK_CODE['subtract_key'] = 0x6D
VK_CODE['decimal_key'] = 0x6E
VK_CODE['divide_key'] = 0x6F
VK_CODE['F1'] = 0x70
VK_CODE['F2'] = 0x71
VK_CODE['F3'] = 0x72
VK_CODE['F4'] = 0x73
VK_CODE['F5'] = 0x74
VK_CODE['F6'] = 0x75
VK_CODE['F7'] = 0x76
VK_CODE['F8'] = 0x77
VK_CODE['F9'] = 0x78
VK_CODE['F10'] = 0x79
VK_CODE['F11'] = 0x7A
VK_CODE['F12'] = 0x7B
VK_CODE['F13'] = 0x7C
VK_CODE['F14'] = 0x7D
VK_CODE['F15'] = 0x7E
VK_CODE['F16'] = 0x7F
VK_CODE['F17'] = 0x80
VK_CODE['F18'] = 0x81
VK_CODE['F19'] = 0x82
VK_CODE['F20'] = 0x83
VK_CODE['F21'] = 0x84
VK_CODE['F22'] = 0x85
VK_CODE['F23'] = 0x86
VK_CODE['F24'] = 0x87
VK_CODE['num_lock'] = 0x90
VK_CODE['scroll_lock'] = 0x91
VK_CODE['left_shift'] = 0xA0
VK_CODE['right_shift '] = 0xA1
VK_CODE['left_control'] = 0xA2
VK_CODE['right_control'] = 0xA3
VK_CODE['left_menu'] = 0xA4
VK_CODE['right_menu'] = 0xA5
VK_CODE['browser_back'] = 0xA6
VK_CODE['browser_forward'] = 0xA7
VK_CODE['browser_refresh'] = 0xA8
VK_CODE['browser_stop'] = 0xA9
VK_CODE['browser_search'] = 0xAA
VK_CODE['browser_favorites'] = 0xAB
VK_CODE['browser_start_and_home'] = 0xAC
VK_CODE['volume_mute'] = 0xAD
VK_CODE['volume_Down'] = 0xAE
VK_CODE['volume_up'] = 0xAF
VK_CODE['next_track'] = 0xB0
VK_CODE['previous_track'] = 0xB1
VK_CODE['stop_media'] = 0xB2
VK_CODE['play/pause_media'] = 0xB3
VK_CODE['start_mail'] = 0xB4
VK_CODE['select_media'] = 0xB5
VK_CODE['start_application_1'] = 0xB6
VK_CODE['start_application_2'] = 0xB7
VK_CODE['attn_key'] = 0xF6
VK_CODE['crsel_key'] = 0xF7
VK_CODE['exsel_key'] = 0xF8
VK_CODE['play_key'] = 0xFA
VK_CODE['zoom_key'] = 0xFB
VK_CODE['clear_key'] = 0xFE
VK_CODE['+'] = 0xBB
VK_CODE[','] = 0xBC, 
VK_CODE['-'] = 0xBD
VK_CODE['.'] = 0xBE
VK_CODE['/'] = 0xBF
#VK_CODE['`'] = 0xC0,    #us layout?
VK_CODE["'"] = 0xC0    #uk\euro layout
VK_CODE['`'] = 0xDF    #uk\euro layout
VK_CODE[';'] = 0xBA
VK_CODE['['] = 0xDB
VK_CODE['\\'] = 0xDC
VK_CODE[']'] = 0xDD
#VK_CODE["'"]:0xDE,    # us layout?
VK_CODE['#'] = 0xDE    #uk\euro layout
VK_KEY = {v: k for k, v in VK_CODE.items()}


        
