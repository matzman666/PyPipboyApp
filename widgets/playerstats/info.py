from widgets import widgets

from .statswidget import StatsWidget

class ModuleInfo(widgets.ModuleInfoBase):
    
    LABEL = 'playerstats'
    NAME = 'Player Statsistics'

    @staticmethod
    def createWidgets(handle, parent):
        return StatsWidget(handle, parent)
