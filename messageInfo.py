'''
messageInfo.py
The data structures for the CANaconda filters.
'''

import queue


# This instances of this class are filters created from
# the metadata file. This class gets instantiated during the
# call to xmlimport().
##
# xmlimport is responsible for creating entries in the
# dataBack.messages dictionary.
##
class MessageInfo():
    def __init__(self):
        self.name = ''
        self.id = ''
        self.pgn = ''
        self.desc = ''
        self.parent = ''
        self.fields = {}
        self.freqQueue = queue.Queue()
        self.freq = 0

    # A method used to determine if any of the fields must be
    # displayed by value.
    def isByValue(self):
        for field in self.fields:
            if field.byValue:
                return True
        return False

    def __iter__(self):
        return iter(self.fields)
        # a sub argument of the filters option
        #self.messageNames = []

    def __str__(self):
        return self.name + str(self.fields)


# This class gets instantiated and added to the fields dictionary
# of the Filter class.
class Field():
    # field an ElementTree object
    def __init__(self, field):
        self.header = ''
        self.length = ''
        self.name = ''
        self.offset = ''
        self.signed = ''
        self.units_ = ''
        self.scaling = ''
        self.endian = ''
        self.unitsConversion = None
        self.byValue = []

    def __str__(self):
        return self.name

    def __iter__(self):
        return iter([self.name, self.header, self.length, self.offset,
                 self.signed, self.units, self.scaling, self.endian,
                 self.unitsConversion, self.byValue])

