
from widgets import widgets


class ModuleInfo(widgets.ModuleInfoBase):
    
    LABEL = 'akstatus'
    NAME = 'Status'

    @staticmethod
    def createWidgets(handle, parent):
        # Import and create widget only on windows
        if handle.application.hotkeymanager:
            from .akstatuswidget import AKStatusWidget
            return AKStatusWidget(handle, parent)
        else:
            return None
