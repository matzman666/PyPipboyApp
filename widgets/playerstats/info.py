from widgets import widgets
from .playerstatscontroller import PlayerStatsController

class ModuleInfo(widgets.ModuleInfoBase):
    
    LABEL = 'playerstats'
    NAME = 'Player Statsistics'

    @staticmethod
    def createWidgets(handle, parent):
        Controller = PlayerStatsController(handle)
        
        LimbWidget = Controller.CreateLimbWidget(parent)
        StatsWidget = Controller.CreateStatsWidget(parent)
        SpecialWidget = Controller.CreateSpecialWidget(parent)
        
        return [LimbWidget, StatsWidget, SpecialWidget]
