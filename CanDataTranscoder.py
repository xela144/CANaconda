'''
This script is responsible for decoding CAN messages as they are received over the CANtoUSB device, and also for encoding as they are being transmitted.

CLI mode: When the threading object is created in CANaconda.py, the target function is CanTranscoderRun().

GUI mode: When the threading object is created in ui_mainwindow.py, the target function is Can

This function waits for raw CAN messages to be pushed to the CanacondaRx_Transcode_queue. Once
a raw message is popped it gets decoded with CANacondaMessageParse() and then printed from here.


Notes:

CANacondaMessageParse -- main parser
hexToVal --------------- converts the payload data

A Regex Match object is passed to this parsing function contained in this file.
Example parsed message:
(None, '09FD0284', '8', 'D410002841FAFFFF', '5CCC')
parsedmsg.groups() will give:
     (1)               (2)            (3)          (4)       (5)
header for 't'    header for 'T'     length        body      junk
'''
from backend import conversionMap
from Nmea2000 import Iso11783Decode
from queue import Queue
from CanMessage import *
from outmessage import *
import time
import sys
from math import ceil

from messageInfo import CAN_FORMAT_EXTENDED

class CanTranscoder():
    def __init__(self, dataBack):

        self.dataBack = dataBack

        # The user-defined metadata needed for parsing messages, via MessageInfo objects
        self.metaData = dataBack.messages

        # A queue that has regex match objects that come off the serial port
        self.CanacondaRx_TranscodeQueue = dataBack.CANacondaRx_TranscodeQueue

        # A queue that has CANacondaMessage objects that the UI will use
        self.CanacondaRxMsg_queue = dataBack.CANacondaRxMsg_queue

    def CanTranscoderRun(self):
        while True:
            msg = self.CanacondaRx_TranscodeQueue.get()
            newCanMessage = CANacondaMessage()
            CANacondaMessageParse(msg, newCanMessage, self.metaData, self.dataBack)
            # Pretty-print the message to the terminal. Note that this is used only in the command-line version
            self.PrintMessage(newCanMessage)


try:
    from PyQt5.QtCore import pyqtSignal, QObject

    class CanTranscoderGUI(QObject):
        parsedMsgPut = pyqtSignal()
        newMessageUp = pyqtSignal()

        def __init__(self, dataBack):
            CanTranscoder.__init__(self, dataBack)
            QObject.__init__(self)

        # Continuously pop from the transcode queue, parse, and put to the 'RxMsg_queue' 
        # for access to the CANacondaMessage objects from within the GUI thread.
        # This queue separates the serial layer from the rest of the program.
        def CanTranscoderRun(self):
            while True:
                msg = self.CanacondaRx_TranscodeQueue.get()
                newCanMessage = CANacondaMessage()
                CANacondaMessageParse(msg, newCanMessage, self.dataBack.messages, self.dataBack) #FIXME: make parameter names consistent with function
                self.dataBack.CANacondaRxMsg_queue.put(newCanMessage)
                self.parsedMsgPut.emit()
                # If not present already, add the message's messageInfo
                # and field name to the dataBack.messagesSeenSoFar dict,
                # and emit a signal for redrawing the messages table
                if newCanMessage.name not in self.dataBack.messagesSeenSoFar and newCanMessage.name is not '':
                    self.dataBack.messagesSeenSoFar[newCanMessage.name] = []
                    for field in newCanMessage.body:
                        self.dataBack.messagesSeenSoFar[newCanMessage.name].append(field)
                        self.newMessageUp.emit()

except ImportError:
    pass


