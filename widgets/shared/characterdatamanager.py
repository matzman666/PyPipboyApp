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
        self.playerDataPath = None
        self.playerDataBasePath = 'percharacterdata/'
        self.collectedcollectablesuffix = '/collectedcollectables'
        self.collectableFormIDs = []

        self._signalInfoUpdated.connect(self._slotInfoUpdated)

    def init(self, app, datamanager, collectableDefs):
        self.dataManager = datamanager
        self.dataManager.registerRootObjectListener(self._onPipRootObjectEvent)
        self.globalMap = app.iwcGetEndpoint('globalmapwidget')
        self._app = app
        self.fullUpdateFlag = True

        for catKey, catData in collectableDefs.items():
            for collectable in catData.get('items'):
                self.collectableFormIDs.append(int(collectable.get('formid'), 16))

    def _onPipRootObjectEvent(self, rootObject):
        self.pipInventoryInfo = rootObject.child('Inventory')
        # Only listen to book and misc category to avoid too many false alarms (e.g. ammo consumption)
        self.pipInvCatBooks = self.pipInventoryInfo.child('30')
        self.pipInvCatMisc = self.pipInventoryInfo.child('35')
        if self.pipInvCatBooks:
            self.pipInvCatBooks.registerValueUpdatedListener(self._onPipInventoryInfoUpdate, 1)
        if self.pipInvCatMisc:
            self.pipInvCatMisc.registerValueUpdatedListener(self._onPipInventoryInfoUpdate, 1)
            
        self.pipPlayerObject = rootObject.child('PlayerInfo')
        if self.pipPlayerObject:
            self.pipPlayerObject.registerValueUpdatedListener(self._onPipPlayerReset)
            self._onPipPlayerReset(None, None, None)
            
        self.fullUpdateFlag = True
        self._signalInfoUpdated.emit()

    def _onPipPlayerReset(self, caller, value, pathObjs):
        if self.pipPlayerObject:
            name = self.pipPlayerObject.child('PlayerName')
            if name is not None and self.pipPlayerName != name:
                self.pipPlayerName = name.value()
                self.playerDataPath = self.playerDataBasePath + self.pipPlayerName
                self.fullUpdateFlag = True

    def _onPipInventoryInfoUpdate(self, caller, value, pathObjs):
        self._signalInfoUpdated.emit()

    @QtCore.pyqtSlot()
    def _slotInfoUpdated(self):
        if self.pipInventoryInfo and self.playerDataPath is not None:
            def _filterFunc(i):
                if (inventoryutils.itemHasAnyFilterCategory(i, inventoryutils.eItemFilterCategory.Misc) and
                        (self.collectableFormIDs is not None and i.child('formID').value() in self.collectableFormIDs)):
                    return True
                else:
                    return False
            collectables = inventoryutils.inventoryGetItems(self.pipInventoryInfo, _filterFunc)
            index = self._app.settings.value(self.playerDataPath + self.collectedcollectablesuffix, None)
            if index is None:
                index = []
            if collectables is not None and self.pipPlayerName is not None:
                for item in collectables:
                    if str(item.child('formID').value()) not in index:
                        index.append(str(item.child('formID').value()))    
            if self.globalMap is not None:
                if self.fullUpdateFlag:
                    index = list(set(index)) # Remove duplicates
                    self.globalMap.iwcSetCollectablesCollectedState(index, True)
                    self.fullUpdateFlag = False
                else:
                    self.globalMap.iwcSetCollectablesCollectedState(index, False)
            else:
                self._logger.error("No globalmap?")
            self._app.settings.setValue(self.playerDataPath + self.collectedcollectablesuffix, index)
            


