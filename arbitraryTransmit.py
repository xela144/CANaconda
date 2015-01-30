from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QObject, pyqtSignal
import outmessage
from CanMessage import TxCanMessage
from math import floor

# from PyQt5.QtWidgets import QMessageBox
baseTuple = ('x', 'b', 'o', 'X', 'B', 'O')

MAXWIDTH = 30

IDLABEL, ID, LENGTHLABEL, LENGTH, BODYLINE, BYTE1, BYTE2, BYTE3, BYTE4, BYTE5, BYTE6, BYTE7, BYTE8, LABEL, FREQ, BUTTON = range(16)

class ArbitraryTransmitGridWidget(QObject):
    newOutMessageUp = pyqtSignal()

    def setup(self, parent, dataBack, realParent, singleshot=False):
        super(ArbitraryTransmitGridWidget, self).__init__()
        self.dataBack = dataBack
        self.parent = parent
        self.realParent = parent
        self.singleshot = singleshot
        # Create the grid and a label to go along with it
        self.txGrid = QtWidgets.QGridLayout(parent)
        self.txGrid.setHorizontalSpacing(10)
        self.txGrid.setColumnStretch(1, 2)
        self.txGrid.setColumnStretch(3, 2)
        ####FIXME#### gridlayouts don't behave the way we need. Use hbox layout instead.
        self.txGrid.setRowMinimumHeight(1,25)
        self.txGrid.setRowStretch(1,100)

        # A helper button that drops us into the python debugger
        if self.dataBack.args.debug:
            self.buttonPdb = QtWidgets.QPushButton()
            self.buttonPdb.setText("drop into pdb from here")
            self.buttonPdb.clicked.connect(self.pdbset)
            self.txGrid.addWidget(self.buttonPdb, 0,0)

        self.arbitraryIDlabel = QtWidgets.QLabel()
        self.arbitraryIDlabel.setText("Enter a ID (hex):")
        self.arbitraryID = QtWidgets.QLineEdit()

        self.arbitraryBytes = QtWidgets.QLabel()
        self.arbitraryBytes.setText("bytes:")

        self.arbitraryLengthLabel = QtWidgets.QLabel()
        self.arbitraryLengthLabel.setText("length:")
        self.arbitraryLength = QtWidgets.QLineEdit()
        self.arbitraryLength.setMaximumWidth(MAXWIDTH)

        self.byte1 = QtWidgets.QLineEdit()
        self.byte2 = QtWidgets.QLineEdit()
        self.byte3 = QtWidgets.QLineEdit()
        self.byte4 = QtWidgets.QLineEdit()
        self.byte5 = QtWidgets.QLineEdit()
        self.byte6 = QtWidgets.QLineEdit()
        self.byte7 = QtWidgets.QLineEdit()
        self.byte8 = QtWidgets.QLineEdit()

        self.byte1.setMaximumWidth(MAXWIDTH)
        self.byte2.setMaximumWidth(MAXWIDTH)
        self.byte3.setMaximumWidth(MAXWIDTH)
        self.byte4.setMaximumWidth(MAXWIDTH)
        self.byte5.setMaximumWidth(MAXWIDTH)
        self.byte6.setMaximumWidth(MAXWIDTH)
        self.byte7.setMaximumWidth(MAXWIDTH)
        self.byte8.setMaximumWidth(MAXWIDTH)

        self.txFreqLabel = QtWidgets.QLabel()
        self.txFreqLabel.setText("Frequency [Hz]: ")
        self.txFreq = QtWidgets.QLineEdit()
        self.txFreq.setMaximumWidth(40)
        self.txFreq.setToolTip("<font color=black>For a single-shot timer, use \"0\"</font>")
        self.txButton = QtWidgets.QPushButton()
        self.txButton.setText("Activate")
        #self.txButton.setDisabled(True)
        self.txButton.clicked.connect(self.arbitraryTxActivateHandler)

        
        # Insert the widgets to the grid at their coordinates
        self.txGrid.addWidget(self.arbitraryIDlabel,    1,  IDLABEL)
        self.txGrid.addWidget(self.arbitraryID,         1,       ID)
        self.txGrid.addWidget(self.arbitraryLengthLabel,1,LENGTHLABEL)
        self.txGrid.addWidget(self.arbitraryLength,     1,   LENGTH)
        self.txGrid.addWidget(self.arbitraryBytes,      1, BODYLINE)
        self.txGrid.addWidget(self.byte1,               1,    BYTE1)
        self.txGrid.addWidget(self.byte2,               1,    BYTE2)
        self.txGrid.addWidget(self.byte3,               1,    BYTE3)
        self.txGrid.addWidget(self.byte4,               1,    BYTE4)
        self.txGrid.addWidget(self.byte5,               1,    BYTE5)
        self.txGrid.addWidget(self.byte6,               1,    BYTE6)
        self.txGrid.addWidget(self.byte7,               1,    BYTE7)
        self.txGrid.addWidget(self.byte8,               1,    BYTE8)
        self.txGrid.addWidget(self.txFreqLabel,         1,    LABEL)
        self.txGrid.addWidget(self.txFreq,              1,     FREQ)
        self.txGrid.addWidget(self.txButton,            1,   BUTTON)

        # For stand-alone mode. If we don't add a layout then the window will come
        # up with nothing in it.
        if singleshot:
            vbox = QtWidgets.QVBoxLayout()
            vbox.addLayout(self.txGrid)
            if self.dataBack.args.debug:
                vbox.addWidget(self.buttonPdb)
            self.setLayout(vbox)

    # This is called when user clicks on 'activate' button. Error checking happens, then correct messages
    # are sent to the messageTxInit function, which pushes messages to a serial queue
    def arbitraryTxActivateHandler(self):
        warnFlag = False
        self.payload = None
        # We shouldn't transmit anything if we are not streaming yet.
        if not self.dataBack.alreadyStreaming:
            self.notStreamingWarn()
            return
        self.txTypeErrorFlag = False
        # A list to store QLineEdits that have bad data. If this list is non-empty, then an error occured.
        self.errContainer = []
        # Error checking on the ID, length, body, and frequency.
        self.checkMessageIDintegrity(self.errContainer)
        self.checkBodyIntegrity(self.errContainer)
        self.checkFrequencyIntegrity(self.errContainer)
        # Check to see if an error occurred. If it did, then change the color of the line edit where the data is bad.
        if len(self.errContainer) >0:
            for badData in self.errContainer:
                badData.setStyleSheet("QLineEdit{background: red;}")
            warnFlag = True
        # Handle the dialog window here that shows a warning, if an error occurred
        warnString = ''
        if self.invalidID:
            warnString += "\ninvalid message ID"
        if self.dataTooBig:
            warnString += "\ninvalid payload"
        if self.badLength:
            warnString += "\ninvalid message length"
        if self.invalidFreq:
            warnString += "\ninvalid frequency"
        if warnFlag:
            self.transmissionWarn(warnString)
        # Otherwise the data was good.
        else:
            # Create an outgoing message object
            newTxCanMessage = TxCanMessage()
            newTxCanMessage.ID = self.arbitraryID.text()
            newTxCanMessage.length = int(self.arbitraryLength.text())
            newTxCanMessage.body = self.getBodyFromLineEdits()
            newTxCanMessage.CanMessageString = self.getPayloadFromLineEdits()
            freq = float(self.txFreq.text())
            self.TxCanMessage = newTxCanMessage
            if freq == 0:
                self.disconnectTimer()
                newTxCanMessage.freq = 0
                self.pushToTransmitQueue(newTxCanMessage.CanMessageString)
            else:
                newTxCanMessage.freq = freq
                self.messageTxInit(newTxCanMessage)
            self.dataBack.messagesToSerial[newTxCanMessage.ID] = newTxCanMessage
            self.newOutMessageUp.emit()

    # Simply tries to convert to float, and ensures frequency is positive. Then store the frequency.
    def checkFrequencyIntegrity(self, errContainer):
        self.invalidFreq = False
        try:
            freq = float(self.txFreq.text())
            if freq < 0:
                errContainer.append(self.txFreq)
                self.invalidFreq = True
            else:
                self.txFreq.setStyleSheet("QLineEdit{background: white;}")
        except ValueError:
            errContainer.append(self.txFreq)
            self.invalidFreq = True

    # Check that the message ID is correct. This means that it is a proper hex number, less than 30 bits
    def checkMessageIDintegrity(self, errContainer):
        self.invalidID = False
        try:
            ID = self.arbitraryID.text()
            self.arbitraryID.setText(ID.upper())
            integerValue = int(ID, 16)
            if integerValue < 0:
                errContainer.append(self.arbitraryID)
                self.invalidID = True
            binaryValue = bin(integerValue)[2:]
            # We can't have an ID field greater than 29 bits
            if len(binaryValue) > 29:
                errContainer.append(self.arbitraryID)
                self.invalidID = True
            else:
                self.arbitraryID.setStyleSheet("QLineEdit{background: white;}")
        except ValueError:
            errContainer.append(self.arbitraryID)
            self.invalidID = True

    # Check each byte for proper hex format, and make sure its integer value is less than 256
    def checkBodyIntegrity(self, errContainer):
        self.dataTooBig = False
        self.badLength = False
        try:
            try:
                length = int(self.arbitraryLength.text())
            # User entered a non-integer for length. Set to 0 so that no data will be entered into line edits
            except ValueError:
                length = 0
                errContainer.append(self.arbitraryLength)
                self.badLength = True
                return

            if length > 8 or length < 0:
                errContainer.append(self.arbitraryLength)
                self.dataTooBig = True
            else:
                self.arbitraryLength.setStyleSheet("QLineEdit{background: white;}")
        except ValueError:
            errContainer.append(self.arbitraryLength)

        # Check each LineEdit byte by byte
        bytes = [self.byte1, self.byte2, self.byte3, self.byte4, self.byte5, self.byte6, self.byte7, self.byte8]
        # Limit the bytes we look at by 'length'
        for byte in bytes[0:length]:
            # Assume empty bytes to be 0's
            if byte.text() == '':
                byte.setText('00')
            # Don't let user enter a nibble. Prepend a 0.
            if len(byte.text()) == 1:
                byte.setText('0'+byte.text())
            try:
                # Value larger than 255 is more than one byte.
                if int(byte.text(), 16) > 255:
                    errContainer.append(byte)
                    self.dataTooBig = True
                else:
                    byte.setText(byte.text().upper())
                    byte.setStyleSheet("QLineEdit{background: white;}")
            except ValueError:
                errContainer.append(byte)
        # Now remove the remaining bytes, since the user has identified the length
        for byte in bytes[length:]:
            byte.setText('')

    def getBodyFromLineEdits(self):
        bodyString = ''
        bodyString += self.byte1.text()
        bodyString += self.byte2.text()
        bodyString += self.byte3.text()
        bodyString += self.byte4.text()
        bodyString += self.byte5.text()
        bodyString += self.byte6.text()
        bodyString += self.byte7.text()
        bodyString += self.byte8.text()
        return bodyString

    # Capture all the text from the line edits. 
    def getPayloadFromLineEdits(self):
        #FIXME: Handle case for 't'
        payloadString = ''
        payloadString += 'T'
        payloadString += self.arbitraryID.text()
        payloadString += self.arbitraryLength.text()
        payloadString += self.byte1.text()
        payloadString += self.byte2.text()
        payloadString += self.byte3.text()
        payloadString += self.byte4.text()
        payloadString += self.byte5.text()
        payloadString += self.byte6.text()
        payloadString += self.byte7.text()
        payloadString += self.byte8.text()
        return payloadString


    # Push the encoded message to the transmit queue, and send a signal
    def messageTxInit(self, TxCanMessage):
        # If no timer has been used, create one. Otherwise, re-start it, 
        # but first disconnect from signals.
        try:
            self.TxTimer.timeout.disconnect()
            
        except AttributeError:
            self.TxTimer = QtCore.QTimer()
        freq = 1/TxCanMessage.freq
        freq = freq * 1000  # use milliseconds
        self.TxTimer.timeout.connect(self.pushToTransmitQueue)
        self.TxTimer.start(freq)

    def pushToTransmitQueue(self):
        self.dataBack.CANacondaTxMsg_queue.put(self.TxCanMessage.CanMessageString)
        self.changeColor()
        print(self.TxCanMessage.CanMessageString)

    def changeColor(self):
        self.changeColorToGreen()
        self.toWhite = QtCore.QTimer()
        self.toWhite.timeout.connect(self.changeColorToWhite)
        self.toWhite.start(100)

    def changeColorToGreen(self):
        lineEdits = [self.arbitraryID, self.arbitraryLength, self.byte1, self.byte2, self.byte3,
                     self.byte4, self.byte5, self.byte6, self.byte7, self.byte8, self.txFreq]
        for edit in lineEdits:
            edit.setStyleSheet("QLineEdit{background: green;}")

    def changeColorToWhite(self):
        lineEdits = [self.arbitraryID, self.arbitraryLength, self.byte1, self.byte2, self.byte3,
                     self.byte4, self.byte5, self.byte6, self.byte7, self.byte8, self.txFreq]
        for edit in lineEdits:
            edit.setStyleSheet("QLineEdit{background: white;}")
        self.toWhite.timeout.disconnect()

    def disconnectTimer(self):
        try:
            self.TxTimer.timeout.disconnect()
        except AttributeError:
            pass


    def txTypeError(self):
        errormsg = QtWidgets.QMessageBox()
        errormsg.setText("Message Transmit Error")
        errormsg.setInformativeText("Payload and frequency values must\
                                    be of type 'int' or 'float'. \nIf 'int', they must be of base 16\
                                    (0x), base 8 (0o), or base 2 (0b). No base specified is \
                                    interpreted as base 10.")
        errormsg.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        errormsg.exec()

    def notStreamingWarn(self):
        warn = QtWidgets.QMessageBox()
        warn.setText("Message Transmit Error")
        warn.setInformativeText("Make sure you have already begun streaming messages")
        warn.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        warn.exec()

    def transmissionWarn(self, errorString):
        warn = QtWidgets.QMessageBox()
        warn.setText("Transmission Error")
        warn.setInformativeText(errorString)
        warn.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        warn.exec()

    def pdbset(self):
        QtCore.pyqtRemoveInputHook()
        import pdb
        pdb.set_trace()
