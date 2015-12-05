# -*- coding: utf-8 -*-


from widgets.shared.graphics import ImageFactory
from .playerinfowidget import PlayerInfoWidget
from .playerconditionwidget import PlayerConditionWidget
    
class Controller:
    
    def __init__(self, handle):
        self.mhandle = handle
        self.imageFactory = ImageFactory(handle.basepath)
        
    def createPlayerInfoWidget(self, parent):
        self.playerInfoWidget = PlayerInfoWidget(self.mhandle, self, parent)
        return self.playerInfoWidget
    
    def createPlayerConditionWidget(self, parent):
        self.playerConditionWidget = PlayerConditionWidget(self.mhandle, self, parent)
        return self.playerConditionWidget
        