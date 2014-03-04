#!/usr/bin/env python

'''
This file is the top level implementation of the canpython script.
Under development:
    console mode
    GUI mode -> pyqt5 filters tree file

'''

# Commandline mode
import argparse
import pdb

# original imports from before refactor...
# some of these will have to be removed -- use IDE to find errors
import threading
import xml.etree.ElementTree as ET
import sys
from messageInfoParse import *
from backend import *
from Nmea2000_decode_encode import *
from setoptions import *
import outmessage

# Move this comment to appropriate file:
# This is a function which handles the parsing of an entire
# CAN message.
# Most of the actual parsing is done through repeated calls to
# parssection which parses each section of the message.
# Example parsed message:
# (None, '09FD0284', '8', 'D410002841FAFFFF', '5CCC')
# parsedmsg.groups() will give:
#      (1)             (2)           (3)          (4)       (5)
# header for 't'  header for 'T'     length       body      junk
# Note that the 'id' tag is referred to as 'header'


def main():

    parser = argparse.ArgumentParser()
    # first the development options --- remove later
    parser.add_argument('--fast', action="store_true",
            help="Load xmltest.txt and choose /dev/ttyUSB0 as port")
    parser.add_argument('--slow', action="store_true",
            help="Don't start the stream thread (nogui mode)")
    # for noGUI mode:
    parser.add_argument('--nogui', nargs=1, metavar='PORT',
            help="No GUI mode. Positional argument: port")
    parser.add_argument('-m', '--messages', metavar="File",
            help="Specify the messages file")
    parser.add_argument('--filter', metavar="FilterID", nargs=1,
            help="Comma-separated list, eg --filter='WSO100{airspeed[mph],\
                    wind_dir},DST800' float values must match precision")
    parser.add_argument('--display', nargs=1,
            help="Comma-separated list, eg: --display=ID,pgn,raw,body")
    parser.add_argument('--csv', action="store_true",
            help="Gives output in CSV format")
    parser.add_argument('--time', action="store_true",
            help="Time stamped output for CSV mode")
    parser.add_argument('--zero', action="store_true",
            help="Give zero-order hold output for CSV mode")
    parser.add_argument('--debug', action='store_true',
                        help='Add debug buttons in GUI mode')

    args = parser.parse_args()

    # Debug print statements
    if (args.fast):
        print("Fast debug mode")

    # create the dataBack singleton
    # command line arguments passed in
# refactor: choose message file in dataBack, not xmlimport
    dataBack = CanData(args)

    # begin nogui mode
    if args.nogui:
        # nogui imports
        import canport

        # '--filter' option must come with '--messages'
        if args.filter and not args.messages:
            print("\nYou are selectively displaying messages",
                "without specifying a way to parse CAN",
                "messages.\n\t(Hint: Use option -m)")
            return

        # import filters, and return a boolean value as 'filtersNotImpoted'
        fileName = dataBack.args.messages
        noMessagesImported = xmlImport(dataBack, args, fileName)

        # a typical usage might be something like:
        # ./canpython.py --nogui /dev/ttyUSB0 -m xmltest.txt --filter='WSO100{airspeed},WSO200{wind_dir=2,vel}' --slow

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
                print("setUnitsConversion failed")
                return

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
        if args.messages and not args.csv:
            print("Filters to be displayed: ",
                str(sorted(dataBack.messageInfoList))[1:-1])

        # create displayList
        if args.display and args.messages:
            for arg in args.display[0].split(','):
                dataBack.displayList[arg] = True
        else:
            dataBack.displayList['pgn'] = True
            dataBack.displayList['ID'] = True
            dataBack.displayList['body'] = True

        if noMessagesImported:
            print("Running CANaconda without messages specified,",
                "for raw message viewing")

        # For CSV mode:
        if args.csv:
            # Check argument syntax
            if not args.messages:
                print("Please specify a messages file.",
                    "Use option -m")
                return

            # Setup for the CSV display
            else:
                if args.time:
                    dataBack.CSVtimeFlag = True
                setDisplayCSVmode(dataBack)
        else:
            print("Opening connection to", dataBack.comport)

        # If --slow was given, halt program here.
        # Otherwise, start streaming messages.
        if not args.slow:
            # create the threading object
            canPort = canport.CANPort(dataBack)
            #start the thread
            serialThread = threading.Thread(target=canPort.getmessage)
            # find a way to intercept KeyBoardInterrupt exception
            # when quitting
            try:
                serialThread.start()
            except: 
                pass


######### GUI #########
    else:
        # Qt imports
        from PyQt5.QtWidgets import QApplication, QMainWindow, QStyleFactory
        import ui_mainwindow
        import canport_QT

        if (args.fast):
            # import the filters from xml
            xmlImport(dataBack, args, 'exampleMetaData.xml')
        # create the threading object
        # Note: this canport is different from
        # the one used in the console mode.
        # This should be fixed.
        dataBack.canPort = canport_QT.CANPort_QT(dataBack)
        dataBack.noGui = bool(args.nogui)  # aka FALSE

        # Start the serial thread if --fast was given as option
        if args.fast:
            serialThread = threading.Thread(target=dataBack.canPort.getmessage)
                                           # change to canport.py
            serialThread.daemon = True
            serialThread.start()

        # pyqt stuff
        app = QApplication(sys.argv)
        app.setStyle(QStyleFactory.create("Fusion"))
        #app.setQuitOnLastWindowClosed()
        #app.lastWindowClosed.connect(app.destroy)
        mainWindow = QMainWindow()
        ui = ui_mainwindow.Ui_MainWindow()
        # connect the signal to the slot
        if args.fast:
            dataBack.canPort.parsedMsgPut.connect(ui.updateUi)
        # call setupUi with the necessary objects
        ui.setupUi(mainWindow, dataBack)
        # run the gui
        mainWindow.show()
        sys.exit(app.exec_())


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
