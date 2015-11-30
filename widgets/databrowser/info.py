
from widgets import widgets

from .databrowserwidget import DataBrowserWidget

class ModuleInfo(widgets.ModuleInfoBase):
    
    LABEL = 'databrowser'
    NAME = 'Data Browser'

    @staticmethod
    def createWidgets(handle, parent):
        return DataBrowserWidget(handle, parent)
