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
from printmessage import *
from backend import conversionMap
from Nmea2000 import Iso11783Decode

# Constants
from messageInfo import CAN_FORMAT_EXTENDED

# A list of CanUSB commands for setting baudrates
BAUDLIST = ['10k', '20k', '50k', '100k', '125k', '250k', '500k', '800k', '1M']

# A dictionary map from baudrate to CanUSB set commands
BAUDMAP = {'10k':b'S0', '20k':b'S1', '50k':b'S2', '100k':b'S3', '125k':b'S4', '250k':b'S5', '500k':b'S6', '800k':b'S7', '1M':b'S8'}

# An inverse dictionary of the previous
MAPBAUD = dict(zip(BAUDMAP.values(), BAUDMAP.keys()))

# Carriage return command for CanUSB
CR = b'\r'

# Open command for CanUSB
OPEN = b'O\r'

# Close command for CanUSB
CLOSE = b'C\r'

# CanPort is the thread which handles direct communication with the CAN device.
# CanPort initializes the connection and then receives and parses standard CAN
# messages. These messages are then passed to the CanTranscoder thread for parsing
# into CanMessage objects.
class CANPort():
    '''
    Error constants to be returned by pyserialInit():
    ERROR_NO_DATA    No data being transmitted.
    ERROR_NO_CONNECT Could not open serial port
    ERROR_TIMEOUT    Timeout in sending the 'O' command to CANusb device
    ERROR_BAUD       Could not set the baud rate for CAN bus
    SUCCESS          No errors
    '''
    ERROR_NO_DATA, ERROR_NO_CONNECT, ERROR_TIMEOUT, ERROR_BAUD, SUCCESS = range(5)

    # Set the timeout (in seconds) for connecting to the CANusb hardware.
    TIMEOUT = 5

    def __init__(self, dataBack):
        self.dataBack = dataBack
        self.CANacondaRx_TranscodeQueue = dataBack.CANacondaRx_TranscodeQueue
        self.comport = dataBack.comport
        self.args = dataBack.args
        # This flag should prevent executing Parsing code unless it is True
        self.live = False
        # A string that indicates the current baudrate
        self.canBaudRate = ''

    # Opens a serial connect, creates a regex parser, and initializes the CANusb hardware
    def pyserialInit(self, baudrate=57600, canbaud=BAUDMAP['250k']):
        #opens a serial connection called serialCAN on COM? at 57600 Baud
        try:
            serialCAN = serial.Serial(self.comport, baudrate, timeout=3, writeTimeout=0)
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
            # (In practice, looks like we're expecting a 2.) Also, do this at least 10 times
            # because the device is picky. Even then sometimes it does not work
            i = 0
            while i < 10:
                val = serialCAN.write(CLOSE)
                if val != 2:
                    return CANPort.ERROR_NO_CONNECT
                i += 1
                time.sleep(.01)

            StatusMsg = self.CanUSBinit(serialCAN, canbaud)
            if StatusMsg != CANPort.SUCCESS:
                return StatusMsg
            else: 
                # Set the baudrate of the object so that we can access it later
                self.canBaudRate = MAPBAUD[canbaud]

            StatusMsg = self.CanUSBopen(serialCAN)
            if StatusMsg != CANPort.SUCCESS:
                return StatusMsg

            # Finally, if we have made it to here, the serialCAN object was created successfully
            # and the CanUSB device is ready for read/write operations
            self.live = True
            print("serialCAN good")
            return serialCAN

    def changeCanUSBbaud(self, serialCAN, newBaud):
        self.live = False
        # First close the device, otherwise setting a new baud rate is
        # not possible. If we don't do this 10 times, CanUSB barfs on us.
        # Then the Python threading module barfs on us too.
        i = 1
        while i < 10:
            i +=1
            val = serialCAN.write(CLOSE)
            if val != 2:
                return CANPort.ERROR_NO_CONNECT
            time.sleep(.01)
        # Set the CanUSB baud rate to the new value
        StatusMsg = self.CanUSBinit(serialCAN, newBaud)
        if StatusMsg != CANPort.SUCCESS:
            return StatusMsg
        else: 
            # Set the baudrate of the object so that we can access it later
            self.canBaudRate = MAPBAUD[newBaud]
        # Open the CanUSB device once more
        StatusMsg = self.CanUSBopen(serialCAN)
        if StatusMsg != CANPort.SUCCESS:
            return StatusMsg
        # Succesfully changed the CanUSB baud
        self.live = True
        return CANPort.SUCCESS

    # Initialize the CANusb hardware. 'serialCAN' is a class instance of CANPort
    def CanUSBinit(self, serialCAN, canbaud):
        # Start a timer to see if initialization has taken too long, erroring out in that case.
        start = time.time()
        setupBytes = canbaud + CR
        # Now keep looping until we've successfully configured the CANusb hardware.
        try:
            temp = serialCAN.read()
        except serial.serialutil.SerialException:
            self.CanUSBinit(serialCAN, canbaud) # hahaha
        while temp != CR:
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
        print("canusb good")
        return CANPort.SUCCESS

    # CanUSBopen. CanUSB flags have been set, now send the command for the device 
    # to open its connection over serial.
    def CanUSBopen(self, serialCAN):
        # Open the CAN port to begin receiving messages, using timer as above
        start = time.time()
        val = serialCAN.write(OPEN)
        while val != 2:
            val = serialCAN.write(OPEN)
            if time.time() - start - 5 > CANPort.TIMEOUT:
                return CANPort.ERROR_TIMEOUT
        return CANPort.SUCCESS

    # CANport thread repeat target is the getMessages function, which calls the actual
    # parsing function. If the serial connection is closed, for example, when changing the
    # baudrate, then we don't parse anything.
    # FIXME: serialCAN.closed being False may not be a sufficient condition, because when
    # serial is re-established, the CanUSB device does not immediately open...
    def getMessages(self, serialCAN):
        i = 0
        while True:
            i += 1
            if not self.live:
                # This return here should exit the getMessages thread
                return
            if self.live:
                # serialParse blocks thread
                self.serialParse(serialCAN)
                if self.dataBack.CANacondaTxMsg_queue.qsize() > 0:
                    time.sleep(.01)
                    while self.dataBack.CANacondaTxMsg_queue.qsize() > 0:
                        msg = self.dataBack.CANacondaTxMsg_queue.get_nowait() 
                        numbytes = serialCAN.write(bytes(msg, 'UTF-8'))
                        print("______________________________________", msg, numbytes, "bytes written to serial")


    # parse the serial string, create the CanMessage object, and print it.
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
        while character != (CR or '\r'):
            # Wrap the read() call in a try/except to catch possible serial port errors since we 
            # never check the state of the serial port after initial opening.
            try:
                character = serialCAN.read()
            except serial.serialutil.SerialException:
                return None
            # appends the newly read character to
            # the message being built
            if character == b'':
                print("           ", character, "character was received")
            rawmsg += bytes(character)
        bytesarray = rawmsg
        binascii.hexlify(bytesarray)
        rawmsg = rawmsg.decode('utf-8')
        print(bytesarray, rawmsg)
        matchedMsg = self.regex.match(rawmsg)
        return matchedMsg

    # Not is use at the moment because of massive resource usage.
    def sendMessages(self, serialCAN):
        while True:
            if not self.live:
                return
            if self.live:
                while self.dataBack.CANacondaTxMsg_queue.qsize() > 0:
                    msg = self.dataBack.CANacondaTxMsg_queue.get()
                    serialCAN.write(bytes(msg, 'UTF-8'))

    def getCanBaud(self):
        return self.canBaudrate


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
            matchedmsg = self.getMatchObject(serialCAN)
            newCanMessage = CanMessage()
            if matchedmsg: 
                self.dataBack.CANacondaRx_TranscodeQueue.put(matchedmsg)
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


