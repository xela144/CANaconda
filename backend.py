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
This file contains the CanData class, which is implemented as a singleton
'dataBack' at run-time.
'''

import queue
import CANaconda

# displayList
from outmessage import ID, PGN, BODY, RAW

# conversionMap is a mapping of valid base units to converted units.
# For each base units, a map to the new units will be given by the
# inner dicionary's tuple as follows:
# newValue = (oldValue+tuple(1))*tuple(0)+tuple(2)
# For the console mode, if the user tries an invalid units conversion,
# ie from radians to mph, an error message is given and program halts.
# For GUI mode, options for changing units are given in a
# combo box populated from the conversionMap dictionary.

conversionMap = {
    # Velocity units
    'MPS': {'MPS': (1, 0, 0), 'MPH': (2.237, 0, 0), 'KNOT': (1.944, 0, 0)},
    'MPH': {'MPS': (0.447, 0, 0), 'MPH': (1, 0, 0), 'KNOT': (0.869, 0, 0)},
    'KNOT': {'MPS': (0.5144, 0, 0), 'MPH': (1.151, 0, 0), 'KNOT': (1, 0, 0)},

    # Angle units
    'RAD': {'RAD': (1, 0, 0), 'DEG': (57.3, 0, 0)},
    'DEG': {'RAD': (0.0175, 0, 0), 'DEG': (1, 0, 0)},

    # Temperature units
    'K': {'K': (1, 0, 0), 'CEL': (1, -273.15, 0), 'FAR': (1.8, -273.15, 32)},
    'FAR': {'K': (0.556, -32.0, 273.15), 'CEL': (0.556, -32, 0),
            'FAR': (1, 0, 0)},
    'CEL': {'K': (1, 273.15, 0), 'CEL': (1, 0, 0), 'FAR': (1.8, 0, 32)}
    }


class CanData():
    def __init__(self, args):
        # Store args from argparse:
        self.args = args
        # An array which contains all of the most recent messages for
        # each type seen so far
        self.messagesSeenSoFar = {}

        #A flag to indicate if loging is enabled
        self.logflag = 0
        #The file where loging will takeplace if it is turned on
        self.logfile = None
        #This defines which COM port is used
        if args.nogui:
            if not bool(args.port):
                raise Exception("Please specify a port (using --port option)")
            else:
                self.comport = args.port[0]
        else:
            self.comport = None

        # All of the current messages applied by the user.
        # Populated with messageInfo objects
        self.messages = {}

        # threading.Thread objects
        self.serialRxThread = None
        self.serialTxThread = None

        # Multithreading queue for passing decoded CAN messages
        self.CANacondaRxMsg_queue = queue.Queue()

        # Multithreading queue for receiving messages from the serial port
        self.CANacondaRx_TranscodeQueue = queue.Queue()

        # Multithreading queue for transmitting messages tot he bus
        self.CANacondaTxMsg_queue = queue.Queue()

        # Storage for the outgoing message in hex, ascii format (for serial):
        self.asciiBucket = '' 

        # A nested dictionary of 'messageInfo'->'field'->'latest message'
        self.latest_CANacondaMessages = {}

        ## message stream window:
        # This flag is used so that raw data and XML defined messages don't
        # mix on screen
        self.messageInfoFlag = False

        # For the hourglass not to be triggered twice:
        self.alreadyStreaming = False
        
        # GUI flag
        if args.nogui:
            self.nogui = True
        else:
            self.nogui = False

        # For nogui mode:
        # Used to set the displaylist for CSV mode, and
        # to print a message once at consoleMode launch.
        self.messageInfoList = []

        # For noGUI mode: Dictionary of filter and values to be displayed
        self.messageInfo_to_fields = {}

        # For display in GUI. Change name
        self.container = {}

        # For matching message ID to messageInfo self.messages, which uses
        # 'name' as key
        # e.g. id_to_name = {'091234F': 'WSO500'}
        # This map is set at program launch.
        self.id_to_name = {}

        # For matching message PGN to name, as in previous example.
        self.pgn_to_name = {}

        # We will use this to give an ID while encoding messages
        self.IDencodeMap = {}
        
        # For noGUI+CSV mode: Dictionary of messageInfo and values with units,
        # if any.
        # This map is set once at program launch, and accessed in
        # Message.__init__().
        self.messageInfo_to_fields_units = {}

        # For noGUI+CSV mode: all the fieds that must be displayed
        self.fieldList_CSV = {}

        # A dictionary object for counting the frequencies of message
        # message transmission. GUI only.
        self.frequencyMap = {}
        self.latest_frequencies = {}

        # defaults to display pgn, ID, body
        self.displayList = {PGN: False, RAW:  False,
                            ID:  False, BODY: False}

        # A dictionary mapping for the Display By Value mode
        # not used
        # self.displayByValue_dict = {}

        # For displaying column titles in csv mode
        self.csvDisplayList = {}

        # For CSV output, an index mapping dictionary
        self.fieldIndices = {}

        # For CSV output in GUI mode
        self.GUI_CSVflag = False

        # For raw output in GUI mode
        self.GUI_rawFlag = False

    # when a messageInfo is removed from the treeview:
    # deletes from memory, but does not change xml file.
    # Possible alternative: remove from ui.treeWidget instead of here.
    def removeMessageInfo(self, target):
        for messageInfo in self.messages:
            if messageInfo.name == target:
                self.messages.remove(messageInfo)
                del messageInfo

    
    def __str__(self):
        return str(self.messages)
