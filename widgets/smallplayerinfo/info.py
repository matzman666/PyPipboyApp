
from widgets import widgets

from .smallplayerinfowidget import SmallPlayerInfoWidget

class ModuleInfo(widgets.ModuleInfoBase):
    
    LABEL = 'smallplayerinfow'
    NAME = 'Small Player Info'

    @staticmethod
    def createWidgets(handle, parent):
        return SmallPlayerInfoWidget(handle, parent)
