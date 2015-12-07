# -*- coding: utf-8 -*-


import os
import sys
import importlib
import traceback
import platform
import logging.config
from PyQt5 import QtWidgets, QtCore, uic
from pypipboy.network import NetworkChannel
from pypipboy.datamanager import PipboyDataManager
from dialogs.selecthostdialog import SelectHostDialog
from dialogs.connecthostdialog import ConnectHostDialog
from widgets.widgets import ModuleHandle 


class ApplicationStyle(QtCore.QObject):
    def __init__(self, app, name, styledir):
        self.app = app
        self.name = name
        self.styledir = styledir


# Application Main-Window
class PipboyMainWindow(QtWidgets.QMainWindow):
    # Signal that is emitted when the application should be closed.
    signalWantsToQuit = QtCore.pyqtSignal()
    
    # Constructor
    def __init__(self, parent = None):
        super().__init__(parent)
        uic.loadUi('ui/mainwindow.ui', self)
        self.connectionStatusLabel = QtWidgets.QLabel("No Connection")
        self.statusbar.addPermanentWidget(self.connectionStatusLabel)
        self.setCentralWidget(None) # damn thing cannot be removed in Qt-Designer
        self.setDockNestingEnabled(True)
        self.setTabPosition(QtCore.Qt.AllDockWidgetAreas, QtWidgets.QTabWidget.North)
        
    # Init function that is called after everything has been set up
    def init(self, app, networkchannel, datamanager):
        wstate = self.windowState()
        if wstate == QtCore.Qt.WindowFullScreen:
            self.wstateBeforeFullscreen = QtCore.Qt.WindowNoState
            self.actionFullscreen.setChecked(True)
        else:
            self.wstateBeforeFullscreen = wstate
            self.actionFullscreen.setChecked(False)
        self.actionFullscreen.toggled.connect(self.setFullscreen)
        
    def closeEvent(self, event):
        event.ignore() # We do our own shutdown handling
        self.signalWantsToQuit.emit()
        
    @QtCore.pyqtSlot(bool)        
    def setFullscreen(self, fullscreen):
        if fullscreen:
            self.wstateBeforeFullscreen = self.windowState()
            self.setWindowState(QtCore.Qt.WindowFullScreen)
        else:
            self.setWindowState(self.wstateBeforeFullscreen)



