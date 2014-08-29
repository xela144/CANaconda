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
def CANacondaMessageParse(match, newMsg, metaData, dataBack):
    # Parse out the ID from the regex Match object. Keep it an integer!
    if match.group(1):
        newMsg.id = int(match.group(1), 16)
    elif match.group(2):
        newMsg.id = int(match.group(2), 16)

    payloadSize = int(match.group(3))

    payloadString = match.group(4)
    if payloadSize * 2 != len(payloadString):
        payloadString = payloadString[0:2 * payloadSize]

    #FIXME: From here on, we should no longer use the regex match object.
    newMsg.payload = ParseBody(payloadString)

    # Now grab a PGN value if one's found
    [pgn, x, y, z] = Iso11783Decode(newMsg.id)
    newMsg.pgn = pgn

    # Now that we have the current message's ID, raw, and pgn values,
    # find and assign the message's name to newMsg.name
    for key in metaData.keys():
        if metaData[key].pgn == str(newMsg.pgn) or metaData[key].id == newMsg.id:
            newMsg.name = metaData[key].name
            break
    # If newMsg.name is still None, then the  message is not in the xml 
    # file and is not of interest:
    if not newMsg.name:
        return
    
    # make a pointer to the MessageInfo object. First, try with filter ID. Then PGN.
    try:
        currentMessage = metaData[dataBack.id_to_name[newMsg.id]]
    except:
        currentMessage = metaData[dataBack.pgn_to_name[str(newMsg.pgn)]]

    if newMsg.id not in dataBack.IDencodeMap:
        dataBack.IDencodeMap[newMsg.name] = newMsg.id

    # grab the values from the data field(s)
    for fieldName in currentMessage.fields: 
        #dataFilter is a MessageInfo.Field object. Used for parsing field data.
        dataFilter = currentMessage.fields[fieldName]  
        # The field data may be an int or a bitfield, depending on the type specified in metadata.
        # FIXME: dataFilter is just currentMessage.fields[fieldname], which is passed
        # in as a parameter here.
        # Should be using newMsg.payload anyway.
        payLoadData = getBodyFieldData(dataFilter, currentMessage, match, newMsg.payload)

        newMsg.body[dataFilter.name] = payLoadData

    # Now to calculate message frequency:
    if newMsg.name not in dataBack.frequencyMap:
        dataBack.frequencyMap[newMsg.name] = Queue()
    else:
        dataBack.frequencyMap[newMsg.name].put(time.time())

    # If the first element(s) in the queue is/are older than 5 seconds, remove:
    # FIXME: This is a hacked circular buffer. Do a real one.
    if dataBack.frequencyMap[newMsg.name].qsize() > 0:
        while time.time() - dataBack.frequencyMap[newMsg.name].queue[0] > 5.0:
            null = dataBack.frequencyMap[newMsg.name].get()
            if dataBack.frequencyMap[newMsg.name].empty():
                break
    # Division by 5 now gives us a running average
    newMsg.freq = dataBack.frequencyMap[newMsg.name].qsize()/5.0

    # The CANacondaMessage has now been created.

########### GUI related #################################
    # Add data to the headers and messages sets
    dataBack.headers.add(newMsg.id)
    dataBack.pgnSeenSoFar.add(newMsg.pgn)

    # Add a copy of the CANacondaMessage to the 'latest_messages' dictionary:
    dataBack.latest_CANacondaMessages[newMsg.name] = newMsg.body

    # Add the frequency to the 'latest_frequencies' dictionary:
    dataBack.latest_frequencies[newMsg.name] = newMsg.freq
    
    # Make the frequency calculation and add to CANacondaMessage object:
    # dataBack.frequencyMap[newMsg.name].qsize()


