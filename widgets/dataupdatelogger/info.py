
from widgets import widgets

from .dataupdateloggerwidget import DataUpdateLoggerWidget

class ModuleInfo(widgets.ModuleInfoBase):
    
    LABEL = 'dataupdatelogger'
    NAME = 'Data Update Logger'

    @staticmethod
    def createWidgets(handle, parent):
        return DataUpdateLoggerWidget(handle, parent)
