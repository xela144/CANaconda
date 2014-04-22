'''
This file includes the code for the CanPort class, which is run from the
recieveMessage_helper function from canpython.py

The CanPort deal with the serial data from the CAN to USB node.
Once a message has been received, a Message object is created and
the serial data is no longer dealt with for that message.
'''

import re
import time
import backend
from CanMessage import CanMessage
from CANacondaMessageParse import *
from outmessage import *
import serial
import sys

# CanPort is the thread which handles direct communication with the CAN device.
# CanPort initializes the connection and then receives and parses standard CAN
# messages. These messages are then passed to the GUI thread via the
# CANacondaRxMsg_queue queue where they are added to the GUI
class CANPort():

    # Declare some error constants to be returned by pyserialInit().
    # FIXME: Add documentation for what each of these error codes means
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
        (rawmsg, matchedmsg) = self.getRegex(serialCAN)
        
        # Once we've parsed out a complete message, actually process the data for display.
        canacondamessage = CANacondaMessage()
        if matchedmsg:
            CANacondaMessageParse(canacondamessage, matchedmsg, self.dataBack)

        # Finally just print the message since we're running in command line mode already.
        self.PrintMessage(canacondamessage)

    # FIXME: Change to a descriptive name
    def getRegex(self, serialCAN):
        character = None
        rawmsg = b""
        # Reads in characters from the serial stream until
        # a carriage return is encountered
        while character != (b'\r' or '\r'):
            character = serialCAN.read()
            # appends the newly read character to
            # the message being built
            rawmsg += bytes(character)
        rawmsg = rawmsg.decode('utf-8')
        matchedMsg = self.regex.match(rawmsg)
        return rawmsg, matchedMsg

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
            rawmsg, matchedmsg = self.getRegex(serialCAN)
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

