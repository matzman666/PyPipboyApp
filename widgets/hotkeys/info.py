
from widgets import widgets

from .hotkeys import HotkeyWidget

class ModuleInfo(widgets.ModuleInfoBase):
    
    LABEL = 'hotkeyswidget'
    NAME = 'Hotkeys'

    @staticmethod
    def createWidgets(handle, parent):
        return HotkeyWidget(handle, parent)
