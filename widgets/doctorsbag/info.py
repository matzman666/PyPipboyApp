
from widgets import widgets

from .doctorsbagwidget import DoctorsBagWidget

class ModuleInfo(widgets.ModuleInfoBase):
    
    LABEL = 'doctorsbag'
    NAME = 'Doctor\'s Bag'

    @staticmethod
    def createWidgets(handle, parent):
        return DoctorsBagWidget(handle, parent)
