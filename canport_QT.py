
#  This script is meant to be just a wrapper class
#  around the original canport script.
#  However, for the sake of time I'm re-implementing
#  everything here just to get the GUI up and running
#  with the new functionality of the consolemode.
#  Once that is done, delete this file and

from PyQt5.QtCore import pyqtSignal, QObject
#import canport # not used because Qt stuff wasn't working
import re
import time
import backend
import serial
import pdb
from PyQt5.QtCore import pyqtRemoveInputHook as pyqtrm
from CANacondaMessage import *
from CANacondaMessageParse import *


class CANPort_QT(QObject):
    parsedMsgPut = pyqtSignal()
    messageUp = pyqtSignal()
    stopHourGlass = pyqtSignal()
    
    def __init__(self, dataBack, parent=None):
        QObject.__init__(self)
        super(CANPort_QT, self).__init__(parent)
        self.dataBack = dataBack
        self.CANacondaMessage_queue = dataBack.CANacondaMessage_queue
        self.comport = dataBack.comport
        self.args = dataBack.args

    def getmessage(self):
        # emit the startHourGlass here
        #open a serial connection at 57600 Baud
        try:
            serialCAN = serial.Serial(self.comport, 57600)
            # self.comport is the com port which is opened
        except:
            #self.mainwindow.comportUnavailable()
            pass
        else:
            # compiles a regular expression to parse both the short
            # and long form messages as defined in the CAN-USB manual
            self.regex = re.compile(r"\s*(?:t([0-9a-fA-F]{3})|T([0-9a-fA-F]{8}))(\d)((?:[0-9a-fA-F][0-9a-fA-F]){0,8})((?:[0-9a-fA-F][0-9a-fA-F]){2})?")
            # determines that the serial port has opened correctly
            temp = None
            # initializes the CAN-USB device to 250Kbit/s which is the
            # maritime standard. if the CAN device is not closed
            # properly this may take up to ~20 seconds to clear the
            #serial buffer of old messages
            temp = serialCAN.read()
            while(temp != (b'\r' or b't' or b'T')):
                time.sleep(.2)
                #initialize the CAN-USB device at 250Kbits/s
                serialCAN.write(b'S5\r')
                #print(temp)
                temp = serialCAN.read()
            time.sleep(1)
            #Opens the CAN port to begin reciveing messages
            serialCAN.write(b'O\r')
            time.sleep(1)
            #Sets the CAN port to disable timestamps
            serialCAN.write(b'Z0\r')
            time.sleep(1)
            i = 0

            # Make cursor go back to normal
            self.stopHourGlass.emit()
            
            while(1):
                self.serialParse(serialCAN)

    def serialParse(self, serialCAN):
        dataBack = self.dataBack
        rawmsg, matchedmsg = self.getRegex(serialCAN)
        newCANacondaMessage = CANacondaMessage()
        if matchedmsg:
            CANacondaMessageParse(newCANacondaMessage, matchedmsg,
                                  rawmsg, dataBack)
            # use dataBack.nogui?
            self.dataBack.CANacondaMessage_queue.put(newCANacondaMessage)
            self.parsedMsgPut.emit()

            # If not present already, add the message's filter
            # and field name to the dataBack.messagesSeenSoFar dict,
            # and emit a signal.
            if (newCANacondaMessage.name not in self.dataBack.
                messagesSeenSoFar and newCANacondaMessage.name is not ''):
                #pyqtrm()
                #pdb.set_trace()
                self.dataBack.messagesSeenSoFar[
                    newCANacondaMessage.name] = []
                for field in newCANacondaMessage.body:
                    self.dataBack.messagesSeenSoFar[newCANacondaMessage.
                                                    name].append(field)
                self.messageUp.emit()

    def getRegex(self, serialCAN):
        character = None
        rawmsg = b""
        # Reads in characters from the serial stream until
        # a carriage return is encountered
        while(character != (b'\r' or '\r')):
            character = serialCAN.read()
            # appends the newly read character to
            # the message being built
            rawmsg += bytes(character)
        rawmsg = rawmsg.decode('utf-8')
        matchedmsg = self.regex.match(rawmsg)
        return rawmsg, matchedmsg
