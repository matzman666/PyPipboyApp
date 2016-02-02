import os
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from widgets import widgets
from widgets.shared.PipboyIcon import PipboyIcon
from .workshopsmodel import WorkshopTableModel, SortProxyModel
from widgets.shared import settings

class WorkshopsWidget(widgets.WidgetBase):
    WorkshopInfoSignal = QtCore.pyqtSignal()
    ColorUpdateSignal = QtCore.pyqtSignal(QColor)
    
    Widgets = None
    
    DataManager = None
    WorkshopData = None
    ColorData = None
    
    Icons = None
        
    def __init__(self, mhandle, parent):
        super().__init__("Workshops", parent)
        
        self.Widgets = uic.loadUi(os.path.join(mhandle.basepath, "ui", "workshopswidget.ui"))
        self.setWidget(self.Widgets)
        
        self.Icons = [
            PipboyIcon("People.svg", self.Widgets.iconPeople)
            , PipboyIcon("Food.svg", self.Widgets.iconFood)
            , PipboyIcon("Drop.svg", self.Widgets.iconWater)
            , PipboyIcon("Energy.svg", self.Widgets.iconPower)
            , PipboyIcon("Shield.svg", self.Widgets.iconDefense)
            , PipboyIcon("Bed.svg", self.Widgets.iconBeds)
            , PipboyIcon("Smile.svg", self.Widgets.iconHappiness)
            , PipboyIcon("Warning.svg", self.Widgets.warningPeople)
            , PipboyIcon("Warning.svg", self.Widgets.warningFood)
            , PipboyIcon("Warning.svg", self.Widgets.warningWater)
            , PipboyIcon("Warning.svg", self.Widgets.warningPower)
            , PipboyIcon("Warning.svg", self.Widgets.warningDefense)
            , PipboyIcon("Warning.svg", self.Widgets.warningBeds)
            , PipboyIcon("Warning.svg", self.Widgets.warningHappiness)
        ]
        
        for i in self.Icons:
            if i.FileName == "Warning.svg":
                i.Enabled = False
            i.Update()
        
        self.WorkshopInfoSignal.connect(self.UpdateWorkshopInfo)
        self.ColorUpdateSignal.connect(self.UpdateIconColor)
        
    def init(self, app, dataManager):
        super().init(app, dataManager)
        self.app = app
        self.DataManager = dataManager
        self.selectedWorkshop = None
        self.workshopModel = WorkshopTableModel(self.Widgets.workshopList)
        self.sortModel = SortProxyModel(app.settings, 'workshopsbrowser')
        self.sortModel.setSourceModel(self.workshopModel)
        self.Widgets.workshopList.setModel(self.sortModel) # we need to call setModel() before selectionModel() (and never afterwards)
        self.Widgets.workshopList.selectionModel().currentChanged.connect(self.WorkshopListCurrentChanged)
        self.Widgets.workshopList.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.Widgets.workshopList.customContextMenuRequested.connect(self.workshopListMenuRequested)
        # Init Splitter
        settings.setSplitterState(self.Widgets.splitter, self.app.settings.value('workshopsbrowser/splitterState', None))
        self.Widgets.splitter.splitterMoved.connect(self._slotSplitterMoved)
        # Init table header
        self.tableHeader = self.Widgets.workshopList.horizontalHeader()
        self.tableHeader.setSectionsMovable(True)
        self.tableHeader.setStretchLastSection(True)
        settings.setHeaderSectionSizes(self.tableHeader, self.app.settings.value('workshopsbrowser/HeaderSectionSizes', []))
        settings.setHeaderSectionVisualIndices(self.tableHeader, self.app.settings.value('workshopsbrowser/HeaderSectionVisualIndices', []))
        if self.sortModel.sortReversed:
            self.Widgets.workshopList.sortByColumn(self.sortModel.sortColumn, QtCore.Qt.DescendingOrder)
        else:
            self.Widgets.workshopList.sortByColumn(self.sortModel.sortColumn, QtCore.Qt.AscendingOrder)
        self.tableHeader.sectionResized.connect(self._slotTableSectionResized)
        self.tableHeader.sectionMoved.connect(self._slotTableSectionMoved)
        self.DataManager.registerRootObjectListener(self.DataManagerUpdated)
        
    def getMenuCategory(self):
        return 'Map && Locations'

    @QtCore.pyqtSlot(QtCore.QPoint)
    def workshopListMenuRequested(self, pos):
        if self.selectedWorkshop:
            menu = QMenu(self)
            def _fastTravelTo():
                try:
                    mapMarkerID = self.selectedWorkshop.child("mapMarkerID").value()
                    for k in self.rootObject.child('Map').child('World').child('Locations').value():
                        if k.child('LocationMarkerFormId').value() == mapMarkerID:
                            self.DataManager.rpcFastTravel(k)
                except:
                    pass
            location_name = self.selectedWorkshop.child("text").value()
            addFastTravelAction = QAction('Fast Travel to ' + location_name , menu)
            addFastTravelAction.triggered.connect(_fastTravelTo)
            menu.addAction(addFastTravelAction)
            menu.exec(self.Widgets.workshopList.mapToGlobal(pos))

    def DataManagerUpdated(self, rootObject):
        self.rootObject = rootObject
        self.WorkshopData = self.rootObject.child("Workshop")
        self.ColorData = self.rootObject.child("Status").child("EffectColor")
        
        if self.WorkshopData:
            self.workshopModel.setPipWorkshops(self.DataManager, self.WorkshopData)
        
        if self.ColorData:
            self.ColorData.registerValueUpdatedListener(self.ColorDataUpdated, 1)
            
            R = self.ColorData.child(0).value() * 255
            G = self.ColorData.child(1).value() * 255
            B = self.ColorData.child(2).value() * 255
            
            self.ColorUpdateSignal.emit(QColor.fromRgb(R, G, B))
        self.WorkshopInfoSignal.emit()
    
    def ColorDataUpdated(self, caller, value, pathObjs):
        if self.ColorData:
            R = self.ColorData.child(0).value() * 255
            G = self.ColorData.child(1).value() * 255
            B = self.ColorData.child(2).value() * 255
            
            self.ColorUpdateSignal.emit(QColor.fromRgb(R, G, B))
    
    def SetWarningWidget(self, widget, state):
        for i in self.Icons:
            if i.Widget == widget:
                i.Enabled = state
                i.Update()

    @QtCore.pyqtSlot(QModelIndex, QModelIndex)
    def WorkshopListCurrentChanged(self, index, previous):
        tmp = self.workshopModel.getPipValue(self.sortModel.mapToSource(index).row())
        if tmp:
            self.selectedWorkshop = tmp
            self.WorkshopInfoSignal.emit()
    
    @QtCore.pyqtSlot(QColor)
    def UpdateIconColor(self, iconColor):
        for i in self.Icons:
            i.Color = iconColor
            i.Update()
        
    @QtCore.pyqtSlot(int, int)
    def _slotSplitterMoved(self, pos, index):
        self.app.settings.setValue('workshopsbrowser/splitterState', settings.getSplitterState(self.Widgets.splitter))
            
    @QtCore.pyqtSlot(int, int, int)
    def _slotTableSectionResized(self, logicalIndex, oldSize, newSize):
        self.app.settings.setValue('workshopsbrowser/HeaderSectionSizes', settings.getHeaderSectionSizes(self.tableHeader))
        
    @QtCore.pyqtSlot(int, int, int)
    def _slotTableSectionMoved(self, logicalIndex, oldVisualIndex, newVisualIndex):
        self.app.settings.setValue('workshopsbrowser/HeaderSectionVisualIndices', settings.getHeaderSectionVisualIndices(self.tableHeader))
       
    
    @QtCore.pyqtSlot()
    def UpdateWorkshopInfo(self):
        if self.isVisible():
            if self.selectedWorkshop:
                Name = self.selectedWorkshop.child("text").value()
                PopulationValue = self.selectedWorkshop.child("workshopData").child(0).child("Value").value()
                PopulationRating = self.selectedWorkshop.child("workshopData").child(0).child("rating").value()
                FoodValue = self.selectedWorkshop.child("workshopData").child(1).child("Value").value()
                FoodRating = self.selectedWorkshop.child("workshopData").child(1).child("rating").value()
                WaterValue = self.selectedWorkshop.child("workshopData").child(2).child("Value").value()
                WaterRating = self.selectedWorkshop.child("workshopData").child(2).child("rating").value()
                PowerValue = self.selectedWorkshop.child("workshopData").child(3).child("Value").value()
                PowerRating = self.selectedWorkshop.child("workshopData").child(3).child("rating").value()
                DefenseValue = self.selectedWorkshop.child("workshopData").child(4).child("Value").value()
                DefenseRating = self.selectedWorkshop.child("workshopData").child(4).child("rating").value()
                BedsValue = self.selectedWorkshop.child("workshopData").child(5).child("Value").value()
                BedsRating = self.selectedWorkshop.child("workshopData").child(5).child("rating").value()
                HappinessValue = self.selectedWorkshop.child("workshopData").child(6).child("Value").value()
                HappinessRating = self.selectedWorkshop.child("workshopData").child(6).child("rating").value()
                
                self.Widgets.labelLocation.setText(Name)
                self.Widgets.numberPeople.setText(str(PopulationValue))
                self.Widgets.numberFood.setText(str(FoodValue))
                self.Widgets.numberWater.setText(str(WaterValue))
                self.Widgets.numberPower.setText(str(PowerValue))
                self.Widgets.numberDefense.setText(str(DefenseValue))
                self.Widgets.numberBeds.setText(str(BedsValue))
                self.Widgets.numberHappiness.setText(str(HappinessValue))
                
                if PopulationRating < 0:
                    self.SetWarningWidget(self.Widgets.warningPeople, True)
                else:
                    self.SetWarningWidget(self.Widgets.warningPeople, False)
                
                if FoodRating < 0:
                    self.SetWarningWidget(self.Widgets.warningFood, True)
                else:
                    self.SetWarningWidget(self.Widgets.warningFood, False)
                
                if WaterRating < 0:
                    self.SetWarningWidget(self.Widgets.warningWater, True)
                else:
                    self.SetWarningWidget(self.Widgets.warningWater, False)
                
                if PowerRating < 0:
                    self.SetWarningWidget(self.Widgets.warningPower, True)
                else:
                    self.SetWarningWidget(self.Widgets.warningPower, False)
                
                if DefenseRating < 0:
                    self.SetWarningWidget(self.Widgets.warningDefense, True)
                else:
                    self.SetWarningWidget(self.Widgets.warningDefense, False)
                
                if BedsRating < 0:
                    self.SetWarningWidget(self.Widgets.warningBeds, True)
                else:
                    self.SetWarningWidget(self.Widgets.warningBeds, False)
                
                if HappinessRating < 0 and HappinessValue > 20:
                    self.SetWarningWidget(self.Widgets.warningHappiness, True)
                else:
                    self.SetWarningWidget(self.Widgets.warningHappiness, False)