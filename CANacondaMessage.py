'''
The data structures for the CANacondaMessage object.
'''


class CANacondaMessage():
    def __init__(self):
        self.name = ''
        self.pgn = ''
        self.ID = ''
        self.body = {}
        self.raw = ''