# Main application class
class PyPipboyApp(QtWidgets.QApplication):
    
    PROGRAM_NAME = 'Unofficial Pipboy Application'
    PROGRAM_VERSION = 'v0.1-prealpha'
    PROGRAM_ABOUT_TEXT = 'ToDo: About Text'
    PROGRAM_ABOUT_LICENSE = 'ToDo'
    PROGRAM_ABOUT_COPYRIGHT = 'Copyright (c) 2015 matzman666'
    PROGRAM_WIDGETS_DIR = 'widgets'
    PROGRAM_STYLES_DIR = 'styles'
    
    # public signals
    signalConnectToHost = QtCore.pyqtSignal(str, int, bool)
    signalShowWarningMessage = QtCore.pyqtSignal(str, str)
    signalRequestQuit = QtCore.pyqtSignal()
    
    # internal signals
    _signalConnectToHostFinished = QtCore.pyqtSignal(bool, str)
    _signalAutodiscoveryFinished = QtCore.pyqtSignal()
    
    #constructor
    def __init__(self, args):
        super().__init__(args)
        # Prepare QSettings for application-wide use
        QtCore.QCoreApplication.setOrganizationName("PyPipboyApp")
        QtCore.QCoreApplication.setApplicationName("PyPipboyApp")
        self.settings = QtCore.QSettings()
        # Init PyPipboy communication layer
        self.dataManager = PipboyDataManager()
        self.networkChannel = self.dataManager.networkchannel
        self.networkChannel.registerConnectionListener(self._onConnectionStateChange)
        # Connect internal signals
        self._signalAutodiscoveryFinished.connect(self._slotAutodiscoveryFinished)
        self.signalConnectToHost.connect(self.connectToHost)
        self._signalConnectToHostFinished.connect(self._slotConnectToHostFinished)
        self.signalShowWarningMessage.connect(self.showWarningMessage)
        self.signalRequestQuit.connect(self.requestQuit)
        self._connectHostMessageBox = None
        self._connectHostThread = None
        self._logger = logging.getLogger('pypipboyapp.main')
        
        # Import hotkeymanager only on windows
        if platform.system() == 'Windows':
            import hotkeymanager
            self.hotkeymanager = hotkeymanager.HotkeyManager()
            win_event_filter = hotkeymanager.WinEventFilter(hm)
            pipboyApp.installNativeEventFilter(win_event_filter)     
        else:
            self.hotkeymanager = None
    
    
    # run the application
    def run(self):
        self.mainWindow = PipboyMainWindow()
        # Load Styles
        self._loadStyles()
        # Load widgets
        self._loadWidgets()
        # Restore saved window state
        savedGeometry = self.settings.value('mainwindow/geometry')
        if savedGeometry:
            self.mainWindow.restoreGeometry(savedGeometry)
        savedState = self.settings.value('mainwindow/windowstate')
        if savedState:
            self.mainWindow.restoreState(savedState)
        # connect with main window
        self.mainWindow.actionConnect.triggered.connect(self.startAutoDiscovery)
        self.mainWindow.actionConnectTo.triggered.connect(self.showConnectToDialog)
        self.mainWindow.actionDisconnect.triggered.connect(self.disconnect)
        self.mainWindow.actionQuit.triggered.connect(self.requestQuit)
        self.mainWindow.signalWantsToQuit.connect(self.requestQuit)
        self.mainWindow.actionShowAbout.triggered.connect(self.showAboutDialog)
        self.mainWindow.actionShowAboutQt.triggered.connect(self.aboutQt)
        self.mainWindow.actionAuto_Connect_on_Start_up.triggered.connect(self.autoConnectToggled)
        # Main window is ready, so show it
        self.mainWindow.init(self, self.networkChannel, self.dataManager)
        self._initWidgets()
        self.mainWindow.show()
        # start main event loop
        if int(self.settings.value('mainwindow/autoconnect', 0)):
            self.mainWindow.actionAuto_Connect_on_Start_up.setChecked(True)
            host = 'localhost'
            port = 27000
            if self.settings.value('mainwindow/lasthost'):
                host = self.settings.value('mainwindow/lasthost')
            if self.settings.value('mainwindow/lastport'):
                port = int(self.settings.value('mainwindow/lastport'))
            self.signalConnectToHost.emit(host, port, False)
        sys.exit(self.exec_())

    @QtCore.pyqtSlot(bool)
    def autoConnectToggled(self, value):
        self.settings.setValue('mainwindow/autoconnect', int(value))

        
    # Start auto discovery (non-blocking)
    # Auto discovery is done in its own thread, we don't want to block the gui
    # returns true when the thread was successfully started
    @QtCore.pyqtSlot()
    def startAutoDiscovery(self, busyDialog = True):
        if not self.networkChannel.isConnected:
            if busyDialog:
                self._autodiscoverMessageBox = QtWidgets.QMessageBox(self.mainWindow)
                self._autodiscoverMessageBox.setWindowTitle('Autodiscovery')
                self._autodiscoverMessageBox.setText('Searching for host, please wait.')
                self._autodiscoverMessageBox.setStandardButtons(QtWidgets.QMessageBox.NoButton)
                self._autodiscoverMessageBox.show()
            else:
                self._autodiscoverMessageBox = None
            parentself = self # Capture self for inner class
            class _AutodiscoverThread(QtCore.QThread):
                def run(self):
                    parentself._logger.debug('Starting Autodiscovery Thread')
                    parentself._autodiscoverHosts = NetworkChannel.discoverHosts()
                    parentself._signalAutodiscoveryFinished.emit()
                    parentself._logger.debug('Autodiscovery Thread finished')
            self._autodiscoverThread = _AutodiscoverThread()
            self._autodiscoverThread.start()
            return True
        else:
            return False
        
    # internal slot connected to the 'auto discovery thread is finished' signal
    @QtCore.pyqtSlot()
    def _slotAutodiscoveryFinished(self):
        # close busy dialog
        if self._autodiscoverMessageBox:
            self._autodiscoverMessageBox.hide()
            self._autodiscoverMessageBox = None
        # Wait for thread before deleting it
        self._autodiscoverThread.wait()
        self._autodiscoverThread = None
        # Let the user select a host
        selectDialog = SelectHostDialog(self.mainWindow)
        if selectDialog.exec(self._autodiscoverHosts):
            host = selectDialog.getSelectedHost()
            if host:
                self.signalConnectToHost.emit(host['addr'], NetworkChannel.PIPBOYAPP_PORT, False)
                
    # Shows a 'connect to host' dialog and then connects 
    @QtCore.pyqtSlot()        
    def showConnectToDialog(self):
        if not self.networkChannel.isConnected:
            connectDialog = ConnectHostDialog(self.mainWindow)
            host = 'localhost'
            port = 27000
            if self.settings.value('mainwindow/lasthost'):
                host = self.settings.value('mainwindow/lasthost')
            if self.settings.value('mainwindow/lastport'):
                port = self.settings.value('mainwindow/lastport')
            connectDialog.hostInput.setText(host)
            connectDialog.portInput.setText(str(port))
            if connectDialog.exec():
                try:
                    host = connectDialog.hostInput.text()
                    port = int(connectDialog.portInput.text())
                    retry = connectDialog.retryCheckbox.isChecked()
                    #self.signalConnectToHost.emit(host, port, retry)
                    self.connectToHost(host, port, retry)
                except ValueError as e:
                    QtWidgets.QMessageBox.warning(self.mainWindow, 'Connection to host failed', 
                            'Caught exception while parsing port: ' + str(e),
                            QtWidgets.QMessageBox.Ok)
            
                    
    # connect to specified host (non blocking)
    # connect happens in its own thread
    # returns true when the thread was successfully started
    @QtCore.pyqtSlot(str, int, bool, bool)        
    def connectToHost(self, host, port, retry = False,  busydialog= True):
        if not self.networkChannel.isConnected:
            self._logger.info('Connecting to host ' + host + ':' + str(port) + ' Retry=' + str(retry))
            # show busy dialog
            if busydialog:
                self._connectHostMessageBox = QtWidgets.QMessageBox(self.mainWindow)
                self._connectHostMessageBox.setWindowTitle('Connecting')
                self._connectHostMessageBox.setText('Connecting to host, please wait.')
                self._connectHostMessageBox.setStandardButtons(QtWidgets.QMessageBox.Cancel)
                self._connectHostMessageBox.buttonClicked.connect(self.cancelConnectToHost)
                self._connectHostMessageBox.show()
            else:
                self._connectHostMessageBox = None
            # start connect thread
            parentself = self # capture self for inner class
            if not self._connectHostThread or not self._connectHostThread.isRunning():
                class _ConnectHostThread(QtCore.QThread):
                    def run(self):
                        parentself._logger.debug('Connect to Host Thread started')
                        self._cancelThread = False
                        while not self._cancelThread:
                            try:
                                if not parentself.networkChannel.connect(host, port = port):
                                    parentself._signalConnectToHostFinished.emit(False, 'Host denied connection.')
                                    break
                                else:
                                    parentself._signalConnectToHostFinished.emit(True, '')
                                    break
                            except Exception as e:
                                if not retry:
                                    parentself._signalConnectToHostFinished.emit(False, 'Caught exception while connecting to host: ' + str(e))
                                    break
                        parentself._logger.debug('Connect to Host Thread finished')
                self._connectHostThread = _ConnectHostThread()
                self._connectHostThread.start()
                return True
            else:
                QtWidgets.QMessageBox.warning(self.mainWindow, 'Connection to host failed', 
                        'There is another connection thread already running', QtWidgets.QMessageBox.Ok)
                return False
        else:
            return False
            
    # Cancels any currently running 'connect to host' operation
    @QtCore.pyqtSlot(QtWidgets.QAbstractButton)        
    def cancelConnectToHost(self, button):
        if self._connectHostThread and self._connectHostThread.isRunning():
            self._logger.info('Connect to Host Thread Cancel Request received')
            self._connectHostThread._cancelThread = True
            self.networkChannel.cancelConnectionAttempt()
            try:
                self._connectHostThread.wait()
            except:
                pass
            self._connectHostThread = None
                    
    
    # internal slot connected to the 'connect thread is finished' signal
    @QtCore.pyqtSlot(bool, str)        
    def _slotConnectToHostFinished(self, status, msg):
        # hide busy dialog
        if self._connectHostMessageBox:
            self._connectHostMessageBox.hide()
            self._connectHostMessageBox = None
        # delete thread
        if self._connectHostThread:
            self._connectHostThread.wait()
            self._connectHostThread = None
        # Handle errors
        if status:
            pass
        else:
            QtWidgets.QMessageBox.warning(self.mainWindow, 'Connection to host failed', msg)
                
    # Shows a warning message dialog
    @QtCore.pyqtSlot(str, str)        
    def showWarningMessage(self, title, text):
            QtWidgets.QMessageBox.warning(self.mainWindow, title, text)
            
    
    # disconnects the current network session
    @QtCore.pyqtSlot()        
    def disconnect(self):
        if self.networkChannel.isConnected:
            self.networkChannel.disconnect()

    # Request the user to quit, saves state and quits
    @QtCore.pyqtSlot()        
    def requestQuit(self):
        # do you really wanna
        if not self.settings.value('mainwindow/promptBeforeQuit', True) or  QtWidgets.QMessageBox.question(self.mainWindow, 'Close', 'Are you sure you want to quit?',
                            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                            QtWidgets.QMessageBox.No) == QtWidgets.QMessageBox.Yes:
            # disconnect any network sessions
            if self.networkChannel.isConnected:
                self.networkChannel.disconnect()
            # save state
            self.settings.setValue('mainwindow/geometry', self.mainWindow.saveGeometry())
            self.settings.setValue('mainwindow/windowstate', self.mainWindow.saveState())
            self.settings.sync()
            # quit
            self.quit()
    
    # Shows the about dialog
    def showAboutDialog(self):
        QtWidgets.QMessageBox.about(self.mainWindow, 'About ' + self.PROGRAM_NAME,
            self.PROGRAM_NAME + ' ' + self.PROGRAM_VERSION + '\n\n' +
            self.PROGRAM_ABOUT_TEXT + '\n\n' + 
            'License:\n\n' + self.PROGRAM_ABOUT_LICENSE + ' \n\n' +
            self.PROGRAM_ABOUT_COPYRIGHT)
        
    # event listener for pypipboy network state events
    def _onConnectionStateChange(self, state, errstatus = 0, errmsg = ''):
        self._logger.info('Connection State Changed: ' + str(state) + ' - ' + str(errstatus) + ' - ' + str(errmsg))
        if state: # connect
            # menu management stuff
            self.mainWindow.actionConnect.setEnabled(False)
            self.mainWindow.actionConnectTo.setEnabled(False)
            self.mainWindow.actionDisconnect.setEnabled(True)
            # status bar update
            tmp = str(self.networkChannel.hostAddr) + ':' + str(self.networkChannel.hostPort) + ' ('
            tmp += 'Version: ' + str(self.networkChannel.hostVersion) + ", "
            tmp += 'Lang: ' +str(self.networkChannel.hostLang) + ")"
            self.mainWindow.connectionStatusLabel.setText('Connected to ' + tmp)
            self.settings.setValue('mainwindow/lasthost', str(self.networkChannel.hostAddr))
            self.settings.setValue('mainwindow/lastport', self.networkChannel.hostPort)

            
        else: # disconnect
            # menu management stuff
            self.mainWindow.actionConnect.setEnabled(True)
            self.mainWindow.actionConnectTo.setEnabled(True)
            self.mainWindow.actionDisconnect.setEnabled(False)
            # status bar update
            self.mainWindow.connectionStatusLabel.setText('No Connection')
            # error handling
            if errstatus != 0:
                self.signalShowWarningMessage.emit('Connection Error', 'Connection Error: ' + str(errmsg))
                
    # load widgets
    def _loadWidgets(self):
        self.widgets = list()
        self.modulehandles = dict()
        for dir in os.listdir(self.PROGRAM_WIDGETS_DIR):
            dirpath = os.path.join(self.PROGRAM_WIDGETS_DIR, dir)
            if dir != 'shared' and not dir.startswith('__') and os.path.isdir(dirpath):
                self._logger.debug('Tyring to load widget dir "' + dir + '"')
                module = None
                try:
                    module = importlib.import_module(self.PROGRAM_WIDGETS_DIR + '.' + dir + '.info')
                    info = getattr(module, 'ModuleInfo')
                    if info:
                        self._logger.debug('Found info module')
                        if info.LABEL in self.modulehandles:
                            raise Exception('Module with same name already exists.')
                        handle = ModuleHandle(self, dirpath)
                        self.modulehandles[info.LABEL] = handle
                        widgets = info.createWidgets(handle, self.mainWindow)
                        if widgets:
                            if not type(widgets) == list:
                                nl = list()
                                nl.append(widgets)
                                widgets = nl
                            i = 0
                            for w in widgets:
                                w.setObjectName(info.LABEL + '_' + str(i))
                                self.mainWindow.addDockWidget(QtCore.Qt.TopDockWidgetArea, w)
                                self.widgets.append(w)
                                i += 1
                            self._logger.info('Successfully loaded widget dir "' + dir + '"')
                        else:
                            self._logger.warning('Could not load widget dir "' + dir + '": No widgets returned')
                    else:
                        self._logger.warning('Could not load widget dir "' + dir + '": No Info')
                except Exception as e:
                    self._logger.warning('Could not load widget dir "' + dir + '": ' + str(e))
                    traceback.print_exc(file=sys.stdout)
                    
    # load widgets
    def _initWidgets(self):
        for w in self.widgets:
            w.init(self, self.dataManager)
            
    def _loadStyles(self):
        self.styles = dict()
        for dir in os.listdir(self.PROGRAM_STYLES_DIR):
            dirpath = os.path.join(self.PROGRAM_STYLES_DIR, dir)
            if not dir.startswith('__') and dir != 'default' and os.path.isdir(dirpath):
                self._logger.debug('Tyring to add style "' + dir + '"')
                stylefile = os.path.join(dirpath, 'style.qss')
                if os.path.isfile(stylefile):
                    style = ApplicationStyle(self, dir, dirpath)
                    self.styles[dir] = style
                    self._logger.info('Added style "' + dir + '"')
                else:
                    self._logger.warn('Could not add style "' + dir + '": No style.qss found')
        menu = self.mainWindow.menuStyles
        def _genSlotSetStyles(app, name):
            return lambda : app.setStyle(name)
        for s in self.styles:
            action = menu.addAction(self.styles[s].name)
            action.triggered.connect(_genSlotSetStyles(self, self.styles[s].name))
        self.mainWindow.actionStylesDefault.triggered.connect(_genSlotSetStyles(self, 'default'))
        if (self.settings.value('mainwindow/lastStyle')):
            self.setStyle(self.settings.value('mainwindow/lastStyle'))
        
            
    def setStyle(self, name):
        if name == 'default':
            self.setStyleSheet('')
        else:
            style = self.styles[name]
            stylefilepath = os.path.join(style.styledir, 'style.qss')
            self.setStyleSheet('file:///' + stylefilepath)
        self.settings.setValue('mainwindow/lastStyle', name) 

            
# Main entry point
if __name__ == "__main__":
    try:
        logging.config.fileConfig('logging.config')
    except Exception as e:
        logging.basicConfig(level=logging.WARN)
        logging.error('Error while reading logging config: ' + str(e))
    pipboyApp = PyPipboyApp(sys.argv)
    pipboyApp.run()
