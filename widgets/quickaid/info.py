from widgets import widgets
from .quickaidwidget import QuickAidWidget

class ModuleInfo(widgets.ModuleInfoBase):
    
    LABEL = 'quickaid'
    NAME = 'Quick Aid'

    @staticmethod
    def createWidgets(handle, parent):
        return QuickAidWidget(handle, parent)