'''
This file includes the code for the CanPort class, which is run from the
recieveMessage_helper function from canpython.py

The CanPort deal with the serial data from the CAN to USB node.
Once a message has been received, a Message object is created and
the serial data is no longer dealt with for that message.
'''

# Standard libraries
import re
import time
import sys
from queue import Queue

# Other libraries
import serial

# User libraries
from CanMessage import *
from outmessage import *
from backend import conversionMap
from Nmea2000 import Iso11783Decode

# CanPort is the thread which handles direct communication with the CAN device.
# CanPort initializes the connection and then receives and parses standard CAN
# messages. These messages are then passed to the GUI thread via the
# CANacondaRxMsg_queue queue where they are added to the GUI
class CANPort():

    # Error constants to be returned by pyserialInit():
    # ERROR_NO_DATA    No data being transmitted.
    # ERROR_NO_CONNECT Could not open serial port
    # ERROR_TIMEOUT    Timeout in sending the 'O' command to CANusb device
    # ERROR_BAUD       Could not set the baud rate for CAN bus
    ERROR_NO_DATA, ERROR_NO_CONNECT, ERROR_TIMEOUT, ERROR_BAUD = range(4)

    # Set the timeout (in seconds) for connecting to the CANusb hardware.
    TIMEOUT = 5

    def __init__(self, dataBack):
        self.dataBack = dataBack
        self.CANacondaRxMsg_queue = dataBack.CANacondaRxMsg_queue
        self.comport = dataBack.comport
        self.args = dataBack.args

    def pyserialInit(self):
        #opens a serial connection called serialCAN on COM? at 57600 Baud
        try:
            serialCAN = serial.Serial(self.comport, 57600)
            # self.comport is the com port which is opened
        except:
            return CANPort.ERROR_NO_CONNECT
        else:
            # compiles a regular expression to parse both the short
            # and long form messages as defined in the CAN-USB manual
            self.regex = re.compile(r"\s*(?:t([0-9a-fA-F]{3})|T([0-9a-fA-F]{8}))(\d)((?:[0-9a-fA-F][0-9a-fA-F]){0,8})((?:[0-9a-fA-F][0-9a-fA-F]){2})?")
            
            # If the port is open already, the following may fail. We therefore try to close
            # the first first, and ignore whatever output we received.
            val = serialCAN.write(b'C\r')
            if val != 2:
                return CANPort.ERROR_NO_CONNECT

            # Start a timer to see if initialization has taken too long, erroring out in that case.
            start = time.time()
            
            # Now keep looping until we've successfully configured the CANusb hardware.
            temp = serialCAN.read()
            while temp != b'\r':
                time.sleep(.1)
                # Initialize the CAN-USB device at 250Kbits/s, the NMEA standard
                val = serialCAN.write(b'S5\r')

                # If a bell was received after sending 'S5', it means an error's occurred
                if val == 7:
                    return CANPort.ERROR_BAUD

                # Store the initial bytes in a temporary variable.
                temp = serialCAN.read()

                # Return if no data is being received over serial:
                if time.time() - start - 5 > CANPort.TIMEOUT:
                    return CANPort.ERROR_NO_DATA

            # Open the CAN port to begin receiving messages, using timer as above
            start = time.time()
            val = serialCAN.write(b'O\r')
            while val != 2:
                val = serialCAN.write(b'O\r')
                if time.time() - start - 5 > CANPort.TIMEOUT:
                    return CANPort.ERROR_TIMEOUT
            time.sleep(.1)
            return serialCAN

    # CANport thread can repeat targed is the getMessages function:
    def getMessages(self, serialCAN):
        while True:
            self.serialParse(serialCAN)

    # parse the serial string, create the CANacondaMessage object, and print it.
    def serialParse(self, serialCAN):
        # Sit and wait for all the bytes for an entire CAN message from the serial port.
        matchedmsg = self.getMatchObject(serialCAN)
        
        # Once we've parsed out a complete message, actually process the data for display.
        if matchedmsg:
            canacondamessage = CANacondaMessage()

            CANacondaMessageParse(canacondamessage, matchedmsg, self.dataBack)

            self.PrintMessage(canacondamessage)

    # Build up a message character by character from the serial stream, and then wrap it
    # in a regex match object.
    def getMatchObject(self, serialCAN):
        character = None
        rawmsg = b""
        # Reads in characters from the serial stream until
        # a carriage return is encountered
        while character != (b'\r' or '\r'):
            # Wrap the read() call in a try/except to catch possible serial port errors since we 
            # never check the state of the serial port after initial opening.
            try:
                character = serialCAN.read()
            except SerialException:
                return None
            # appends the newly read character to
            # the message being built
            rawmsg += bytes(character)
        rawmsg = rawmsg.decode('utf-8')
        matchedMsg = self.regex.match(rawmsg)
        return matchedMsg

