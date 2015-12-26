# -*- coding: utf-8 -*-


from PyQt5 import QtWidgets, uic

class RelaySettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi('ui/relaysettingsdialog.ui', self)
