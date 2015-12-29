# -*- coding: utf-8 -*-
import datetime
import os
from PyQt5 import QtGui, QtWidgets, QtCore, uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from pypipboy.types import eValueType
from .. import widgets
from pypipboy import inventoryutils

import logging

class DoctorsBagWidget(widgets.WidgetBase):
    _signalInfoUpdated = QtCore.pyqtSignal()
    _signalColorUpdated = QtCore.pyqtSignal(QtGui.QColor)
    drugmodel = QStandardItemModel()
    
    def __init__(self, mhandle, parent):
        super().__init__('Doctor\'s Bag', parent)
        self.widget = uic.loadUi(os.path.join(mhandle.basepath, 'ui', 'doctorsbagwidget.ui'))
        self._logger = logging.getLogger('pypipboyapp.doctorsbagwidget')
        self.setWidget(self.widget)
        self.pipColour = None
        self.pipInventoryInfo = None
        self.foreColor = QtGui.QColor.fromRgb(0,255,0)

        
        self._signalInfoUpdated.connect(self._slotInfoUpdated)
        self._signalColorUpdated.connect(self._slotColorUpdated)

    def init(self, app, datamanager):
        super().init(app, datamanager)
        self.dataManager = datamanager
        self.dataManager.registerRootObjectListener(self._onPipRootObjectEvent)
        self._app = app
        self.hiddenItems = []
        
        settingPath = 'doctorsbag/hiddenItems'
        self.hiddenItems = self._app.settings.value(settingPath, [])
        
        if len(self.hiddenItems) == 0:
            self.resetItemFilter()
        
        self.widget.drugView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.widget.drugView.customContextMenuRequested.connect(self.drugViewMenuRequested)
        
        self.widget.drugView.clicked.connect(self.drugViewClicked)
        
        self._slotColorUpdated(self.foreColor)

    def colouriseIcon(self, img, colour):
        size = img.size()
        image = QImage(QtCore.QSize(size.width()+1,size.height()+1), QImage.Format_ARGB32_Premultiplied)
        image.fill(QtCore.Qt.transparent)
        p = QPainter(image)
        p.setCompositionMode(QPainter.CompositionMode_SourceOver)
        p.drawImage(QtCore.QRect(1,1,size.width(), size.height()), img)
        p.setCompositionMode(QPainter.CompositionMode_SourceAtop)
        p.setBrush(colour)
        p.drawRect(QtCore.QRect(0,0,size.width()+1,size.height()+1))
        p.end()
        return QPixmap.fromImage(image)        
        
    def _onPipRootObjectEvent(self, rootObject):
        self.pipInventoryInfo = rootObject.child('Inventory')
        if self.pipInventoryInfo:
            self.pipInventoryInfo.registerValueUpdatedListener(self._onPipInventoryInfoUpdate, 1)
        self._signalInfoUpdated.emit()

        self.pipColor = rootObject.child('Status').child('EffectColor')
        self.pipColor.registerValueUpdatedListener(self._onPipColorChanged, 1)
        self._onPipColorChanged(None, None, None)
        
    def _onPipColorChanged(self, caller, value, pathObjs):
        if self.pipColor:
            r = self.pipColor.child(0).value() * 255
            g = self.pipColor.child(1).value() * 255
            b = self.pipColor.child(2).value() * 255
            self.foreColor = QtGui.QColor.fromRgb(r,g,b)
            self._signalColorUpdated.emit(self.foreColor)

        
    def _onPipInventoryInfoUpdate(self, caller, value, pathObjs):
        self._signalInfoUpdated.emit()

    @QtCore.pyqtSlot(QtGui.QColor)
    def _slotColorUpdated(self, color):
        return
        
    @QtCore.pyqtSlot()
    def _slotInfoUpdated(self):
        self.updateDrugView()

    def _isItemReal(self, item):
        if(self.pipInventoryInfo):
            for i in range (0, self.pipInventoryInfo.child('sortedIDS').childCount()):
                if (item and item.pipId == self.pipInventoryInfo.child('sortedIDS').child(i).value()):
                    return True
        return False


    @QtCore.pyqtSlot(QtCore.QPoint)
    def drugViewMenuRequested(self, pos):
        menu = QMenu(self)
        #print ('dvmr: ' + str(pos))
        index = self.widget.drugView.indexAt(pos)
        if (index.isValid()):
            model = self.widget.drugView.model() 
            modelIndex = model.index(index.row(), 0)
            clickedItemName = str(model.data(modelIndex))
            #print('dvcr: ' + clickedItemName)

            def _hideAidItem():
                #print('hide: ' + clickedItemName)
                self.hiddenItems.append(clickedItemName).lower()
                settingPath = 'doctorsbag/hiddenItems'
                self._app.settings.setValue(settingPath, self.hiddenItems)
                self.updateDrugView()
            hideItemAction = QAction('Hide ' + clickedItemName, menu)
            hideItemAction.triggered.connect(_hideAidItem)
            menu.addAction(hideItemAction)

        resetFilterAction = QAction('Reset item filter to default', menu)
        resetFilterAction.triggered.connect(self.resetItemFilter)
        menu.addAction(resetFilterAction)

        showAllAction = QAction('Show all items', menu)
        showAllAction.triggered.connect(self.showAllAidItems)
        menu.addAction(showAllAction)

        menu.exec(self.widget.drugView.mapToGlobal(pos))
        return
        
    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def drugViewClicked(self, index):
        model = self.widget.drugView.model() 
        modelIndex = model.index(index.row(), 0)
        #print('dvc: ' + str(model.data(modelIndex)))
        self.useItemByName('48', str(model.data(modelIndex)))
        return

    def resetItemFilter(self):
        self.hiddenItems = []
        ### drugs
        self.hiddenItems.append("endangerol syringe")
        self.hiddenItems.append("addictol")
        self.hiddenItems.append("berry mentats")
        self.hiddenItems.append("buffjet")
        self.hiddenItems.append("buffout")
        self.hiddenItems.append("bufftats")
        self.hiddenItems.append("calmex")
        self.hiddenItems.append("daddy-o")
        self.hiddenItems.append("day tripper")
        self.hiddenItems.append("fury")
        self.hiddenItems.append("grape mentats")
        #self.hiddenItems.append("jet")
        self.hiddenItems.append("jet fuel")
        #self.hiddenItems.append("med-x")
        self.hiddenItems.append("mentats")
        self.hiddenItems.append("mysterious serum")
        self.hiddenItems.append("orange mentats")
        self.hiddenItems.append("overdrive")
        #self.hiddenItems.append("psycho")
        self.hiddenItems.append("psycho jet")
        self.hiddenItems.append("psychobuff")
        self.hiddenItems.append("psychotats")
        #self.hiddenItems.append("rad-x")
        #self.hiddenItems.append("radaway")
        self.hiddenItems.append("skeeto spit")
        #self.hiddenItems.append("stimpak")
        self.hiddenItems.append("ultra jet")
        self.hiddenItems.append("vault 81 cure")
        self.hiddenItems.append("x-111 compound")
        self.hiddenItems.append("x-cell")
        self.hiddenItems.append("railroad stealth boy")
        self.hiddenItems.append("stealth boy")

        ### food
        self.hiddenItems.append("baked bloatfly")
        self.hiddenItems.append("blamco brand mac and cheese")
        self.hiddenItems.append("bloatfly meat")
        self.hiddenItems.append("bloodbug meat")
        self.hiddenItems.append("bloodbug steak")
        self.hiddenItems.append("bloodleaf")
        self.hiddenItems.append("brahmin meat")
        self.hiddenItems.append("brain fungus")
        self.hiddenItems.append("bubblegum")
        self.hiddenItems.append("canned dog food")
        self.hiddenItems.append("carrot")
        self.hiddenItems.append("carrot flower")
        self.hiddenItems.append("cat meat")
        self.hiddenItems.append("cooked softshell meat")
        self.hiddenItems.append("corn")
        self.hiddenItems.append("cram")
        self.hiddenItems.append("crispy squirrel bits")
        self.hiddenItems.append("dandy boy apples")
        self.hiddenItems.append("deathclaw egg")
        self.hiddenItems.append("deathclaw egg omelette")
        self.hiddenItems.append("deathclaw meat")
        self.hiddenItems.append("deathclaw steak")
        self.hiddenItems.append("deathclaw wellingham")
        self.hiddenItems.append("experimental plant")
        self.hiddenItems.append("fancy lads snack cakes")
        self.hiddenItems.append("food paste")
        self.hiddenItems.append("fresh carrot")
        self.hiddenItems.append("fresh corn")
        self.hiddenItems.append("fresh melon")
        self.hiddenItems.append("fresh mutfruit")
        self.hiddenItems.append("glowing fungus")
        self.hiddenItems.append("gourd")
        self.hiddenItems.append("gourd blossom")
        self.hiddenItems.append("grilled radroach")
        self.hiddenItems.append("grilled radstag")
        self.hiddenItems.append("gum drops")
        self.hiddenItems.append("happy birthday sweet roll")
        self.hiddenItems.append("hubflower")
        self.hiddenItems.append("iguana bits")
        self.hiddenItems.append("iguana on a stick")
        self.hiddenItems.append("iguana soup")
        self.hiddenItems.append("instamash")
        self.hiddenItems.append("institute food packet")
        self.hiddenItems.append("melon")
        self.hiddenItems.append("mirelurk cake")
        self.hiddenItems.append("mirelurk egg")
        self.hiddenItems.append("mirelurk egg omelette")
        self.hiddenItems.append("mirelurk meat")
        self.hiddenItems.append("mirelurk queen steak")
        self.hiddenItems.append("moldy food")
        self.hiddenItems.append("mole rat chunks")
        self.hiddenItems.append("mole rat meat")
        self.hiddenItems.append("mongrel dog meat")
        self.hiddenItems.append("mutant hound chops")
        self.hiddenItems.append("mutant hound meat")
        self.hiddenItems.append("mutated fern flower")
        self.hiddenItems.append("mutfruit")
        self.hiddenItems.append("mutt chops")
        self.hiddenItems.append("noodle cup")
        self.hiddenItems.append("perfectly preserved pie")
        self.hiddenItems.append("pork n' beans")
        self.hiddenItems.append("potato crisps")
        self.hiddenItems.append("potted meat")
        self.hiddenItems.append("preserved instamash")
        self.hiddenItems.append("pristine deathclaw egg")
        self.hiddenItems.append("queen mirelurk meat")
        self.hiddenItems.append("radroach meat")
        self.hiddenItems.append("radscorpion egg")
        self.hiddenItems.append("radscorpion egg omelette")
        self.hiddenItems.append("radscorpion meat")
        self.hiddenItems.append("radscorpion steak")
        self.hiddenItems.append("radstag meat")
        self.hiddenItems.append("radstag stew")
        self.hiddenItems.append("razorgrain")
        self.hiddenItems.append("ribeye steak")
        self.hiddenItems.append("roasted mirelurk meat")
        self.hiddenItems.append("salisbury steak")
        self.hiddenItems.append("silt bean")
        self.hiddenItems.append("slocum's buzzbites")
        self.hiddenItems.append("softshell mirelurk meat")
        self.hiddenItems.append("squirrel bits")
        self.hiddenItems.append("squirrel on a stick")
        self.hiddenItems.append("squirrel stew")
        self.hiddenItems.append("stingwing filet")
        self.hiddenItems.append("stingwing meat")
        self.hiddenItems.append("sugar bombs")
        self.hiddenItems.append("sweet roll")
        self.hiddenItems.append("synthetic gorilla meat")
        self.hiddenItems.append("tarberry")
        self.hiddenItems.append("tasty deathclaw omelette")
        self.hiddenItems.append("tato")
        self.hiddenItems.append("tato flower")
        self.hiddenItems.append("thistle")
        self.hiddenItems.append("vegetable soup")
        self.hiddenItems.append("wild mutfruit")
        self.hiddenItems.append("yao guai meat")
        self.hiddenItems.append("yao guai ribs")
        self.hiddenItems.append("yao guai roast")
        self.hiddenItems.append("yumyum deviled eggs")
        ### drink
        self.hiddenItems.append("beer")
        self.hiddenItems.append("bobrov's best moonshine")
        self.hiddenItems.append("bourbon")
        self.hiddenItems.append("deezer's lemonade")
        self.hiddenItems.append("dirty wastelander")
        self.hiddenItems.append("dirty water")
        self.hiddenItems.append("drugged water")
        self.hiddenItems.append("glowing blood pack")
        self.hiddenItems.append("gwinnett ale")
        self.hiddenItems.append("gwinnett brew")
        self.hiddenItems.append("gwinnett lager")
        self.hiddenItems.append("gwinnett pale")
        self.hiddenItems.append("gwinnett pilsner")
        self.hiddenItems.append("gwinnett stout")
        self.hiddenItems.append("ice cold beer")
        self.hiddenItems.append("ice cold gwinnett ale")
        self.hiddenItems.append("ice cold gwinnett brew")
        self.hiddenItems.append("ice cold gwinnett lager")
        self.hiddenItems.append("ice cold gwinnett pale")
        self.hiddenItems.append("ice cold gwinnett pilsner")
        self.hiddenItems.append("ice cold gwinnett stout")
        self.hiddenItems.append("ice cold nuka cherry")
        self.hiddenItems.append("ice cold nuka cola")
        self.hiddenItems.append("ice cold nuka cola quantum")
        self.hiddenItems.append("institute bottled water")
        self.hiddenItems.append("irradiated blood")
        self.hiddenItems.append("nuka cherry")
        self.hiddenItems.append("nuka cola")
        self.hiddenItems.append("nuka cola quantum")
        self.hiddenItems.append("poisoned wine")
        self.hiddenItems.append("purified water")
        self.hiddenItems.append("refreshing beverage")
        self.hiddenItems.append("rum")
        self.hiddenItems.append("vodka")
        self.hiddenItems.append("whiskey")
        self.hiddenItems.append("wine")


        settingPath = 'doctorsbag/hiddenItems'
        self._app.settings.setValue(settingPath, self.hiddenItems)
        self.updateDrugView()
        return
        
    
        
    def showAllAidItems(self):
        #print('showall')
        self.hiddenItems = []
        settingPath = 'doctorsbag/hiddenItems'
        self._app.settings.setValue(settingPath, self.hiddenItems)
        self.updateDrugView()
        
    def updateDrugView(self):
        self.drugmodel.clear()
 
        if (self.pipInventoryInfo):
            aidItems = self.pipInventoryInfo.child('48')
            if(not aidItems):
                return
            for i in range(0, aidItems.childCount()):
                #if not self._isItemReal(aidItems.child(i)):
                #    continue
            
                name = aidItems.child(i).child('text').value()
                if not name.lower() in self.hiddenItems:
                    count = str(aidItems.child(i).child('count').value())
                    
                    item = [
                        QStandardItem(name) , 
                        QStandardItem(count)
                    ]
                    
                    item[1].setData(QtCore.Qt.AlignCenter, QtCore.Qt.TextAlignmentRole)
                    
                    self.drugmodel.appendRow(item)
            
                    
            self.widget.drugView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            self.widget.drugView.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
            self.widget.drugView.verticalHeader().setStretchLastSection(False)
            self.widget.drugView.horizontalHeader().setStretchLastSection(True)
            self.widget.drugView.setModel(self.drugmodel)
            
            self.widget.drugView.sortByColumn(0, QtCore.Qt.DescendingOrder)

    def useItemByName(self,inventorySection, itemName):
        itemName = itemName.lower()
        if (self.pipInventoryInfo):
            inventory = self.pipInventoryInfo.child(inventorySection)
            for i in range(0, inventory.childCount()):
                name = inventory.child(i).child('text').value()
                if (name.lower() == itemName):
                    self.dataManager.rpcUseItem(inventory.child(i))
                    return
                    
        return        