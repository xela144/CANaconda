
'''
For adding the data to the CANacondaMessage object.
CANacondaMessageParse -- main parser
parseRaw  -------------- gets raw hex  
pgnSet ----------------- gets parameter group number
hexToVal --------------- converts the payload data

A Regex Match object is passed to this parsing function contained in this file.
Example parsed message:
(None, '09FD0284', '8', 'D410002841FAFFFF', '5CCC')
parsedmsg.groups() will give:
     (1)               (2)            (3)          (4)       (5)
header for 't'    header for 'T'     length        body      junk


Note that the 'id' tag is sometimes referred to as 'header'
'''
from backend import conversionMap
from Nmea2000_decode_encode import Iso11783Decode
from queue import Queue
import time
import pdb

from PyQt5.QtCore import pyqtRemoveInputHook as pyqtrm




# The goal here is to fill in all of the following:
# name, pgn, id, body (aka 'payload'), raw
def CANacondaMessageParse(self, match, rawmsg, dataBack):
    self.pgn = pgnSet(match)
    self.raw = parseRaw(rawmsg)
    if match.group(1):
        self.ID = match.group(1)
    elif match.group(2):
        self.ID = match.group(2)

    # Now that we have the current message's ID, raw, and pgn values,
    # find and assign the message's name to self.name
    for key in dataBack.messages.keys():
        if dataBack.messages[key].pgn == str(self.pgn) or dataBack.messages[key].id == self.ID:
            self.name = dataBack.messages[key].name
            break
    # If self.name is still None, then the  message is not in the xml 
    # file and is not of interest:
    if not self.name:
        return

    # make a pointer to the filter. First, try with filter ID. Then PGN.
    try:
        currentMessage = dataBack.messages[dataBack.id_to_name[self.ID]]
    except:
        currentMessage = dataBack.messages[dataBack.pgn_to_name[str(self.pgn)]]
        
    # grab the values from the data field(s)
    for fieldName in currentMessage.fields:
        dataFilter = currentMessage.fields[fieldName]
        try: # may cause an assertion error that we can ignore
            payLoadData = getBodyFieldData(dataFilter, currentMessage, match)
            self.body[dataFilter.name] = payLoadData
        except:
            pass

    # Now to calculate message frequency:
    if self.name not in dataBack.frequencyMap:
        dataBack.frequencyMap[self.name] = Queue()
    else:
        dataBack.frequencyMap[self.name].put(time.time())

    # If the first element(s) in the queue is/are older than 5 seconds, remove:
    if dataBack.frequencyMap[self.name].qsize() > 0:
        while time.time() - dataBack.frequencyMap[self.name].queue[0] > 5.0:
            null = dataBack.frequencyMap[self.name].get()
            if dataBack.frequencyMap[self.name].empty():
                break
    # Division by 5 now gives us a running average
    self.freq = dataBack.frequencyMap[self.name].qsize()/5.0

    # The CANacondaMessage has now been created.

########### GUI related #################################
    # Add data to the headers and messages sets
    dataBack.headers.add(self.ID)
    dataBack.pgnSeenSoFar.add(self.pgn)

    # Add a copy of the CANacondaMessage to the 'latest_messages' dictionary:
    dataBack.latest_CANacondaMessages[self.name] = self.body

    # Add the frequency to the 'latest_frequencies' dictionary:
    dataBack.latest_frequencies[self.name] = self.freq
    
    # Make the frequency calculation and add to CANacondaMessage object:
    # dataBack.frequencyMap[self.name].qsize()

# Parse the message without any information from the metadata file
# This just gives a fancy way of displaying hex data from the
# serial stream.
def parseRaw(rawmsg):
    # Process a standard CAN frame
    if rawmsg[0] == 't':
        head = rawmsg[1:4]
        dataLength = 2 * int(rawmsg[4], 16) # Because it takes 2 hex chars to represent a byte
        data = rawmsg[5:5+dataLength]
    # And an extended CAN frame message
    elif rawmsg[0] == 'T':
        head = rawmsg[1:9]
        dataLength = 2 * int(rawmsg[9], 16) # Because it takes 2 hex chars to represent a byte
        data = rawmsg[10:10+dataLength]
    # And don't do anything for any other message
    else:
        return ""

    # Now split our data every 2 characters
    dataSplit = [data[start:start + 2] for start in range(0, len(data), 2)]
    dataString = " ".join(dataSplit)

    return "Head: 0x{0}, Body: 0x[{1}]".format(head, dataString)


