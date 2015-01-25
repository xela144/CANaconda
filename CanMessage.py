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
The data structures for the CANacondaMessage object.
'''


class CanMessage():
    # Constants for what type of CAN message this is: standard has 11-bit IDs, extended has 29-bit IDs
    StandardType, ExtendedType = range(2)

    def __init__(self):
        self.pgn = 0 # The Parameter Group Number of the CAN message. Only applies to extended packets and only makes sense for NMEA2000 messages. Decoded from the message id.
        self.id = 0 # The message id.
        self.type = CanMessage.StandardType
        self.payload = [] # The payload of the CAN message. Should be between 0 and 8 in length. Each element is a byte.
        self.payloadBitstring = '' # This is a bit-string representation of the
                                   # payload data. This is actually used in
                                   # the code.


    def __str__(self):
        """Convert the CAN message to a human readable version."""

        # Show the PGN if it exists
        pgnStr = ""
        if self.pgn > 0:
            pgnStr = " (PGN: {})".format(self.pgn)

        dataString = ",".join(["{:02X}".format(x) for x in self.payload])

        return "Head: 0x{:X}{}, Body: 0x[{}]".format(self.id, pgnStr, dataString)

class CANacondaMessage(CanMessage):
    """ A wrapper class around CanMessage to help migrate our code over. FIXME: Modify code to use CanMEssage directly."""
    def __init__(self):
        super().__init__()
        self.name = ""
        self.body = {}
        self.freq = 0

    def __str__(self):
        return super().__str__()
