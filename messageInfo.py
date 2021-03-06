'''
 * Copyright Bar Smith, Bryant Mairs, Alex Bardales 2015
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses.
'''

'''
For init'ing the MessageInfo and Field objects that make up the
CANacondaMessage object. MessageInfo is the outer layer of data
abstraction, and Field is contained within.
'''

import xml.etree.ElementTree as ET
import queue
import sys
from Nmea2000 import Iso11783Encode
from math import ceil

CAN_FORMAT_STANDARD, CAN_FORMAT_EXTENDED = range(2)

ACTIVE, EQUAL, LT, GT = range(4)

# A psuedo zero, such that bool(ZERO) does not evaulate to false.
ZERO = '0'

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

        # A file can be included in the metadata. First, we have to scale down the function stack
        for includeFile in root.findall('include'):
            filename_ = 'metadata/' + includeFile.get('file')
            xmlImport(dataBack, filename_)  

        # Now set the function stack size to what it was when we started.

        for message in root.findall('messageInfo'):
            #from PyQt5.QtCore import pyqtRemoveInputHook; pyqtRemoveInputHook(); import pdb; pdb.set_trace()
            newMessageInfo = MessageInfo()
            newMessageInfo.createNew(message, dataBack, fileName)
            if newMessageInfo.pgn and newMessageInfo.id:
                raise Exception("Both PGN and ID specified for message '{}', only one may be specified.".format(newMessageInfo.name))
            if not newMessageInfo.fields:
                raise Exception("No fields found for message '{}'".format(newMessageInfo.name))
            messageName = newMessageInfo.name
            dataBack.messages[messageName] = newMessageInfo
            messageCount += 1
    except ET.ParseError as e:
        raise Exception("Parsing failed for XML file '{}'. Check that file exists and is proper XML.".format(fileName))
    
    if messageCount:
        dataBack.messageInfoFlag = True


# This instances of this class are filters created from
# the metadata file. This class gets instantiated during the
# call to xmlimport().
##
# xmlimport is responsible for creating entries in the
# dataBack.messages dictionary.
class MessageInfo():
    def __init__(self):
        self.name = None
        self.desc = None
        self.format = None
        self.id = None
        self.pgn = None
        self.size = 0
        self.protocol = None
        self.endian = None
        self.anonymous = False
        self.fields = {}

    def createNew(self, messageInfo, dataBack, fileName):
        self.freqQueue = queue.Queue()
        self.freq = 0
        # Most of the rest of the data is pulled directly from the XML data.
        self.name = messageInfo.get('name')
        self.checkFormat(self.name, fileName)
        try:
            self.id = int(messageInfo.get('id'), 16)  # Assumes a hex value from metadata
        except TypeError:
            # If there is no id, then there is a PGN
            # Decode the id using the PGN, 0 as source, 0 as destination, 111 as priorty
            # Also assume a 29-bit id.
            self.id = None
            pgn = int(messageInfo.get('pgn'))
            src = 0
            dest = 0
            pri = 7
            # So as not to disrupt the current flow of code, we are going to use
            # a fakeID, not a real one. The real one is now 'None'. fakeID will
            # be used to transmit only.
            self.fakeID = Iso11783Encode(pgn, src, dest, pri)

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

        dataBack.pgn_to_name[self.pgn] = self.name

        # Get the payload size, in bytes. This is useful for transmission, since
        # the code will then know how to fill in the message body array.
        try:
            self.size = int(messageInfo.get('size'))
        except:
            self.size = 0

        # Get either the endianness or the protocol of the message.
        protocol = messageInfo.get('protocol')
        endian = messageInfo.get('endian')
        if endian is None and protocol is None:
            raise Exception("Parsing failed in XML file '{}' for message '{}': Please specify either endian-ness or protocol.".format(fileName, self.name))
        if endian is None or protocol == 'nmea2000':
            endian = 'little'
        self.protocol = protocol
        self.endian = endian

        # get the fields
        self.fields = {}
        newFields = messageInfo.findall('field')
        for xmlField in newFields:
            name = xmlField.get('name')
            self.fields[name] = Field()
            self.fields[name].createNew(self, xmlField, fileName)

    def checkFormat(self, string, fileName):
        if string[0] == ' ' or string[-1] == ' ':
            raise Exception("Parsing failed for XML file '{}'. '{}' has leading or trailing space character".format(fileName, string))

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
        if self.protocol is not None:
            return self.name + self.protocol + str(self.fields)
        else:
            return self.name + self.endian + "endian" + str(self.fields)