class CANPortCLI(CANPort):

    def __init__(self, dataBack):
        """Initialization only requires initializing the parent class, which really does all the work."""
        super(CANPortCLI, self).__init__(dataBack)

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

try:
    from PyQt5.QtCore import pyqtSignal, QObject
    from PyQt5.QtCore import pyqtRemoveInputHook as pyqtrm

    class CANPortGUI(CANPort, QObject):

        parsedMsgPut = pyqtSignal()
        newMessageUp = pyqtSignal()

        def __init__(self, dataBack):
            CANPort.__init__(self, dataBack)
            QObject.__init__(self)

        def serialParse(self, serialCAN):
            dataBack = self.dataBack
            matchedmsg = self.getMatchObject(serialCAN)
            newCANacondaMessage = CANacondaMessage()
            if matchedmsg:
                CANacondaMessageParse(newCANacondaMessage, matchedmsg, dataBack)
                # use dataBack.nogui?
                self.dataBack.CANacondaRxMsg_queue.put(newCANacondaMessage)
                self.parsedMsgPut.emit()

                # If not present already, add the message's messageInfo
                # and field name to the dataBack.messagesSeenSoFar dict,
                # and emit a signal for redrawing the messages table
                if newCANacondaMessage.name not in self.dataBack.messagesSeenSoFar and newCANacondaMessage.name is not '':
                    self.dataBack.messagesSeenSoFar[newCANacondaMessage.name] = []
                    for field in newCANacondaMessage.body:
                        self.dataBack.messagesSeenSoFar[newCANacondaMessage.name].append(field)
                    self.newMessageUp.emit()
except ImportError:
    pass

'''
For adding the data to the CANacondaMessage object.
CANacondaMessageParse -- main parser
hexToVal --------------- converts the payload data

A Regex Match object is passed to this parsing function contained in this file.
Example parsed message:
(None, '09FD0284', '8', 'D410002841FAFFFF', '5CCC')
parsedmsg.groups() will give:
     (1)               (2)            (3)          (4)       (5)
header for 't'    header for 'T'     length        body      junk


Note that the 'id' tag is sometimes referred to as 'header'
'''
from backend import conversionMap
from Nmea2000 import Iso11783Decode
from queue import Queue

# The goal here is to fill in all of the following:
# name, pgn, id, body (aka 'payload'), raw
def CANacondaMessageParse(self, match, dataBack):
    # Parse out the ID from the regex Match object. Keep it an integer!
    if match.group(1):
        self.id = int(match.group(1), 16)
    elif match.group(2):
        self.id = int(match.group(2), 16)

    payloadSize = int(match.group(3))

    payloadString = match.group(4)
    if payloadSize * 2 != len(payloadString):
        payloadString = payloadString[0:2 * payloadSize]

    self.payload = ParseBody(payloadString)

    # Now grab a PGN value if one's found
    [pgn, x, y, z] = Iso11783Decode(self.id)
    self.pgn = pgn

    # Now that we have the current message's ID, raw, and pgn values,
    # find and assign the message's name to self.name
    for key in dataBack.messages.keys():
        if dataBack.messages[key].pgn == str(self.pgn) or dataBack.messages[key].id == self.id:
            self.name = dataBack.messages[key].name
            #break
    # If self.name is still None, then the  message is not in the xml 
    # file and is not of interest:
    if not self.name:
        return
    
    # make a pointer to the MessageInfo object. First, try with filter ID. Then PGN.
    try:
        currentMessage = dataBack.messages[dataBack.id_to_name[self.id]]
    except:
        currentMessage = dataBack.messages[dataBack.pgn_to_name[str(self.pgn)]]

    if self.id not in dataBack.IDencodeMap:
        dataBack.IDencodeMap[self.name] = self.id

    # grab the values from the data field(s)
    for fieldName in currentMessage.fields:
        dataFilter = currentMessage.fields[fieldName]  # dataFilter is a MessageInfo.Field object. Used for parsing field data.
        # The field data may be an int or a bitfield, depending on the type specified in metadata.
        payLoadData = getBodyFieldData(dataFilter, currentMessage, match)

        self.body[dataFilter.name] = payLoadData

    # Now to calculate message frequency:
    if self.name not in dataBack.frequencyMap:
        dataBack.frequencyMap[self.name] = Queue()
    else:
        dataBack.frequencyMap[self.name].put(time.time())

    # If the first element(s) in the queue is/are older than 5 seconds, remove:
    if dataBack.frequencyMap[self.name].qsize() > 0:
        while time.time() - dataBack.frequencyMap[self.name].queue[0] > 5.0:
            null = dataBack.frequencyMap[self.name].get()
            if dataBack.frequencyMap[self.name].empty():
                break
    # Division by 5 now gives us a running average
    self.freq = dataBack.frequencyMap[self.name].qsize()/5.0

    # The CANacondaMessage has now been created.

