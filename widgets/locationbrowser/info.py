# -*- coding: utf-8 -*-


from widgets import widgets

from .locationbrowser import LocationBrowserWidget

class ModuleInfo(widgets.ModuleInfoBase):
    
    LABEL = 'locationbrowser'
    NAME = 'Location Browser'

    @staticmethod
    def createWidgets(handle, parent):
        return LocationBrowserWidget(handle, parent)
