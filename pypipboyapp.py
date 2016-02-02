# -*- coding: utf-8 -*-


import os, platform
import sys
import json
import time
import importlib
import traceback
import faulthandler
import logging.config
import threading
import urllib.request
from PyQt5 import QtGui, QtWidgets, QtCore, uic
from pypipboy.network import NetworkChannel
from pypipboy.datamanager import PipboyDataManager
from pypipboy.relayserver import RelayController
from dialogs.selecthostdialog import SelectHostDialog
from dialogs.connecthostdialog import ConnectHostDialog
from dialogs.relaysettingsdialog import RelaySettingsDialog
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
        if self.isFullScreen():
            self.actionFullscreen.setChecked(True)
        else:
            self.actionFullscreen.setChecked(False)
        self.actionFullscreen.toggled.connect(self.setFullscreen)
        
    def closeEvent(self, event):
        event.ignore() # We do our own shutdown handling
        self.signalWantsToQuit.emit()
        
    @QtCore.pyqtSlot(bool)        
    def setFullscreen(self, fullscreen):
        if fullscreen:
            self.showFullScreen()
        else:
            self.showMaximized()



# Main application class
class PyPipboyApp(QtWidgets.QApplication):
    
    PROGRAM_NAME = 'PyPipboyApp'
    PROGRAM_VERSION_MAJOR = 0
    PROGRAM_VERSION_MINOR = 0
    PROGRAM_VERSION_REV = 0
    PROGRAM_VERSION_SUFFIX = 'unknown'
    #PROGRAM_ABOUT_TEXT = 'ToDo: About Text'
    PROGRAM_ABOUT_LICENSE = 'GPL 3.0<br><br>Contains Graphical Assets owned by Bethesda and subject to their terms of service.'
    PROGRAM_ABOUT_AUTHORS = '<li>matzman666</li><li>akamal</li><li>killean</li><li>gwhittey</li>'
    PROGRAM_WIDGETS_DIR = 'widgets'
    PROGRAM_STYLES_DIR = 'styles'
    
    # public signals
    signalConnectToHost = QtCore.pyqtSignal(str, int, bool)
    signalShowWarningMessage = QtCore.pyqtSignal(str, str)
    signalRequestQuit = QtCore.pyqtSignal()
    
    # internal signals
    _signalConnectToHostFinished = QtCore.pyqtSignal(bool, str)
    _signalAutodiscoveryFinished = QtCore.pyqtSignal()
    _signalFinishedCheckVersion = QtCore.pyqtSignal(dict, bool, bool, str, bool)
    
    #constructor
    def __init__(self, args, inifile):
        super().__init__(args)
        self._logger = logging.getLogger('pypipboyapp.main')

        self.startedFromWin32Launcher = False;
        
        for i in range(0, len(args)):
            if args[i].lower() == '--startedfromwin32launcher':
                self.startedFromWin32Launcher = True

        # Prepare QSettings for application-wide use
        QtCore.QCoreApplication.setOrganizationName("PyPipboyApp")
        QtCore.QCoreApplication.setApplicationName("PyPipboyApp")
        if inifile:
            self._logger.info('Using ini-file "' + str(inifile) + '".')
            self.settings = QtCore.QSettings(inifile, QtCore.QSettings.IniFormat)
        elif platform.system() == 'Windows':
            self.settings = QtCore.QSettings(QtCore.QSettings.IniFormat, QtCore.QSettings.UserScope, "PyPipboyApp", "PyPipboyApp")
            # If there are no settings, copy existing settings from registry
            if len(self.settings.allKeys()) <= 0:
                registrySettings = QtCore.QSettings(QtCore.QSettings.NativeFormat, QtCore.QSettings.UserScope, "PyPipboyApp", "PyPipboyApp")
                for k in registrySettings.allKeys():
                    self.settings.setValue(k, registrySettings.value(k))
                    #registrySettings.remove(k)
                #registrySettings.sync()
        else: 
            # Non-Windows OS already use the ini-format, they just use another file-extension. That's why we stick with nativeFormat.
            self.settings = QtCore.QSettings(QtCore.QSettings.NativeFormat, QtCore.QSettings.UserScope, "PyPipboyApp", "PyPipboyApp")
        
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
        self._signalFinishedCheckVersion.connect(self._slotFinishedCheckVersion)
        self._connectHostMessageBox = None
        self._connectHostThread = None
        self._iwcEndpoints = dict()
        self.widgetMenu = QtWidgets.QMenu()
        
        pipboyAppIcon = QtGui.QIcon()
        pipboyAppIcon.addFile(os.path.join('ui', 'res', 'PyPipBoyApp-Launcher.ico'))
        self.setWindowIcon(pipboyAppIcon)
        
        try:
            versionFile = open('VERSION', 'r')
            versionJSON = json.loads(versionFile.read())
            versionFile.close()
            self.PROGRAM_VERSION_MAJOR = versionJSON['major']
            self.PROGRAM_VERSION_MINOR = versionJSON['minor']
            self.PROGRAM_VERSION_REV = versionJSON['rev']
            self.PROGRAM_VERSION_SUFFIX = versionJSON['suffix']
        except Exception as e:
            self._logger.warn('Could not determine program version: ' + str(e))

    
    
    # run the application
    def run(self):
        self.mainWindow = PipboyMainWindow()

        if (self.startedFromWin32Launcher):
            basepath = os.path.dirname(os.path.realpath(__file__))
            launcherpath = os.path.abspath(os.path.join(basepath, os.pardir, 'PyPipBoyApp-Launcher.exe'))
            print ('launcherpath: ' + str(launcherpath))
            if 'nt' in os.name:
                from win32com.propsys import propsys, pscon
                import pythoncom
                hwnd = self.mainWindow.winId()
                propStore = propsys.SHGetPropertyStoreForWindow(hwnd, propsys.IID_IPropertyStore)
                propStore.SetValue(pscon.PKEY_AppUserModel_ID, propsys.PROPVARIANTType(u'matzman666.pypipboyapp.win32', pythoncom.VT_ILLEGAL))
                propStore.SetValue(pscon.PKEY_AppUserModel_RelaunchDisplayNameResource, propsys.PROPVARIANTType('PyPipBoyApp', pythoncom.VT_ILLEGAL))
                propStore.SetValue(pscon.PKEY_AppUserModel_RelaunchCommand, propsys.PROPVARIANTType(launcherpath, pythoncom.VT_ILLEGAL))
                propStore.Commit()        
        # Load Styles
        self._loadStyles()
        # Load widgets
        self.helpWidget = uic.loadUi(os.path.join('ui', 'helpwidget.ui'))
        self.helpWidget.textBrowser.setSource(QtCore.QUrl.fromLocalFile(os.path.join('ui', 'res', 'helpwidget.html')))
        self.mainWindow.addDockWidget(QtCore.Qt.TopDockWidgetArea, self.helpWidget)
        self._loadWidgets()
        # Restore saved window state
        savedFullScreen = bool(int(self.settings.value('mainwindow/fullscreen', 0)))
        if savedFullScreen:
            self.mainWindow.showFullScreen()
        savedGeometry = self.settings.value('mainwindow/geometry')
        if savedGeometry:
            self.mainWindow.restoreGeometry(savedGeometry)
        savedState = self.settings.value('mainwindow/windowstate')
        if savedState:
            self.mainWindow.restoreState(savedState)
        # Create widgets menu entry
        self.widgetMenu.setTitle('Widgets')
        menuActions = self.mainWindow.menuBar().actions()
        self.mainWindow.menuBar().insertMenu(menuActions[len(menuActions)-1], self.widgetMenu)
        # connect with main window
        self.mainWindow.actionConnect.triggered.connect(self.startAutoDiscovery)
        self.mainWindow.actionConnectTo.triggered.connect(self.showConnectToDialog)
        self.mainWindow.actionDisconnect.triggered.connect(self.disconnect)
        self.mainWindow.actionQuit.triggered.connect(self.requestQuit)
        self.mainWindow.signalWantsToQuit.connect(self.requestQuit)
        self.mainWindow.actionShowAbout.triggered.connect(self.showAboutDialog)
        self.mainWindow.actionShowAboutQt.triggered.connect(self.aboutQt)
        self.mainWindow.actionAuto_Connect_on_Start_up.triggered.connect(self.autoConnectToggled)
        self.mainWindow.actionExportData.triggered.connect(self.exportData)
        self.mainWindow.actionImportData.triggered.connect(self.importData)
        self.mainWindow.actionVersionCheck.triggered.connect(self.startVersionCheckVerbose)
        stayOnTop = bool(int(self.settings.value('mainwindow/stayOnTop', 0)))
        self.mainWindow.actionStayOnTop.toggled.connect(self.setWindowStayOnTop)
        self.mainWindow.actionStayOnTop.setChecked(stayOnTop)
        promptBeforeQuit = bool(int(self.settings.value('mainwindow/promptBeforeQuit', 1)))
        self.mainWindow.actionPromptBeforeQuit.toggled.connect(self.setPromptBeforeQuit)
        self.mainWindow.actionPromptBeforeQuit.setChecked(promptBeforeQuit)
        self.mainWindow.actionRelayModeSettings.triggered.connect(self._slotRelayModeSettings)
        # Init Relay Mode
        self.relayModeEnabled = bool(int(self.settings.value('mainwindow/relayModeEnabled', 0)))
        self.relayModeAutodiscovery = bool(int(self.settings.value('mainwindow/relayModeAutodiscovery', 0)))
        self.relayModePort = int(self.settings.value('mainwindow/relayModePort', 27000))
        self.relayController = RelayController(self.dataManager)
        if self.relayModeEnabled:
            self.relayController.startRelayService(port=self.relayModePort)
            if self.relayModeAutodiscovery:
                self.relayController.startAutodiscoverService()
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
            self.signalConnectToHost.emit(host, port, True)
        self.startVersionCheck()
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
                    try:
                        parentself._logger.debug('Starting Autodiscovery Thread')
                        parentself._autodiscoverHosts = NetworkChannel.discoverHosts()
                        parentself._signalAutodiscoveryFinished.emit()
                        parentself._logger.debug('Autodiscovery Thread finished')
                    except:
                        traceback.print_exc(file=sys.stdout)
                        time.sleep(1) # Just to make sure that the error is correctly written into the log file
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
    
    # Shows a info message dialog
    @QtCore.pyqtSlot(str, str)        
    def showInfoMessage(self, title, text):
            QtWidgets.QMessageBox.information(self.mainWindow, title, text)
    
    # disconnects the current network session
    @QtCore.pyqtSlot()        
    def disconnect(self):
        if self.networkChannel.isConnected:
            self.networkChannel.disconnect()

    # Request the user to quit, saves state and quits
    @QtCore.pyqtSlot()        
    def requestQuit(self):
        # do you really wanna
        if not int(self.settings.value('mainwindow/promptBeforeQuit', 1)) or  QtWidgets.QMessageBox.question(self.mainWindow, 'Close', 'Are you sure you want to quit?',
                            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                            QtWidgets.QMessageBox.No) == QtWidgets.QMessageBox.Yes:
            # disconnect any network sessions
            if self.networkChannel.isConnected:
                self.networkChannel.disconnect()
            # Close Relay Service
            self.relayController.stopRelayService()
            self.relayController.stopAutodiscoverService()
            # save state
            self.settings.setValue('mainwindow/geometry', self.mainWindow.saveGeometry())
            self.settings.setValue('mainwindow/fullscreen', int(self.mainWindow.isFullScreen()))
            self.settings.setValue('mainwindow/windowstate', self.mainWindow.saveState())
            self.settings.sync()
            # quit
            self.quit()
    
    def getVersionString(self, versionData = None):
        if versionData:
            major = versionData['major']
            minor = versionData['minor']
            rev = versionData['rev']
            suffix = versionData['suffix']
        else:
            major = self.PROGRAM_VERSION_MAJOR
            minor = self.PROGRAM_VERSION_MINOR
            rev = self.PROGRAM_VERSION_REV
            suffix = self.PROGRAM_VERSION_SUFFIX
        version = 'v' + str(major) + '.' + str(minor)
        if rev > 0:
            version += '.' + str(rev)
        if suffix:
            version += '-' + suffix
        return version
    
    # Shows the about dialog
    def showAboutDialog(self):
        QtWidgets.QMessageBox.about(self.mainWindow, 'About ' + self.PROGRAM_NAME,
            '<b>' + self.PROGRAM_NAME + '</b><br>' + self.getVersionString() + '<br><br>' +
            #self.PROGRAM_ABOUT_TEXT + '<br><br>' + 
            '<b>License:</b><br>' + self.PROGRAM_ABOUT_LICENSE + '<br><br>' +
            '<b>Authors:</b><ul>' + self.PROGRAM_ABOUT_AUTHORS + '<ul>')
        
    @QtCore.pyqtSlot()        
    def exportData(self):
        fileName = QtWidgets.QFileDialog.getSaveFileName(self.mainWindow, '', '', 'Pipboy Data (*.pip)')
        if fileName[0]:
            #try:
                file = open(fileName[0], 'w')
                data = {}
                data['PipDatabase'] = self.dataManager.exportData()
                data['PipDatabase'].reverse()
                file.write(json.dumps(data))
                file.close()
            #except Exception as e:
            #    self.showWarningMessage('Export Data', 'Could not export data: '  + str(e))
        
    @QtCore.pyqtSlot()        
    def importData(self):
        fileName = QtWidgets.QFileDialog.getOpenFileName(self.mainWindow, '', '', 'Pipboy Data (*.pip)')
        if fileName[0]:
            #try:
                file = open(fileName[0], 'r')
                self.dataManager.importData(json.loads(file.read())['PipDatabase'])
                file.close()
            #except Exception as e:
            #    self.showWarningMessage('Import Data', 'Could not import data: '  + str(e))
        
        
    # event listener for pypipboy network state events
    def _onConnectionStateChange(self, state, errstatus = 0, errmsg = ''):
        self._logger.info('Connection State Changed: ' + str(state) + ' - ' + str(errstatus) + ' - ' + str(errmsg))
        if state: # connect
            # menu management stuff
            self.mainWindow.actionConnect.setEnabled(False)
            self.mainWindow.actionConnectTo.setEnabled(False)
            self.mainWindow.actionDisconnect.setEnabled(True)
            self.mainWindow.actionExportData.setEnabled(True)
            self.mainWindow.actionImportData.setEnabled(False)
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
            self.mainWindow.actionExportData.setEnabled(False)
            self.mainWindow.actionImportData.setEnabled(True)
            # status bar update
            self.mainWindow.connectionStatusLabel.setText('No Connection')
            # error handling
            if errstatus != 0:
                self.signalShowWarningMessage.emit('Connection Error', 'Connection Error: ' + str(errmsg))
                
    @QtCore.pyqtSlot()
    def startVersionCheckVerbose(self):
        self.startVersionCheck(True)
    
    @QtCore.pyqtSlot()
    def startVersionCheck(self, verbose = False):
        def _checkVersion():
            try:
                rawData = urllib.request.urlopen('https://raw.githubusercontent.com/matzman666/PyPipboyApp/versionCheck/VERSION').read().decode()
                versionData = json.loads(rawData)
                major = versionData['major']
                minor = versionData['minor']
                rev = versionData['rev']
                suffix = versionData['suffix']
                newVersionAvailable = False
                if (self.PROGRAM_VERSION_MAJOR < major 
                        or (self.PROGRAM_VERSION_MAJOR == major and self.PROGRAM_VERSION_MINOR < minor) 
                        or (self.PROGRAM_VERSION_MAJOR == major and self.PROGRAM_VERSION_MINOR == minor and self.PROGRAM_VERSION_REV < rev)):
                    newVersionAvailable = True
                self._signalFinishedCheckVersion.emit(versionData, newVersionAvailable, False, '', verbose)
            except Exception as e:
                self._logger.warn('Could not check for new version: ' + str(e))
                self._signalFinishedCheckVersion.emit({}, False, True, str(e), verbose)
        self._checkVersionThread = threading.Thread(target = _checkVersion)
        self._checkVersionThread.start()
    
    
    @QtCore.pyqtSlot(dict, bool, bool, str, bool)
    def _slotFinishedCheckVersion(self, versionData, newVersionAvailable, errorState, errorString, verbose):
        self._checkVersionThread.join()
        self._checkVersionThread = None
        if errorState:
            if verbose:
                self.showWarningMessage('Version Check', 'Could not check for new version: ' + errorString)
        elif newVersionAvailable:
            self.showInfoMessage('Version Check', '<b>New version is available!<br><br>' 
                                                + self.getVersionString(versionData) + '</b> (current: ' 
                                                + self.getVersionString() + ').<br><br>'
                                                + 'Download from:<ul>'
                                                + '<li><a href="http://www.nexusmods.com/fallout4/mods/4664">nexusmods.com</a><li>'
                                                + '<li><a href="http://github.com/matzman666/PyPipboyApp">github.com</a></li></ul>')
        elif verbose:
            self.showInfoMessage('Version Check', 'Current version is up-to-date.')
    
    @QtCore.pyqtSlot(bool)
    def setWindowStayOnTop(self, value):
        self.settings.setValue('mainwindow/stayOnTop', int(value))
        if value:
            self.mainWindow.setWindowFlags(self.mainWindow.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        else:
            self.mainWindow.setWindowFlags(self.mainWindow.windowFlags() & ~QtCore.Qt.WindowStaysOnTopHint)
        self.mainWindow.show()

    @QtCore.pyqtSlot(bool)
    def setPromptBeforeQuit(self, value):
        self.settings.setValue('mainwindow/promptBeforeQuit', int(value))
        
    def _slotRelayModeSettings(self):
        dialog = RelaySettingsDialog(self.mainWindow)
        dialog.relayGroupBox.setChecked(self.relayModeEnabled)
        dialog.autodiscoveryCheckBox.setChecked(self.relayModeAutodiscovery)
        dialog.relayPortEdit.setText(str(self.relayModePort))
        if dialog.exec():
            try:
                enabled = dialog.relayGroupBox.isChecked()
                autodiscovery = dialog.autodiscoveryCheckBox.isChecked()
                port = int(dialog.relayPortEdit.text())
                if not enabled:
                    self.relayController.stopAutodiscoverService()
                    self.relayController.stopRelayService()
                else:
                    if not autodiscovery:
                        self.relayController.stopAutodiscoverService()
                    else:
                        self.relayController.startAutodiscoverService()
                    if self.relayModePort != port:
                        self.relayController.stopRelayService()
                    self.relayController.startRelayService(port=port)
                self.relayModeAutodiscovery = autodiscovery
                self.relayModePort = port
                self.relayModeEnabled = enabled
                self.settings.setValue('mainwindow/relayModeEnabled', int(self.relayModeEnabled))
                self.settings.setValue('mainwindow/relayModeAutodiscovery', int(self.relayModeAutodiscovery))
                self.settings.setValue('mainwindow/relayModePort', self.relayModePort)
            except Exception as e:
                self.showWarningMessage('Relay Mode', 'Could not change settings: ' + str(e))
    
    
    # load widgets
    def _loadWidgets(self):
        self.widgets = list()
        self.modulehandles = dict()
        menuCategoryMap = dict()
        self.widgetMenuEntries = list()
        lastWidget = self.helpWidget
        for dir in os.listdir(self.PROGRAM_WIDGETS_DIR):
            dirpath = os.path.join(self.PROGRAM_WIDGETS_DIR, dir)
            if dir != 'shared' and not dir.startswith('__') and os.path.isdir(dirpath):
                self._logger.debug('Tyring to load widget "' + dir + '"')
                module = None
                try:
                    module = importlib.import_module(self.PROGRAM_WIDGETS_DIR + '.' + dir + '.info')
                    info = getattr(module, 'ModuleInfo')
                    if info:
                        if info.isEnabled():
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
                                    if w.getMenuCategory():
                                        try:
                                            m = menuCategoryMap[w.getMenuCategory()]
                                            m.addAction(w.toggleViewAction())
                                        except:
                                            m = QtWidgets.QMenu(w.getMenuCategory())
                                            menuCategoryMap[w.getMenuCategory()] = m
                                            self.widgetMenuEntries.append(m)
                                            m.addAction(w.toggleViewAction())
                                    else:
                                        self.widgetMenuEntries.append(w.toggleViewAction())
                                    w.setVisible(False)
                                    if lastWidget:
                                        self.mainWindow.tabifyDockWidget(lastWidget, w)
                                    lastWidget = w
                                    i += 1
                                self._logger.info('Successfully loaded widget "' + dir + '"')
                            else:
                                self._logger.warning('Could not load widget "' + dir + '": No widgets returned')
                        else:
                            self._logger.info('Widget "' + dir + '" is not enabled')
                    else:
                        self._logger.warning('Could not load widget "' + dir + '": No Info')
                except Exception as e:
                    self._logger.warning('Could not load widget "' + dir + '": ' + str(e))
                    traceback.print_exc(file=sys.stdout)
        for e in self.widgetMenuEntries:
            if type(e) == QtWidgets.QMenu:
                self.widgetMenu.addMenu(e)
            else:
                self.widgetMenu.addAction(e)
    
    def iwcRegisterEndpoint(self, key, endpoint):
        self._iwcEndpoints[key] = endpoint
        
    def iwcUnregisterEndpoint(self, key):
        if key in self._iwcEndpoints:
            del self._iwcEndpoints[key]
            
    def iwcGetEndpoint(self, key):
        try:
            return self._iwcEndpoints[key]
        except:
            return None
    
    # load widgets
    def _initWidgets(self):
        for w in self.widgets:
            w.iwcSetup(self)
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
            action.setCheckable(True)
        self.mainWindow.actionStylesDefault.triggered.connect(_genSlotSetStyles(self, 'default'))
        if (self.settings.value('mainwindow/lastStyle')):
            self.setStyle(self.settings.value('mainwindow/lastStyle'))
        else:
            self.setStyle('default')
        
            
    def setStyle(self, name):
        if (name == 'default' or not name in self.styles):
            name = 'default'
            self.setStyleSheet('')
        else:
            style = self.styles[name]
            stylefilepath = os.path.join(style.styledir, 'style.qss')
            self.setStyleSheet('file:///' + stylefilepath)
        actionFound = False
        for a in self.mainWindow.menuStyles.actions():
            if a.text() == name:
                a.setChecked(True)
                actionFound = True
            else:
                a.setChecked(False)
        if not actionFound:
            self.mainWindow.actionStylesDefault.setChecked(True)
        self.settings.setValue('mainwindow/lastStyle', name) 
        
           
            
    def isWidgetReallyVisisble(self, widget):
        return not widget.visibleRegion().isEmpty()
                
    def popWidget(self, widgetName):
        self._logger.debug('popWidget: widgetName: ' + str(widgetName))
        for widget in self.widgets:
            if (widget.windowTitle().lower() == widgetName):
                widget.raise_()
                break
        return
        
    def cycleWidgets(self, widgetNameList):
        self._logger.debug('cycleWidgets: widgetNameList: ' + str(widgetNameList))
        nextWidgetIndex = 0
        currentWidget = None
        for widget in self.widgets:
            #self._logger.debug('cycleWidgets: \t: ' + str(widget.windowTitle()))
            if (widget.windowTitle().lower() in widgetNameList
            and self.isWidgetReallyVisisble(widget)):
                currentWidget = widget
                break

        if (currentWidget):
            for i in range(0, len(widgetNameList)):
                if (currentWidget.windowTitle().lower() == widgetNameList[i]):
                    nextWidgetIndex = i + 1
                    break
                        
        if(nextWidgetIndex >= len(widgetNameList)):
            nextWidgetIndex = 0

        nextWidgetName = widgetNameList[nextWidgetIndex]
        self.popWidget(nextWidgetName)   
        return        

            
# Main entry point
if __name__ == "__main__":
    try:
        stdlogfile = None
        inifile = None
        i = 1
        while i < len(sys.argv):
            if sys.argv[i] == '--stdlog':
                if i == len(sys.argv) -1 :
                    logging.error('Missing argument for --stdlog')
                else:
                    i += 1
                    stdlogfile = sys.argv[i]
            elif sys.argv[i] == '--inifile':
                if i == len(sys.argv) -1 :
                    logging.error('Missing argument for --inifile')
                else:
                    i += 1
                    inifile = sys.argv[i]
            i += 1
        if stdlogfile != None:
            stdlog = open(stdlogfile, 'w')
            sys.stdout = stdlog
            sys.stderr = stdlog
        try:
            logging.config.fileConfig('logging.config')
        except Exception as e:
            logging.basicConfig(level=logging.WARN)
            logging.error('Error while reading logging config: ' + str(e))
    
        try:
            faulthandler.enable()
        except Exception as e:
            logging.error('Error calling Faulthandle.enable(): ' + str(e))
            
        if (faulthandler.is_enabled()):
            logging.warn('Faulthandler is enabled')
            #faulthandler.dump_traceback_later(5)
        else:
            logging.error('Faulthandler is NOT enabled')
    
        if 'nt' in os.name:
            from ctypes import windll
            windll.shell32.SetCurrentProcessExplicitAppUserModelID(u'matzman666.pypipboyapp')
        pipboyApp = PyPipboyApp(sys.argv, inifile)
        pipboyApp.run()
    except:
        traceback.print_exc(file=sys.stdout)
        time.sleep(1) # Just to make sure that the error is correctly written into the log file

