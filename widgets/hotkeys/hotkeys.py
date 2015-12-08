# -*- coding: utf-8 -*-
import datetime
import os
from PyQt5 import QtWidgets, QtCore, uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from pypipboy.types import eValueType
from .. import widgets

import logging

class HotkeyWidget(widgets.WidgetBase):
    _signalInfoUpdated = QtCore.pyqtSignal()
    
    hotkeysModel = QStandardItemModel()
    
    def __init__(self, mhandle, parent):
        super().__init__('HotkeyWidget', parent)
        self.widget = uic.loadUi(os.path.join(mhandle.basepath, 'ui', 'hotkeys.ui'))
        self._logger = logging.getLogger('pypipboyapp.llhookey')
        self.setWidget(self.widget)
        self.pipPlayerInfo = None
        self.pipInventoryInfo = None
        
        self._signalInfoUpdated.connect(self._slotInfoUpdated)
        
    def init(self, app, datamanager):
        super().init(app, datamanager)
        self.dataManager = datamanager
        self.dataManager.registerRootObjectListener(self._onPipRootObjectEvent)
        self._app = app
        
        self.widget.pushButton.clicked.connect(self._testButtonHandler)
        
        self.llh = LLHookey()

        #self.llh.addHotkey(223, action=self.useJet) #`
        #self.llh.addHotkey(36, action=self.useItemByName, params=("48", "psycho")) #home
        #self.llh.addHotkey(89, action=datamanager.rpcUseStimpak) #y
        #self.llh.addHotkey(71, action=self.equipNextGrendae) #g
        #self.llh.addHotkey(188, action=self.useItemByName, params=("29", "formal hat")) #,
        #self.llh.addHotkey(190, action=self.useItemByFormID, params=("43", 598551)) #.
        
        self.llh.addHotkey( Hotkey(keycode=VK_CODE.get('`'), action=self.useJet) )
        self.llh.addHotkey( Hotkey(keycode=VK_CODE.get('g'), action=self.equipNextGrendae) )
        self.llh.addHotkey( Hotkey(keycode=VK_CODE.get('y'), action=datamanager.rpcUseStimpak))
        self.llh.addHotkey( Hotkey(keycode=VK_CODE.get('h'), control=True, action=self.llh.toggleAllHotkeys) )

        #h1 = Hotkey(keycode=VK_CODE.get(','), action=self.useItemByName, params=("29", "formal hat"))
        #h2 = Hotkey(keycode=VK_CODE.get('/'), action=self.llh.removeHotkey, params=(h1))
        #h3 = Hotkey(keycode=VK_CODE.get('/'), action=self.llh.disableHotkey, params=(h1))
        #self.llh.addHotkey( h1 )
        #self.llh.addHotkey( h2 )
        #self.llh.addHotkey( h3 )
        #self.llh.addHotkey( Hotkey(keycode=VK_CODE.get('#'), action=self.llh.removeAllHotkeys) )
        
        

        self.availableGrenades = []
        
    def equipNextGrendae(self):
        getIndex = 0
        numGrenades = len(self.availableGrenades)
        if (numGrenades > 0):
            for i in range(0, numGrenades):
                if (self.availableGrenades[i][1]):
                    getIndex = i + 1
                    break
                    
            if (getIndex == numGrenades):
                getIndex = 0
            
            self.useItemByName("43", self.availableGrenades[getIndex][0])
                
    def useJet(self):   
        self.useItemByName("48", "jet")

    def useItemByFormID(self,inventorySection, itemFormID):
        if (self.pipInventoryInfo):
            inventory = self.pipInventoryInfo.child(inventorySection)
            for i in range(0, inventory.childCount()):
                formid = inventory.child(i).child('formID').value()
                if (formid == itemFormID):
                    self.dataManager.rpcUseItem(inventory.child(i))

    def useItemByName(self,inventorySection, itemName):
        itemName = itemName.lower()
        if (self.pipInventoryInfo):
            inventory = self.pipInventoryInfo.child(inventorySection)
            for i in range(0, inventory.childCount()):
                name = inventory.child(i).child('text').value()
                if (name.lower() == itemName):
                    self.dataManager.rpcUseItem(inventory.child(i))

    def _onPipRootObjectEvent(self, rootObject):
        self.pipInventoryInfo = rootObject.child('Inventory')
        if self.pipInventoryInfo:
            self.pipInventoryInfo.registerValueUpdatedListener(self._onPipPlayerInfoUpdate, 1)
        self._signalInfoUpdated.emit()
        pass

    def _onPipPlayerInfoUpdate(self, caller, value, pathObjs):
        self._signalInfoUpdated.emit()
        
    @QtCore.pyqtSlot()
    def _slotInfoUpdated(self):
        self.availableGrenades = []
        if (self.pipInventoryInfo):
            weapons = self.pipInventoryInfo.child('43')
            for i in range(0, weapons.childCount()):
                equipped = False
                name = weapons.child(i).child('text').value()
                if (name.lower().find('mine') > -1 
                or name.lower().find('grenade') > -1 
                or name.lower().find('molotov') > -1 ):
                    count = str(weapons.child(i).child('count').value())
                    if (weapons.child(i).child('equipState').value() == 3):
                        equipped = True
                    
                    self.availableGrenades.append([name.lower(), equipped])
                    

    @QtCore.pyqtSlot()
    def _testButtonHandler(self):
        keys = self.llh.getHotkeys()
        for hk in keys:
            self.addToModel(hk )
        
    def addToModel(self, key):
    
        item = [
            QStandardItem(""),
            QStandardItem(str(key.keycode)),
            QStandardItem(str(key.control)),
            QStandardItem(str(key.alt)),
            QStandardItem(str(key.shift)),
            QStandardItem(str(key.action)),
            QStandardItem(str(key.params)),
            QStandardItem(str(key.enabled))
            ]
        

        self.hotkeysModel.insertRow(0,item)
        self.hotkeysModel.setHeaderData(0, QtCore.Qt.Horizontal, "key")
        self.hotkeysModel.setHeaderData(1, QtCore.Qt.Horizontal, "key_code")
        self.hotkeysModel.setHeaderData(2, QtCore.Qt.Horizontal, "ctrl")
        self.hotkeysModel.setHeaderData(3, QtCore.Qt.Horizontal, "alt")
        self.hotkeysModel.setHeaderData(4, QtCore.Qt.Horizontal, "shift")
        self.hotkeysModel.setHeaderData(5, QtCore.Qt.Horizontal, "action")
        self.hotkeysModel.setHeaderData(6, QtCore.Qt.Horizontal, "params")
        self.hotkeysModel.setHeaderData(7, QtCore.Qt.Horizontal, "enabled")
        
        self.widget.hotkeysView.setModel(self.hotkeysModel)

    