def debugMode():
    from PyQt5.QtCore import pyqtRemoveInputHook
    pyqtRemoveInputHook()
    import pdb
    pdb.set_trace()
   
def input_thread(serialCAN, msg):
    while(1):
        time.sleep(.1)
        chars = input()
        try: 
            freq = float(chars)
            per = 1/freq
            startTime = time.time()
            # how many time periods have passed:
            cycle = 0
            while (1):
                # don't waste resources
                time.sleep(.01)
                # step function that increments with each time period
                curCycle = (time.time() - startTime) // per
                # If the step function has incremented, write to serial
                if curCycle > cycle:
                    cycle = curCycle
                    numbytes = serialCAN.write(bytes(msg, 'UTF-8'))
                    # Lawicel returns a 'z', and this should be discarded
                    #throwAway = serialCAN.read()
                    print("______________________________________", msg, numbytes, "bytes written to serial")
                    #print(throwAway)
            
        except ValueError:
            pass


if __name__ == "__main__":
    print("Debug Canport.py")
    print("Once streaming starts, you can enter a frequency")
    print("A message will be written to serial at that frequency")
    print("Only one frequency can be chosen per run")
    s = input('To run synchronous, type "s" (default to asynchronous) ')
    if s == 's':
        sync = True
    else:
        sync = False
    
    msg = 't0804FFFFFFFF'

    import argparse
    import binascii
    parser = argparse.ArgumentParser()
    from backend import CanData
    import time
    parser.add_argument('-p', '--port', nargs=1, metavar='PORT',help="Choose a port")
    args = parser.parse_args()
    args.nogui = True
    dataBack = CanData(args)
    serialThread = CANPort(dataBack) # Not really a thread
    serialCAN = serialThread.pyserialInit()
    if not sync:
        import _thread
        _thread.start_new_thread(input_thread,(serialCAN,msg))
    else:
        freq = float(input("Enter a frequency: "))
        per = 1/freq
        startTime = time.time()
        # how many time periods have passed:
        cycle = 0

    while(1):
        serialThread.serialParse(serialCAN)
        if sync:
            # step function that increments with each time period
            curCycle = (time.time() - startTime) // per
            # If the step function has incremented, write to serial
            if curCycle > cycle:
                cycle = curCycle
                print(cycle)
                numbytes = serialCAN.write(bytes(msg, 'UTF-8'))
                # Lawicel returns a 'z', and this should be discarded
                #throwAway = serialCAN.read()
                print("______________________________________", msg, numbytes, "bytes written to serial")
                #print(throwAway)
                #continue




