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
        self.playerDataBasePath = None
        self.playerDataPath = None

        self.collectableFormIDs = []
        inputfile = open(os.path.join('widgets', 'shared', 'res', 'collectables-processed.json'))
        collectables = json.load(inputfile)

        for catKey, catData in collectables.items():
            for collectable in catData.get('items'):
                #self._logger.info(collectable.get('formid'))
                self.collectableFormIDs.append(int(collectable.get('formid'), 16))

        self._signalInfoUpdated.connect(self._slotInfoUpdated)

    def init(self, app, datamanager):
        self.dataManager = datamanager
        self.dataManager.registerRootObjectListener(self._onPipRootObjectEvent)
        self.playerDataBasePath = 'percharacterdata/'
        self.collectedcollectablesuffix = '/collectedcollectables'
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
            if name is not None:
                self.pipPlayerName = name.value()

            if self.pipPlayerName is not None:
                self.playerDataPath = self.playerDataBasePath + self.pipPlayerName

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
                    index = self._app.settings.value(self.playerDataPath + self.collectedcollectablesuffix, None)
                    if index is None:
                        index = []
                    if str(item.child('formID').value()) not in index:
                        index.append(str(item.child('formID').value()))
                        self._app.settings.setValue(self.playerDataPath + self.collectedcollectablesuffix, index)
                        if self.globalMap is not None:
                            self.globalMap.iwcSetCollectableCollected(item.child('formID').value())
                        else:
                            self._logger.error("No globalmap?")