# This object gets assigned to one of the 'fields' dictionary of a MessageInfo object.
class Field():
    def __init__(self):
        self.name = None
        self.type = None
        self.length = 0
        self.offset = 0   
        self.signed = 'no'
        self.units = None
        self.scaling = 1
        self.unitsConversion = None 
        self.byValue = {ACTIVE:False, EQUAL:None, LT:None, GT:None}

    # 'parent' is a string with the name of the message this field is a member of
    # 'field' is an ElementTree object
    def createNew(self, parent, field, fileName):
        # The 'byValue' dictionary will have three entries:
        self.byValue = {ACTIVE:False, EQUAL:None, LT:None, GT:None}

        # set the 'field' information based on what's in the xml file.
        # 'field' must be an xml-etree object.
        self.name = field.get('name')
        self.checkFormat(self.name, fileName)

        # If the 'type' for a field is not specified, assume int (as that will be the most common).
        # This SHOULD be explicitly set by the user, so warn them via stderr.
        self.type = field.get('type')
        if self.type not in ('int', 'bitfield', 'boolean', 'enum'): # Future work: map enum's to human-readable strings
            print("Specified type for '{}.{}' was not specified, assuming int.".format(parent.name, self.name), file=sys.stderr)
            self.type = 'int'

        # The length of the field data, as specified by user. Allow for user to omit length if type is boolean.
        try:
            self.length = int(field.get('length'))
        except TypeError:  # Could not convert NoneType to string
            if self.type == 'boolean':
                self.length = 1
            else:
                raise Exception("Parsing failed for XML file '{}'. Check that field '{}.{}' has correct length.".format(fileName, parent.name, self.name))

        # The offset and signed-ness of the field
        self.offset = int(field.get('offset'))
        self.signed = field.get('signed')

        # The field units
        units_ = field.get('units')
        try:
            if units_ == 'm/s':
                self.units = 'MPS'
            else:
                self.units = units_.upper()
        except AttributeError:
            # No units were specified
            self.units = ''

        # Get the scaling factor, if none is specified set to 1.
        scalar = field.get('scaling')
        if scalar is None:
            scalar = "1"
        if 'e' in scalar:
            raise Exception("Parsing failed for XML file '{}'. Field '{}.{}' has incorrect scaling. Exponential notation is not supported, please use standard decimal notation instead.".format(fileName, parent.name, self.name))
        try:
            self.scaling = float(scalar)
        except ValueError:
            raise Exception("Parsing failed for XML file '{}'. Field '{}.{}' has a non-numerical scaling.".format(fileName, parent.name, self.name))

        # For decoding messages only. This is never displayed to user
        self.endian = parent.endian

        # Set the bounds for this field once, so we don't need to constantly recalculate them.
        # This is valid as the field range can only be changed in the XML file.
        def round_down(num, divisor):
            """Round 'num' down to nearest multiple of 'divisor'."""
            return num - (num % divisor)

        if self.signed == 'yes':
            bound = 2**(self.length - 1)
            bounds = (round_down(-bound * self.scaling, self.scaling), round_down((bound - 1) * self.scaling, self.scaling))
        else:
            bound = 2**(self.length)
            bounds = (0, round_down((bound - 1) * self.scaling, self.scaling))

        lower_bound = int(bounds[0])
        if bounds[0] != lower_bound:
            lower_bound = bounds[0]
        upper_bound = int(bounds[1])
        if bounds[1] != upper_bound:
            upper_bound = bounds[1]
        self.bounds = (lower_bound, upper_bound)

        # Set the display format for this field. A fixed-width implementation is used for all fields
        self.disp_format = None
        if self.type == 'int':
            self.disp_format = "{:>"
            if self.bounds[0] < 0:
                self.disp_format += " "

            # Pull the width portion from the bounds values
            bounds_lengths = [len(str(x).split('.')[0]) for x in self.bounds]
            self.disp_format += str(max(bounds_lengths))

            # And pull the precision portion from the scaling factor
            # For regular integers, we need to make sure we specify '.0' so there's
            # no fractional value shown.
            self.disp_format += '.'
            try:
                self.disp_format += str(len(scalar.split('.')[1]))
            except:
                self.disp_format += '0'

            self.disp_format += "f}"

    def checkFormat(self, string, fileName):
        if string[0] == ' ' or string[-1] == ' ':
            raise Exception("Parsing failed for XML file '{}'. '{}' has leading or trailing space character".format(fileName, string))


    def __str__(self):
        return "Field name: {0}, length: {1}".format(self.name, self.length)

    def __iter__(self):
        return iter([self.name, self.type, self.length, self.offset,
                 self.signed, self.units, self.scaling,
                 self.unitsConversion, self.byValue])