# Use the Iso11783 decoding routine to extract the PGN from
# the CAN ID field.
def pgnSet(match):
    pgn = None
    if match.group(1):
        [pgn, x, y, z] = Iso11783Decode(match.group(1))
    elif match.group(2):
        [pgn, x, y, z] = Iso11783Decode(match.group(2))
    return pgn


# Function parameters: hexData is the raw hex value of the message body
# dataFilter is the CAN message specification given in the meta data by the user.
# The return value is the CAN message payload, before filtering
def getPayload(hexData, dataFilter):
    # Variables used in this function:
    endian = dataFilter.endian
    signed = dataFilter.signed
    offset = dataFilter.offset
    length = dataFilter.length

    # Strip the time stamp off the end of the message if it is there
    hexData = hexData[0:2 * length]

    assert(length == len(hexData))
    count = len(hexData)
    dataflipped = ""
    while count > 0:
        # this flips the order of all the hex bits to switch from little
        # to big endian
        dataflipped = dataflipped + hexData[count - 2] + hexData[count - 1]
        count = count - 2

    binaryData = bin(int(dataflipped, 16))  # converts the data to binary
    binaryData = (4 * len(hexData) - (len(binaryData) - 2)) * '0'\
                                                            + binaryData[2:]
    # This prepends the number of dropped 0's to the front of the binary

    #shifting indices to the right
    start = len(binaryData) - offset
    stop = len(binaryData) - (length + offset)

    datasect = binaryData[stop: start]
    # from the offset to the end of size is selected to separate
    # the relevant data

    dataset = []
    while len(datasect) > 8:
    # This code converts from binary to a set of integers for the
    # int.from_bytes() function to use
        highdata = datasect[-8:]
        datasect = datasect[:-8]
        dataset.append(int(highdata, 2))
    dataset.append(int(datasect, 2))

    #little endian unsigned
    if endian == "little" and signed == "no":
        value = int.from_bytes(dataset, byteorder='little', signed=False)

    #little endian signed
    elif endian == "little" and signed == "yes":
        value = int.from_bytes(dataset, byteorder='little', signed=True)

    #big endian signed
    elif endian == "big" and signed == "yes":
        value = int.from_bytes(dataset, byteorder='big', signed=True)

    #big endian unsigned
    elif endian == "big" and signed == "no":
        value = int.from_bytes(dataset, byteorder='big', signed=False)

    else:
        print("not valid")

    return value



# Retrieves the data field from the CAN message body and does any units 
# conversion and/or filtering specified by the user during runtime.
def getBodyFieldData(dataFilter, currentMessage, match):
    msgBody = match.group(4)
    value = getPayload(msgBody, dataFilter)
    # Check for invalid data.
    # 0xFFFF is the 'invalid data' code
    if value == 65535:
        value = 'NaN'

    # Normal data processing is the default case:
    else:
        value *= dataFilter.scaling
        if dataFilter.unitsConversion:
            try:
            # Data conversion done by adding, multiplying, then
            # adding the tuple entries found in the conversion map
            # in backend.py
                value += float(conversionMap[dataFilter.units][
                                        dataFilter.unitsConversion][1])
                value *= float(conversionMap[dataFilter.units][
                                        dataFilter.unitsConversion][0])
                value += float(conversionMap[dataFilter.units][
                                        dataFilter.unitsConversion][2])
            except KeyError:
                pass

    # Last but not least, if we are doing a 'filterByValue':
    if dataFilter.byValue:
        if value not in dataFilter.byValue:
            value = ''
    return value
