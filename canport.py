'''
This file includes the code for the CanPort class, which is run from the
recieveMessage_helper function from canpython.py

The CanPort deals with the serial data from the CAN to USB node.
Once a message has been received, a regex match object is created and
the serial data is discarded.


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
#from CanDataTranscoder import *
from outmessage import *
from backend import conversionMap
from Nmea2000 import Iso11783Decode

# Constants
from messageInfo import CAN_FORMAT_EXTENDED

# CanPort is the thread which handles direct communication with the CAN device.
# CanPort initializes the connection and then receives and parses standard CAN
# messages. These messages are then passed to the CanTranscoder thread for parsing
# into CANacondaMessage objects.
class CANPort():
    '''
    Error constants to be returned by pyserialInit():
    ERROR_NO_DATA    No data being transmitted.
    ERROR_NO_CONNECT Could not open serial port
    ERROR_TIMEOUT    Timeout in sending the 'O' command to CANusb device
    ERROR_BAUD       Could not set the baud rate for CAN bus
    '''
    ERROR_NO_DATA, ERROR_NO_CONNECT, ERROR_TIMEOUT, ERROR_BAUD, SUCCESS = range(5)

    # Set the timeout (in seconds) for connecting to the CANusb hardware.
    TIMEOUT = 5

    def __init__(self, dataBack):
        self.dataBack = dataBack
        self.CANacondaRx_TranscodeQueue = dataBack.CANacondaRx_TranscodeQueue
        self.comport = dataBack.comport
        self.args = dataBack.args

    def pyserialInit(self, baudrate=57600):
        #opens a serial connection called serialCAN on COM? at 57600 Baud
        try:
            serialCAN = serial.Serial(self.comport, baudrate)
            # self.comport is the com port which is opened
        except:
            return CANPort.ERROR_NO_CONNECT
        else:
            # compiles a regular expression to parse both the short
            # and long form messages as defined in the CAN-USB manual
            self.regex = re.compile(r"\s*(?:t([0-9a-fA-F]{3})|T([0-9a-fA-F]{8}))(\d)((?:[0-9a-fA-F][0-9a-fA-F]){0,8})((?:[0-9a-fA-F][0-9a-fA-F]){2})?")
            
            # If the port is open already, close it first. Do this by writing the character 'C'
            # followed by the carriage return. The hardware will return either a carriage
            # return (13) or a bell (7) (At least that's what the docs for this device say)
            # (In practice, looks like we're expecting a 2.)
            val = serialCAN.write(b'C\r')
            if val != 2:
                return CANPort.ERROR_NO_CONNECT

            StatusMsg = self.CanUSBinit(serialCAN)
            if StatusMsg != CANPort.SUCCESS:
                return StatusMsg
            
            StatusMsg = self.CanUSBopen(serialCAN)
            if StatusMsg != CANPort.SUCCESS:
                return StatusMsg

            # Finally, if we have made it to here, the serialCAN object was created successfully
            # and the CanUSB device is ready for read/write operations
            return serialCAN


    def CanUSBinit(self, serialCAN, setup='S5'):
        # Start a timer to see if initialization has taken too long, erroring out in that case.
        start = time.time()
        setupBytes = setup.encode() + b'\r'
        # Now keep looping until we've successfully configured the CANusb hardware.
        temp = serialCAN.read()
        while temp != b'\r':
            time.sleep(.1)
            # Initialize the CAN-USB device at 250Kbits/s, the NMEA standard
            val = serialCAN.write(setupBytes)
            # If a bell was received after sending 'S5', it means an error's occurred
            if val == 7:
                return CANPort.ERROR_BAUD

            # Store the initial bytes in a temporary variable.
            temp = serialCAN.read()

            # Return if no data is being received over serial:
            if time.time() - start - 5 > CANPort.TIMEOUT:
                return CANPort.ERROR_NO_DATA

        # Fall through to SUCCESS
        return CANPort.SUCCESS

    # CanUSBopen. CanUSB flags have been set, now send the command for the device to open its
    # connection over serial.
    def CanUSBopen(self, serialCAN):
        # Open the CAN port to begin receiving messages, using timer as above
        start = time.time()
        val = serialCAN.write(b'O\r')
        while val != 2:
            val = serialCAN.write(b'O\r')
            if time.time() - start - 5 > CANPort.TIMEOUT:
                return CANPort.ERROR_TIMEOUT
        return CANPort.SUCCESS

    # CANport thread repeat target is the getMessages function, which calls the actual
    # parsing function. If the serial connection is closed, for example, when changing the
    # baudrate, then we don't parse anything.
    # FIXME: serialCAN.closed being False may not be a sufficient condition, because when
    # serial is re-established, the CanUSB device does not immediately open...
    def getMessages(self, serialCAN):
        while True:
            if not serialCAN.closed:
                self.serialParse(serialCAN)

    # parse the serial string, create the CANacondaMessage object, and print it.
    def serialParse(self, serialCAN):
        # Sit and wait for all the bytes for an entire CAN message from the serial port.
        matchedmsg = self.getMatchObject(serialCAN)

        
        # Push the match object to this queue for parsing from within CanDataTranscoder.py
        if matchedmsg:
            self.dataBack.CANacondaRx_TranscodeQueue.put(matchedmsg)

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
            except serial.serialutil.SerialException:
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


try:
    from PyQt5.QtCore import pyqtSignal, QObject

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
                self.dataBack.CANacondaRx_TranscodeQueue.put(matchedmsg)
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


def debugMode():
    from PyQt5.QtCore import pyqtRemoveInputHook
    pyqtRemoveInputHook()
    import pdb
    pdb.set_trace()
    
