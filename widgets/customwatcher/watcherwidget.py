import os
from PyQt5 import QtWidgets, QtCore, QtGui, uic
from widgets import widgets
from widgets.shared import settings
from pypipboy import inventoryutils

import logging




class CustomWatcherWidget(widgets.WidgetBase):
    _signalInfoUpdated = QtCore.pyqtSignal()
    """"""

    def __init__(self, mhandle, parent):
        super().__init__('Custom Watcher', parent)
        self.widget = uic.loadUi(os.path.join(mhandle.basepath, 'ui', 'customwatcher.ui'))
        self._logger = logging.getLogger('pypipboyapp.customwatcher')
        self.setWidget(self.widget)
        self.pipColour = None
        self.pipInventoryInfo = None
        self.defaultColor = QtGui.QColor.fromRgb(255,255,255)
        self._signalInfoUpdated.connect(self._slotInfoUpdated)
        self.watchFrame = self.widget.watchFrame
        self.layout = QtWidgets.QVBoxLayout(self)
        self.watcherBntDict = {}
        self.watcherLabelDict = {}
        self.makeButton('test1asdasdasdasdasd')
        self.makeButton('test2adsadasdasda')
        self.makeButton('test3adasdasdsdsd')
        self.makeLabel("TestLabel")
        self.watchFrame.setLayout(self.layout)


    def init(self, app, datamanager):
        super().init(app, datamanager)
        self.dataManager = datamanager
        self.dataManager.registerRootObjectListener(self._onPipRootObjectEvent)
        self._app = app
        self.ammoItems = []

    def buttonClick(self,button):
        print(button.text())

    def makeLabel(self, lblName):
        self.watcherLabelDict[lblName] = QtWidgets.QLabel()
        self.watcherLabelDict[lblName].setText(lblName)
        self.layout.addWidget(self.watcherLabelDict[lblName])

    def makeButton(self,bntName):
        self.watcherBntDict[bntName] = QtWidgets.QPushButton(bntName, self)
        self.layout.addWidget(self.watcherBntDict[bntName])
        self.watcherBntDict[bntName].clicked.connect(lambda: self.buttonClick(self.watcherBntDict[bntName]))

    def _onPipRootObjectEvent(self, rootObject):
        self.pipInventoryInfo = rootObject.child('Inventory')
        if self.pipInventoryInfo:
            self.pipInventoryInfo.registerValueUpdatedListener(self._onPipInventoryInfoUpdate, 1)
        self._signalInfoUpdated.emit()

    def _onPipInventoryInfoUpdate(self, caller, value, pathObjs):
        self._signalInfoUpdated.emit()

    @QtCore.pyqtSlot()
    def _slotInfoUpdated(self):
        print('ok')

    def rowCount(self, parent = QtCore.QModelIndex()):
        if self.pipRadio:
            return self.pipRadio.childCount()
        else:
            return 0

    def columnCount(self, parent = QtCore.QModelIndex()):
        return 2

    def headerData(self, section, orientation, role = QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal:
            if role == QtCore.Qt.DisplayRole:
                if section == 0:
                    return 'Name'
                elif section == 1:
                    return 'Count'
        return None