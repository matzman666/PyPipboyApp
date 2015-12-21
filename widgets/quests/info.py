
from widgets import widgets

from .questswidget import QuestsWidget

class ModuleInfo(widgets.ModuleInfoBase):
    
    LABEL = 'quests'
    NAME = 'Quests'

    @staticmethod
    def createWidgets(handle, parent):
        return QuestsWidget(handle, parent)
