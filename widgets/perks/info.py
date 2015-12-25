
from widgets import widgets

from .perkswidget import PerksWidget

class ModuleInfo(widgets.ModuleInfoBase):
    
    LABEL = 'perks'
    NAME = 'Perks'

    @staticmethod
    def createWidgets(handle, parent):
        return PerksWidget(handle, parent)
