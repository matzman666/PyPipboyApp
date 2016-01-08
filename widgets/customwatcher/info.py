# -*- coding: utf-8 -*-


from widgets import widgets

from .watcherwidget import CustomWatcherWidget

class ModuleInfo(widgets.ModuleInfoBase):
    
    LABEL = 'customwatcher'
    NAME = 'Custom Inventory Browser'

    @staticmethod
    def createWidgets(handle, parent):
        return CustomWatcherWidget(handle, parent)
