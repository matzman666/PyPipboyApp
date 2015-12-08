
from widgets import widgets

from .hotkeys import HotkeyWidget

class ModuleInfo(widgets.ModuleInfoBase):
    
    LABEL = 'hotkeyswidget'
    NAME = 'Hotkeys'

    @staticmethod
    def createWidgets(handle, parent):
        if platform.system() == 'Windows':
            return HotkeyWidget(handle, parent)
        else
            return None
