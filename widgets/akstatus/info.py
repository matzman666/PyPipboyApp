
from widgets import widgets

from .akstatuswidget import AKStatusWidget

class ModuleInfo(widgets.ModuleInfoBase):
    
    LABEL = 'akstatus'
    NAME = 'Status'

    @staticmethod
    def createWidgets(handle, parent):
        return AKStatusWidget(handle, parent)
