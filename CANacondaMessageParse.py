
'''
For adding the data to the CANacondaMessage object.
CANacondaMessageParse
parseRaw
pgnSet
hexToVal
'''
from backend import conversionMap
from Nmea2000_decode_encode import Iso11783Decode
import pdb

# The goal here is to fill in all of the following:
# name, pgn, id, body (aka 'payload'), raw
def CANacondaMessageParse(self, match, rawmsg, dataBack):
    self.pgn = pgnSet(match)
    self.raw = parseRaw(rawmsg)
    if match.group(1):
        self.ID = match.group(1)
    elif match.group(2):
        self.ID = match.group(2)

#    # Find the metadata that matches the parsed message
#    if message_id in dataBack.id_to_name or str(self.pgn) in\
#                     dataBack.pgn_to_name:
#        # Give the message the ID
#        self.ID = message_id

    # Now that we have the current message's ID, raw, and pgn values,
    # find and assign the message's name to self.name
    for key in dataBack.messages.keys():
        if ((dataBack.messages[key].pgn == str(self.pgn)) or 
                 (dataBack.messages[key].id == self.ID)):
            self.name = dataBack.messages[key].name
            break
    # If self.name is still None, then the  message is not in the xml 
    # file and is not of interest:
    if not self.name:
        return

    # If the metadata did not give an ID, we need to add it for completeness:
#    if self.ID not in dataBack.id_to_name:
#        try:
#            dataBack.messages[dataBack.pgn_to_name[
#                                        str(self.pgn)]].id = self.ID
#        except:
#            pass
#        dataBack.id_to_name[self.ID] = dataBack.messages[
#                        dataBack.pgn_to_name[str(self.pgn)]].name

    # make a pointer to the filter. First, try with filter ID. Then PGN.
    try:
        currentMessage = dataBack.messages[dataBack.id_to_name[self.ID]]
    except:
        currentMessage = dataBack.messages[dataBack.pgn_to_name[str(self.pgn)]]
        
    # grab the values from the data field(s)
    for fieldName in currentMessage.fields:
        dataFilter = currentMessage.fields[fieldName]
        try: # may cause an assertion error that we can ignore
            self.body[dataFilter.name] = getPayload(dataFilter, 
                                                    currentMessage, match)
        except:
            pass
    # The CANacondaMessage has now been created.

########### GUI related #################################
    # Add data to the headers and messages sets
    dataBack.headers.add(self.ID)
    dataBack.pgnSeenSoFar.add(self.pgn)

    # Add a copy of the message to the self.messageRecord dict.
    dataBack.latest_CANacondaMessages[self.name] = self.body


# Parse the message without any information from the metadata file
# This just gives a fancy way of displaying hex data from the
# serial stream.
def parseRaw(rawmsg):
    raw = "Head: 0x"
    if (rawmsg[0] == 'T'):
        raw += rawmsg[1:9] + ", Body: 0x["
    n = 9
    while (n < 9 + 2 * int(rawmsg[9])):
        raw += rawmsg[n:n + 2] + " "
        n += 2
    raw = raw[:-1] + "]"
    return raw


# Use the Iso11783 decoding routine to extract the PGN from
# the CAN ID field.
def pgnSet(match):
    pgn = None
    if match.group(1):
        [pgn, x, y, z] = Iso11783Decode(match.group(1))
    else:
        [pgn, x, y, z] = Iso11783Decode(match.group(2))
    return pgn


# hexToVal
# Function paramaters: hexData is the raw hex value of the message body
# The return value is the CAN message payload
def hexToVal(hexData, dataFilter):
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

    #shifting indicies to right orentated
    start = len(binaryData) - offset
    stop = len(binaryData) - (length + offset)

    datasect = binaryData[stop: start]
    # from the offset to the end of size is selected to seperate
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
    if(endian == "little" and signed == "no"):
        value = int.from_bytes(dataset, byteorder='little', signed=False)

    #little endian signed
    elif(endian == "little" and signed == "yes"):
        value = int.from_bytes(dataset, byteorder='little', signed=True)

    #big endian signed
    elif(endian == "big" and signed == "yes"):
        value = int.from_bytes(dataset, byteorder='big', signed=True)

    #big endian unsigned
    elif(endian == "big" and signed == "no"):
        value = int.from_bytes(dataset, byteorder='big', signed=False)

    else:
        print("not valid")

    return value



        # make a pointer to the field
def getPayload(dataFilter, currentMessage, match):
    msgBody = match.group(4)
    value = hexToVal(msgBody, dataFilter)
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
            # at the top of this file.
                value += float(conversionMap[dataFilter.units][
                                        dataFilter.unitsConversion][1])
                value *= float(conversionMap[dataFilter.units][
                                        dataFilter.unitsConversion][0])
                value += float(conversionMap[dataFilter.units][
                                        dataFilter.unitsConversion][2])
            except KeyError:
                pass

    # Check for data.byValue
    if dataFilter.byValue:
        #pdb.set_trace()
        if value not in dataFilter.byValue:
            value = ''

    return value

        # Add the value to the Message.body dictionary
