'''
The data structures for the CANacondaMessage object.
'''


class CanMessage():
    def __init__(self):
        self.pgn = 0 # The Parameter Group Number of the CAN message. Only applies to extended packets and only makes sense for NMEA2000 messages. Decoded from the message id.
        self.id = 0 # The message id.
        self.payload = [] # The payload of the CAN message. Should be between 0 and 8 in length. Each element is a byte.


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
