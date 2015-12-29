# -*- coding: utf-8 -*-

from .limbwidget import LimbWidget
from .statswidget import StatsWidget
from .specialwidget import SpecialWidget

class PlayerStatsController:
    def __init__(self, handle):
        self.mhandle = handle
    
    def CreateLimbWidget(self, parent):
        self.PlayerStatsLimbWidget = LimbWidget(self.mhandle, parent)
        return self.PlayerStatsLimbWidget
        
    def CreateStatsWidget(self, parent):
        self.PlayerStatsWidget = StatsWidget(self.mhandle, parent)
        return self.PlayerStatsWidget
        
    def CreateSpecialWidget(self, parent):
        self.PlayerStatsSpecialWidget = SpecialWidget(self.mhandle, parent)
        return self.PlayerStatsSpecialWidget
    
    