# -*- coding: utf-8 -*-
import os
from PyQt5 import QtGui, QtWidgets, QtCore, uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from widgets.shared.graphics import ImageFactory
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
        self.imageFactory = ImageFactory(os.path.join(mhandle.basepath, 'res'))
        self._logger = logging.getLogger('pypipboyapp.doctorsbagwidget')
        self.setWidget(self.widget)
        self.foreColor = QtGui.QColor.fromRgb(0,255,0)
        self.pipColour = None
        self.pipInventoryInfo = None

        self._signalInfoUpdated.connect(self._slotInfoUpdated)
        self._signalColorUpdated.connect(self._slotColorUpdated)

    def init(self, app, datamanager):
        super().init(app, datamanager)
        self.dataManager = datamanager
        self.dataManager.registerRootObjectListener(self._onPipRootObjectEvent)

        self._app = app
        self.customIcon = self.imageFactory.getImage('aid-custom.png')
        self.customIconA = self.imageFactory.getImage('aid-custom.png')
        self.drugsIcon = self.imageFactory.getImage('aid-drugs.png')
        self.drugsIconA = self.imageFactory.getImage('aid-drugs.png')
        self.drinkIcon = self.imageFactory.getImage('aid-drink.png')
        self.drinkIconA = self.imageFactory.getImage('aid-drink.png')
        self.foodIcon = self.imageFactory.getImage('aid-food.png')
        self.foodIconA = self.imageFactory.getImage('aid-food.png')
        self.allIcon = self.imageFactory.getImage('aid-all.png')
        self.allIconA = self.imageFactory.getImage('aid-all.png')

        #self.viewMode = 'All'
        self.drugItems = []
        self.foodItems = []
        self.drinkItems = []
        self.loadItemLists()
        
        self.customItems = []
        settingPath = 'doctorsbag/customItems'
        self.customItems = self._app.settings.value(settingPath, [])
        
        self.widget.drugView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.widget.drugView.customContextMenuRequested.connect(self.drugViewMenuRequested)
        
        self.widget.btnCustom.clicked.connect(self.showCustom)
        self.widget.btnDrugs.clicked.connect(self.showDrugs)
        
        
        self.widget.btnDrink.clicked.connect(self.showDrink)
        self.widget.btnFood.clicked.connect(self.showFood)
        self.widget.btnAll.clicked.connect(self.showAll)
        
        self.widget.drugView.clicked.connect(self.drugViewClicked)
        
        self._slotColorUpdated(self.foreColor)
        
        if len(self.customItems) > 0:
            #self.showCustom()
            self.widget.btnCustom.click()
        else:
            #self.showDrugs()
            self.widget.btnDrugs.click()
        
    def getMenuCategory(self):
        return 'Inventory && Gear'

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
        ImageFactory.colorizeImage(self.customIcon, QtCore.Qt.black)
        ImageFactory.colorizeImage(self.customIconA, self.foreColor)
        customIcon = QIcon(QPixmap.fromImage(self.customIcon))
        customIcon.addPixmap(QPixmap.fromImage(self.customIconA), QIcon.Active)
        customIcon.addPixmap(QPixmap.fromImage(self.customIconA), QIcon.Normal, QIcon.On)
        self.widget.btnCustom.setIcon(customIcon)
        self.widget.btnCustom.setText('')


        ImageFactory.colorizeImage(self.drugsIcon, QtCore.Qt.black)
        ImageFactory.colorizeImage(self.drugsIconA, self.foreColor)
        drugsIcon = QIcon(QPixmap.fromImage(self.drugsIcon))
        drugsIcon.addPixmap(QPixmap.fromImage(self.drugsIconA), QIcon.Active)
        drugsIcon.addPixmap(QPixmap.fromImage(self.drugsIconA), QIcon.Normal, QIcon.On)
        self.widget.btnDrugs.setIcon(drugsIcon)
        self.widget.btnDrugs.setText('')

        ImageFactory.colorizeImage(self.drinkIcon, QtCore.Qt.black)
        ImageFactory.colorizeImage(self.drinkIconA, self.foreColor)
        drinkIcon = QIcon(QPixmap.fromImage(self.drinkIcon))
        drinkIcon.addPixmap(QPixmap.fromImage(self.drinkIconA), QIcon.Active)
        drinkIcon.addPixmap(QPixmap.fromImage(self.drinkIconA), QIcon.Normal, QIcon.On)
        self.widget.btnDrink.setIcon(drinkIcon)
        self.widget.btnDrink.setText('')

        ImageFactory.colorizeImage(self.foodIcon, QtCore.Qt.black)
        ImageFactory.colorizeImage(self.foodIconA, self.foreColor)
        foodIcon = QIcon(QPixmap.fromImage(self.foodIcon))
        foodIcon.addPixmap(QPixmap.fromImage(self.foodIconA), QIcon.Active)
        foodIcon.addPixmap(QPixmap.fromImage(self.foodIconA), QIcon.Normal, QIcon.On)
        self.widget.btnFood.setIcon(foodIcon)
        self.widget.btnFood.setText('')

        ImageFactory.colorizeImage(self.allIcon, QtCore.Qt.black)
        ImageFactory.colorizeImage(self.allIconA, self.foreColor)
        allIcon = QIcon(QPixmap.fromImage(self.allIcon))
        allIcon.addPixmap(QPixmap.fromImage(self.allIconA), QIcon.Active)
        allIcon.addPixmap(QPixmap.fromImage(self.allIconA), QIcon.Normal, QIcon.On)
        self.widget.btnAll.setIcon(allIcon)   
        self.widget.btnAll.setText('')
        return
        
    @QtCore.pyqtSlot()
    def _slotInfoUpdated(self):
        if self.widget.btnCustom.isChecked(): # self.viewMode == 'Custom':
            self.updateDrugView(self.customItems, showitemswithzerocount=True)
        elif self.widget.btnDrugs.isChecked():
            self.updateDrugView(self.drugItems)
        elif self.widget.btnDrink.isChecked():
            self.updateDrugView(self.drinkItems)
        elif self.widget.btnFood.isChecked():
            self.updateDrugView(self.foodItems)
        elif self.widget.btnAll.isChecked():
            self.updateDrugView(None)
        else:
            self.updateDrugView(None)

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

            if not self.widget.btnCustom.isChecked():
                def _addItemToCustomList():
                    #print('hide: ' + clickedItemName)
                    self.customItems.append(clickedItemName.lower())
                    settingPath = 'doctorsbag/customItems'
                    self._app.settings.setValue(settingPath, self.customItems)
                if not clickedItemName.lower() in self.customItems:
                    addItemToCustomListAction = QAction('Add ' + clickedItemName + ' to custom list' , menu)
                    addItemToCustomListAction.triggered.connect(_addItemToCustomList)
                    menu.addAction(addItemToCustomListAction)

            else:
                def _removeFromCustomList():
                    self.customItems.remove(clickedItemName.lower())
                    settingPath = 'doctorsbag/customItems'
                    self._app.settings.setValue(settingPath, self.customItems)
                    self._signalInfoUpdated.emit()
                if clickedItemName.lower() in self.customItems:
                    removeFromCustomListAction = QAction('Remove ' + clickedItemName + ' from custom list' , menu)
                    removeFromCustomListAction.triggered.connect(_removeFromCustomList)
                    menu.addAction(removeFromCustomListAction)


        menu.exec(self.widget.drugView.mapToGlobal(pos))
        return
        
    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def drugViewClicked(self, index):
        model = self.widget.drugView.model() 
        modelIndex = model.index(index.row(), 0)
        #print('dvc: ' + str(model.data(modelIndex)))
        self.useItemByName(str(model.data(modelIndex)))
        return

    def loadItemLists(self):
        self.drugItems = []
        self.foodItems = []
        self.drinkItems = []
        ### drugs
        self.drugItems.append("endangerol syringe")
        self.drugItems.append("addictol")
        self.drugItems.append("berry mentats")
        self.drugItems.append("buffjet")
        self.drugItems.append("buffout")
        self.drugItems.append("bufftats")
        self.drugItems.append("calmex")
        self.drugItems.append("daddy-o")
        self.drugItems.append("day tripper")
        self.drugItems.append("fury")
        self.drugItems.append("grape mentats")
        self.drugItems.append("jet")
        self.drugItems.append("jet fuel")
        self.drugItems.append("med-x")
        self.drugItems.append("mentats")
        self.drugItems.append("mysterious serum")
        self.drugItems.append("orange mentats")
        self.drugItems.append("overdrive")
        self.drugItems.append("psycho")
        self.drugItems.append("psycho jet")
        self.drugItems.append("psychobuff")
        self.drugItems.append("psychotats")
        self.drugItems.append("rad-x")
        self.drugItems.append("radaway")
        self.drugItems.append("skeeto spit")
        self.drugItems.append("stimpak")
        self.drugItems.append("ultra jet")
        self.drugItems.append("vault 81 cure")
        self.drugItems.append("x-111 compound")
        self.drugItems.append("x-cell")
        self.drugItems.append("railroad stealth boy")
        self.drugItems.append("stealth boy")

        ### food
        self.foodItems.append("baked bloatfly")
        self.foodItems.append("blamco brand mac and cheese")
        self.foodItems.append("bloatfly meat")
        self.foodItems.append("bloodbug meat")
        self.foodItems.append("bloodbug steak")
        self.foodItems.append("bloodleaf")
        self.foodItems.append("brahmin meat")
        self.foodItems.append("brain fungus")
        self.foodItems.append("bubblegum")
        self.foodItems.append("canned dog food")
        self.foodItems.append("carrot")
        self.foodItems.append("carrot flower")
        self.foodItems.append("cat meat")
        self.foodItems.append("cooked softshell meat")
        self.foodItems.append("corn")
        self.foodItems.append("cram")
        self.foodItems.append("crispy squirrel bits")
        self.foodItems.append("dandy boy apples")
        self.foodItems.append("deathclaw egg")
        self.foodItems.append("deathclaw egg omelette")
        self.foodItems.append("deathclaw meat")
        self.foodItems.append("deathclaw steak")
        self.foodItems.append("deathclaw wellingham")
        self.foodItems.append("experimental plant")
        self.foodItems.append("fancy lads snack cakes")
        self.foodItems.append("food paste")
        self.foodItems.append("fresh carrot")
        self.foodItems.append("fresh corn")
        self.foodItems.append("fresh melon")
        self.foodItems.append("fresh mutfruit")
        self.foodItems.append("glowing fungus")
        self.foodItems.append("gourd")
        self.foodItems.append("gourd blossom")
        self.foodItems.append("grilled radroach")
        self.foodItems.append("grilled radstag")
        self.foodItems.append("gum drops")
        self.foodItems.append("happy birthday sweet roll")
        self.foodItems.append("hubflower")
        self.foodItems.append("iguana bits")
        self.foodItems.append("iguana on a stick")
        self.foodItems.append("iguana soup")
        self.foodItems.append("instamash")
        self.foodItems.append("institute food packet")
        self.foodItems.append("melon")
        self.foodItems.append("mirelurk cake")
        self.foodItems.append("mirelurk egg")
        self.foodItems.append("mirelurk egg omelette")
        self.foodItems.append("mirelurk meat")
        self.foodItems.append("mirelurk queen steak")
        self.foodItems.append("moldy food")
        self.foodItems.append("mole rat chunks")
        self.foodItems.append("mole rat meat")
        self.foodItems.append("mongrel dog meat")
        self.foodItems.append("mutant hound chops")
        self.foodItems.append("mutant hound meat")
        self.foodItems.append("mutated fern flower")
        self.foodItems.append("mutfruit")
        self.foodItems.append("mutt chops")
        self.foodItems.append("noodle cup")
        self.foodItems.append("perfectly preserved pie")
        self.foodItems.append("pork n' beans")
        self.foodItems.append("potato crisps")
        self.foodItems.append("potted meat")
        self.foodItems.append("preserved instamash")
        self.foodItems.append("pristine deathclaw egg")
        self.foodItems.append("queen mirelurk meat")
        self.foodItems.append("radroach meat")
        self.foodItems.append("radscorpion egg")
        self.foodItems.append("radscorpion egg omelette")
        self.foodItems.append("radscorpion meat")
        self.foodItems.append("radscorpion steak")
        self.foodItems.append("radstag meat")
        self.foodItems.append("radstag stew")
        self.foodItems.append("razorgrain")
        self.foodItems.append("ribeye steak")
        self.foodItems.append("roasted mirelurk meat")
        self.foodItems.append("salisbury steak")
        self.foodItems.append("silt bean")
        self.foodItems.append("slocum's buzzbites")
        self.foodItems.append("softshell mirelurk meat")
        self.foodItems.append("squirrel bits")
        self.foodItems.append("squirrel on a stick")
        self.foodItems.append("squirrel stew")
        self.foodItems.append("stingwing filet")
        self.foodItems.append("stingwing meat")
        self.foodItems.append("sugar bombs")
        self.foodItems.append("sweet roll")
        self.foodItems.append("synthetic gorilla meat")
        self.foodItems.append("tarberry")
        self.foodItems.append("tasty deathclaw omelette")
        self.foodItems.append("tato")
        self.foodItems.append("tato flower")
        self.foodItems.append("thistle")
        self.foodItems.append("vegetable soup")
        self.foodItems.append("wild mutfruit")
        self.foodItems.append("yao guai meat")
        self.foodItems.append("yao guai ribs")
        self.foodItems.append("yao guai roast")
        self.foodItems.append("yumyum deviled eggs")
        ### drink
        self.drinkItems.append("beer")
        self.drinkItems.append("bobrov's best moonshine")
        self.drinkItems.append("bourbon")
        self.drinkItems.append("deezer's lemonade")
        self.drinkItems.append("dirty wastelander")
        self.drinkItems.append("dirty water")
        self.drinkItems.append("drugged water")
        self.drinkItems.append("glowing blood pack")
        self.drinkItems.append("gwinnett ale")
        self.drinkItems.append("gwinnett brew")
        self.drinkItems.append("gwinnett lager")
        self.drinkItems.append("gwinnett pale")
        self.drinkItems.append("gwinnett pilsner")
        self.drinkItems.append("gwinnett stout")
        self.drinkItems.append("ice cold beer")
        self.drinkItems.append("ice cold gwinnett ale")
        self.drinkItems.append("ice cold gwinnett brew")
        self.drinkItems.append("ice cold gwinnett lager")
        self.drinkItems.append("ice cold gwinnett pale")
        self.drinkItems.append("ice cold gwinnett pilsner")
        self.drinkItems.append("ice cold gwinnett stout")
        self.drinkItems.append("ice cold nuka cherry")
        self.drinkItems.append("ice cold nuka cola")
        self.drinkItems.append("ice cold nuka cola quantum")
        self.drinkItems.append("institute bottled water")
        self.drinkItems.append("irradiated blood")
        self.drinkItems.append("nuka cherry")
        self.drinkItems.append("nuka cola")
        self.drinkItems.append("nuka cola quantum")
        self.drinkItems.append("poisoned wine")
        self.drinkItems.append("purified water")
        self.drinkItems.append("refreshing beverage")
        self.drinkItems.append("rum")
        self.drinkItems.append("vodka")
        self.drinkItems.append("whiskey")
        self.drinkItems.append("wine")
        return
        
    
    def showFood(self):
        self.updateDrugView(self.foodItems)
        return
    
    def showDrink(self):
        self.updateDrugView(self.drinkItems)
        return
    
    def showDrugs(self):
        self.updateDrugView(self.drugItems)
        return
    
    def showCustom(self):
        self.updateDrugView(self.customItems, showitemswithzerocount=True)
        return
    
    def showAll(self):
        self.updateDrugView(None)

    def getItemToolTip(self, item):
        descCount = 0
        text  =''
        isFirst = True
        for info in item.child('itemCardInfoList').value():
            itext = info.child('text').value()
            isDesc = info.child('showAsDescription')
            ivalue = info.child('Value').value()
            if not itext[0] == '$' and not itext[0] == '%' and ((isDesc and isDesc.value() and descCount == 0) or ivalue != 0.0):
                if isFirst:
                    isFirst = False
                else:
                    text += '\n'
                text += itext
                if not isDesc or not isDesc.value():
                    duration = info.child('duration')
                    scaleWithDur = info.child('scaleWithDuration')
                    if scaleWithDur and scaleWithDur.value():
                        ivalue *= duration.value()
                    asPercent = info.child('showAsPercent')
                    if (not asPercent or not asPercent.value()) and ivalue > 0:
                        text += ' +' + str(int(ivalue))
                    else:
                        text += ' ' + str(int(ivalue))
                    if asPercent and asPercent.value():
                        text += '%'
                    if duration and duration.value() > 0.0:
                        if scaleWithDur and scaleWithDur.value():
                            text += ' over '
                        else:
                            text += ' ('
                        text += str(int(duration.value())) + 'sec'
                        if scaleWithDur and scaleWithDur.value():
                            pass
                        else:
                            text += ')'
                else:
                    descCount += 1

        return text

    def updateDrugView(self, itemList, showitemswithzerocount=False):
        self.drugmodel.clear()

        if (self.pipInventoryInfo):
            def _filterFunc(item):
                if (inventoryutils.itemHasAnyFilterCategory(item, inventoryutils.eItemFilterCategory.Aid)
                        and (itemList is None or item.child('text').value().lower() in itemList)):
                    return True
                else:
                    return False

            aidItems = inventoryutils.inventoryGetItems(self.pipInventoryInfo, _filterFunc)
            if (not aidItems):
                return
            for i in aidItems:
                name = i.child('text').value()
                count = str(i.child('count').value())
                itemtooltip = self.getItemToolTip(i)
                modelitem = self.createDrugModelItem(name, count, itemtooltip)

                self.drugmodel.appendRow(modelitem)

            if showitemswithzerocount:
                itemsinmodel = []
                for row in range(0, self.drugmodel.rowCount()):
                    itemsinmodel.append(self.drugmodel.item(row, 0).text().lower())

                for item in itemList:
                    if not item in itemsinmodel:
                        modelitem = self.createDrugModelItem(item.capitalize(), '-', '')
                        self.drugmodel.appendRow(modelitem)

            if (self.widget.btnCustom.isChecked() and self.drugmodel.rowCount() == 0):
                self.drugmodel.appendRow([QStandardItem(''), QStandardItem('Right click on items')])
                self.drugmodel.appendRow([QStandardItem(''), QStandardItem('in the other lists to ')])
                self.drugmodel.appendRow([QStandardItem(''), QStandardItem('add them to this list')])


            self.widget.drugView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            self.widget.drugView.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
            self.widget.drugView.verticalHeader().setStretchLastSection(False)
            self.widget.drugView.horizontalHeader().setStretchLastSection(True)
            self.widget.drugView.setModel(self.drugmodel)

            self.widget.drugView.sortByColumn(0, QtCore.Qt.AscendingOrder)

    def createDrugModelItem(self, name, count, itemtooltip):
        tooltipstr = 'Left-click to use item\n'
        if self.widget.btnCustom.isChecked():
            tooltipstr += 'Right-click to remove from custom list\n\n'
        else:
            tooltipstr += 'Right-click to add to custom list\n\n'
        tooltipstr += itemtooltip
        item = [
            QStandardItem(name),
            QStandardItem(count)
        ]
        item[0].setToolTip(tooltipstr)
        item[1].setToolTip(tooltipstr)
        item[1].setData(QtCore.Qt.AlignCenter, QtCore.Qt.TextAlignmentRole)
        return item

    def useItemByName(self, itemName):
        itemName = itemName.lower()
        def _filterFunc(item):
            if (inventoryutils.itemHasAnyFilterCategory(item,inventoryutils.eItemFilterCategory.Aid) 
                    and item.child('text').value().lower() == itemName):
                return True
            else:
                return False
        item = inventoryutils.inventoryGetItem(self.pipInventoryInfo, _filterFunc)
        if item:
            try:
                self.dataManager.rpcUseItem(item)
            except Exception as e:
                self._logger.error('DoctorsBag: Exception in rpc call: ' + str(e))
