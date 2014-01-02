'''
For init'ing the MessageInfo and Field objects that make up the
CANacondaMessage object. MessageInfo is the outer layer of data
abstraction, and Field is contained within.
'''

from messageInfo import *
import xml.etree.ElementTree as ET
import pdb
from PyQt5.QtCore import pyqtRemoveInputHook as pyqtrm

# xmlImport 
# Reads the messages file, written in xml format. Parses the xml, creates
# and initializes the messageInfo objects that are used to parse the incoming 
# serial messages.
# This function is shared by the command-line and GUI modes.
def xmlImport(dataBack, args, fileName):
    if not dataBack.nogui:
        if dataBack.args.fast:
            fileName = 'xmltest.xml'
        #else:
        #    fileName = args.messages
    if fileName is None and dataBack.nogui:
        return True  # Used in main in command-line mode
    try:
        xmlFile = open(fileName, 'r')
        rawXML = xmlFile.read()
        root = ET.fromstring(rawXML)
        for message in root.findall('messageInfo'):
            if 'pgn' in message.keys() and 'id' in message.keys():
                if dataBack.args.nogui:
                    print("Please specify only one of either: id, PGN.\n",
                          "Update meta data file and try again.")
                    return True
            newMessageInfo = MessageInfo()
            messageInfoInit(newMessageInfo, message, dataBack)
            messageName = newMessageInfo.name
            dataBack.messages[messageName] = newMessageInfo
    except:
        pass


### Moved from backend.py ###
# 'self' is a MessageInfo object
# 'messageInfo' is an xml-etree object
def messageInfoInit(self, messageInfo, dataBack):
    self.name = messageInfo.get('name')
    self.id = messageInfo.get('id')
    self.pgn = messageInfo.get('pgn')
    self.desc = messageInfo.get('desc')
    # for filtering messages, map id to name
    if self.id is not None:
        dataBack.id_to_name[self.id.upper()] = self.name
    # map pgn to name -- this could be wrong!
    dataBack.pgn_to_name[self.pgn] = self.name
    newFields = messageInfo.findall('field')
    # get the fields
    for field in newFields:
        name = field.get('name')
        self.fields[name] = Field(field)
        fieldInit(self.fields[name], field)
        # add to the fields list in dataBack
        # Not used for now.
        # dataBack.fields.append(newField)


# set the 'field' information based on what's in the xml file.
# 'field' must be an xml-etree object.
def fieldInit(self, field):
    self.name = field.get('name')
    self.length = int(field.get('length'))
    self.offset = int(field.get('offset'))
    self.signed = field.get('signed')
    units_ = field.get('units')
    if units_ == 'm/s':
        self.units = 'MPS'
    else:
        self.units = units_.upper()
    self.scaling = float(field.get('scaling'))
    self.endian = field.get('endian')
    self.unitsConversion = None

