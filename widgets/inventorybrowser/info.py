# -*- coding: utf-8 -*-


from widgets import widgets

from .inventorybrowser import InventoryBrowserWidget

class ModuleInfo(widgets.ModuleInfoBase):
    
    LABEL = 'inventorybrowser'
    NAME = 'Inventory Browser'

    @staticmethod
    def createWidgets(handle, parent):
        return InventoryBrowserWidget(handle, parent)
