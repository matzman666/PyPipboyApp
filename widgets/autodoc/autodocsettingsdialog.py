import os
import logging
from PyQt5 import QtCore, QtWidgets, QtGui, uic

class AutoDocSettingsDialog(QtWidgets.QDialog):
    Settings = None
    Widgets = None
    Logger = None
    
    WidgetEnabled = False
    StimpakEnabled = True
    MedXEnabled = False
    RadAwayEnabled = True
    RadXEnabled = False
    AddictolEnabled = False
    
    EnabledScene = QtWidgets.QGraphicsScene()
    DisabledScene = QtWidgets.QGraphicsScene()
    
    def __init__(self, settings, parent = None):
        super().__init__(parent)
        
        self.Settings = settings
        self.Widgets = uic.loadUi(os.path.join(os.path.dirname(os.path.realpath(__file__)), "ui", "autodocsettingsdialog.ui"), self)
        self.Logger = logging.getLogger("pypipboyapp.widgets.autodoc")
        
        self.EnabledScene.setBackgroundBrush(QtGui.QBrush(QtGui.QColor.fromRgb(0, 255, 0)))
        self.DisabledScene.setBackgroundBrush(QtGui.QBrush(QtGui.QColor.fromRgb(255, 0, 0)))
        
        self.Widgets.useWidgetButton.clicked.connect(self.UseWidgetButtonClicked)
        self.Widgets.useStimpakButton.clicked.connect(self.UseStimpakButtonClicked)
        self.Widgets.useMedXButton.clicked.connect(self.UseMedXButtonClicked)
        self.Widgets.useRadAwayButton.clicked.connect(self.UseRadAwayButtonClicked)
        self.Widgets.useRadXButton.clicked.connect(self.UseRadXButtonClicked)
        self.Widgets.useAddictolButton.clicked.connect(self.UseAddictolButtonClicked)
        
        self.Widgets.timerDelay.valueChanged.connect(self.TimerDelayValueChanged)
        
        self.Widgets.stimpakPercent.valueChanged.connect(self.StimpakPercentValueChanged)
        self.Widgets.stimpakLimit.valueChanged.connect(self.StimpakLimitValueChanged)
        
        self.Widgets.medxUse.currentIndexChanged.connect(self.MedXUseIndexChanged)
        self.Widgets.medxLimit.valueChanged.connect(self.MedXLimitValueChanged)
        
        self.Widgets.radawayUse.currentIndexChanged.connect(self.RadAwayUseIndexChanged)
        self.Widgets.radawayLimit.valueChanged.connect(self.RadAwayLimitValueChanged)
        
        self.Widgets.radxUse.currentIndexChanged.connect(self.RadXUseIndexChanged)
        self.Widgets.radxLimit.valueChanged.connect(self.RadXLimitValueChanged)
        
        self.Widgets.addictolLimit.valueChanged.connect(self.AddictolLimitValueChanged)
        
        self.LoadUI()
    
    @QtCore.pyqtSlot()
    def UseWidgetButtonClicked(self):
        self.WidgetEnabled = not self.WidgetEnabled
        self.Settings.setValue("AutoDocWidget/Enabled", int(self.WidgetEnabled))
        self.Widgets.useWidgetButton.setText(self.ButtonStateText(self.WidgetEnabled) + " Auto Doc")
        self.Widgets.useWidgetView.setScene(self.ButtonStateScene(self.WidgetEnabled))
        self.Widgets.useWidgetView.show()
    
    @QtCore.pyqtSlot()
    def UseStimpakButtonClicked(self):
        self.StimpakEnabled = not self.StimpakEnabled
        self.Settings.setValue("AutoDocWidget/Stimpak/Enabled", int(self.StimpakEnabled))
        self.Widgets.useStimpakButton.setText(self.ButtonStateText(self.StimpakEnabled) + " Stimpak")
        self.Widgets.useStimpakView.setScene(self.ButtonStateScene(self.StimpakEnabled))
        self.Widgets.useStimpakView.show()
    
    @QtCore.pyqtSlot()
    def UseMedXButtonClicked(self):
        self.MedXEnabled = not self.MedXEnabled
        self.Settings.setValue("AutoDocWidget/MedX/Enabled", int(self.MedXEnabled))
        self.Widgets.useMedXButton.setText(self.ButtonStateText(self.MedXEnabled) + " Med-X")
        self.Widgets.useMedXView.setScene(self.ButtonStateScene(self.MedXEnabled))
        self.Widgets.useMedXView.show()
    
    @QtCore.pyqtSlot()
    def UseRadAwayButtonClicked(self):
        self.RadAwayEnabled = not self.RadAwayEnabled
        self.Settings.setValue("AutoDocWidget/RadAway/Enabled", int(self.RadAwayEnabled))
        self.Widgets.useRadAwayButton.setText(self.ButtonStateText(self.RadAwayEnabled) + " RadAway")
        self.Widgets.useRadAwayView.setScene(self.ButtonStateScene(self.RadAwayEnabled))
        self.Widgets.useRadAwayView.show()
    
    @QtCore.pyqtSlot()
    def UseRadXButtonClicked(self):
        self.RadXEnabled = not self.RadXEnabled
        self.Settings.setValue("AutoDocWidget/RadX/Enabled", int(self.RadXEnabled))
        self.Widgets.useRadXButton.setText(self.ButtonStateText(self.RadXEnabled) + " Rad-X")
        self.Widgets.useRadXView.setScene(self.ButtonStateScene(self.RadXEnabled))
        self.Widgets.useRadXView.show()
    
    @QtCore.pyqtSlot()
    def UseAddictolButtonClicked(self):
        self.AddictolEnabled = not self.AddictolEnabled
        self.Settings.setValue("AutoDocWidget/Addictol/Enabled", int(self.AddictolEnabled))
        self.Widgets.useAddictolButton.setText(self.ButtonStateText(self.AddictolEnabled) + " Addictol")
        self.Widgets.useAddictolView.setScene(self.ButtonStateScene(self.AddictolEnabled))
        self.Widgets.useAddictolView.show()
    
    @QtCore.pyqtSlot(int)
    def TimerDelayValueChanged(self, value):
        self.Settings.setValue("AutoDocWidget/General/TimerDelay", value)
    
    @QtCore.pyqtSlot(int)
    def StimpakPercentValueChanged(self, value):
        self.Settings.setValue("AutoDocWidget/Stimpak/Percent", value)
        self.Widgets.stimpakPercentLabel.setText(str(value))
    
    @QtCore.pyqtSlot(int)
    def StimpakLimitValueChanged(self, value):
        self.Settings.setValue("AutoDocWidget/Stimpak/Limit", value)
    
    @QtCore.pyqtSlot(int)
    def MedXUseIndexChanged(self, index):
        self.Settings.setValue("AutoDocWidget/MedX/Use", index)
    
    @QtCore.pyqtSlot(str)
    def MedXLimitValueChanged(self, value):
        self.Settings.setValue("AutoDocWidget/MedX/Limit", value)
    
    @QtCore.pyqtSlot(int)
    def RadAwayUseIndexChanged(self, index):
        self.Settings.setValue("AutoDocWidget/RadAway/Use", index)
    
    @QtCore.pyqtSlot(str)
    def RadAwayLimitValueChanged(self, value):
        self.Settings.setValue("AutoDocWidget/RadAway/Limit", value)
    
    @QtCore.pyqtSlot(int)
    def RadXUseIndexChanged(self, index):
        self.Settings.setValue("AutoDocWidget/RadX/Use", index)
    
    @QtCore.pyqtSlot(str)
    def RadXLimitValueChanged(self, value):
        self.Settings.setValue("AutoDocWidget/RadX/Limit", value)
    
    @QtCore.pyqtSlot(str)
    def AddictolLimitValueChanged(self, value):
        self.Settings.setValue("AutoDocWidget/Addictol/Limit", value)

    def LoadUI(self):
        self.WidgetEnabled = bool(int(self.Settings.value("AutoDocWidget/Enabled", 0)))
        self.StimpakEnabled = bool(int(self.Settings.value("AutoDocWidget/Stimpak/Enabled", 1)))
        self.MedXEnabled = bool(int(self.Settings.value("AutoDocWidget/MedX/Enabled", 0)))
        self.RadAwayEnabled = bool(int(self.Settings.value("AutoDocWidget/RadAway/Enabled", 1)))
        self.RadXEnabled = bool(int(self.Settings.value("AutoDocWidget/RadX/Enabled", 0)))
        self.AddictolEnabled = bool(int(self.Settings.value("AutoDocWidget/Addictol/Enabled", 0)))
        
        self.Widgets.useWidgetButton.setText(self.ButtonStateText(self.WidgetEnabled) + " Auto Doc")
        self.Widgets.useWidgetView.setScene(self.ButtonStateScene(self.WidgetEnabled))
        self.Widgets.useWidgetView.show()
        self.Widgets.useStimpakButton.setText(self.ButtonStateText(self.StimpakEnabled) + " Stimpak")
        self.Widgets.useStimpakView.setScene(self.ButtonStateScene(self.StimpakEnabled))
        self.Widgets.useStimpakView.show()
        self.Widgets.useMedXButton.setText(self.ButtonStateText(self.MedXEnabled) + " Med-X")
        self.Widgets.useMedXView.setScene(self.ButtonStateScene(self.MedXEnabled))
        self.Widgets.useMedXView.show()
        self.Widgets.useRadAwayButton.setText(self.ButtonStateText(self.RadAwayEnabled) + " RadAway")
        self.Widgets.useRadAwayView.setScene(self.ButtonStateScene(self.RadAwayEnabled))
        self.Widgets.useRadAwayView.show()
        self.Widgets.useRadXButton.setText(self.ButtonStateText(self.RadXEnabled) + " Rad-X")
        self.Widgets.useRadXView.setScene(self.ButtonStateScene(self.RadXEnabled))
        self.Widgets.useRadXView.show()
        self.Widgets.useAddictolButton.setText(self.ButtonStateText(self.AddictolEnabled) + " Addictol")
        self.Widgets.useAddictolView.setScene(self.ButtonStateScene(self.AddictolEnabled))
        self.Widgets.useAddictolView.show()
        
        self.Widgets.timerDelay.setValue(int(self.Settings.value("AutoDocWidget/General/TimerDelay", 2000)))
        
        self.Widgets.stimpakPercent.setValue(int(self.Settings.value("AutoDocWidget/Stimpak/Percent", 80)))
        self.Widgets.stimpakLimit.setValue(int(self.Settings.value("AutoDocWidget/Stimpak/Limit", 10)))
        
        self.Widgets.medxUse.setCurrentIndex(int(self.Settings.value("AutoDocWidget/MedX/Use", 0)))
        self.Widgets.medxLimit.setValue(int(self.Settings.value("AutoDocWidget/MedX/Limit", 5)))
        
        self.Widgets.radawayUse.setCurrentIndex(int(self.Settings.value("AutoDocWidget/RadAway/Use", 0)))
        self.Widgets.radawayLimit.setValue(int(self.Settings.value("AutoDocWidget/RadAway/Limit", 10)))
        
        self.Widgets.radxUse.setCurrentIndex(int(self.Settings.value("AutoDocWidget/RadX/Use", 0)))
        self.Widgets.radxLimit.setValue(int(self.Settings.value("AutoDocWidget/RadX/Limit", 5)))
        
        self.Widgets.addictolLimit.setValue(int(self.Settings.value("AutoDocWidget/Addictol/Limit", 5)))
    
    def ButtonStateScene(self, state):
        if state:
            return self.EnabledScene
        else:
            return self.DisabledScene
    
    def ButtonStateText(self, state):
        if state:
            return "Disable"
        else:
            return "Enable"