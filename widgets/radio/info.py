# -*- coding: utf-8 -*-


from widgets import widgets

from .radiowidget import RadioWidget

class ModuleInfo(widgets.ModuleInfoBase):
    
    LABEL = 'radio'
    NAME = 'Radio'

    @staticmethod
    def createWidgets(handle, parent):
        return RadioWidget(handle, parent)
