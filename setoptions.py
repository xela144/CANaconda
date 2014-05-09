'''
setoptions.py
Function definitions that are used during the setup of the console 
mode. Certain functions need to be re-written to make better use of
argparse module.
'''

import backend
import pdb


# create the display modifiers, if filters were specified.
# for NOGUI mode
## Refactor when dataBack.filters is a dict type.
def createListAndDict(dataBack, filterString):
    while filterString.find('{') > 0 or filterString.find(',') > 0:
        # A '{' found, but we don't know its relation to a ','
        if filterString.find('{') > 0:
            tuple = filterString.partition('{')

            # If the ',' comes before the next '{', then there is a toplevel
            # filter that comes before a lower level filter
            if ',' in tuple[0]:
                tuple1 = tuple[0].partition(',')
                # messageInfoList is used to print a message at console
                # mode launch and to create displayList_CSV
                dataBack.messageInfoList.append(tuple1[0])
                dataBack.messageInfo_to_fields[tuple1[0]] = []
                filterString = filterString.replace(tuple1[0], '')[1:]

            # The '{' comes before the next ',' so we have lower level filters
            # specified.
            else:
                upper = tuple[2].find('}')
                if upper < 0:
                    print("didn'tclosecurlies")
                    # For syntax error checking
                    return False
                dataBack.messageInfoList.append(tuple[0])
                dataBack.messageInfo_to_fields[tuple[0]] = tuple[2][:upper]\
                                                        .split(',')
                filterString = tuple[2][upper + 2:]

        # there were no '{' or none remain
        else:
            tuple = filterString.partition(',')
            dataBack.messageInfoList.append(tuple[0])
            dataBack.messageInfo_to_fields[tuple[0]] = []
            filterString = tuple[2]
    # Case: one last message type remains, not containing '{',
    # which means that all the fields of that message type
    # will be displayed. Populate the fields list with all
    # available from the meta data file
## Refactor when dataBack.filters is a dict type.
    if filterString:
        dataBack.messageInfoList.append(filterString)
        dataBack.messageInfo_to_fields[filterString] = []
        #print("\t\t",dataBack.messageInfo_to_fields)
    # For syntax error checking
#    print("full messageInfoList:",dataBack.messageInfoList,"\n\n\n")
    return True


# Nested for loops :D
# This can be corrected by refactoring backend.py
# However this loop is only executed once.
# Refactor when necessary.
def setFieldsFilterFieldDict(dataBack):
    for key in dataBack.messageInfo_to_fields:
        for messageInfo in dataBack.messages:
            if key == messageInfo:
                if len(dataBack.messageInfo_to_fields[key]) == 0:
                    for field in dataBack.messages[key]:
                        dataBack.messageInfo_to_fields[key].append(field)


# Set the filter-by-value functionality
def setFilterByValue(dataBack):
    for key in dataBack.messageInfo_to_fields:
        for fieldString in dataBack.messageInfo_to_fields[key]:
            if fieldString.find('=') > 0:
                tuple = fieldString.partition('=')
                if tuple[0] not in dataBack.messages[key].fields:
                    print("\nWARNING, '" + tuple[0] + "' not found in '"\
                            + key + "' metadata.\n")
                    return
                dataBack.messages[key].fields[tuple[0]].byValue.append(
                                                            float(tuple[2]))

    # Remove later
    for messageInfo in dataBack.messages:
        for field in dataBack.messages[messageInfo].fields:
            if dataBack.messages[messageInfo].fields[field].byValue:
                byValue = dataBack.messages[messageInfo].fields[field].byValue
                print(field, byValue)

    # Now that the flags were extracted,
    # clean up the messageInfo_to_fields:
    for key in dataBack.messageInfo_to_fields:
        newFields = []
        for field in dataBack.messageInfo_to_fields[key]:
            tuple = field.partition('=')
            if tuple[0] in newFields:
                pass
            else:
                newFields.append(tuple[0])
        dataBack.messageInfo_to_fields[key] = newFields


