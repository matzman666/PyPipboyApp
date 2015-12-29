from widgets import widgets

from .playerstatscontroller import PlayerStatsController

class ModuleInfo(widgets.ModuleInfoBase):
    
    LABEL = 'playerstats'
    NAME = 'Player Statsistics'

    @staticmethod
    def createWidgets(handle, parent):
        controller = PlayerStatsController(handle)
        
        LimbWidget = controller.CreateLimbWidget(parent)
        StatsWidget = controller.CreateStatsWidget(parent)
        SpecialWidget = controller.CreateSpecialWidget(parent)
        
        return [LimbWidget, StatsWidget, SpecialWidget]
