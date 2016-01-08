import os
from PyQt5 import QtWidgets, QtCore, QtGui, uic
from widgets import widgets
from widgets.shared import settings
from pypipboy import inventoryutils

import logging




class AmmoCountWidget(widgets.WidgetBase):
    _signalInfoUpdated = QtCore.pyqtSignal()
    """"""

    def __init__(self, mhandle, parent):
        super().__init__('Ammo Count', parent)
        self.widget = uic.loadUi(os.path.join(mhandle.basepath, 'ui', 'watcherwidget.ui'))
        self._logger = logging.getLogger('pypipboyapp.ammoinfowidget')
        self.setWidget(self.widget)
        self.pipColour = None
        self.pipInventoryInfo = None
        self.foreColor = QtGui.QColor.fromRgb(0,255,0)
        self._signalInfoUpdated.connect(self._slotInfoUpdated)

    def init(self, app, datamanager):
        super().init(app, datamanager)
        self.dataManager = datamanager
        self.dataManager.registerRootObjectListener(self._onPipRootObjectEvent)
        self._app = app
        self.ammoItems = []

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