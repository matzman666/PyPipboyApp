# -*- coding: utf-8 -*-


from widgets import widgets

from .effectswidget import EffectWidget

class ModuleInfo(widgets.ModuleInfoBase):
    
    LABEL = 'effects'
    NAME = 'Effects'

    @staticmethod
    def createWidgets(handle, parent):
        return EffectWidget(handle, parent)
