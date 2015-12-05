# -*- coding: utf-8 -*-

from widgets import widgets

from .controller import MapController

class ModuleInfo(widgets.ModuleInfoBase):
    
    LABEL = 'mapwidgets'
    NAME = 'Map'

    @staticmethod
    def createWidgets(handle, parent):
        controller = MapController(handle)
        globalWidget = controller.createGlobalWidget(parent)
        localWidget = controller.createLocalWidget(parent)
        return [globalWidget, localWidget]
