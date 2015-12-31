# -*- coding: utf-8 -*-


import os
import logging
from widgets.shared.graphics import ImageFactory
from .globalmapwidget import GlobalMapWidget
from .localmapwidget import LocalMapWidget


class MapCoordinates:
    # Simple Coordinate Translation
    # x2 = ax * x1 + bx
    # y2 = ay * y1 + by
    # The constants ax, ay, bx, by are calculated as follow:
    #  * We get North West (NWX, NWY), North East (NEX, NEY) and
    #       South West (SWX, SWY) coordinates from the game (/Map/World/Extents)
    #  * We state for each map we want to load NW, NE and SW coordinates 
    #  * We calculate the constants by simple equation solving
    # How to we get the coordinates for the map: by experimenting.
    def __init__(self):
        self._ax = 1
        self._bx = 0
        self._ay = 1
        self._by = 0
        self.isValid = False
    def init(self, pnwx, pnwy, pnex, pney, pswx, pswy, mnwx, mnwy, mnex, mney, mswx, mswy):
        self._ax = float(mnex-mnwx)/float(pnex-pnwx)
        self._bx = mnwx - pnwx*self._ax 
        self._ay = float(mswy-mnwy)/float(pswy-pnwy)
        self._by = mnwy - pnwy*self._ay
        self.isValid = True
    def pip2map_x(self, x):
        return self._ax*x + self._bx
    def pip2map_y(self, y):
        return self._ay*y + self._by
    def map2pip_x(self, x):
        return (x-self._bx)/self._ax
    def map2pip_y(self, y):
        return (y-self._by)/self._ay
    
    
class MapController:
    
    def __init__(self, handle):
        self.mhandle = handle
        self.imageFactory = ImageFactory(handle.basepath)
        self.globalResImageFactory = ImageFactory(os.path.join('ui', 'res'))
        
    def createGlobalWidget(self, parent):
        self.globalWidget = GlobalMapWidget(self.mhandle, self, parent)
        return self.globalWidget
    
    def createLocalWidget(self, parent):
        self.localWidget = LocalMapWidget(self.mhandle, self, parent)
        return self.localWidget
        