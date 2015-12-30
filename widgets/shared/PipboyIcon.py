from os import path
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from .graphics import ImageFactory

class PipboyIcon:
    ImageLoader = None
    ImageData = None
    ImageScene = None
    FileName = None
    Widget = None
    Text = None
    Color = None
    BGColor = None
    Size = None
    Enabled = None
    
    def __init__(self, fileName, widget = None, size = 30, toolTip = ""):
        self.ImageLoader = ImageFactory(path.join("widgets", "shared", "res"))
        self.FileName = fileName
        self.Widget = widget
        self.Text = toolTip
        self.Color = QColor.fromRgb(255, 255, 255)
        self.BGColor = QColor.fromRgb(0, 0, 0)
        self.Size = size
        self.Enabled = True
    
    def Update(self):
        if self.Enabled:
            self.ImageData = self.ImageLoader.getPixmap(self.FileName, self.Size, self.Size, self.Color)
        else:
            self.ImageData = self.ImageLoader.getPixmap(self.FileName, self.Size, self.Size, self.BGColor)
        
        if self.Widget:
            self.ImageScene = QGraphicsScene()
            self.ImageScene.setSceneRect(0, 0, self.Size, self.Size)
            self.ImageScene.setBackgroundBrush(QBrush(self.BGColor))
            self.ImageScene.addPixmap(self.ImageData)
            
            if self.Text:
                self.Widget.setToolTip(self.Text)
            
            self.Widget.setScene(self.ImageScene)
            self.Widget.show()