########### GUI related #################################
    # Add data to the headers and messages sets
    dataBack.headers.add(self.id)
    dataBack.pgnSeenSoFar.add(self.pgn)

    # Add a copy of the CANacondaMessage to the 'latest_messages' dictionary:
    dataBack.latest_CANacondaMessages[self.name] = self.body

    # Add the frequency to the 'latest_frequencies' dictionary:
    dataBack.latest_frequencies[self.name] = self.freq
    
    # Make the frequency calculation and add to CANacondaMessage object:
    # dataBack.frequencyMap[self.name].qsize()

# Function parameters: hexData is the raw hex value of the message body
# dataFilter is the CAN message specification given in the meta data by the user.
# The return value is the CAN message payload, before filtering
# FIXME: Parse out the data from CanMessage.payload instead
def getPayload(hexData, dataFilter):
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
        dataflipped = dataflipped + hexData[count - 2] + hexData[count - 1]
        count = count - 2

    binaryData = bin(int(dataflipped, 16))  # converts the data to binary
    binaryData = (4 * len(hexData) - (len(binaryData) - 2)) * '0'\
                                                            + binaryData[2:]
    # This prepends the number of dropped 0's to the front of the binary

    #shifting indices to the right
    start = len(binaryData) - offset
    stop = len(binaryData) - (length + offset)

    datasect = binaryData[stop: start]
    # from the offset to the end of size is selected to separate
    # the relevant data

    dataset = []
    while len(datasect) > 8:
    # This code converts from binary to a set of integers for the
    # int.from_bytes() function to use
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
        # Convert the value into a bitfield. The actual type is an 'int'.
        #value = int(bin(int.from_bytes(dataset, byteorder=endian))[2:])  ## UGLY
        value = bin(int.from_bytes(dataset, byteorder=endian))  ## UGLY

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

# yeah so what else needs to happen here???
# Need to check for return value length. Should be same as 'length'
# specified in metadata. Current code does not handle numbers that are too big.
def encodePayload(payload, dataFilter):
    endian = dataFilter.endian
    _signed = dataFilter.signed
    offset = dataFilter.offset
    length = dataFilter.length
    scaling = dataFilter.scaling

    # byte order still needs to be adjusted.
    payload = hex(int(payload/scaling))[2:]
    while len(payload) < length//4:
        payload += '0'
#    if _signed == 'no':
#        _signed = False
#    else:
#        _signed = True
    return payload

    


# Retrieves the data field from the CAN message body and does any units 
# conversion and/or filtering specified by the user during runtime.
# FIXME: Don't pull data from `match`, instead pull from self.payload
def getBodyFieldData(dataFilter, currentMessage, match):
    msgBody = match.group(4)
    value = getPayload(msgBody, dataFilter)
    # Check for invalid data.
    # 0xFFFF is the 'invalid data' code
   
    # If we have a bitfield for status or error codes, just return the string.
    if dataFilter.type == 'bitfield':
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

def getBitfield(dataFilter, currentMessage, payload, match):
    from PyQt5.QtCore import pyqtRemoveInputHook
    pyqtRemoveInputHook()
    import pdb
    pdb.set_trace()
    msgBody = payload
    
