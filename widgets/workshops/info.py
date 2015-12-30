from widgets import widgets
from .workshopswidget import WorkshopsWidget

class ModuleInfo(widgets.ModuleInfoBase):
    LABEL = "workshops"
    NAME = "Workshops"
    
    @staticmethod
    def createWidgets(handle, parent):
        return WorkshopsWidget(handle, parent)