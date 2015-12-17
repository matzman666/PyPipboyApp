# widgets.WidgetBase inherits from QtDockWidget
import os
from PyQt5 import QtWidgets, QtCore, uic
from .. import widgets
import socket
class FO4VaWidget(widgets.WidgetBase):
    _signalPipWorldQuestsUpdated = QtCore.pyqtSignal()
    _signalPipWorldLocationsUpdated = QtCore.pyqtSignal()
    def __init__(self, mhandle, parent):
        super().__init__('FO4VA', parent)
        self.widget = uic.loadUi(os.path.join(mhandle.basepath, 'ui', 'fo4va.ui'))
        self.setWidget(self.widget)
    # Gets called when everything has been set up
    #   framework ... reference to the framework
    #   datamanager ... reference to the PipboyDataManager instance from PyPipboy library
    def init(self, app, datamanager):
        super().init(app, datamanager)
        self.dataManager = datamanager
        self.dataManager.registerRootObjectListener(self._onRootObjectEvent)
        self.widget.msgLabel.setText("YES")
        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serversocket.bind(('localhost', 8089))
        self.serversocket.listen(5) # become a server socket, maximum 5 connections

    def _onRootObjectEvent(self, rootObject):
        self.pipMapObject = rootObject.child('Map')
        if self.pipMapObject:
            self.pipMapObject.registerValueUpdatedListener(self._onPipMapReset)
            self._onPipMapReset(None, None, None)

    def rspCallback(Fo4response):
        print("CallBack")
        print(Fo4response)

    def _onPipMapReset(self, caller, value, pathObjs):
        self.pipMapWorldObject = self.pipMapObject.child('World')
        if self.pipMapWorldObject:
            self.pipWorldLocations = self.pipMapWorldObject.child('Locations')
            if self.pipWorldLocations:
                self.pipWorldLocations.registerValueUpdatedListener(self._onPipWorldLocationsUpdated, 0)
                self._signalPipWorldLocationsUpdated.emit()
        while True:
            connection, address = self.serversocket.accept()
            buf = connection.recv(64)
            if len(buf) > 0:
                print(buf)
                strFound = False
                sName = buf.decode()
                for k in self.pipWorldLocations.value():
                    for x in k.value():
                        if x == 'Name':
                            curName = k.child(x).value()
                            if curName.lower() == sName.lower():
                                curKey = k.pipParentKey
                                strFound = True
                                print('curKey ' + str(curKey))
                if strFound:
                    curPoint = self.pipWorldLocations.child(curKey)
                    print(curPoint.pipId)
                    self.dataManager.rpcFastTravel(curPoint)
                    data = "OK"
                    connection.send(data.encode('utf-8'))
                else:
                    print("error No KeyFound")

    def _onPipWorldLocationsUpdated(self, caller, value, pathObjs):
        self._signalPipWorldLocationsUpdated.emit()

