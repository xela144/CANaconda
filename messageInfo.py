'''
For init'ing the MessageInfo and Field objects that make up the
CANacondaMessage object. MessageInfo is the outer layer of data
abstraction, and Field is contained within.
'''

import xml.etree.ElementTree as ET
import queue
import sys
from math import ceil

CAN_FORMAT_STANDARD, CAN_FORMAT_EXTENDED = range(2)

# xmlImport 
# Reads the messages file, written in xml format. Parses the xml, creates
# and initializes the messageInfo objects that are used to parse the incoming 
# serial messages.
# This function is shared by the command-line and GUI modes.
def xmlImport(dataBack, fileName):
    messageCount = 0

    # Now try and process the XML file.
    try:
        root = ET.parse(fileName)
        for message in root.findall('messageInfo'):
            newMessageInfo = MessageInfo(message, dataBack)
            if newMessageInfo.pgn and newMessageInfo.id:
                raise Exception("Both PGN and ID specified for message '{}', only one may be specified.".format(newMessageInfo.name))
            if not newMessageInfo.fields:
                raise Exception("No fields found for message '{}'".format(newMessageInfo.name))
            messageName = newMessageInfo.name
            dataBack.messages[messageName] = newMessageInfo
            messageCount += 1
    except ET.ParseError as e:
        raise Exception("Parsing failed for XML file '{}'. Check that file exists and is proper XML.".format(fileName))
    except Exception as e:
        raise e

    if not messageCount:
        raise Exception("No messages found in XML file '{}'".format(fileName))

    return messageCount


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
        self.freqQueue = queue.Queue()
        self.freq = 0
        # Most of the rest of the data is pulled directly from the XML data.
        self.name = messageInfo.get('name')
        try:
            self.id = int(messageInfo.get('id'), 16)  # Assumes a hex value from metadata
        except TypeError:
            self.id = None

        # Set the PGN
        self.pgn = messageInfo.get('pgn')

        # Now if a PGN is set, this must be in extended format, so just set that.
        # But otherwise we need to check for either 'extended' or 'standard'
        if self.pgn:
            self.format = CAN_FORMAT_EXTENDED
        else:
            if messageInfo.get('format') == 'extended':
                self.format = CAN_FORMAT_EXTENDED
            else:
                self.format = CAN_FORMAT_STANDARD
        try:
            self.desc = messageInfo.find('desc').text
        except AttributeError:
            self.desc = ''

        # for filtering messages, map id to name
        if self.id is not None:
            dataBack.IDencodeMap[self.name] = self.id
            dataBack.id_to_name[self.id] = self.name

        # map pgn to name -- this could be wrong!
        dataBack.pgn_to_name[self.pgn] = self.name

        # Get the payload size
        try:
            self.size = int(messageInfo.get('size'))
        except:
            self.size = 0

        # get the fields
        self.fields = {}
        newFields = messageInfo.findall('field')
        for xmlField in newFields:
            name = xmlField.get('name')
            self.fields[name] = Field(self.name, xmlField)

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
    # 'parent' is a string with the name of the message this field is a member of
    # 'field' is an ElementTree object
    def __init__(self, parent, field):
        # Initialize some fields to default values
        self.byValue = []

        # set the 'field' information based on what's in the xml file.
        # 'field' must be an xml-etree object.
        self.name = field.get('name')

        # If the 'type' for a field is not specified, assume int (as that will be the most common).
        # This SHOULD be explicitly set by the user, so warn them via stderr.
        self.type = field.get('type')
        if self.type != 'int' and self.type != 'bitfield':
            print("Specified type for '{}.{}' was not specified, assuming int.".format(parent, self.name), file=sys.stderr)
            self.type = 'int'

        self.length = int(field.get('length'))
        self.offset = int(field.get('offset'))
        self.signed = field.get('signed')
        units_ = field.get('units')
        try:
            if units_ == 'm/s':
                self.units = 'MPS'
            else:
                self.units = units_.upper()
        except AttributeError:
            self.units = ''

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
        return "Field {name: {0}, length: {1}}".format(self.name, self.length)

    def __iter__(self):
        return iter([self.name, self.type, self.length, self.offset,
                 self.signed, self.units, self.scaling, self.endian,
                 self.unitsConversion, self.byValue])

