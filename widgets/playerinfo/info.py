
from widgets import widgets

from .controller import Controller

class ModuleInfo(widgets.ModuleInfoBase):
    
    LABEL = 'playerinfo'
    NAME = 'Player Info'

    @staticmethod
    def createWidgets(handle, parent):
        controller = Controller(handle)
        infoWidget = controller.createPlayerInfoWidget(parent)
        conditionWidget = controller.createPlayerConditionWidget(parent)
        return [infoWidget, conditionWidget]