class CanTranscoderCLI(CanTranscoder):

    def __init__(self, dataBack):
        """Initialization only requires initializing the parent class, which really does all the work."""
        super().__init__(dataBack)
        self.args = dataBack.args

    def PrintMessage(self, canacondamessage):
        """Print the given message to stdout. It accounts for some program settings regarding how the output should look."""
        outmsg = ''

        if self.args.csv:
            # If specified, do zero-order hold on output CSV data.
            if self.args.zero:
                outmsg = noGuiParseCSV_zero(
                               self.dataBack, canacondamessage)
            # If CSV mode is specified, print data comma-separated.
            else:
                outmsg = noGuiParseCSV(self.dataBack,
                                       canacondamessage)
        else:
            # If we have metadata for messages, pretty-print using it.
            if self.args.messages is not None:
                outmsg = noGuiParse(self.dataBack,
                                    canacondamessage)
            # Otherwise just print out the raw message data
            else:
                # Prepend timestamp to millisecond precision if the user requested it.
                if self.args.time:
                    outmsg = "{0:0.3f} ".format(time.time())
                
                # And then output the raw message data.
                outmsg += str(canacondamessage)

        # Finally print the message data. We call flush here to speed up the output.
        # This allows the CSV output to be used as input for pipePlotter and render
        # in real-time.
        if outmsg:
            print(outmsg)
            sys.stdout.flush()


# The goal here is to fill in all of the following:
# name, pgn, id, body (aka 'payload'), raw
# FIXME: Make this a series of smaller function calls so that it is more readable
def CANacondaMessageParse(match, newCanMessage, metaData, dataBack):
    # Parse out the ID from the regex Match object. Keep it an integer!
    if match.group(1):
        newCanMessage.id = int(match.group(1), 16)
    elif match.group(2):
        newCanMessage.id = int(match.group(2), 16)

    payloadSize = int(match.group(3))

    payloadString = match.group(4)
    if payloadSize * 2 != len(payloadString):
        payloadString = payloadString[0:2 * payloadSize]

    newCanMessage.payload = ParseBody(payloadString)

    # This bit string is a big-endian representation of the above.
    # Do this here once rather than each time a payload field is parsed below
    newCanMessage.payloadBitstring = ParseBodyBits(payloadString)

    # Now grab a PGN value if one's found
    [pgn, x, y, z] = Iso11783Decode(newCanMessage.id)
    newCanMessage.pgn = pgn

    # Now that we have the current message's ID, raw, and pgn values,
    # find and assign the message's name to newCanMessage.name
    for key in metaData.keys():
        if metaData[key].pgn == str(newCanMessage.pgn) or metaData[key].id == newCanMessage.id:
            newCanMessage.name = metaData[key].name
            break
    # If newCanMessage.name is still None, then the  message is not in the xml 
    # file and is not of interest:
    if not newCanMessage.name:
        return
    
    # In order to continue assigning values to newCanMessage, we need access to the
    # corresponding MessageInfo object. First, try with filter ID. Then PGN.
    try:
        currentMessageInfo = metaData[dataBack.id_to_name[newCanMessage.id]]
    except:
        currentMessageInfo = metaData[dataBack.pgn_to_name[str(newCanMessage.pgn)]]
    if newCanMessage.id not in dataBack.IDencodeMap.values():
        dataBack.IDencodeMap[newCanMessage.name] = newCanMessage.id
    # grab the values from the data field(s)
    for fieldName in currentMessageInfo.fields: 
        #dataFilter is a MessageInfo.Field object. Used for parsing field data.
        dataFilter = currentMessageInfo.fields[fieldName]  

        # The field data may be an int or a bitfield, depending on the type 
        # specified in metadata.
        payloadData = getBodyFieldData(dataFilter, newCanMessage)
        if dataFilter.type == 'bitfield':
            newCanMessage.body[dataFilter.name] = payloadData
        else:
            newCanMessage.body[dataFilter.name] = assignPayload(dataFilter, newCanMessage, payloadData)

    if not dataBack.nogui:
        # Now to calculate message frequency:
        calcFrequency(newCanMessage, dataBack)

        # Add a copy of the CANacondaMessage to the 'latest_messages' dictionary:
        dataBack.latest_CANacondaMessages[newCanMessage.name] = newCanMessage.body

        # Add the frequency to the 'latest_frequencies' dictionary:
        dataBack.latest_frequencies[newCanMessage.name] = newCanMessage.freq


