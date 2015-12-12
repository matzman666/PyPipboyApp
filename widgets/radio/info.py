# -*- coding: utf-8 -*-


from widgets import widgets

from .radiowidget import EffectWidget

class ModuleInfo(widgets.ModuleInfoBase):
    
    LABEL = 'radio'
    NAME = 'Radio'

    @staticmethod
    def createWidgets(handle, parent):
        return EffectWidget(handle, parent)
