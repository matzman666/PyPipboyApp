import re
import json
from collections import OrderedDict

#
# post processes the simple output of the FO4Edit script into 
# into something more useful 
#

inputfile = 'collectables.json'
outputfile = 'collectables-processed.json'

collectables = OrderedDict()

def prettifyBobbleName(name):
    ret = re.findall(r"'(.*?)' ", name, re.DOTALL)
    if len(ret) > 0:
        return ret[0]
    else:
        return name

def prettifyPerkMagName(name):
    ret = re.findall(r"'(.*?)' ", name, re.DOTALL)
    if len(ret) > 0:
        rNum = re.findall(r"^.*?([0-9]*) '", name, re.DOTALL)
        if len(rNum) > 0:
            return ret[0] + ' ' + rNum[0]
        else:
            return ret[0]
    else:
        return name
    return newline
        
def prettifyName(type, name):
    if type == 'bobblehead':
        return prettifyBobbleName(name)
    elif type == 'perkmagazine':
        return prettifyPerkMagName(name)
    else:
        return name
        
def extractFormIDForPerkMag(name):
        ret = re.findall(r" \[BOOK:(.*?)\]", name, re.DOTALL)
        if len(ret) > 0:
            return '0x' + ret[0]
        else:
            return name
def extractFormIDForBobble(name):
        ret = re.findall(r" \[MISC:(.*?)\]", name, re.DOTALL)
        if len(ret) > 0:
            return '0x' + ret[0]
        else:
            return name
            
def extractFormID(type, name):
    if type == 'bobblehead':
        return extractFormIDForBobble(name)
    elif type == 'perkmagazine':
        return extractFormIDForPerkMag(name)
    else:
        return name
        


        