# A helper function that further parses the payloadData for the newCanacondaMessage
def assignPayload(dataFilter, newCanMessage, payloadData):
    # If it is an N2K FFFF, return Not A Number.
    # FIXME: Make this a mask instead
    if payloadData == 65535:
        return 'NaN'

    payloadData *= dataFilter.scaling

    # Check to see of user has changed units
    if dataFilter.unitsConversion:
        payloadData = convertUnits(payloadData, dataFilter)

    # Last but not least, if we are doing a 'filterByValue':
    if dataFilter.byValue:
        if payloadData not in dataFilter.byValue:
            payloadData = ''

    return payloadData


# Retrieves the data field from the CAN message body and does any units 
# conversion and/or filtering specified by the user during runtime.
def getBodyFieldData(dataFilter, newCanMessage):
    payloadBits = newCanMessage.payloadBitstring

    # To convert the payload to a human-readable form, we use 'int.from_bytes()', which
    # needs an array of bytes. See Python documentation.
    byteArray = getByteArray(dataFilter.offset, dataFilter.length, payloadBits)

    # 'type_' refers to the type of message. Could be 'int' or 'bitfield'
    type_   = dataFilter.type

    # If it is a bitfield, just return the bits as a string.
    if type_ == 'bitfield':
        if dataFilter.byValue:
            # If the user is doing 'byValue' filtering (GUI), then adjust accordingly
            if int(payloadData[2:], 2) not in dataFilter.byValue:
                payloadData = ''
        # Convert the payloadData into a binary string that shows every bit
        else:
            payloadData = ("{:#0" + str(2 + dataFilter.length) + "b}").format(int.from_bytes(byteArray, byteorder=dataFilter.endian))
        return payloadData

    # The payload data is an int
    else:
        # Assign the payload value using the int.from_bytes in this switch statement
        return payloadSwitch(dataFilter.endian, dataFilter.signed, byteArray)

# Convert units as input by the user, i.e. from degrees Celsius Fahrenheit
def convertUnits(payloadData, dataFilter):
    try:
    # Data conversion done by adding, multiplying, then
    # adding the tuple entries found in the conversion map
    # in backend.py
    # FIXME: the conversion relation is linear in two variables, not three
        payloadData += float(conversionMap[dataFilter.units][
                                dataFilter.unitsConversion][1])
        payloadData *= float(conversionMap[dataFilter.units][
                                dataFilter.unitsConversion][0])
        payloadData += float(conversionMap[dataFilter.units][
                                dataFilter.unitsConversion][2])
    except KeyError:
        pass
    return payloadData


# Calculate the frequeny at which the message is being broadcast. Useful for GUI mode only
def calcFrequency(newCanMessage, dataBack):
    if newCanMessage.name not in dataBack.frequencyMap:
        dataBack.frequencyMap[newCanMessage.name] = Queue()
    else:
        dataBack.frequencyMap[newCanMessage.name].put(time.time())

    # If the first element(s) in the queue is/are older than 5 seconds, remove:
    # FIXME: This is a hacked circular buffer. Do a real one.
    if dataBack.frequencyMap[newCanMessage.name].qsize() > 0:
        while time.time() - dataBack.frequencyMap[newCanMessage.name].queue[0] > 5.0:
            null = dataBack.frequencyMap[newCanMessage.name].get()
            if dataBack.frequencyMap[newCanMessage.name].empty():
                break
    # Division by 5 now gives us a running average
    newCanMessage.freq = dataBack.frequencyMap[newCanMessage.name].qsize()/5.0


# getByteArray: Before using the int.from_bytes function, we must format the data
# into this array. 
# parameters:
#    offset and length are from the messageInfo field objects for the current field
#    payloadBits is the bit array for the current CanMessage object. It is a string.
# return value:
# 'byteArray' is an array of int, where each int represents a byte of data
def getByteArray(offset, length, payloadBits):

    # Define the start:stop indices used to slice the payload bits
    start = len(payloadBits) - offset
    stop = start - length

    # This is the subset payloadBits that are relevant to the current field
    payloadSlice = payloadBits[stop: start]

    # Next create an array of bytes that will be used to convert with int.from_bytes()
    byteArray = []
    while len(payloadSlice) > 8:
        # Store the lowest 8 bits
        highdata = payloadSlice[-8:]
        # Convert the stored bits to an int, and append to byteArray array
        byteArray.append(int(highdata, 2))
        # and then chop them off from bitstring
        payloadSlice = payloadSlice[:-8]
    # For the left-over bits, convert them to int and append
    try:
        if payloadSlice:
            output = int(payloadSlice, 2)
            byteArray.append(output)
    except: # FIXME: find out what this error was
        pass
    return byteArray


