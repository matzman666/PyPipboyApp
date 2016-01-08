from PyQt5 import QtWidgets, QtCore, QtGui, uic
from widgets.shared import settings


class AmmoTabelModel(QtCore.QAbstractTableModel):
     def __init__(self, settings, qparent = None):
        super().__init__(qparent)
        self.settings = settings