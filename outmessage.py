
'''
outmessage.py
Build the output string for the message stream.
For both the console mode and the GUI mode.
'''

import time
import pdb
from PyQt5.QtCore import pyqtRemoveInputHook as pyqtrm

# this is just a copy of the parseMessage function from canpython
# add boolean checks to match args for correct outmsg format
# Messages not specified in messages file still have a PGN number,
# which may or may not be valued. These PGN numbers will still
# be displayed.
def noGuiParse(dataBack, message):
    if message.name not in dataBack.messageInfo_to_fields:
        return
    # Build a text string that gets put to screen.
    outmsg = ""
    #datddaFound = False
    for field in message.body:
        if field in dataBack.messageInfo_to_fields[message.name]:
            break
    else:
        return
    dataFound = False
    if message.name:
        outmsg += "\n" + message.name
    if dataBack.displayList['pgn']:
        outmsg += "\nPGN: " + str(message.pgn)
    if dataBack.displayList['raw']:
        outmsg += "\n" + message.raw
    if message.ID:  # prevent execution of uninitialised message
        if dataBack.displayList['ID']:
            outmsg += "\nFilter ID: " + message.ID
        # if displayList is empty, display all:
        if dataBack.displayList['body']:
            for field in message.body:
                if field in dataBack.messageInfo_to_fields[message.name]:
                    if field:
                        dataFound = True
                    try:
                        outmsg += "\n" + field + ": " + '{0:3f}'.\
                                    format((message.body[field]))
                    except:
                        outmsg += "\n" + field + ": " + message.body[field]
    if dataFound:
        return outmsg


# For CSV output. First column is time stamp.
def noGuiParseCSV(dataBack, message):
    # A mapping dictionary from fields to array indices
    fieldIndices = dataBack.fieldIndices
    # An array initialized with null strings for populating later.
    lineData = [''] * (len(dataBack.csvDisplayList) + 1)
    dataFound = False
    # Populate lineData
    for field in message.body:
        if field in fieldIndices:   # field.name holds the complete name
                                    # of the field, including the name
                                    # of the message it's in.

            lineData[fieldIndices[field]] = str(message.body[field])
            # won't work because field.name is not part of message.body
            # message.body is a dictionary of {field.name: field.value}
            dataFound = True
    # Display message
    if dataFound:
        if dataBack.CSVtimeFlag:
            lineData[0] = "{0:0.5f}".format(time.time())
        return (','.join(lineData))


# This version of the output in CSV mode is used when the user
# gives the --zero or 'zero order hold' option. It uses a global
# dictionary whose values are either updated when new data is present
# or held over from the previous message when no data is present.
# Either way, a new message is output with all fields populated at
# every new message event.
def noGuiParseCSV_zero(dataBack, message):
    outmsg = ""
    # this list contains all the fields to be parsed,
    # passed in from the command line
    fieldList = dataBack.fieldList_CSV

    for field in message.body:
        if message.name in dataBack.messageInfo_to_fields:
            if field in dataBack.messageInfo_to_fields[message.name]:
                fieldList[field] = message.body[field]
    if dataBack.CSVtimeFlag:
        outmsg += "{0:0.5f}".format(time.time()) + ", "
    outmsg += (str([(fieldList[key]) for key in sorted(fieldList)])[1:-1])
    return (outmsg)


# good enough for now
def guiParseCSV(dataBack, message):
    # A mapping dictionary from fields to array indices
    fieldIndices = dataBack.fieldIndices
    # An array initialized with null strings for populating later.
    lineData = [''] * (len(dataBack.fieldIndices) + 1)
    dataFound = False
    # Populate lineData
    for field in message.body:
        if field in fieldIndices:   # field.name holds the complete name
                                    # of the field, including the name
                                    # of the message it's in.
            lineData[fieldIndices[field]] = str(message.body[field])
            # won't work because field.name is not part of message.body
            # message.body is a dictionary of {field.name: field.value}
            dataFound = True
    # Display message
    if dataFound:
        #if dataBack.CSVtimeFlag:
        lineData[0] = "{0:0.5f}".format(time.time())
        return (','.join(lineData))