def setUnitsConversion(dataBack):
    # dataBack.messageInfo_to_fields has items that were set
    # in the previous function, and now they to be cleaned
    # of any '[' and ']' characters, while extracting the
    # unit conversion flags
    for messageInfo in dataBack.messages:
        for field in dataBack.messages[messageInfo]:
            if messageInfo in dataBack.messageInfo_to_fields:
                for _field in dataBack.messageInfo_to_fields[messageInfo]:
                    if _field.find('[') >= 0:
                        # If there is a unit conversion arg,
                        # there will be a ['
                        if _field.partition('[')[0] == field:
                            lower = _field.find('[') + 1
                            upper = _field.find(']')
                            if upper < 0:
                                print("didn'tclosebraces")
                                # For syntax error checking
                                return False
                            target = _field[lower:upper].upper()
                            fieldUnits = dataBack.messages[messageInfo]\
                                                        .fields[field].units
                            #Check to see if units conversion is a valid mapping
                            if target in backend.conversionMap[fieldUnits]:
                                # This is where the magic happens
                                dataBack.messages[messageInfo].fields[field]\
                                                    .unitsConversion = target
                                break
                            else:
                                print("Units conversion error: Invalid mapping.\n{} can't be converted to {}".format(fieldUnits, target))
                                return False
    # Now that the flags were extracted,
    # clean up the messageInfo_to_fields:
    for key in dataBack.messageInfo_to_fields:
        newFields = []
        for field in dataBack.messageInfo_to_fields[key]:
            if field.find('[') >= 0:
                lower = field.find('[')
                upper = field.find(']')
                target = field[lower:upper + 1]
                field = field.replace(target, '')
                newFields.append(field)
            else:
                newFields.append(field)
            dataBack.messageInfo_to_fields[key] = newFields
    # For syntax error checking
    return True


# No --filter argument, therefore populate the display dictionary with
# all CAN message types as keys, and all the fields in a list as the value
def createListAndDict_noFilter(dataBack):
    dataBack.messageInfo_to_fields = {messageInfo: [] for messageInfo
                                    in dataBack.messages.keys()}
    for key in dataBack.messageInfo_to_fields:
        dataBack.messageInfoList.append(key)
        for messageInfo in dataBack.messages:
            if key == messageInfo:
                for field in dataBack.messages[messageInfo].fields.keys():
                    dataBack.messageInfo_to_fields[key].append(field)


# Set the dictionary map that is used in CSV mode
def setDisplayCSVmode(dataBack):
    for messageInfo in dataBack.messageInfoList:
        # The user has specific field from a certain CAN message
        if messageInfo in dataBack.messageInfo_to_fields_units:
            for field in dataBack.messageInfo_to_fields_units[messageInfo]:
                # There may be a filter by value argment:

                # There may be units specified:
                if dataBack.messageInfo_to_fields_units[messageInfo]:
                    dataBack.csvDisplayList[field] = messageInfo + field

                    # Strip the units to avoid creating
                    # extra keys in fieldList_CSV dictionary
                    field_ = field.partition('[')[0]
                    dataBack.fieldList_CSV[field_] = 0

        # The user hasn't specified any fields, so display everything
        else:
            for _messageInfo in dataBack.messages:
                if _messageInfo == messageInfo:
                    for field in dataBack.messages[_messageInfo]:
                        dataBack.csvDisplayList[field] = messageInfo + field
                        dataBack.fieldList_CSV[field] = 0

    # Print a column heading list for CSV formatting.
    out = ""
    i = 1

    for key in sorted(dataBack.csvDisplayList):
        out += str(dataBack.csvDisplayList[key]) + ","
        dataBack.fieldIndices[key] = i
        i += 1
    if dataBack.args.time:
        print("t,",out[:-1])
    else:
        print(out[:-1])

''' this is how you iterate through all the filters/fields in dataBack.messages:

        for filter in dataBack.messages:
            print(filter)
            for field in dataBack.messages[filter]:
                print("\t",field)
                for attrib in dataBack.messages[filter].fields[field]:
                    print("\t\t", attrib)
'''
# example commandline launch
# ./canpython.py --nogui /dev/ttyUSB0 -m xmltest.txt --filter='WSO100{airspeed},WSO200{wind_dir=2,vel}' --slow