# formatPayloadFromInts
# Takes a message.payload array and returns a byte string after reversal
# haha, deprecated
def formatPayloadFromInts(payload):
    newPayload = payload[::-1] # reverse the list without modifying it like .reverse() does
    for a, int_ in enumerate(newPayload):
        if int_ == 0:
            newPayload[a] = '00'
            continue
        if len(hex(int_)) == 3:
            newPayload[a] = ('0' + hex(int_)[2])
        else:
            newPayload[a] = (hex(int_)[2:4])
    return "".join(newPayload)


def ParseBody(payloadString):
    """Parse out an array of integers from a string of hex chars"""
    # Set the size of the output array
    payloadSize = len(payloadString) // 2

    # Parse out each byte from the payload string into an integer array
    payload = [None] * payloadSize 
    for i in range(payloadSize):
        charIndex = 2 * i
        payload[i] = (int(payloadString[charIndex], 16) << 4) + int(payloadString[charIndex + 1], 16)

    return payload


# ParseBodyBits
# 'hexData' is the string of bytes that represent the message body. This function 
# changes the endianness of this hex string and changes its representation to bits.
def ParseBodyBits(hexData):
    count = len(hexData)
    dataflipped = ""
    while count > 0:
        # this flips the order of all the hex bits to switch from little
        # to big endian
        dataflipped = dataflipped + hexData[count-2:count]
        count -= 2
    binaryData = bin(int(dataflipped, 16))  # converts the data to binary
    # Strip the '0b' and pad with leading 0's
    binaryData = (4 * len(hexData) - (len(binaryData) - 2)) * '0' + binaryData[2:]
    return binaryData


# Function parameters:
# 'endian' and 'signed' are from the metadata provided by the user, via messageInfo objects.
# 'byteArray' is an array of ints that represent bytes, which is the type of parameter
# that the function 'int.from_bytes' needs
# The return value is the integer value of the payload, before unit/scaling conversion
def payloadSwitch(endian, signed, byteArray):

    #little endian unsigned
    if endian == "little" and signed == "no":
        pay = int.from_bytes(byteArray, byteorder='little', signed=False)

    #little endian signed
    elif endian == "little" and signed == "yes":
        pay = int.from_bytes(byteArray, byteorder='little', signed=True)

    #big endian signed
    elif endian == "big" and signed == "yes":
        pay = int.from_bytes(byteArray, byteorder='big', signed=True)

    #big endian unsigned
    elif endian == "big" and signed == "no":
        pay = int.from_bytes(byteArray, byteorder='big', signed=False)

    return pay


# count: size of message body in bytes
# hexData: message body in hex format
# return value: string of body data in hex format, with nibbles flipped.
def flipNibbles(count, hexData):
    dataflipped = ""
    i = 0
    while i < count:
        try:
            dataflipped += hexData[i+1] + hexData[i]
        except IndexError:
            dataflipped += hexData[i]
        i += 2
    return dataflipped


