import os
from PyQt5 import QtWidgets, QtCore, QtGui, uic, QtSvg
from widgets.shared.graphics import ImageFactory
from widgets import widgets
from widgets.shared import settings

class EditNoteDialog(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.basepath = os.path.join("widgets", "map")
        uic.loadUi(os.path.join(self.basepath, 'ui', 'editnotedialog.ui'), self)
