'''
For init'ing the MessageInfo and Field objects that make up the
CANacondaMessage object. MessageInfo is the outer layer of data
abstraction, and Field is contained within.
'''

import xml.etree.ElementTree as ET
import queue
from PyQt5.QtCore import pyqtRemoveInputHook as pyqtrm

# xmlImport 
# Reads the messages file, written in xml format. Parses the xml, creates
# and initializes the messageInfo objects that are used to parse the incoming 
# serial messages.
# This function is shared by the command-line and GUI modes.
def xmlImport(dataBack, fileName):
    # If there is a problem opening and/or reading from the file, error out.
    try:
        xmlFile = open(fileName, 'r')
        rawXML = xmlFile.read()
    except:
        return False

    # Now try and process the XML file.
    try:
        root = ET.fromstring(rawXML)
        for message in root.findall('messageInfo'):
            if 'pgn' in message.keys() and 'id' in message.keys():
                if dataBack.args.nogui:
                    print("Please specify only one of either: id, PGN.\n",
                          "Update meta data file and try again.")
                    return False
            pyqtrm()
            import pdb
            pdb.set_trace()
            newMessageInfo = MessageInfo(message, dataBack)
            messageName = newMessageInfo.name
            dataBack.messages[messageName] = newMessageInfo
    except:
        if dataBack.args.nogui:
            print("ERROR: Invalid XML file provided!")
        return False

    # If we parsed successfully, we can return True
    return True


# This instances of this class are filters created from
# the metadata file. This class gets instantiated during the
# call to xmlimport().
##
# xmlimport is responsible for creating entries in the
# dataBack.messages dictionary.
##
class MessageInfo():
    def __init__(self, messageInfo, dataBack):
        # Initialize some base values
        self.parent = ''
        self.fields = {}
        self.freqQueue = queue.Queue()
        self.freq = 0

        # Most of the rest of the data is pulled directly from the XML data.
        self.name = messageInfo.get('name')
        self.id = messageInfo.get('id')
        self.pgn = messageInfo.get('pgn')
        self.desc = messageInfo.get('desc')

        # for filtering messages, map id to name
        if self.id is not None:
            dataBack.IDencodeMap[self.name] = self.id.upper()
            dataBack.id_to_name[self.id.upper()] = self.name

        # map pgn to name -- this could be wrong!
        dataBack.pgn_to_name[self.pgn] = self.name
        newFields = messageInfo.findall('field')

        # get the fields
        for xmlField in newFields:
            name = xmlField.get('name')
            self.fields[name] = Field(xmlField)

    # A method used to determine if any of the fields must be
    # displayed by value.
    def isByValue(self):
        for field in self.fields:
            if field.byValue:
                return True
        return False

    def __iter__(self):
        return iter(self.fields)

    def __str__(self):
        return self.name + str(self.fields)


# This class gets instantiated and added to the fields dictionary
# of the Filter class.
class Field():
    # field an ElementTree object
    def __init__(self, field):
        # Initialize some fields to default values
        self.header = '' # FIXME: Check that this needs to exist
        self.byValue = []

        # set the 'field' information based on what's in the xml file.
        # 'field' must be an xml-etree object.
        self.name = field.get('name')
        self.length = int(field.get('length'))
        self.offset = int(field.get('offset'))
        self.signed = field.get('signed')
        units_ = field.get('units')
        if units_ == 'm/s':
            self.units = 'MPS'
        else:
            self.units = units_.upper()
        scalar = field.get('scaling')
        if scalar is None:
            scalar = 1
        self.scaling = float(scalar)
        endian = field.get('endian')
        if endian is None:
            endian = 'little'
        self.endian = endian
        self.unitsConversion = None

    def __str__(self):
        return dir(self)

    def __iter__(self):
        return iter([self.name, self.header, self.length, self.offset,
                 self.signed, self.units, self.scaling, self.endian,
                 self.unitsConversion, self.byValue])

