from widgets import widgets
from .ammocountwidget import AmmoCountWidget

class ModuleInfo(widgets.ModuleInfoBase):
    LABEL = "ammocount"
    NAME = "Ammo Tracker"
    
    @staticmethod
    def createWidgets(handle, parent):
        return AmmoCountWidget(handle, parent)