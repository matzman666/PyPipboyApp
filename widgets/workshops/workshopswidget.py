import os
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from widgets import widgets
from widgets.shared.PipboyIcon import PipboyIcon

class WorkshopsWidget(widgets.WidgetBase):
    WorkshopListSignal = QtCore.pyqtSignal()
    WorkshopInfoSignal = QtCore.pyqtSignal()
    ColorUpdateSignal = QtCore.pyqtSignal(QColor)
    
    WorkshopListModel = QStandardItemModel()
    
    Widgets = None
    
    DataManager = None
    WorkshopData = None
    WorkshopInfoData = None
    ColorData = None
    
    Icons = None
    SelectedWorkshopId = -1
        
    def __init__(self, mhandle, parent):
        super().__init__("Workshops Browser", parent)
        
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
        
        self.WorkshopListSignal.connect(self.UpdateWorkshopList)
        self.WorkshopInfoSignal.connect(self.UpdateWorkshopInfo)
        self.ColorUpdateSignal.connect(self.UpdateIconColor)
        
        self.Widgets.workshopList.setModel(self.WorkshopListModel) # we need to call setModel() before selectionModel() (and never afterwards)
        self.Widgets.workshopList.selectionModel().currentChanged.connect(self.WorkshopListCurrentChanged)
        self.Widgets.workshopList.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.Widgets.workshopList.customContextMenuRequested.connect(self.workshopListMenuRequested)
    def init(self, app, dataManager):
        super().init(app, dataManager)
        
        self.DataManager = dataManager
        self.DataManager.registerRootObjectListener(self.DataManagerUpdated)

    @QtCore.pyqtSlot(QtCore.QPoint)
    def workshopListMenuRequested(self, pos):
        menu = QMenu(self)
        index = self.Widgets.workshopList.indexAt(pos)
        if (index.isValid()):
            model = self.Widgets.workshopList.model()
            modelIndex = model.index(index.row(), 0)
            self.locationIndex = int(model.data(modelIndex))
            location_name = self.WorkshopData.child(self.locationIndex).child("text").value()
            addFastTravelAction = QAction('Fast Travel to ' + location_name , menu)
            addFastTravelAction.triggered.connect(self._fastTravelTo)
            menu.addAction(addFastTravelAction)
        menu.exec(self.Widgets.workshopList.mapToGlobal(pos))
        return

    def _fastTravelTo(self):
        mapMarkerID = self.WorkshopData.child(self.locationIndex).child("mapMarkerID").value()
        pipWorldLocations = self.rootObject.child('Map').child('World').child('Locations')
        if pipWorldLocations:
            for k in pipWorldLocations.value():
                if k.child('LocationMarkerFormId').value() == mapMarkerID:
                    self.DataManager.rpcFastTravel(k)

    def DataManagerUpdated(self, rootObject):
        self.rootObject = rootObject
        self.WorkshopData = self.rootObject.child("Workshop")
        self.ColorData = self.rootObject.child("Status").child("EffectColor")
        
        if self.WorkshopData:
            self.WorkshopData.registerValueUpdatedListener(self.WorkshopDataUpdated, 2)
        
        if self.ColorData:
            self.ColorData.registerValueUpdatedListener(self.ColorDataUpdated, 1)
            
            R = self.ColorData.child(0).value() * 255
            G = self.ColorData.child(1).value() * 255
            B = self.ColorData.child(2).value() * 255
            
            self.ColorUpdateSignal.emit(QColor.fromRgb(R, G, B))

        self.WorkshopListSignal.emit()
        self.WorkshopInfoSignal.emit()
    
    def WorkshopDataUpdated(self, caller, value, pathObjs):
        self.WorkshopListSignal.emit()
    
    def WorkshopInfoDataUpdated(self, caller, value, pathObjs):
        self.WorkshopInfoSignal.emit()
    
    def ColorDataUpdated(self, caller, value, pathObjs):
        if self.ColorData:
            R = self.ColorData.child(0).value() * 255
            G = self.ColorData.child(1).value() * 255
            B = self.ColorData.child(2).value() * 255
            
            self.ColorUpdateSignal.emit(QColor.fromRgb(R, G, B))
    
    def SetWorkshopId(self, workshopId):
        self.SelectedWorkshopId = workshopId
        
        if self.WorkshopData:            
            if self.WorkshopInfoData:
                self.WorkshopInfoData.unregisterValueUpdatedListener(self.WorkshopInfoDataUpdated)
            
            self.WorkshopInfoData = self.WorkshopData.child(self.SelectedWorkshopId)
            self.WorkshopInfoData.registerValueUpdatedListener(self.WorkshopInfoDataUpdated, 3)
        
        self.WorkshopInfoSignal.emit()
    
    def SetWarningWidget(self, widget, state):
        for i in self.Icons:
            if i.Widget == widget:
                i.Enabled = state
                i.Update()

    @QtCore.pyqtSlot(QModelIndex, QModelIndex)
    def WorkshopListCurrentChanged(self, index, previous):
        NewIndex = self.WorkshopListModel.index(index.row(), 0)
        DataId = self.WorkshopListModel.data(NewIndex)
        
        if DataId:
            self.SetWorkshopId(int(DataId))
    
    @QtCore.pyqtSlot(QColor)
    def UpdateIconColor(self, iconColor):
        for i in self.Icons:
            i.Color = iconColor
            i.Update()
    
    @QtCore.pyqtSlot()
    def UpdateWorkshopList(self):
        self.WorkshopListModel.clear()
        
        HighlightFont = QFont()
        HighlightFont.setBold(True)
        
        if self.WorkshopData.childCount():
            for i in range(0, self.WorkshopData.childCount()):
                Owned = self.WorkshopData.child(i).child("owned").value()
                Name = None
                Rating = None
                
                if Owned:
                    Name = self.WorkshopData.child(i).child("text").value()
                    Rating = self.WorkshopData.child(i).child("rating").value()
                    
                    NameItem = QStandardItem(Name)
                    
                    if Rating <= -1:
                        NameItem.setFont(HighlightFont)
                    
                    ListItem = [
                        QStandardItem(str(i)),
                        NameItem
                    ]
                    self.WorkshopListModel.appendRow(ListItem)
                    
            self.Widgets.workshopList.sortByColumn(1, Qt.AscendingOrder)
            self.Widgets.workshopList.hideColumn(0)
            
            if self.SelectedWorkshopId == -1:
                ModelIndex = self.WorkshopListModel.index(0, 0)
                DataId = self.WorkshopListModel.data(ModelIndex)
                
                if DataId:
                    self.SetWorkshopId(int(DataId))
    
    @QtCore.pyqtSlot()
    def UpdateWorkshopInfo(self):
        if self.WorkshopData.childCount() and self.WorkshopInfoData:
            Name = self.WorkshopData.child(self.SelectedWorkshopId).child("text").value()
            PopulationValue = self.WorkshopInfoData.child("workshopData").child(0).child("Value").value()
            PopulationRating = self.WorkshopInfoData.child("workshopData").child(0).child("rating").value()
            FoodValue = self.WorkshopInfoData.child("workshopData").child(1).child("Value").value()
            FoodRating = self.WorkshopInfoData.child("workshopData").child(1).child("rating").value()
            WaterValue = self.WorkshopInfoData.child("workshopData").child(2).child("Value").value()
            WaterRating = self.WorkshopInfoData.child("workshopData").child(2).child("rating").value()
            PowerValue = self.WorkshopInfoData.child("workshopData").child(3).child("Value").value()
            PowerRating = self.WorkshopInfoData.child("workshopData").child(3).child("rating").value()
            DefenseValue = self.WorkshopInfoData.child("workshopData").child(4).child("Value").value()
            DefenseRating = self.WorkshopInfoData.child("workshopData").child(4).child("rating").value()
            BedsValue = self.WorkshopInfoData.child("workshopData").child(5).child("Value").value()
            BedsRating = self.WorkshopInfoData.child("workshopData").child(5).child("rating").value()
            HappinessValue = self.WorkshopInfoData.child("workshopData").child(6).child("Value").value()
            HappinessRating = self.WorkshopInfoData.child("workshopData").child(6).child("rating").value()
            
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