# Function parameters: hexData is the raw hex string of one of the message body fields.
# dataFilter a messagInfo.Field type, extracted from the meta data given by the user.
# The return value is a single field payload, before filtering/error checking.
# FIXME: Parse out the data from CanMessage.payload instead
# FIXME: Returning a single field item, yet parsing the entire message body with each call
def getPayload(hexData, dataFilter, payload):
    # Variables used in this function:
    endian = dataFilter.endian
    signed = dataFilter.signed
    offset = dataFilter.offset
    length = dataFilter.length
    type   = dataFilter.type

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
    #shifting indices to the right
    start = len(binaryData) - offset
    stop = len(binaryData) - (length + offset) # could be 'start - length' too.

    datasect = binaryData[stop: start]
    # from the offset to the end of size is selected to separate
    # the relevant data

    dataset = []
    while len(datasect) > 8:
    # This code converts from binary to a set of integers for int.from_bytes() further down
        highdata = datasect[-8:]
        datasect = datasect[:-8]
        dataset.append(int(highdata, 2))
    output = 0
    try:
        output = int(datasect, 2)
    except:
        pass
    dataset.append(output)
    
    if type == 'bitfield':
        # Convert the value into a binary string that shows every bit
        value = ("{:#0" + str(2 + length) + "b}").format(int.from_bytes(dataset, byteorder=endian))
    #little endian unsigned
    elif endian == "little" and signed == "no":
        value = int.from_bytes(dataset, byteorder='little', signed=False)

    #little endian signed
    elif endian == "little" and signed == "yes":
        value = int.from_bytes(dataset, byteorder='little', signed=True)

    #big endian signed
    elif endian == "big" and signed == "yes":
        value = int.from_bytes(dataset, byteorder='big', signed=True)

    #big endian unsigned
    elif endian == "big" and signed == "no":
        value = int.from_bytes(dataset, byteorder='big', signed=False)

    else:
        print("not valid")

    return value

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

# generateMessage: Creates a hex encoded message
# 'payload' is a dictionary mapping of field names to payload data
# 'messageName' is a string that came from the QComboBox (GUI) or a command-line argument (CLI)
def generateMessage(dataBack, payload, messageName):
    messageInfo = dataBack.messages[messageName]  # MessageInfo object
    # Construct a string that we will use to .format() later on. 'formatString' needs to 
    # adjust itself for any CAN message body length; 'bodyFormatter' does this.
    bodylength = messageInfo.size*2
    bodyFormatter = "0" + str(bodylength) + "x"
    formatString = 't{:03x}{:1d}{:' + bodyFormatter + '}\r'
    if messageInfo.format == CAN_FORMAT_EXTENDED:
        formatString = 'T{:08x}{:1d}{:' + bodyFormatter + '}\r'
    try:
        # This will work only if the node is connected and broadcasting.
        id = dataBack.IDencodeMap[messageName]  
    except KeyError:
        # We assumed the node was connected and broadcasting but it was not.
        # Need to use the Nmea11783Encode version of the ID instead.
        id = dataBack.messages[messageInfo.name].fakeID

    # Initialize an array of 0's of length equal to number of bits in message body
    payloadArray = [0]*messageInfo.size*8
    for field in messageInfo.fields:
        dataFilter = dataBack.messages[messageName].fields[field]
        if len(bin(ceil(abs(payload[field])))) - 2 > dataFilter.length:
            # If user gives a message whose bit-length is longer than specified in medata, barf on user.
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
        payloadHexString.zfill(bodylength)

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

    


# Retrieves the data field from the CAN message body and does any units 
# conversion and/or filtering specified by the user during runtime.
# FIXME: Don't pull data from `match`, instead pull from self.payload
def getBodyFieldData(dataFilter, currentMessage, match, payload):
    msgBody = match.group(4)
    value = getPayload(msgBody, dataFilter, payload)
    # Check for invalid data.
    # 0xFFFF is the 'invalid data' code
   
    # If we have a bitfield for status or error codes, just return the string.
    if dataFilter.type == 'bitfield':
        if dataFilter.byValue:
            if int(value[2:], 2) not in dataFilter.byValue:
                value = ''
        return value

    # If it is an N2K FFFF, return Not A Number.
    if value == 65535:
        value = 'NaN'

    # Otherwise continue processing the int with scalar, converting to float.
    else:
        value *= dataFilter.scaling
        if dataFilter.unitsConversion:
            try:
            # Data conversion done by adding, multiplying, then
            # adding the tuple entries found in the conversion map
            # in backend.py
                value += float(conversionMap[dataFilter.units][
                                        dataFilter.unitsConversion][1])
                value *= float(conversionMap[dataFilter.units][
                                        dataFilter.unitsConversion][0])
                value += float(conversionMap[dataFilter.units][
                                        dataFilter.unitsConversion][2])
            except KeyError:
                pass

    # Last but not least, if we are doing a 'filterByValue':
    if dataFilter.byValue:
        if value not in dataFilter.byValue:
            value = ''
    return value

def debugMode():
    from PyQt5.QtCore import pyqtRemoveInputHook
    pyqtRemoveInputHook()
    import pdb
    pdb.set_trace()
    
