import os
import json
from PyQt5 import QtCore

from pypipboy import inventoryutils
import logging


class CharacterDataManager(QtCore.QObject):
    _signalInfoUpdated = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__()
        self._logger = logging.getLogger('pypipboyapp.characterdatamanager')
        self.pipPlayerObject = None
        self.pipPlayerName = None
        self.dataManager = None
        self.globalMap = None
        self._app = None

        self.collectableFormIDs = []
        inputfile = open(os.path.join('collectables-processed.json'))
        collectables = json.load(inputfile)

        for k, v in collectables.items():
            for i in v.get('items', None):
                self.collectableFormIDs.append(int(i.get('formid'), 16))

        self._signalInfoUpdated.connect(self._slotInfoUpdated)

    def init(self, app, datamanager):
        self.dataManager = datamanager
        self.dataManager.registerRootObjectListener(self._onPipRootObjectEvent)
        self.globalMap = app.iwcGetEndpoint('globalmapwidget')
        self._app = app

    def _onPipRootObjectEvent(self, rootObject):
        self.pipInventoryInfo = rootObject.child('Inventory')
        if self.pipInventoryInfo:
            self.pipInventoryInfo.registerValueUpdatedListener(self._onPipInventoryInfoUpdate, 1)
        self._signalInfoUpdated.emit()

        self.pipPlayerObject = rootObject.child('PlayerInfo')
        if self.pipPlayerObject:
            self.pipPlayerObject.registerValueUpdatedListener(self._onPipPlayerReset)
            self._onPipPlayerReset(None, None, None)

    def _onPipPlayerReset(self, caller, value, pathObjs):
        if self.pipPlayerObject:
            name = self.pipPlayerObject.child('PlayerName')
            if name:
                self.pipPlayerName = name.value()

    def _onPipInventoryInfoUpdate(self, caller, value, pathObjs):
        self._signalInfoUpdated.emit()

    @QtCore.pyqtSlot()
    def _slotInfoUpdated(self):
        if self.pipInventoryInfo:
            def _filterFunc(i):
                if (inventoryutils.itemHasAnyFilterCategory(i, inventoryutils.eItemFilterCategory.Misc) and
                        (self.collectableFormIDs is not None and i.child('formID').value() in self.collectableFormIDs)):
                    return True
                else:
                    return False

            collectables = inventoryutils.inventoryGetItems(self.pipInventoryInfo, _filterFunc)
            if collectables is not None and self.pipPlayerName is not None:
                for item in collectables:
                    collectedcollectablesSettings = 'percharacterdata/' + self.pipPlayerName + '/collectedcollectables'
                    index = self._app.settings.value(collectedcollectablesSettings, None)
                    if index is None:
                        index = []

                    if str(item.child('formID').value()) not in index:
                        index.append(item.child('formID').value())
                        self._app.settings.setValue(collectedcollectablesSettings, index)
                        self.globalMap.iwcSetCollectableCollected(item.child('formID').value())
