
from widgets import widgets

from .datetimewidget import DateTimeWidget

class ModuleInfo(widgets.ModuleInfoBase):
    
    LABEL = 'datetime'
    NAME = 'Date/Time'

    @staticmethod
    def createWidgets(handle, parent):
        return DateTimeWidget(handle, parent)