# generateMessage: Creates a hex encoded message
# 'payload' is a dictionary mapping of field names to payload data
# 'messageName' is a string that came from the QComboBox (GUI) or a command-line argument (CLI)
def generateMessage(dataBack, payload, messageName):
    messageInfo = dataBack.messages[messageName]  # MessageInfo object
    # Construct a string that we will use to .format() later on. 'formatString' needs to 
    # adjust itself for any CAN message body length; 'bodyFormatter' does this.
    bodylength = messageInfo.size*2
    bodyFormatter = "0" + str(bodylength) + "X"
    formatString = 't{:03x}{:1d}{:' + bodyFormatter + '}\r'
    if messageInfo.format == CAN_FORMAT_EXTENDED:
        formatString = 'T{:08x}{:1d}{:' + bodyFormatter + '}\r'

    # This will work only if the node is connected and broadcasting.
    try:
        id = dataBack.IDencodeMap[messageName]  
    except KeyError:
        # We assumed the node was connected and broadcasting but it was not.
        # Need to use the Nmea11783Encode version of the ID instead.
        id = dataBack.messages[messageInfo.name].fakeID

    # Initialize an array of 0's of length equal to number of bits in message body
    payloadArray = [0]*messageInfo.size*8

    # For each of the fields, populate the corresponding entries in payloadArray with
    # the bits that are obtained from 'encodePayload'
    for field in messageInfo.fields:
        dataFilter = dataBack.messages[messageName].fields[field]

        if len(bin(ceil(abs(payload[field])))) - 2 > dataFilter.length:
            # The length of the stringified binary represenation of the number, after
            # the ceiling function is applied (rounding up to nearest integer). The '- 2'
            # accounts for the '0b' at the beginning of the string. This must be longer than
            # the length specified in the metaData.
            raise Exception ("{} field allows up to {} bits of data".format(field, dataFilter.length))
        fieldData = encodePayload(payload[field], dataFilter)
        # Find appropriate array indices, and insert fieldData into the payloadArray
        start = dataFilter.offset
        stop  = dataFilter.offset + dataFilter.length
        payloadArray[start:stop] = fieldData

    # Collapse 
    payloadString = ''.join(map(str,payloadArray))
    payloadInt = int(payloadString, 2)
    payloadHexString = hex(payloadInt)[2:]

    # Pad the hex string with leading zeros, using zfill().
    if len(payloadHexString) < bodylength:
        payloadHexString = payloadHexString.zfill(bodylength)

    # And return the transmit message as a properly formatted message.
    outStr = formatString.format(id, messageInfo.size, int(payloadHexString, 16))
    print(outStr)
    return outStr


# Need to check for return value length. Should be same as 'length'
# specified in metadata. Current code does not handle numbers that are too big.
# Returns an array of 0's and 1's, of length 'length'.
def encodePayload(payload, dataFilter):
    endian = dataFilter.endian
    _signed = dataFilter.signed == 'yes'
    offset = dataFilter.offset
    length = dataFilter.length
    scaling = dataFilter.scaling
    _type = dataFilter.type
    # First check for proper length of signed fields
    if _signed:
        if payload < -2**(length-1)  or payload > 2**(length-1)-1:
            raise Exception ("The {} field uses a signed data type, and the range of values is from {} to {}.".format(dataFilter.name, -(2**(length-1)), 2**(length-1)-1))

    # If the payload is signed, handle this correctly.
    Negative = False
    if _signed and payload < 0:
        payload = -payload
        Negative = True

    # If the user has entered a negative number for an unsigned field, error out.    
    elif not _signed and payload < 0:
        raise Exception ("The value {} is not allowed for the {} field, because its data type is unsigned. Use a positive number.".format(payload, dataFilter.name))

    # Convert the payload to a binary string
    if Negative:
        pay = bin(int(-payload/scaling) % (1<<length))[2:]  # two's complement
    else:
        pay = bin(int(payload/scaling))[2:]

    # Initialize an array of zeros with correct length
    fieldData = [0]*length

    for i in range(len(pay)):
        try:
            # Fill in fieldData, starting from the right.
            fieldData[-i-1] = int(pay[-i-1])
        except IndexError: #  payload scaled up and has become too big for data type
            raise Exception ("The value {} is too large for the {} field, which is scaled by {}.\nUse a number of length {} bits.".format(payload, dataFilter.name, 1/scaling,length))
    return fieldData


def debugMode():
    from PyQt5.QtCore import pyqtRemoveInputHook
    pyqtRemoveInputHook()
    import pdb
    pdb.set_trace()
   


## For the left-over dangling bits, convert them to int and append
#  output = 0
#  try:
#      output = int(payloadSlice, 2)
#  except:
#      pass
#  dataset.append(output)
