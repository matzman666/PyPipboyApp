from widgets import widgets
from .gamestatswidget import GameStatsWidget

class ModuleInfo(widgets.ModuleInfoBase):
    
    LABEL = "gamestats"
    NAME = "Game Statistics"

    @staticmethod
    def createWidgets(handle, parent):
        return GameStatsWidget(handle, parent)