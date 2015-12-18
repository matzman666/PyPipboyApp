# -*- coding: utf-8 -*-


def getHeaderSectionSizes(headerView):
    sectionSizes = []
    for i in range(0, headerView.count()):
        sectionSizes.append(headerView.sectionSize(i))
    return sectionSizes


def setHeaderSectionSizes(headerView, sectionSizes):
    for i in range(0, len(sectionSizes)):
        headerView.resizeSection(i, int(sectionSizes[i]))


def getHeaderSectionVisualIndices(headerView):
    visualIndices = []
    for i in range(0, headerView.count()):
        visualIndices.append(headerView.visualIndex(i))
    return visualIndices
    
    
def setHeaderSectionVisualIndices(headerView, visualIndices):
    for i in range(0, len(visualIndices)):
        headerView.moveSection(headerView.visualIndex(i), int(visualIndices[i]))
        
        
def getSplitterState(splitter):
    return splitter.saveState()


def setSplitterState(splitter, state):
    if state:
        splitter.restoreState(state)

