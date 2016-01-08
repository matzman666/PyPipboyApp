from widgets import widgets
from .ammocountwidget import WorkshopsWidget

class ModuleInfo(widgets.ModuleInfoBase):
    LABEL = "ammocount"
    NAME = "Ammo Tracker"
    
    @staticmethod
    def createWidgets(handle, parent):
        return WorkshopsWidget(handle, parent)