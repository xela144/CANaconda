'''
This code has the classes that contain all the backend data structures.
The messageInfo's and fields are already implemented.
The message class is to be used to capture data from the serial connection.
All message data will be accessed through this class
'''

import queue
import canpython
from Nmea2000_decode_encode import *
import pdb

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
        # Store arg from argparse:
        self.args = args
        #Headers is the set of all CAN IDs that have been seen
        self.headers = set()
        #pgn is the set of all PGNs that have been seen
        self.pgnSeenSoFar = set()
        # An array which contains all of the most recent messages for
        # each type seen so far
        self.messagesSeenSoFar = {}

        #A flag to indicate if loging is enabled
        self.logflag = 0
        #The file where loging will takeplace if it is turned on
        self.logfile = None
        #This defines which COM port is used
        if (args.nogui):
            self.comport = args.nogui[0]
        else:
            self.comport = None
        if (args.fast):
            self.comport = '/dev/ttyUSB0'

        # All of the current messages applied by the user.
        # Populated with messageInfo objects
        self.messages = {}

        # This queue is used to move data between threads
        self.CANacondaMessage_queue = queue.Queue()

        # A nested dictionary of 'messageInfo'->'field'->'latest message'
        self.latest_CANacondaMessages = {}

        ## message stream window:
        # This flag is used so that raw data and XML defined messages don't
        # mix on screen
        self.messageInfoFlag = False

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

        # For noGUI+CSV mode: Dictionary of messageInfo and values with units,
        # if any.
        # This map is set once at program launch, and accessed in
        # Message.__init__().
        self.messageInfo_to_fields_units = {}

        # For noGUI+CSV mode: all the fieds that must be displayed
        self.fieldList_CSV = {}

        # defaults to display pgn, ID, body
        self.displayList = {'pgn': False, 'raw': False,
                            'ID': False, 'body': False}

        # A dictionary mapping for the Display By Value mode
        # not used
        # self.displayByValue_dict = {}

        # For displaying column titles in csv mode
        self.csvDisplayList = {}

        # Add a time stamp in csv mode
        self.CSVtimeFlag = False

        # For CSV output, an index mapping dictionary
        self.fieldIndices = {}

        # For CSV output in GUI mode
        self.GUI_CSVflag = False

    # when a messageInfo is removed from the treeview:
    # deletes from memory, but does not change xml file.
    # Possible alternative: remove from ui.treeWidget instead of here.
    def removeMessageInfo(self, target):
        #pdb.set_trace()
        for messageInfo in self.messages:
            if messageInfo.name == target:
                self.messages.remove(messageInfo)
                del messageInfo


# This instances of this class are messageInfos created from
# the metadata file. This class gets instantiated during the
# call to xmlimport().
##
# xmlimport is responsible for creating entries in the
# dataBack.messages dictionary.
##
# The init function of this class includes an instantiation
# of the Field object, which becomes a key in the
# self.fields dictionary of this class.





# This class is used to create a Message object that results from a rawmessage
# being filtered in the canport object. Arguments passed in:
# dataBack is a CanData singleton
# rawmsg: format is utf-8
# match: regex match object
# Example parsed message:
# (None, '09FD0284', '8', 'D410002841FAFFFF', '5CCC')
# match.groups() will give:
#      (1)                 (2)           (3)          (4)        (5)
# header for 't'     header for 'T'     length        body       junk
# Note that the 'id' tag is referred to as 'header'

### Moved to CANacondaMessage.py and CANacondaMessageParse.py
