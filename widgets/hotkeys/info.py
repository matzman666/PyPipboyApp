
from widgets import widgets
import platform

class ModuleInfo(widgets.ModuleInfoBase):
    
    LABEL = 'hotkeyswidget'
    NAME = 'Hotkeys'
    
    @staticmethod
    def isEnabled():
        return platform.system() == 'Windows'

    @staticmethod
    def createWidgets(handle, parent):
        if platform.system() == 'Windows':
            from .hotkeys import HotkeyWidget
            return HotkeyWidget(handle, parent)
        else:
            return None
