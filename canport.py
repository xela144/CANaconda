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
from CANacondaMessage import *
from CANacondaMessageParse import *
from outmessage import *
import serial
import sys

# CanPort is the thread which handles direct communication with the CAN device.
# CanPort initializes the connection and then receives and parses standard CAN
# messages. These messages are then passed to the GUI thread via the
# CANacondaMessage_queue queue where they are added to the GUI
class CANPort():
    def __init__(self, dataBack, parent=None):
        self.dataBack = dataBack
        self.CANacondaMessage_queue = dataBack.CANacondaMessage_queue
        self.comport = dataBack.comport
        self.args = dataBack.args

    def getmessage(self):
        #opens a serial connection called serialCAN on COM? at 57600 Baud
        try:
            serialCAN = serial.Serial(self.comport, 57600)
            # self.comport is the com port which is opened
        except:
            print("ERROR: Could not open connection to {0}. Is port already in use?".format(self.comport))
            return
        else:
            # compiles a regular expression to parse both the short
            # and long form messages as defined in the CAN-USB manual
            self.regex = re.compile(r"\s*(?:t([0-9a-fA-F]{3})|T([0-9a-fA-F]{8}))(\d)((?:[0-9a-fA-F][0-9a-fA-F]){0,8})((?:[0-9a-fA-F][0-9a-fA-F]){2})?")
            temp = None
            while temp != b'\r':
                time.sleep(.2)
                # Initialize the CAN-USB device at 250Kbits/s, the NMEA standard
                serialCAN.write(b'S5\r')
                #print(temp)
                temp = serialCAN.read()
            time.sleep(.1)
            # Open the CAN port to begin receiving messages
            val = serialCAN.write(b'O\r')
            while val != 2:
                val = serialCAN.write(b'O\r')
            time.sleep(.1)
            # Disable timestamps on the CAN port
            serialCAN.write(b'Z0\r')
            time.sleep(.1)

            # Now that set-up is complete, the CANport thread can repeat
            # forever with the following call:
            while True:
                self.serialParse(serialCAN)

    # parse the serial string, create the CANacondaMessage object, and print it.
    def serialParse(self, serialCAN):
        # Sit and wait for all the bytes for an entire CAN message from the serial port.
        (rawmsg, matchedmsg) = self.getRegex(serialCAN)
        
        # Once we've parsed out a complete message, actually process the data for display.
        canacondamessage = CANacondaMessage()
        if matchedmsg:
            CANacondaMessageParse(canacondamessage, matchedmsg,
                                  rawmsg, self.dataBack)

        # Finally just print the message since we're running in command line mode already.
        self.PrintMessage(canacondamessage)

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

    def PrintMessage(self, canacondamessage):
        outmsg = None

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
                outmsg += canacondamessage.raw

        # Finally print the message data. We call flush here to speed up the output.
        # This allows the CSV output to be used as input for pipePlotter and render
        # in real-time.
        if outmsg:
            print(outmsg)
            sys.stdout.flush()


