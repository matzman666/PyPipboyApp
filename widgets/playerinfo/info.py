
from widgets import widgets

from .playerinfowidget import PlayerInfoWidget

class ModuleInfo(widgets.ModuleInfoBase):
    
    LABEL = 'playerinfo'
    NAME = 'Player Info'

    @staticmethod
    def createWidgets(handle, parent):
        return PlayerInfoWidget(handle, parent)
