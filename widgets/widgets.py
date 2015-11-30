
from PyQt5 import QtWidgets

class ModuleInfoBase(object):
    pass

class ModuleHandle(object):
    def __init__(self, basepath):
        self.basepath = basepath

class WidgetBase(QtWidgets.QDockWidget):
    def __init__(self, title, parent):
        super().__init__(title, parent)
        
    def init(self, framework, datamanager):
        pass

