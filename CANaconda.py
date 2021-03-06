#!/usr/bin/env python3
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
This file is the top level implementation of the canpython script.
Both the CLI and GUI versions are launched from within this script.
'''

# Commandline mode
import argparse
import pdb

import threading
import xml.etree.ElementTree as ET
import sys
from messageInfo import *
from backend import *
from setoptions import *
import printmessage
from printmessage import ID, PGN, BODY, RAW


def main():
    parser = argparse.ArgumentParser()
    parserInit(parser)
    args = parser.parse_args()

    # Create the dataBack singleton
    try:
        dataBack = CanData(args)
    except Exception as e:
        print("ERROR in data backend: " + str(e))
        return
    # If the user doesn't want a GUI, run only the required things
    if args.nogui:
        try:
            canacondaNoGuiInit(dataBack)
        except Exception as e:
            print("ERROR: " + str(e))
            return

        # Check to see if the user has given a --canbaud arg, and if the arg is valid
        from canport import BAUDLIST
        try:
            canbaudString = args.canbaud[0]
        except TypeError:
            canbaudString = None
        if canbaudString:
            if canbaudString not in BAUDLIST:
                print("Choose a baud from", ", ".join(BAUDLIST))
                return
        else:
            # 250k is the default value
            canbaudString = '250k'
        ErrorType = pyserialNoGuiInit(dataBack, canbaudString)

        # Make sure the serial port was initialized properly before settings things up to read from
        #  it.
        if type(ErrorType) != int:
            pyserialNoGuiRun(dataBack)
        # Later on when we define the different error cases for serial init, we can reportback to
        # the user here.
        elif ErrorType == dataBack.canPort.ERROR_NO_DATA:
            print("ERROR: No data is being transmitted on bus. Are CAN nodes connected?")
        elif ErrorType == dataBack.canPort.ERROR_NO_CONNECT:
            print("ERROR: Could not open connection to {0}. Is port already in use?".format(dataBack.comport))
        elif ErrorType == dataBack.canPort.ERROR_TIMEOUT:
            print("ERROR: Could not open the CANusb device.")
        elif ErrorType == dataBack.canPort.ERROR_BAUD:
            print("ERROR: Could not set the baud rate on CAN bus.")

    # Otherwise we launch our GUI versions of this code.
    else:
        pyserialGuiInit(dataBack)
        canacondaGuiRun(dataBack)


def parserInit(parser):
    # for noGUI mode:
    parser.add_argument('--nogui', action='store_true',
            help="CLI mode")
    parser.add_argument('-p', '--port', nargs=1, metavar='PORT',
            help="Choose port from command line (required for CLI, optional for GUI)")
    parser.add_argument('-m', '--metadata', metavar="File",
            help="Specify the messages file")
    parser.add_argument('--filter', metavar="FilterID", nargs=1,
            help="Comma-separated list (CLI), eg --filter='WSO100{airspeed[mph],\
                    wind_dir},DST800' float values must match precision")
    parser.add_argument('--display', nargs=1,
            help="Comma-separated list, eg: --display=ID,pgn,raw,body")
    parser.add_argument('--csv', action="store_true",
            help="Gives output in CSV format (CLI)")
    parser.add_argument('--time', action="store_true",
            help="Time stamped output for CSV mode (CLI)")
    parser.add_argument('--zero', action="store_true",
            help="Give zero-order hold output for CSV mode (CLI)")
    parser.add_argument('--debug', action='store_true',
                        help='Add debug buttons in GUI mode')
    parser.add_argument('--canbaud', nargs=1,# metavar='canbaud',
            help="Choose a baud for the CAN to USB device. Example: 100k, 125k, 250k, etc.\
                    Defaults to 250k, the maritime standard")


def canacondaNoGuiInit(dataBack):
    args = dataBack.args
    # '--filter' option must come with '--messages'
    if args.filter and not args.metadata:
        print("\nYou are selectively displaying messages",
            "without specifying a way to parse CAN",
            "messages.\n\t(Hint: Use option -m)")
        return

    # import filters, and return a boolean value as 'filtersNotImpoted'
    fileName = dataBack.args.metadata
    if fileName is not None:
        xmlImport(dataBack, fileName)

    # a typical usage might be something like:
    # ./canpython.py --nogui /dev/ttyUSB0 -m xmltest.txt --filter='WSO100{airspeed},WSO200{wind_dir=2,vel}'

    if args.filter:
        filterString = args.filter[0]
        # createListAndDict: load filters and syntax checking.
        # After this call, the messageInfo_to_fields is created
        # and the values are lists of fields to be displayed.
        # Also messageInfoList is a list that contains all the
        # keys that are in messageInfo_to_fields.
        if not createListAndDict(dataBack, filterString):
            print("createListAndDict failed")
            return

        # The following function takes the messageInfo_to_fields
        # and checks for empty list in the dictionary values.
        # If empty, populate list with all the fields in the
        # meta data file.
        setFieldsFilterFieldDict(dataBack)

        # load units conversion and syntax checking:
        # Units conversion is set in field.unitsConversion,
        # which interacts with the backend.conversionMap
        # dictionary when a message is being parsed.
        if not setUnitsConversion(dataBack):
            exit()

        # If the user has chosen to filter the data
        # by value, this function handles those
        # arguments:
        setFilterByValue(dataBack)

        # Now that the filters are set,
        # make a copy of the messageInfo_to_fields
        # for displaying the header in CSV mode
        dataBack.messageInfo_to_fields_units = dataBack.messageInfo_to_fields.copy()

    # No --filter argument given, just display all the messages
    else:
        createListAndDict_noFilter(dataBack)

    # refactor:
    if args.metadata and not args.csv:
        print("Filters to be displayed: ",
            str(sorted(dataBack.messageInfoList))[1:-1])

    # create displayList
    if args.display and args.metadata:
        for arg in args.display[0].split(','):
            dataBack.displayList[arg] = True
    else:
        dataBack.displayList[PGN] = True
        dataBack.displayList[ID] = True
        dataBack.displayList[BODY] = True

    noMessagesImported = not dataBack.messageInfoFlag
    if noMessagesImported:
        print("Running CANaconda without messages specified,",
            "for raw message viewing")

    # For CSV mode:
    if args.csv:
        # Check argument syntax
        if not args.metadata:
            print("Please specify a messages file.",
                "Use option -m")
            return

        # Setup for the CSV display
        else:
            setDisplayCSVmode(dataBack)
    else:
        print("Opening connection to", dataBack.comport)
  

def pyserialNoGuiInit(dataBack, canbaudString):
    from canport import CANPortCLI
    # Create a threading object that communicates with the serial bus
    dataBack.canPort = CANPortCLI(dataBack)
    # initialize the serial connection to the CANusb device

    from canport import BAUDMAP
    canbaud = BAUDMAP[canbaudString]
    serialCAN = dataBack.canPort.pyserialInit(57600, canbaud)

    # If we successfully initialized the CANusb hardware and connected,
    # start up a thread for processing messages
    if type(serialCAN) != int:
        dataBack.serialThread = threading.Thread(target=dataBack.canPort.getMessages, args=(serialCAN,))

    # Create another threading object that will encode and decode CAN messages
    from CanDataTranscoder import CanTranscoderCLI
    canTranscoder = CanTranscoderCLI(dataBack)
    dataBack.transcoderThread = threading.Thread(target=canTranscoder.CanTranscoderRun)

    # Pass through the return value from pyserialInit()
    # FIXME: find a way to intercept KeyBoardInterrupt exception when quitting
    return serialCAN

def pyserialNoGuiRun(dataBack):
    try:
        dataBack.transcoderThread.start()
        dataBack.serialThread.start()

    # This is the error thrown if serialThread did not initialize
    except AttributeError:
        pass

# Create the serial thread. Don't call .start() yet, since this 
# must be done after the GUI thread has started and user input
# is obtained for certain parameters.
def pyserialGuiInit(dataBack):
    # create the threading object
    from canport import CANPortGUI
    dataBack.canPort = CANPortGUI(dataBack)
    dataBack.noGui = bool(dataBack.args.nogui)  # aka FALSE

    from CanDataTranscoder import CanTranscoderGUI
    dataBack.canTranscoderGUI = CanTranscoderGUI(dataBack)


def canacondaGuiRun(dataBack):
    # Call the wrapper class that inserts widgets into the pyuic5-generated GUI code from Qt Designer
     import canaconda_GUI
     ui = canaconda_GUI.Ui_CANaconda_GUI(dataBack)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
