
from PyQt5 import QtWidgets

class ModuleInfoBase(object):
    LABEL = None
    NAME = None
    
    @staticmethod
    def isEnabled():
        return True
    
    @staticmethod
    def createWidgets(handle, parent):
        return None

class ModuleHandle(object):
    def __init__(self, application, basepath):
        self.application = application
        self.basepath = basepath

class WidgetBase(QtWidgets.QDockWidget):
    def __init__(self, title, parent):
        super().__init__(title, parent)
        
    def iwcSetup(self, framework):
        pass
        
    def init(self, framework, datamanager):
        pass
    
    def getMenuCategory(self):
        return None

