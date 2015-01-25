'''
 * Copyright Alex Bardales 2015
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

from PyQt5 import QtCore, QtWidgets
import outmessage
from CanDataTranscoder import generateMessage
from math import floor

# from PyQt5.QtWidgets import QMessageBox
baseTuple = ('x', 'b', 'o', 'X', 'B', 'O')

MESSAGELABEL, MESSAGEINFO, FIELDLABEL, FIELDS, BODY, UNITSLABEL, FREQLABEL, FREQ, BUTTON = range(9)

class TransmitGridWidget(QtWidgets.QDialog):

    def setup(self, parent, dataBack, realParent, singleshot=False):
        super(TransmitGridWidget, self).__init__()
        self.dataBack = dataBack
        self.realParent = realParent
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
        self.txGrid.addWidget(self.firstTxLabelMsg,      1, MESSAGELABEL)
        self.txGrid.addWidget(self.firstTxMessageInfo,   1, MESSAGEINFO )
        self.txGrid.addWidget(self.firstTxLabelField,    1, FIELDLABEL  )
        self.txGrid.addWidget(self.firstTxField1,        1, FIELDS      )
        self.txGrid.addWidget(self.firstTxBody1,         1, BODY        )
        self.txGrid.addWidget(self.firstTxUnitsLabel,    1, UNITSLABEL  )
        self.txGrid.addWidget(self.firstTxLabelFreq,     1, FREQLABEL   )
        self.txGrid.addWidget(self.firstTxFreq,          1, FREQ        )
        self.txGrid.addWidget(self.firstTxButton,        1, BUTTON      )

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

        # Populate the combobox in alphabetical order
        for messageInfoName in sorted(self.dataBack.messages.keys(), key=lambda s: s.lower()):
            self.firstTxMessageInfo.addItem(messageInfoName)
        self.populateTxField()
        self.firstTxMessageInfo.currentTextChanged.connect(self.populateTxField)

        #self.populateByOffset(self.dataBack.messages, self.firstTxMessageInfo)

    # Once the combo box has been filled with 'messageInfo' items, we have to populate each
    # messageInfo with its field type.
    def populateTxField(self):
        # First delete the old contents
        rowcount = self.txGrid.rowCount()
        for i in range(1, rowcount):
            try:
                # Remove the old widgets from the grid, then delete
                widget5 = self.txGrid.itemAtPosition(i,   UNITSLABEL).widget()
                widget4 = self.txGrid.itemAtPosition(i,         BODY).widget()
                widget3 = self.txGrid.itemAtPosition(i,       FIELDS).widget()
                self.txGrid.removeWidget(widget5)
                self.txGrid.removeWidget(widget4)
                self.txGrid.removeWidget(widget3)
                widget5.deleteLater()
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
        # Order of the field items should match the offset in the meta data
        try:
            fieldsByOffset = self.getFieldsByOffset(self.dataBack.messages[currentMessageInfo])
            for currentfield in fieldsByOffset:
                newLabel = QtWidgets.QLabel()
                newLabel.setText(currentfield)
                newLineEdit = QtWidgets.QLineEdit()
                # Give the user the data range for the field, and set as place-holder text.
                placeholder = self.getPlaceholderText(currentMessageInfo, currentfield, self.dataBack)
                newLineEdit.setPlaceholderText(placeholder)

                # Add a QLabel widget with the units, if they exist
                newUnitsLabel = QtWidgets.QLabel()
                try:
                    units = self.dataBack.messages[currentMessageInfo].fields[currentfield].units
                    unitsLabelText = outmessage.unitStringMap[units]
                    newUnitsLabel.setText(unitsLabelText)
                except KeyError:
                    pass
                # Append to the following list to access from txActivateHandler.
                self.txQLabel_LineContainer.append((newLabel, newLineEdit))
                # Add the new widgets to the grid layout
                self.txGrid.addWidget(newLabel,      row,      FIELDS)
                self.txGrid.addWidget(newLineEdit,   row,        BODY)
                self.txGrid.addWidget(newUnitsLabel, row,  UNITSLABEL)
                row += 1
        # For one iteration, 'key' will be '' and we want to ignore this error.
        except KeyError:
            pass

    # Get a list of Field objects sorted by offset, rather than alphabetical order
    def getFieldsByOffset(self, messageInfo):
        return self.realParent.getFieldsByOffset(self.dataBack.messages[messageInfo.name])

    # This is used to calculate the default text for the user to see bounds on the
    # payload values for transmitting CAN messages.
    def getPlaceholderText(self, messageInfo, field, dataBack):
        fieldInfo = dataBack.messages[messageInfo].fields[field]
        # If it's a bitfield, just tell them how many bits they have
        if fieldInfo.type == 'bitfield':
            return '0 to {} bits'.format(fieldInfo.length)

        # Otherwise it's an integer, so get the range and tell them that
        return '{:g} to {:g}'.format(fieldInfo.bounds[0], fieldInfo.bounds[1])

    # Like above but checks the boundary on the data, making sure that the user-entered
    # data is within the bounds of the CAN message
    def checkBoundsOnPayload(self, payload, messageInfo, fieldInfo):
        if payload >= fieldInfo.bounds[0] and payload <= fieldInfo.bounds[1]:
            return True
        else:
            self.badData[fieldInfo.name] = 'The {} field is restricted to values between {} and {}.'.format(fieldInfo.name, fieldInfo.bounds[0], fieldInfo.bounds[1])
            return False

    # txActivateHandler: Called by a signal that is connected the "Activate" button.
    # Collects all the payload values in the QLineEdits at the moment the button was
    # clicked. If any of the values were formatted in the wrong way, or would fall
    # of the bit boundary of the CAN message because the number is too big, then an
    # error message is generated, the offending QLineEdit changes to red, and the
    # function returns before creating the CAN message.
    def txActivateHandler(self):
        # We shouldn't transmit anything if we are not streaming yet.
        if not self.dataBack.alreadyStreaming:
            self.notStreamingWarn()
            return
        self.txTypeErrorFlag = False
        self.txBoundErrorFlag = False
        # A list to store QLineEdits that have bad data
        self.errContainer = []
        # Store error messages in case the user doesn't get it right:
        self.badData = {}

        # Cycle through all the current payload QLineEdits, and extract the values
        # Do error checking with each cycle. Errors cause QLineEdits go to 'errContainer'
        # for accessing them later. Both good and bad data gets stored in 'payload'.
        payload = self.getPayloadsFromLineEdits()

        # Change the background color to red if the user data is bad
        if len(self.errContainer) > 0:
            for lineEdit in self.errContainer:
                lineEdit.setStyleSheet("QLineEdit{background: red;}")
           # self.txTypeErrorFlag = True

        # The transmission frequency entered by the user. Check that the frequency is valid
        frequencyString = self.firstTxFreq.text()
        frequencyInt = self.checkTypeAndConvert(frequencyString)
        if frequencyInt == None:
            self.txTypeErrorFlag = True

        # We messed up earlier but are returning here
        # after the Line Edits were cleaned up.
        # FIXME: Give a detailed error message here... try entering a value that is
        # too big or too small for the data field length. Error message is too generic
        # Use the same logic as the error messages from generateMessage().
        if self.txTypeErrorFlag or self.txBoundErrorFlag:
            # Before creating the warning dialog, stop current transmission
            self.disconnectTimer()
            self.txTypeError()
            return

        messageName = self.firstTxMessageInfo.currentText()
        # At this point we have done our own error checking here, so the try except block
        # is now redundant
        try:
            self.dataBack.asciiBucket = generateMessage(self.dataBack, payload, messageName)
        except Exception as e:
            # Before creating the warning dialog, stop current transmission
            self.disconnectTimer()
            self.transmissionWarn(str(e))
            return
        if frequencyInt == 0:
            # Broadcast message only once. Skip messagTxInit step and directly push to queue
            self.disconnectTimer()
            self.pushToTransmitQueue()
        else:
            freq = 1/frequencyInt
            self.messageTxInit(freq)

    # getPayloadsFromLineEdits: This is a helper function that does the actual
    # checking, converting, and error reporting of all the values entered by
    # the user. Error flags will be set if there is bad data, and QLineEdits
    # will be stored in a list to be accessed later.
    def getPayloadsFromLineEdits(self):
        # The return value will be this payload dictionary
        payload = {}
        messageInfoName = self.firstTxMessageInfo.currentText()
        currentMessageInfo = self.dataBack.messages[messageInfoName]
        for Label_Line_pair in self.txQLabel_LineContainer:  # has: (QLabel, QLineEdit)
            fieldName = Label_Line_pair[0].text()
            valueString = Label_Line_pair[1].text()

            # Convert the payload to an int
            try:
                valueNumeric = self.checkTypeAndConvert(valueString)
            # If it can't be converted to an int, then the user gave bad data.
            # Just at the bad data to the payload dictionary, and save a reference
            # to the corresponding QLineEdit.
            except ValueError:
                payload[fieldName] = valueString # Bad data being put payload here.
                self.txTypeErrorFlag = True
                self.errContainer.append(Label_Line_pair[1])
                continue

            # Now that we know the payload has been converted to an integer or a float,
            # assign the value to the payload dictionary where it will be actually used
            payload[fieldName] = valueNumeric
            currentField = currentMessageInfo.fields[fieldName]

            # Next we make sure that the payload, once converted to a CAN message, will
            # fit within the bit boundary as specified in the meta data for this field
            if self.checkBoundsOnPayload(valueNumeric, currentMessageInfo, currentField):
                # The current QLine Edit has clean data. Set its background to white
                # in case it was previously set to red.
                Label_Line_pair[1].setStyleSheet("QLineEdit{background: white;}")
            else:
                # Add the QLineEdit with dirty data to this list, so that we can access
                # them all at once.
                self.txBoundErrorFlag = True
                self.errContainer.append(Label_Line_pair[1])

        # Now that payload has been populated with
        # both good and bad data, return it
        return payload

    def checkTypeAndConvert(self, value):
        """
        Parse the value string into a numeric representation.

        This will return either an integer or float datatype. If parsing
        fails, a ValueError will be raised
        """
        # FIXME: Does not catch '1/3'.

        # Assume empty fields are 0
        if len(value) == 0:
            return 0

        # Only support other bases with prefixes, otherwise it's ambiguous.
        if value.startswith('0x') or value.startswith('0X'):
            return int(value, 16)
        elif value.startswith('0o') or value.startswith('0O'):
            return int(value, 8)
        elif value.startswith('0b') or value.startswith('0B'):
            return int(value, 2)
        elif value.startswith('0o') or value.startswith('0O'):
            return int(value, 10)
        else:
            try:
                return int(value, 10)
            except ValueError:
                return float(value)


    # Push the encoded message to the transmit queue, and send a signal
    def messageTxInit(self, freq):
        # If no timer has been used, create one. Otherwise, re-start it,
        # but first disconnect from signals.
        try:
            self.TxTimer.timeout.disconnect()

        except (AttributeError, TypeError):
            self.TxTimer = QtCore.QTimer()

        freq = freq * 1000  # use milliseconds
        self.TxTimer.timeout.connect(self.pushToTransmitQueue)
        self.TxTimer.start(freq)

    def pushToTransmitQueue(self):
        self.dataBack.CANacondaTxMsg_queue.put(self.dataBack.asciiBucket)

    def disconnectTimer(self):
        try:
            self.TxTimer.timeout.disconnect()
        except AttributeError:
            pass

    def txTypeError(self):
        errormsg = QtWidgets.QMessageBox()
        errormsg.setText("Message Transmit Error")
        informativeText = ''
        if self.txTypeErrorFlag:
            informativeText += "Values must be of type 'int' or 'float'. \nIf 'int', they must be of base 16 (0x), base 8 (0o), or base 2 (0b). No base specified is interpreted as base 10.\n"
        if self.txBoundErrorFlag:
            informativeText += '\n'
            for entry in self.badData:
                informativeText += self.badData[entry] + '\n'
        errormsg.setInformativeText(informativeText)
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
