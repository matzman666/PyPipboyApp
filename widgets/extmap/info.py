
from widgets import widgets

from .mapwidget import MapWidget

class ModuleInfo(widgets.ModuleInfoBase):
    
    LABEL = 'extmap'
    NAME = 'Map'

    @staticmethod
    def createWidgets(handle, parent):
        return MapWidget(handle, parent)
