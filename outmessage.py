
'''
outmessage.py
Build the output string for the message stream.
For both the console mode and the GUI mode.
'''

import time

from messageInfo import CAN_FORMAT_STANDARD, CAN_FORMAT_EXTENDED

# FIXME: update this as more cases are discovered from use or by examining
# the packetlogger text
unitStringMap = {
        'MPS':'m/s', 'KNOT':'knots', 'MPH':'MPH',
        'RAD':'radians', 'DEG':'degrees',
        'CEL':'°C', 'FAR': '°F', 'K':'°K',
        'V':'V',
        '%':'%',
        'HPA':'hPa',
        'S':'s',
        'DAYS':'days'
        }

# displayList constants
ID, PGN, BODY, RAW = range(4)

# this is just a copy of the parseMessage function from canpython
# add boolean checks to match args for correct outmsg format
# Messages not specified in messages file still have a PGN number,
# which may or may not be valued. These PGN numbers will still
# be displayed.
def noGuiParse(dataBack, message):
    if message.name not in dataBack.messageInfo_to_fields:
        if dataBack.GUI_rawFlag and not dataBack.messageInfoFlag:
            return str(message)
        else:
            return
    # Build a text string called 'outmsg' that gets put to screen.
    outmsg = ""
    for field in message.body:
        if field in dataBack.messageInfo_to_fields[message.name]:
            break
    else:
        return
    dataFound = False
    # Print the timestamp of the message first, per user request
    if dataBack.args.time:
        outmsg += "\nTime: {0:0.3f}".format(time.time())
    
    # Append the message name as specified in the metadata
    if message.name:
        outmsg += "\n" + message.name
    
    # Then the PGN, if format is extended. First check format.
    Extended = dataBack.messages[message.name].format == CAN_FORMAT_EXTENDED
    if dataBack.displayList[PGN] and Extended:
        outmsg += "\nPGN: " + str(message.pgn)
    
    # Then the raw bytes of the message
    # Note: This is required for GUI operation and is always empty in the command-line interface.
    if dataBack.displayList[RAW]:
        outmsg += " " + str(message)
        dataFound = True
    
    # Append the message ID
    if dataBack.displayList[ID]:
        outmsg += "\nID: " + hex(message.id)

    # Finally, pretty-print the internal data if metadata exists for this message
    if dataBack.displayList[BODY]:
        for field in message.body:
            # If there is no match, message.body[field] will be None, so return.
            if message.body[field] == None:
                dataFound = False
                return

            if field in dataBack.messageInfo_to_fields[message.name]:
                if field:
                    dataFound = True
                try:
                    # If there is no unit conversion the payload is an int, and no decimals should be used.
                    # This flag will be used to sort this out
                    conversion = False
                    if dataBack.messages[message.name].fields[field].unitsConversion:
                        units = dataBack.messages[message.name].fields[field].unitsConversion
                        conversion = True
                    else:
                        units = dataBack.messages[message.name].fields[field].units
                    if conversion:
                        # Since there is a units conversion, there is a reason to format the body as a float
                        body = '{0.3f}'.format(message.body[field])
                    else:
                        # Since there is no units conversion, there is no reason to format the body
                        body = message.body[field]
                        #from PyQt5.QtCore import pyqtRemoveInputHook; pyqtRemoveInputHook(); import pdb; pdb.set_trace()
                    # We need to know how long to make the 'body' string, depending on 
                    # signed-ness, type (float or int) and scaling. Calculate that here.
                    #fieldInfo = dataBack.messages[message.name].fields[field]
                    #formatChar = getFormatForBody(fieldInfo.type, fieldInfo.scaling, fieldInfo.signed, fieldInfo.length, body)
                    prettyUnits = unitStringMap[units]
                    try:
                        outmsg += '\n{0}: {1:g} {2}'.format(field, body, prettyUnits)
                    except ValueError:
                        outmsg += '\n{0}: {1} {2}'.format(field, body, prettyUnits)
                # This will produce a KeyError for unspecified names or names that do
                # not need to be changed. Error won't show up as a stack trace since this
                # is in its own thread FIXME
                except:
                    outmsg += "\n{0}: {1}".format(field, message.body[field])
    if dataFound:
        return outmsg

# This will return the length of the payload string. Not being used for the moment.
def getFormatForBody(type, scaling, signed, length, body):
    if type != 'int':
        return length
    
    tot = 0

    # Add a spot for the negative sign
    if signed == 'yes':
        tot += 1
    
    # The actual length of the number
    tot += len(str(2**length))

    # Add a space for the decimal point
    if float(scaling) != 1:
        tot += 1
    print(tot)


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
        if dataBack.args.time:
            lineData[0] = "{0:0.3f}".format(time.time())
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
    if dataBack.args.time:
        outmsg += "{0:0.3f}".format(time.time()) + ", "
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
        lineData[0] = "{0:0.3f}".format(time.time())
        return (','.join(lineData))

