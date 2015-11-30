# -*- coding: utf-8 -*-


from PyQt5 import QtWidgets, uic

class SelectHostDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi('ui/selecthostdialog.ui', self)
        
    def exec(self, hosts):
        self.hosts = list()
        for h in hosts:
            i = 0
            if not h['IsBusy']:
                text = h['addr'] + ' (' + h['MachineType'] + ')'
                item = QtWidgets.QListWidgetItem(text, self.listWidget)
                self.listWidget.insertItem(i, item)
                if i == 0:
                    self.listWidget.setCurrentRow(0)
                i += 1
                self.hosts.append(h)
        return super().exec()
        
        
    def getSelectedHost(self):
        selection = self.listWidget.selectionModel().selectedRows()
        if len(selection) > 0:
            return self.hosts[selection[0].row()]
        return None
    
