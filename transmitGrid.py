from PyQt5 import QtCore, QtWidgets
import outmessage
from CanDataTranscoder import generateMessage

# from PyQt5.QtWidgets import QMessageBox

class TransmitGridWidget(QtWidgets.QDialog):

    def setup(self, parent, dataBack, singleshot=False):
        super(TransmitGridWidget, self).__init__()
        self.dataBack = dataBack
        self.parent = parent
        self.singleshot = singleshot
        # Create the grid and a label to go along with it
        self.txGrid = QtWidgets.QGridLayout()
        self.txGrid.setHorizontalSpacing(10)
        self.txGrid.setColumnStretch(1, 2)
        self.txGrid.setColumnStretch(3, 2)

        # A helper button that drops us into the python debugger
        if self.dataBack.args.debug:
            self.buttonPdb = QtWidgets.QPushButton()
            self.buttonPdb.setText("pdb")
            self.buttonPdb.clicked.connect(self.pdbset)

        # Create a box layout and at the grid layout to it
        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(self.txGrid)
        if self.dataBack.args.debug:
            vbox.addWidget(self.buttonPdb)
        self.setLayout(vbox)

        # add a vertical layout to the txFrame and put line edits inside it
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
        
        self.txGrid.addWidget(self.txLabel,              0, 3)
        self.txGrid.addWidget(self.firstTxLabelMsg,      1, 0)
        self.txGrid.addWidget(self.firstTxMessageInfo,   1, 1)
        self.txGrid.addWidget(self.firstTxLabelField,    1, 2)
        self.txGrid.addWidget(self.firstTxField1,        1, 3)
        self.txGrid.addWidget(self.firstTxBody1,         1, 4)
        self.txGrid.addWidget(self.firstTxUnitsLabel,    1, 5)
        self.txGrid.addWidget(self.firstTxLabelFreq,     1, 6)
        self.txGrid.addWidget(self.firstTxFreq,          1, 7)
        self.txGrid.addWidget(self.firstTxButton,        1, 8)

        if singleshot:
            self.populateTxMessageInfoCombo()

    # Called when a metadata file is loaded
    # populate the combobox with messageInfo/field names
    def populateTxMessageInfoCombo(self):
        try:
            self.firstTxMessageInfo.currentTextChanged.disconnect(self.populateTxField)
        except:
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
                widget5 = self.txGrid.itemAtPosition(i, 5).widget()
                widget4 = self.txGrid.itemAtPosition(i, 4).widget()
                widget3 = self.txGrid.itemAtPosition(i, 3).widget()
                self.txGrid.removeWidget(widget5)
                self.txGrid.removeWidget(widget4)
                self.txGrid.removeWidget(widget3)
                widget5.deleteLater()
                widget4.deleteLater()
                widget3.deleteLater()
            except AttributeError:
                # If widgets have already been deleted
                pass

        # For storing the QLineEdits
        self.txQLabel_LineContainer = []  # store QLineEdits here
        key = self.firstTxMessageInfo.currentText()
        row = 1   # counter for adding to txGrid row
        # Add all of the widgets to the transmission QGridLayout
        try:
            for field in self.dataBack.messages[key].fields.keys():
                newLabel = QtWidgets.QLabel()
                newLabel.setText(field)
                newLineEdit = QtWidgets.QLineEdit()
                units = self.dataBack.messages[key].fields[field].units
                newUnitsLabel = QtWidgets.QLabel()
                try:
                    newUnitsPretty = '[' + outmessage.unitStringMap[units] + ']'
                except KeyError:
                    newUnitsPretty = ''
                newUnitsLabel.setText(newUnitsPretty)

                # Append to the following list to access from txActivateHandler.
                self.txQLabel_LineContainer.append((newLabel, newLineEdit))  
                self.txGrid.addWidget(newLabel,      row, 3)
                self.txGrid.addWidget(newLineEdit,   row, 4)
                self.txGrid.addWidget(newUnitsLabel, row, 5)
                row += 1
        # For one iteration, 'key' will be '' and we want to ignore this error.
        except KeyError:
            pass

    def txActivateHandler(self):
        # We shouldn't transmit anything if we are not streaming yet.
        if not self.dataBack.alreadyStreaming:
            self.notStreamingWarn()
            return

        # A dictionary for payload fields and values
        payload = {}

        # Cycle through all the current payload QLineEdits, and extract the values
        for pair in self.txQLabel_LineContainer:  # has: (QLabel, QLineEdit)
            payload[pair[0].text()] = pair[1].text()

        # The tranmission frequency as entered by the user
        freq = self.firstTxFreq.text()

        # Check that the frequency value is valid
        freq = self.checkTypeAndConvert(freq)
        if freq == None:
            self.txTypeError()
            return

        # Check that the value entered by the user is valid. Replace '' with '0'
        # where appropriate
        for val in payload:
            payload[val] = self.checkTypeAndConvert(payload[val])
            if payload[val] == None:
                self.txTypeError()
                return

        # For redundancy, insert the values back into the QLineEdits. Necessary
        # if user left the LineEdits blank, which caused a default 0 to be added.
        for pair in self.txQLabel_LineContainer:
            fieldName = pair[0].text()
            fieldData = pair[1]
            fieldData.setText(str(payload[fieldName]))

        messageName = self.firstTxMessageInfo.currentText()
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
                                    be of type 'int' or 'float'")
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