import ctypes
from ctypes import wintypes
from ctypes import windll
from collections import namedtuple
from win32gui import GetWindowText, GetForegroundWindow
#from win32api import MapVirtualKey
import threading


KeyEvent=namedtuple("KeyEvent",(['event_type', 'key_code',
                                             'scan_code', 'alt_pressed',
                                             'time']))
handlers=[]

class Hotkey():
    def __init__(self, keycode=None, action=None, control=False, alt=False, shift=False, enabled=True, params=None):
        self.keycode = keycode
        self.action = action
        self.control = control
        self.alt = alt
        self.shift = shift
        self.enabled = enabled
        self.params = params

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
        #print("_handleKeyHookEvent")
        self._signalKeyEvent.emit(event)        
        
    @QtCore.pyqtSlot(KeyEvent)
    def _onKeyEvent(self, event):
        activeWin = GetWindowText(GetForegroundWindow())
        if (activeWin != "Fallout4"):
            return
        
        #print("_onKeyEvent")
        if(event.event_type == 'key up'):
            if(event.key_code == 160 or event.key_code == 161):
                self.shiftdown = False
            if(event.key_code == 162 or event.key_code == 163):
                self.ctrldown = False
            if(event.key_code == 164):
                self.altdown = False
            if(event.key_code == 91):
                self.windown = False
        if(event.event_type == 'key down'):
            if(event.key_code == 160 or event.key_code == 161):
                self.shiftdown = True
            if(event.key_code == 162 or event.key_code == 163):
                self.ctrldown = True
            if(event.key_code == 164):
                self.altdown = True
            if(event.key_code == 91):
                self.windown = True
                
            for hk in self.Hotkeys:
                if (hk.keycode == event.key_code
                and hk.control == self.ctrldown
                and hk.shift == self.shiftdown
                and hk.alt == self.altdown):
                    if(hk.enabled and hk.action):
                        if (not self.allKeysDisabled or hk.action == self.toggleAllHotkeys):

                            if(hk.params):
                                args = hk.params
                                try:
                                    hk.action(*args)
                                except:
                                    hk.action(hk.params)
                            else:
                                hk.action()

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
        
                
    
        
def listener():
    #print("in listener")
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
        #print("hooked")
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
    
    
VK_CODE = {'backspace':0x08,
           'tab':0x09,
           'clear':0x0C,
           'enter':0x0D,
           'shift':0x10,
           'ctrl':0x11,
           'alt':0x12,
           'pause':0x13,
           'caps_lock':0x14,
           'esc':0x1B,
           'spacebar':0x20,
           'page_up':0x21,
           'page_down':0x22,
           'end':0x23,
           'home':0x24,
           'left_arrow':0x25,
           'up_arrow':0x26,
           'right_arrow':0x27,
           'down_arrow':0x28,
           'select':0x29,
           'print':0x2A,
           'execute':0x2B,
           'print_screen':0x2C,
           'ins':0x2D,
           'del':0x2E,
           'help':0x2F,
           '0':0x30,
           '1':0x31,
           '2':0x32,
           '3':0x33,
           '4':0x34,
           '5':0x35,
           '6':0x36,
           '7':0x37,
           '8':0x38,
           '9':0x39,
           'a':0x41,
           'b':0x42,
           'c':0x43,
           'd':0x44,
           'e':0x45,
           'f':0x46,
           'g':0x47,
           'h':0x48,
           'i':0x49,
           'j':0x4A,
           'k':0x4B,
           'l':0x4C,
           'm':0x4D,
           'n':0x4E,
           'o':0x4F,
           'p':0x50,
           'q':0x51,
           'r':0x52,
           's':0x53,
           't':0x54,
           'u':0x55,
           'v':0x56,
           'w':0x57,
           'x':0x58,
           'y':0x59,
           'z':0x5A,
           'numpad_0':0x60,
           'numpad_1':0x61,
           'numpad_2':0x62,
           'numpad_3':0x63,
           'numpad_4':0x64,
           'numpad_5':0x65,
           'numpad_6':0x66,
           'numpad_7':0x67,
           'numpad_8':0x68,
           'numpad_9':0x69,
           'multiply_key':0x6A,
           'add_key':0x6B,
           'separator_key':0x6C,
           'subtract_key':0x6D,
           'decimal_key':0x6E,
           'divide_key':0x6F,
           'F1':0x70,
           'F2':0x71,
           'F3':0x72,
           'F4':0x73,
           'F5':0x74,
           'F6':0x75,
           'F7':0x76,
           'F8':0x77,
           'F9':0x78,
           'F10':0x79,
           'F11':0x7A,
           'F12':0x7B,
           'F13':0x7C,
           'F14':0x7D,
           'F15':0x7E,
           'F16':0x7F,
           'F17':0x80,
           'F18':0x81,
           'F19':0x82,
           'F20':0x83,
           'F21':0x84,
           'F22':0x85,
           'F23':0x86,
           'F24':0x87,
           'num_lock':0x90,
           'scroll_lock':0x91,
           'left_shift':0xA0,
           'right_shift ':0xA1,
           'left_control':0xA2,
           'right_control':0xA3,
           'left_menu':0xA4,
           'right_menu':0xA5,
           'browser_back':0xA6,
           'browser_forward':0xA7,
           'browser_refresh':0xA8,
           'browser_stop':0xA9,
           'browser_search':0xAA,
           'browser_favorites':0xAB,
           'browser_start_and_home':0xAC,
           'volume_mute':0xAD,
           'volume_Down':0xAE,
           'volume_up':0xAF,
           'next_track':0xB0,
           'previous_track':0xB1,
           'stop_media':0xB2,
           'play/pause_media':0xB3,
           'start_mail':0xB4,
           'select_media':0xB5,
           'start_application_1':0xB6,
           'start_application_2':0xB7,
           'attn_key':0xF6,
           'crsel_key':0xF7,
           'exsel_key':0xF8,
           'play_key':0xFA,
           'zoom_key':0xFB,
           'clear_key':0xFE,
           '+':0xBB,
           ',':0xBC, 
           '-':0xBD,
           '.':0xBE,
           '/':0xBF,
           #'`':0xC0,    #us layout?
           "'":0xC0,    #uk\euro layout
           '`':0xDF,    #uk\euro layout
           ';':0xBA,
           '[':0xDB,
           '\\':0xDC,
           ']':0xDD,
           #"'":0xDE,    # us layout?
           '#':0xDE}    #uk\euro layout
VK_KEY = {v: k for k, v in VK_CODE.items()}


        