with open(inputfile) as infile:
    rawdata = json.load(infile)

    for i in rawdata.get('items'):
            itype = i.get('type', None)
            if itype not in collectables.keys():
                collectables[itype] = OrderedDict()
                if itype == 'bobblehead':
                    collectables[itype]['icon'] = 'award.svg'
                    collectables[itype]['friendlyname'] = 'Bobbleheads'
                    collectables[itype]['color'] = ["255","70","70" ]
                    
                elif itype == 'perkmagazine':
                    collectables[itype]['icon'] = 'book.svg'
                    collectables[itype]['friendlyname'] = 'Perk Magazines'
                    collectables[itype]['color'] = ["70","200","255" ]
                collectables[itype]['items'] = []
                    
            item = OrderedDict()

            item['name'] = prettifyName(itype, i.get('name', ''))
            item['formid'] = extractFormID(itype, i.get('name', ''))
            item['instanceid'] = '0x' + i.get('instanceformid', 0)

            cell = i.get('cell', '')
            world = i.get('world', '')

            if cell != '' and world != '':
                ret = re.findall(r"'(.*?)' ", cell, re.DOTALL)
                if len(ret) > 0:
                    item['cell'] = ret[0]
                    item['description'] = 'Inside ' + item['cell']
                else:
                    item['cell'] = cell
                    item['description'] = 'No Intel (unamed cell)'
                    
                ret = re.findall(r"'(.*?)' ", world, re.DOTALL)
                if len(ret) > 0:
                    item['world'] = ret[0]
                else:
                    item['world'] = world
                    
                    
            elif cell != '' and world == '':
                ret = re.findall(r"(.*?) \[CELL", cell, re.DOTALL)
                if len(ret) > 0:
                    tokenisedcellname = re.sub( r"([A-Z])", r" \1", ret[0]).split()
                    if tokenisedcellname[-1].find('Ext') > -1:
                        del tokenisedcellname[-1]
                        
                    item['cell'] = " ".join(tokenisedcellname)
                    item['description'] = 'Near to ' + item['cell']
                else:
                    item['cell'] = cell
                    item['description'] = 'No Intel (unnamed cell, no world)'

                ret = re.findall(r"'(.*?)' ", cell, re.DOTALL)
                if len(ret) > 0:
                    item['world'] = ret[0]
                else:
                    item['world'] = world

                    
            elif world != '' and cell == '' :
                ret = re.findall(r"'(.*?)' ", world, re.DOTALL)
                if len(ret) > 0:
                    item['world'] = ret[0]
                else:
                    item['world'] = world
                    
                item['description'] = 'No intel (no cell)'

            else:
                item['cell'] = cell
                item['world'] = world
                
            cellx = i.get('cellx', '')
            celly = i.get('celly', '')
            worldx = i.get('worldx', '')
            worldy = i.get('worldy', '')
            
            if cellx != '' and celly != '':
                item['cellx'] = cellx
                item['celly'] = celly
            
            if worldx != '' and worldy != '':
                item['worldx'] = worldx
                item['worldy'] = worldy
            else: 
                item['worldx'] = cellx
                item['worldy'] = celly
                
            if(item['world'] == 'Commonwealth'):
                item['commonwealthx'] = item['worldx']
                item['commonwealthy'] = item['worldy']
            else :
                # TODO: how to handle items that are in an unconnected 
                # worldspace(e.g. GoodNeighbour), and items that are in 
                # unconnected cells (Vault 81, Parsons Admin, etc )
                if(item['formid'] == '0x00178B62'): #BobbleHead_Speech, vault 114
                    print (item['formid'] +':' + item['name'] + ': set coords manually' )
                    item['commonwealthx'] = "8119.56787109375"
                    item['commonwealthy'] = "-17975.1953125"
                    item['description'] = 'Inside Vault 114'
                elif(item['formid'] == '0x001696A1'): #PerkMagAstoundinglyAwesomeTales07, vault 114
                    print (item['formid'] +':' + item['name'] + ': set coords manually' )
                    item['commonwealthx'] = "7919.56787109375"
                    item['commonwealthy'] = "-18175.1953125"
                    item['description'] = 'Inside Vault 114'
                elif(item['formid'] == '0x00178B5B'): #BobbleHead_Medicine, vault 81
                    print (item['formid'] +':' + item['name'] + ': set coords manually' )
                    item['commonwealthx'] = "-37603.19921857"
                    item['commonwealthy'] = "-23620.890625"
                    item['description'] = 'Inside Vault 81'
                elif(item['formid'] == '0x00180A2A'): #PerkMagTattoo04, vault 81
                    print (item['formid'] +':' + item['name'] + ': set coords manually' )
                    item['commonwealthx'] = "-37903.19921857"
                    item['commonwealthy'] = "-23820.890625"
                    item['description'] = 'Inside Vault 81'
                elif(item['formid'] == '0x00184DB2'): #PerkMagRobcoFun02, GoodneighborTheMemoryDen
                    print (item['formid'] +':' + item['name'] + ': set coords manually' )
                    item['commonwealthx'] = "21075.119140625"
                    item['commonwealthy'] = "-12150.7138671985"
                elif(item['formid'] == '0x001C2E24'): #PerkMagLiveAndLove06, GoodneighborTheThirdRail
                    print (item['formid'] +':' + item['name'] + ': set coords manually' )
                    item['commonwealthx'] = "20826.119140625"
                    item['commonwealthy'] = "-11904.7138671985"
                elif(item['formid'] == '0x001C2E28'): #PerkMagLiveAndLove08, GoodneighborHotelRexford
                    print (item['formid'] +':' + item['name'] + ': set coords manually' )
                    item['commonwealthx'] = "20675.119140625"
                    item['commonwealthy'] = "-11650.7138671985"
                else:
                    print (item['formid'] + ': no commonwealth coords!')
                    print ('\tname:' + i.get('name', 'noname?'))
                    print ('\tcell: ' + i.get('cell', 'nocell?'))
                    print ('\tworld: ' + i.get('world', 'noworld?'))

                    
                pass

                
                pass
            
            collectables[itype]['items'].append(item)

with open(outputfile, 'w') as outfile:
    json.dump(collectables, outfile)



