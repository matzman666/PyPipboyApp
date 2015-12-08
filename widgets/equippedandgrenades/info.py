
from widgets import widgets

from .equippedandgrenadeswidget import EquippedAndGrenadesWidget

class ModuleInfo(widgets.ModuleInfoBase):
    
    LABEL = 'equippedandgrenades'
    NAME = 'Equipped and Grenades'

    @staticmethod
    def createWidgets(handle, parent):
        return EquippedAndGrenadesWidget(handle, parent)
