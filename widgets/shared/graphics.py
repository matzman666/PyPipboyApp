# -*- coding: utf-8 -*-


import os
import logging
from PyQt5 import QtWidgets, QtCore, QtGui, uic, QtSvg



class ImageFactory:
    
    def __init__(self, basepath):
        self.basepath = basepath
        self._logger = logging.getLogger('pypipboyapp.shared.imagefactory')
        self._imageMap = dict()
        self._svgRendererMap = dict()
    
    # Colorizes the given image
    @staticmethod
    def colorizeImage(image, color, painter = None):
        if not painter:
            endPainter = True
            painter = painter = QtGui.QPainter(image)
        else:
            endPainter = False
        maskImage = QtGui.QImage(image)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_Multiply)
        painter.fillRect( image.rect(), color)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_DestinationIn)
        painter.drawImage(0, 0, maskImage)
        if endPainter:
            painter.end()
            
    @staticmethod
    def createImageFromSvg(svgRenderer, width = 0, height = 0, color = None, scale = 1.0, size=0):
        if width <= 0 or height <= 0:
            vb = svgRenderer.viewBox()
            owidth = vb.width()
            oheight = vb.height()
            if width <= 0 and height <= 0:
                if size > 0:
                    if owidth == oheight:
                        width = size
                        height = size
                    elif owidth > oheight:
                        height = oheight/owidth * size
                        width = size
                    else:
                        height = size
                        width = owidth/oheight * size
                else:
                    width = int(owidth * scale)
                    height = int(oheight * scale)
            elif height <= 0:
                height = int(width * float(oheight)/float(owidth))
            elif width <= 0:
                width = int(height * float(owidth)/float(oheight))
        image = QtGui.QImage(width, height, QtGui.QImage.Format_ARGB32_Premultiplied)
        image.fill(QtGui.QColor.fromRgb(0,0,0,0))
        painter = QtGui.QPainter(image)
        svgRenderer.render(painter)
        if color:
            ImageFactory.colorizeImage(image, color, painter)
        painter.end()
        return image
        
    def getImage(self, file, width = 0, height = 0, color = None, scale = 1.0, size=0):
        if os.path.splitext(file)[1] == '.svg':
            try:
                renderer = self._svgRendererMap[file]
            except:
                renderer = QtSvg.QSvgRenderer(os.path.join(self.basepath, file))
                if renderer.isValid():
                    self._svgRendererMap[file] = renderer
                else:
                    self._logger.error('Could not load image file "' + file + '".')
                    return QtGui.QImage()
            return ImageFactory.createImageFromSvg(renderer, width, height, color, scale, size)
        else:
            try:
                image = self._imageMap[file]
            except:
                image = QtGui.QImage(os.path.join(self.basepath, file))
                if image.format() == QtGui.QImage.Format_Invalid:
                    self._logger.error('Could not load image file "' + file + '".')
                    return QtGui.QImage()
                self._imageMap[file] = image
            noScale = False
            if width <= 0 or height <= 0:
                owidth = image.width()
                oheight = image.height()
                if width <= 0 and height <= 0:
                    if size > 0:
                        if owidth == oheight:
                            witdth = size
                            height = size
                        elif owidth > oheight:
                            height = oheight/owidth * size
                            width = size
                        else:
                            height = size
                            width = owidth/oheight * size
                    elif scale == 1.0:
                        noScale = True
                    else:
                        width = int(owidth * scale)
                        height = int(oheight * scale)
                elif height <= 0:
                    height = int(width * float(oheight)/float(owidth))
                elif width <= 0:
                    width = int(height * float(owidth)/float(oheight))
            if noScale:
                outimage = QtGui.QImage(image)
            else:
                outimage = image.scaled(width, height)
            if color and outimage:
                self.colorizeImage(outimage, color)
            return outimage
        
    def getPixmap(self, file, width = 0, height = 0, color = None, scale = 1.0, size=0):
        return QtGui.QPixmap.fromImage(self.getImage(file, width, height, color, scale, size))
