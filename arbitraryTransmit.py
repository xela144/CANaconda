from PyQt5 import QtCore, QtWidgets
from CanMessage import TxCanMessage
from PyQt5.QtCore import QObject, pyqtSignal

# from PyQt5.QtWidgets import QMessageBox
baseTuple = ('x', 'b', 'o', 'X', 'B', 'O')

MAXWIDTH = 30

#IDLABEL, ID, LENGTHLABEL, LENGTH, BODYLINE, BYTE1, BYTE2, BYTE3, BYTE4, BYTE5, BYTE6, BYTE7, BYTE8, LABEL, FREQ, BUTTON = range(16)

class ArbitraryTransmitWidget(QObject):
    newOutMessageUp = pyqtSignal()
    def setup(self, parent, dataBack, singleshot=False):
        super(ArbitraryTransmitWidget, self).__init__()
        self.dataBack = dataBack
        self.parent = parent
        self.singleshot = singleshot

        # Create the layouts for this widget: two hboxs put into one vbox 
        vbox = QtWidgets.QVBoxLayout(parent)
        hbox1 = QtWidgets.QHBoxLayout()
        hbox2 = QtWidgets.QHBoxLayout()

        self.nameLabel = QtWidgets.QLabel()
        self.nameLabel.setText("Enter a message description:")
        self.name = QtWidgets.QLineEdit()

        self.arbitraryIDlabel = QtWidgets.QLabel()
        self.arbitraryIDlabel.setText("Enter an ID (hex):")
        self.arbitraryID = QtWidgets.QLineEdit()

        hbox1.addWidget(self.nameLabel)
        hbox1.addWidget(self.name)
        hbox1.addWidget(self.arbitraryIDlabel)
        hbox1.addWidget(self.arbitraryID)

        self.arbitraryLengthLabel = QtWidgets.QLabel()
        self.arbitraryLengthLabel.setText("length:")
        self.arbitraryLength = QtWidgets.QLineEdit()
        self.arbitraryLengthLabel.setBuddy(self.arbitraryLength)
        self.arbitraryLength.setMaximumWidth(MAXWIDTH)

        self.arbitraryBytes = QtWidgets.QLabel()
        self.arbitraryBytes.setText("bytes:")

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
        self.txButton.setText("Enable")
        #self.txButton.setDisabled(True)
        self.txButton.clicked.connect(self.arbitraryTxActivateHandler)

        # Great there are a ton of widgets. Add them to a list
        widgetl = [self.arbitraryLengthLabel, self.arbitraryLength, self.arbitraryBytes,
                   self.byte1, self.byte2, self.byte3, self.byte4, self.byte5, self.byte6, self.byte7,
                   self.byte8, self.txFreqLabel, self.txFreq, self.txButton]
	# Now at the widgets to the horizontal layout
        for widget in widgetl:
            hbox2.addWidget(widget)
	# Add the horizontal layouts to our top-level vertical layout. And we are done.
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)


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
            newTxCanMessage.name = self.name.text()
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

