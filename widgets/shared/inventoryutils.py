# -*- coding: utf-8 -*-


def getItemCardInfoByText(item, text):
    infos = item.child('itemCardInfoList')
    for i in infos.value():
        if i.child('text').value() == text:
            return i
    return None


def getItemValue(item):
    cached = item.getUserCache('$val')
    if not cached or cached.dirtyFlag:
        vInfo = getItemCardInfoByText(item, '$val')
        if vInfo:
            value = vInfo.child('Value').value()
            item.setUserCache('$val', value, 10)
        else:
            value = None
    else:
        value = cached.value
    return value


def getItemWeight(item):
    cached = item.getUserCache('$wt')
    if not cached or cached.dirtyFlag:
        wInfo = getItemCardInfoByText(item, '$wt')
        if wInfo:
            weight = wInfo.child('Value').value()
            item.setUserCache('$wt', weight, 10)
        else:
            weight = None
    else:
        weight = cached.value
    return weight


def getItems(inventory, filterFunc = None):
    retval = []
    sortedIds = inventory.child('sortedIDS')
    if sortedIds:
        for id in sortedIds.value():
            item = inventory.datamanager.getPipValueById(id.value())
            if not filterFunc or filterFunc(item):
                retval.append(item)
    return retval


def isItemCatWeapons(item):
    if item.child('filterFlag').value() & 2:
        return True
    return False

def isItemCatApparel(item):
    if item.child('filterFlag').value() & 4:
        return True
    return False

def isItemCatBooks(item):
    if item.child('filterFlag').value() & 128:
        return True
    return False
    
def isItemCatAmmo(item):
    if item.child('filterFlag').value() & 4096:
        return True
    return False

def isItemCatKeys(item):
    if item.pipParent.pipParentKey == '47':
        return True
    return False

def isItemCatAid(item):
    if item.child('filterFlag').value() & 8:
        return True
    return False

def isItemCatHolotape(item):
    if item.child('filterFlag').value() & 8192:
        return True
    return False

def isItemCatMisc(item):
    if (item.child('filterFlag').value() == 512 
            and item.pipParent.pipParentKey == '35'):
        return True
    return False

def isItemCatJunk(item):
    if item.child('filterFlag').value() & 1024:
        return True
    return False

def isItemCatMods(item):
    if item.child('filterFlag').value() & 2048:
        return True
    return False
