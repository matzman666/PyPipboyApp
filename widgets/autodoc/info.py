from widgets import widgets
from .autodocwidget import AutoDocWidget

class ModuleInfo(widgets.ModuleInfoBase):
    
    LABEL = 'autodoc'
    NAME = 'Auto Doc'

    @staticmethod
    def createWidgets(handle, parent):
        return AutoDocWidget(handle, parent)