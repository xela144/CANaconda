from PyQt5 import QtCore, QtWidgets
import outmessage
from CanDataTranscoder import generateMessage
from math import floor

# from PyQt5.QtWidgets import QMessageBox
baseTuple = ('x', 'b', 'o', 'X', 'B', 'O')

class TransmitGridWidget(QtWidgets.QDialog):

    def setup(self, parent, dataBack, singleshot=False):
        super(TransmitGridWidget, self).__init__()
        self.dataBack = dataBack
        self.parent = parent
        self.singleshot = singleshot
        # Create the grid and a label to go along with it
        self.txGrid = QtWidgets.QGridLayout(parent)
        self.txGrid.setHorizontalSpacing(10)
        self.txGrid.setColumnStretch(1, 2)
        self.txGrid.setColumnStretch(3, 2)

        # A helper button that drops us into the python debugger
        if self.dataBack.args.debug:
            self.buttonPdb = QtWidgets.QPushButton()
            self.buttonPdb.setText("drop into pdb from here")
            self.buttonPdb.clicked.connect(self.pdbset)
            self.txGrid.addWidget(self.buttonPdb, 0,0)

        # All rest of the line-edits and labels created here
        self.txLabel = QtWidgets.QLabel()
        self.txLabel.setText("Transmit Messages")
        self.firstTxMessageInfo = QtWidgets.QComboBox()
        self.firstTxMessageInfo.addItem('Metadata required for transmission')
        self.firstTxMessageInfo.setDisabled(True)
        self.firstTxLabelMsg = QtWidgets.QLabel()
        self.firstTxLabelMsg.setText("Message:")
        self.firstTxLabelField = QtWidgets.QLabel()
        self.firstTxLabelField.setText("Field:")
        self.firstTxField1 = QtWidgets.QLabel()
        self.firstTxField1.setText(' ...')
        self.firstTxBody1 = QtWidgets.QLineEdit()
        self.firstTxBody1.setPlaceholderText('payload data')
        self.firstTxBody1.setDisabled(True)
        self.firstTxUnitsLabel = QtWidgets.QLabel()
        self.firstTxUnitsLabel.setText('[..]')
        self.firstTxLabelFreq = QtWidgets.QLabel()
        self.firstTxLabelFreq.setText("Frequency [Hz]: ")
        self.firstTxFreq = QtWidgets.QLineEdit()
        self.firstTxFreq.setDisabled(True)
        self.firstTxFreq.setMaximumWidth(40)
        self.firstTxFreq.setToolTip("<font color=black>For a single-shot timer, use \"0\"</font>")
        self.firstTxButton = QtWidgets.QPushButton()
        self.firstTxButton.setText("Activate")
        self.firstTxButton.setDisabled(True)
        self.firstTxButton.clicked.connect(self.txActivateHandler)
        
        # Insert the widgets to the grid at their coordinates
        self.txGrid.addWidget(self.txLabel,              0, 3)
        self.txGrid.addWidget(self.firstTxLabelMsg,      1, 0)
        self.txGrid.addWidget(self.firstTxMessageInfo,   1, 1)
        self.txGrid.addWidget(self.firstTxLabelField,    1, 2)
        self.txGrid.addWidget(self.firstTxField1,        1, 3)
        self.txGrid.addWidget(self.firstTxBody1,         1, 4)
        self.txGrid.addWidget(self.firstTxLabelFreq,     1, 5)
        self.txGrid.addWidget(self.firstTxFreq,          1, 6)
        self.txGrid.addWidget(self.firstTxButton,        1, 7)

        # For stand-alone mode. If we don't add a layout then the window will come
        # up with nothing in it.
        if singleshot:
            vbox = QtWidgets.QVBoxLayout()
            vbox.addLayout(self.txGrid)
            if self.dataBack.args.debug:
                vbox.addWidget(self.buttonPdb)
            self.setLayout(vbox)
            self.populateTxMessageInfoCombo()

    # Called when a metadata file is loaded
    # populate the combobox with messageInfo/field names
    def populateTxMessageInfoCombo(self):
        try:
            self.firstTxMessageInfo.currentTextChanged.disconnect(self.populateTxField)
        except TypeError:
            pass
        self.firstTxMessageInfo.clear()            
        self.firstTxMessageInfo.setDisabled(False) 
        try:
            self.firstTxBody1.clear()                  
        except RuntimeError:
            # The widget has already been deleted
            pass
        # move to separate function
        self.firstTxFreq.setDisabled(False)       
        self.firstTxButton.setDisabled(False)     
        for messageInfoName in self.dataBack.messages.keys():
            self.firstTxMessageInfo.addItem(messageInfoName)
        self.populateTxField()
        self.firstTxMessageInfo.currentTextChanged.connect(self.populateTxField)

    def populateTxField(self):
        # First delete the old contents
        rowcount = self.txGrid.rowCount()
        for i in range(1, rowcount):
            try:
                # Remove the old widgets from the grid, then delete
                widget4 = self.txGrid.itemAtPosition(i, 4).widget()
                widget3 = self.txGrid.itemAtPosition(i, 3).widget()
                self.txGrid.removeWidget(widget4)
                self.txGrid.removeWidget(widget3)
                widget4.deleteLater()
                widget3.deleteLater()
            except AttributeError:
                # If widgets have already been deleted
                pass

        # For storing the QLineEdits, so that we can access the text they contain
        # at some other point
        self.txQLabel_LineContainer = []
        currentMessageInfo = self.firstTxMessageInfo.currentText()
        row = 1   # counter for adding to txGrid row
        # Add all of the widgets to the transmission QGridLayout
        try:
            for currentfield in self.dataBack.messages[currentMessageInfo].fields.keys():
                newLabel = QtWidgets.QLabel()
                newLabel.setText(currentfield)
                newLineEdit = QtWidgets.QLineEdit()
                placeholder = self.getPlaceholderText(currentMessageInfo, currentfield, self.dataBack)
                try:
                    units = self.dataBack.messages[currentMessageInfo].fields[currentfield].units
                    placeholder += ' [' + outmessage.unitStringMap[units] + ']'
                except KeyError:
                    pass
                newLineEdit.setPlaceholderText(placeholder)

                # Append to the following list to access from txActivateHandler.
                self.txQLabel_LineContainer.append((newLabel, newLineEdit))  
                self.txGrid.addWidget(newLabel,      row, 3)
                self.txGrid.addWidget(newLineEdit,   row, 4)
                row += 1
        # For one iteration, 'key' will be '' and we want to ignore this error.
        except KeyError:
            pass

    def getPlaceholderText(self, messageInfo, field, dataBack):
        fieldInfo = dataBack.messages[messageInfo].fields[field]
        endian  = fieldInfo.endian
        _signed = fieldInfo.signed == 'yes'
        offset  = fieldInfo.offset
        length  = fieldInfo.length
        scaling = fieldInfo.scaling
        if scaling == 1:
            scaling = int(scaling)
        _type   = fieldInfo.type
        if _type == 'bitfield':
            return '0 to {} bits'.format(length)
        if _signed:
            bound = 2**(length - 1)
            return '{} to {}'.format(-bound*scaling, (bound - 1)*scaling)
        elif not _signed:
            bound = 2**(length) - 1
            return '0 to {}'.format(bound*scaling)
        return "fix this code"


    def checkBoundsOnPayload(self, payload, messageInfo, fieldInfo, dataBack):
        endian  = fieldInfo.endian
        _signed = fieldInfo.signed == 'yes'
        offset  = fieldInfo.offset
        length  = fieldInfo.length
        scaling = fieldInfo.scaling
        if scaling == 1:
            scaling = int(scaling)
        _type   = fieldInfo.type

        # Rescale the payload so that we can check to see if it is within the bounds
        # given by the bit length of its data field
        payload = payload/scaling
        if _signed:
            bound = 2**(length - 1)
            if payload >= -bound and payload <= (bound - 1):
                return True
            else:
                return False
        elif not _signed:
            bound = 2**(length) 
            if payload >= 0 and payload < bound:
                return True
            else:
                return False
        return "fix this code"



    def txActivateHandler(self):
        # We shouldn't transmit anything if we are not streaming yet.
        if not self.dataBack.alreadyStreaming:
            self.notStreamingWarn()
            return
        self.txTypeErrorFlag = False
        # A list to store QLineEdits that have bad data
        self.errContainer = []
        # Cycle through all the current payload QLineEdits, and extract the values
        # Do error checking with each cycle. Errors cause QLineEdits go to 'errContainer'
        # for accessing them later. Both good and bad data gets stored in 'payload'.
        payload = self.getPayloadsFromLineEdits()

        # Change the background color to red if the user data is bad
        if len(self.errContainer) > 0:
            for lineEdit in self.errContainer:
                lineEdit.setStyleSheet("QLineEdit{background: red;}")
            self.txTypeErrorFlag = True
        
        # The tranmission frequency as entered by the user
        freq = self.firstTxFreq.text()

        # Check that the frequency value is valid
        freq = self.checkTypeAndConvert(freq)
        if freq == None:
            self.txTypeErrorFlag = True

        # For redundancy, insert the values back into the QLineEdits. Necessary
        # if user left the LineEdits blank, which caused a default 0 to be added.
        for pair in self.txQLabel_LineContainer:
            # First get the name of the field from the QLabel
            fieldName = pair[0].text()
            fieldDataLineEdit = pair[1]
            # Then set the text from the label to the QLineEdit
            fieldDataLineEdit.setText(str(payload[fieldName]))

        # We messed up earlier but are returning here 
        # after the Line Edits were cleaned up.
        # FIXME: Give a detailed error message here... try entering a value that is
        # too big or too small for the data field length. Error message is too generic
        # Use the same logic as the error messages from generateMessage(). 
        if self.txTypeErrorFlag:
            self.txTypeError()
            return

        messageName = self.firstTxMessageInfo.currentText()
        # At this point we have done our own error checking here, so the try except block
        # is now redundant
        try:
            self.dataBack.asciiBucket = generateMessage(self.dataBack, payload, messageName)
        except Exception as e:
            self.transmissionWarn(str(e))
            return 
        if freq == 0:
            # Broadcase message only once. Skip messagTxInit step and directly push to queue
            self.pushToTransmitQueue()
        else:
            self.messageTxInit(freq)

    def getPayloadsFromLineEdits(self):
        payload = {}
        messageInfoName = self.firstTxMessageInfo.currentText()
        currentMessageInfo = self.dataBack.messages[messageInfoName]
        for Label_Line_pair in self.txQLabel_LineContainer:  # has: (QLabel, QLineEdit)
            fieldName = Label_Line_pair[0].text()
            payloadString = Label_Line_pair[1].text()

            # Convert the payload to an int
            payloadInt = self.checkTypeAndConvert(payloadString)
            # If it can't be converted to an int, then the user gave bad data.
            # Just at the bad data to the payload dictionary, and save a reference
            # to the corresponding QLineEdit.
            if payloadInt == None:
                payload[fieldName] = payloadString # Bad data!
                self.txTypeErrorFlag = True
                self.errContainer.append(Label_Line_pair[1])
                continue

            # Now that we know the payload is has been converted to an integer or a float,
            # assign the value to the payload dictionary where it will be actually used
            payload[fieldName] = payloadInt

            currentField = currentMessageInfo.fields[fieldName]

            # Next we make sure that the payload, once converted to a CAN message, will
            # fit within the bit boundary as specified in the meta data for this field
            Success = self.checkBoundsOnPayload(payloadInt, 
                    currentMessageInfo, currentField, self.dataBack)
            if not Success:
                # Add the QLineEdit with dirty data to this list, so that we can acess
                # them all at once.
                self.errContainer.append(Label_Line_pair[1])
            else:
                # The current QLine Edit has clean data. Set its background to white 
                # in case it was previously set to red.
                Label_Line_pair[1].setStyleSheet("QLineEdit{background: white;}")
        # Now that payload has been populated with
        # both good and bad data, return it
        return payload

    # Push the encoded message to the transmit queue, and send a signal
    def messageTxInit(self, freq):
        # If no timer has been used, create one. Otherwise, re-start it, 
        # but first disconnect from signals.
        try:
            self.TxTimer.timeout.disconnect()
            
        except AttributeError:
            self.TxTimer = QtCore.QTimer()

        freq = freq * 1000  # use milliseconds
        self.TxTimer.timeout.connect(self.pushToTransmitQueue)
        self.TxTimer.start(freq)

    def pushToTransmitQueue(self):
        self.dataBack.CANacondaTxMsg_queue.put(self.dataBack.asciiBucket)

    # Check the type of the payload data. If it is neither int
    # nor float, returns None.
    def checkTypeAndConvert(self, value):
        # First check if field was left blank. If so, assume it means a 0.
        if value == '':
            return 0
        if len(value) > 2:
            if value[1] in baseTuple:
                base = value[1].upper()
                if base == ('X'):
                    try:
                        value = int(value, 16)
                    except ValueError:
                        return None
                elif base == ('O'):
                    try:
                        value = int(value, 8)
                    except ValueError:
                        return None
                elif base == ('B'):
                    try:
                        value = int(value, 2)
                    except ValueError:
                        return None
                else:
                    return None
        try:
            value = int(value)
            return value
        except ValueError:
            try:
                value = float(value)
                return value
            except ValueError:
                return None

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


def main():
    import backend
    import CANaconda
    import argparse
    import sys
    import messageInfo
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    args.nogui = None
    args.debug = True
    dataBack = backend.CanData(args)
    dataBack.alreadyStreaming = True
    messageInfo.xmlImport(dataBack, './metadata/SeaSlug.xml')
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
    ui = TransmitGridWidget()
    singleshot = True
    ui.setup(None, dataBack, singleshot)
    ui.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

