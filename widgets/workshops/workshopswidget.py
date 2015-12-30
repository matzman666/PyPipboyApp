import os
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from widgets import widgets
from widgets.shared.PipboyIcon import PipboyIcon

class WorkshopsWidget(widgets.WidgetBase):
    UIUpdateSignal = QtCore.pyqtSignal()
    ColorUpdateSignal = QtCore.pyqtSignal(QColor)
    WorkshopListModel = QStandardItemModel()
    
    Icons = None
    
    SelectedWorkshopId = -1
    DataManager = None
    WorkshopData = None
    WorkshopSubData = None
    ColorData = None
    
    def __init__(self, mhandle, parent):
        super().__init__("Workshops Browser", parent)
        
        self.widget = uic.loadUi(os.path.join(mhandle.basepath, "ui", "workshopswidget.ui"))
        self.setWidget(self.widget)
        
        self.UIUpdateSignal.connect(self.UpdateUI)
        self.ColorUpdateSignal.connect(self.UpdateIconColor)
        self.widget.workshopList.clicked.connect(self.WorkshopListClicked)

        self.Icons = [
            PipboyIcon("People.svg", self.widget.iconPeople)
            , PipboyIcon("Food.svg", self.widget.iconFood)
            , PipboyIcon("Drop.svg", self.widget.iconWater)
            , PipboyIcon("Energy.svg", self.widget.iconPower)
            , PipboyIcon("Shield.svg", self.widget.iconDefense)
            , PipboyIcon("Bed.svg", self.widget.iconBeds)
            , PipboyIcon("Smile.svg", self.widget.iconHappiness)
            , PipboyIcon("Warning.svg", self.widget.warningPeople)
            , PipboyIcon("Warning.svg", self.widget.warningFood)
            , PipboyIcon("Warning.svg", self.widget.warningWater)
            , PipboyIcon("Warning.svg", self.widget.warningPower)
            , PipboyIcon("Warning.svg", self.widget.warningDefense)
            , PipboyIcon("Warning.svg", self.widget.warningBeds)
            , PipboyIcon("Warning.svg", self.widget.warningHappiness)
        ]
        
        for i in self.Icons:
            if i.FileName == "Warning.svg":
                i.Enabled = False
            i.Update()
    
    def init(self, app, datamanager):
        super().init(app, datamanager)
        
        self.DataManager = datamanager
        self.DataManager.registerRootObjectListener(self.DataManagerUpdated)
        
    def DataManagerUpdated(self, rootObject):
        self.WorkshopData = rootObject.child("Workshop")
        self.ColorData = rootObject.child("Status").child("EffectColor")
        
        if self.WorkshopData:
            self.WorkshopData.registerValueUpdatedListener(self.WorkshopDataUpdated, 2)
        
        if self.ColorData:
            self.ColorData.registerValueUpdatedListener(self.ColorDataUpdated, 1)
            
            R = self.ColorData.child(0).value() * 255
            G = self.ColorData.child(1).value() * 255
            B = self.ColorData.child(2).value() * 255
            self.ColorUpdateSignal.emit(QColor.fromRgb(R, G, B))

        self.UIUpdateSignal.emit()
    
    def WorkshopDataUpdated(self, caller, value, pathObjs):
        self.UIUpdateSignal.emit()
    
    def WorkshopSubDataUpdated(self, caller, value, pathObjs):
        self.UpdateWorkshopInfo()
    
    def ColorDataUpdated(self, caller, value, pathObjs):
        if self.ColorData:
            R = self.ColorData.child(0).value() * 255
            G = self.ColorData.child(1).value() * 255
            B = self.ColorData.child(2).value() * 255
            self.ColorUpdateSignal.emit(QColor.fromRgb(R, G, B))
    
    def SetWorkshopId(self, workshopId):
        self.SelectedWorkshopId = workshopId
        
        if self.WorkshopData:            
            if self.WorkshopSubData:
                self.WorkshopSubData.unregisterValueUpdatedListener(self.WorkshopSubDataUpdated)
            
            self.WorkshopSubData = self.WorkshopData.child(self.SelectedWorkshopId)
            self.WorkshopSubData.registerValueUpdatedListener(self.WorkshopSubDataUpdated, 3)
        
        self.UpdateWorkshopInfo()
    
    @QtCore.pyqtSlot()
    def UpdateUI(self):
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
                    
            self.widget.workshopList.setModel(self.WorkshopListModel)
            self.widget.workshopList.sortByColumn(1, Qt.AscendingOrder)
            self.widget.workshopList.hideColumn(0)
            
            if self.SelectedWorkshopId == -1:
                Index = self.WorkshopListModel.index(0, 0)
                Data = self.WorkshopListModel.data(Index)
                
                if Data:
                    self.SetWorkshopId(int(Data))
    
    @QtCore.pyqtSlot(QColor)
    def UpdateIconColor(self, iconColor):
        for i in self.Icons:
            i.Color = iconColor
            i.Update()
    
    @QtCore.pyqtSlot(QModelIndex)
    def WorkshopListClicked(self, index):
        NewIndex = self.WorkshopListModel.index(index.row(), 0)
        DataId = int(self.WorkshopListModel.data(NewIndex))
        
        self.SetWorkshopId(DataId)
    
    def SetWarningWidget(self, widget, state):
        for i in self.Icons:
            if i.Widget == widget:
                i.Enabled = state
                i.Update()
    
    def UpdateWorkshopInfo(self):
        if self.WorkshopData.childCount() and self.WorkshopSubData:
            Name = self.WorkshopData.child(self.SelectedWorkshopId).child("text").value()
            PopulationValue = self.WorkshopSubData.child("workshopData").child(0).child("Value").value()
            PopulationRating = self.WorkshopSubData.child("workshopData").child(0).child("rating").value()
            FoodValue = self.WorkshopSubData.child("workshopData").child(1).child("Value").value()
            FoodRating = self.WorkshopSubData.child("workshopData").child(1).child("rating").value()
            WaterValue = self.WorkshopSubData.child("workshopData").child(2).child("Value").value()
            WaterRating = self.WorkshopSubData.child("workshopData").child(2).child("rating").value()
            PowerValue = self.WorkshopSubData.child("workshopData").child(3).child("Value").value()
            PowerRating = self.WorkshopSubData.child("workshopData").child(3).child("rating").value()
            DefenseValue = self.WorkshopSubData.child("workshopData").child(4).child("Value").value()
            DefenseRating = self.WorkshopSubData.child("workshopData").child(4).child("rating").value()
            BedsValue = self.WorkshopSubData.child("workshopData").child(5).child("Value").value()
            BedsRating = self.WorkshopSubData.child("workshopData").child(5).child("rating").value()
            HappinessValue = self.WorkshopSubData.child("workshopData").child(6).child("Value").value()
            HappinessRating = self.WorkshopSubData.child("workshopData").child(6).child("rating").value()
            
            self.widget.labelLocation.setText(Name)
            self.widget.numberPeople.setText(str(PopulationValue))
            self.widget.numberFood.setText(str(FoodValue))
            self.widget.numberWater.setText(str(WaterValue))
            self.widget.numberPower.setText(str(PowerValue))
            self.widget.numberDefense.setText(str(DefenseValue))
            self.widget.numberBeds.setText(str(BedsValue))
            self.widget.numberHappiness.setText(str(HappinessValue))
            
            if PopulationRating < 0:
                self.SetWarningWidget(self.widget.warningPeople, True)
            else:
                self.SetWarningWidget(self.widget.warningPeople, False)
            
            if FoodRating < 0:
                self.SetWarningWidget(self.widget.warningFood, True)
            else:
                self.SetWarningWidget(self.widget.warningFood, False)
            
            if WaterRating < 0:
                self.SetWarningWidget(self.widget.warningWater, True)
            else:
                self.SetWarningWidget(self.widget.warningWater, False)
            
            if PowerRating < 0:
                self.SetWarningWidget(self.widget.warningPower, True)
            else:
                self.SetWarningWidget(self.widget.warningPower, False)
            
            if DefenseRating < 0:
                self.SetWarningWidget(self.widget.warningDefense, True)
            else:
                self.SetWarningWidget(self.widget.warningDefense, False)
            
            if BedsRating < 0:
                self.SetWarningWidget(self.widget.warningBeds, True)
            else:
                self.SetWarningWidget(self.widget.warningBeds, False)
            
            if HappinessRating < 0 and HappinessValue > 20:
                self.SetWarningWidget(self.widget.warningHappiness, True)
            else:
                self.SetWarningWidget(self.widget.warningHappiness, False)