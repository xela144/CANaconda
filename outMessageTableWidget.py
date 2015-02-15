
from PyQt5 import QtCore, QtWidgets
import pdb
import backend
from PyQt5.QtCore import pyqtRemoveInputHook as pyqtrm

CHK, NAME, IDCOL, LEN, BOD, FREQ = range(6)

#class OutMessageTableWidget(QtWidgets.QWidget):
class OutMessageTableWidget(QtWidgets.QWidget):

    def setup(self, dataBack, parent, singleshot=False):
        super(OutMessageTableWidget, self).__init__()
        self.dataBack = dataBack
        self.parent = parent
        self.singleshot = singleshot
        tableLabel = QtWidgets.QLabel("Outgoing messages to CAN bus")
        self.tableWidget = QtWidgets.QTableWidget()
        self.tableWidget.setObjectName("OutgoingTableWidget")
        # To hide row numbers, uncomment
        #self.tableWidget.verticalHeader().setVisible(False)
        tableLabel.setBuddy(self.tableWidget)

        if self.dataBack.args.debug:
            self.buttonPdb = QtWidgets.QPushButton()
            self.buttonPdb.setText("pdb")
            self.buttonPdb.clicked.connect(self.pdbset)
        
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(tableLabel)
        vbox.addWidget(self.tableWidget)
        
        if self.dataBack.args.debug:
            vbox.addWidget(self.buttonPdb)

        self.setLayout(vbox)

    def populateTable(self):
        self.stopTimers()
        try:
            self.tableWidget.activated.disconnect(self.spaceBarHandler)
            self.tableWidget.itemChanged.disconnect(self.serialHandler)
        except TypeError:
            pass
        displayList = []
        # Whatever is here gets put in the table
        displayList += self.getDisplayList()
        headerList = ['', 'Description', 'ID', 'Length', 'Body', 'Frequency']
        self.tableWidget.setColumnCount(len(headerList))
        self.tableWidget.setRowCount(len(displayList))
        self.tableWidget.setHorizontalHeaderLabels(headerList)
        for row, txCanMessage in enumerate(displayList):
            # Get the parameters for each message
            name = txCanMessage.name
            ID = txCanMessage.ID
            length = str(txCanMessage.length)
            body = txCanMessage.body
            freq = str(txCanMessage.freq)
            CanMessageString = txCanMessage.CanMessageString
            data0, data1, data2 = QtCore.QTimer(), CanMessageString, txCanMessage.freq

            # The checkBoxItem will control whether the message is being written to serial
            checkBoxItem = QtWidgets.QTableWidgetItem()
            checkBoxItem.setCheckState(QtCore.Qt.Unchecked)
            checkBoxItem.setToolTip("<font color=black>Check to send messages</font>")
            checkBoxItem.setData(0, (data0, data1, data2))
            self.tableWidget.setItem(row, CHK, checkBoxItem)

            nameItem = QtWidgets.QTableWidgetItem(name)
            nameItem.setFlags(QtCore.Qt.ItemFlags(~QtCore.Qt.ItemIsEditable))
            nameItem.setFlags(QtCore.Qt.ItemFlags(QtCore.Qt.ItemIsEnabled))
            self.tableWidget.setItem(row, NAME, nameItem)

            # Create the table widget items
            IDitem = QtWidgets.QTableWidgetItem(ID)
            IDitem.setFlags(QtCore.Qt.ItemFlags(~QtCore.Qt.ItemIsEditable))
            IDitem.setFlags(QtCore.Qt.ItemFlags(QtCore.Qt.ItemIsEnabled))
            self.tableWidget.setItem(row, IDCOL, IDitem)
            
            lengthItem = QtWidgets.QTableWidgetItem(length)
            lengthItem.setFlags(QtCore.Qt.ItemFlags(~QtCore.Qt.ItemIsEditable))
            lengthItem.setFlags(QtCore.Qt.ItemFlags(QtCore.Qt.ItemIsEnabled))
            self.tableWidget.setItem(row, LEN, lengthItem)

            bodyItem = QtWidgets.QTableWidgetItem(body)
            bodyItem.setFlags(QtCore.Qt.ItemFlags(~QtCore.Qt.ItemIsEditable))
            bodyItem.setFlags(QtCore.Qt.ItemFlags(QtCore.Qt.ItemIsEnabled))
            self.tableWidget.setItem(row, BOD, bodyItem)

            freqItem = QtWidgets.QTableWidgetItem(freq)
            freqItem.setFlags(QtCore.Qt.ItemFlags(~QtCore.Qt.ItemIsEditable))
            freqItem.setFlags(QtCore.Qt.ItemFlags(QtCore.Qt.ItemIsEnabled))
            self.tableWidget.setItem(row, FREQ, freqItem)

        # The 'body' column should be large enough to accomodate 8 bytes
        self.tableWidget.setColumnWidth(BOD, 140)
        self.tableWidget.itemChanged.connect(self.serialHandler)
        self.tableWidget.activated.connect(self.spaceBarHandler)

    def spaceBarHandler(self):
        currentRow = self.sender().currentRow()
        try:
            CanMessageString = self.tableWidget.itemAt(0,currentRow).data(0)[1]
        # This will be fixed when we figure out how to capture key press events
        except IndexError:
            return
        self.dataBack.CANacondaTxMsg_queue.put(CanMessageString)
        import sys
        print("ERROR: Only row 0 gets written to serial: " +CanMessageString, file=sys.stderr)

    def getDisplayList(self):
        displayList = []
        for message in self.dataBack.messagesToSerial:
            displayList.append(self.dataBack.messagesToSerial[message])
        return displayList


    # The user has checked or unchecked a message in the OutMessage table widget. This is where
    # we handle that action. With the helper functions within this code, we either start sending
    # messages to the serial thread, or stop messages from being sent.
    def serialHandler(self):
        for row in range(0, self.tableWidget.rowCount()):
            thisItem = self.tableWidget.item(row, CHK)
            try:
                thisTimer, thisMsg, thisFreq = thisItem.data(0) # data(0) is tuple: (qtimer, msg, freq)
            except ValueError:
                # This error generated when a signal is emitted when we didn't need it.
                return
            # If the timer is not in dataBack.timers, and the checkstate is 2 then add it and start it.
            if thisItem.checkState() == QtCore.Qt.Checked:
                if thisTimer.timerId() == -1:
                    # The timer with ID == -1 is not being used. Start the timer here:
                    self.timerHandler(thisTimer, thisFreq)
                    # Add the timer to dataBack.timers.
                    self.dataBack.timers[thisTimer.timerId()] = (thisTimer, thisMsg)
                else:
                    # The timer already has an ID, so it's already in use.
                    continue
            # Here the item has been unchecked but is still in dataBack.timers. Therefore, stop the timer.        
            elif thisTimer.timerId() in self.dataBack.timers:
                # Now remove the timer from our data backend
                byebyeblob = self.dataBack.timers.pop(thisTimer.timerId())
                # If the checkbox is not checked, and the timer is in dataBack.timers, then we 
                thisTimer.stop()
                thisTimer.timeout.disconnect()

    # Start a QTimer with the given frequency
    def timerHandler(self, qtimer, freq):
        freq = 1/freq * 1000
        qtimer.timeout.connect(self.pushToTransmitQueue)
        qtimer.start(freq)

    # Send the CAN message to our serial thread
    def pushToTransmitQueue(self):
        # get the ID of the timer from the sender.
        timerId = self.sender().timerId()
        # extract the message using the ID.
        CanMessageString = self.dataBack.timers[timerId][1]
        # Push it to the serial queue for writing to the serial port
        self.dataBack.CANacondaTxMsg_queue.put(CanMessageString)

    # Stop the timers. This is done when populateTable is called and reference to a timer is lost, causing
    # it to continue timing out even when we no longer need it.
    def stopTimers(self):
        for timer in self.dataBack.timers.keys():
            time = self.dataBack.timers[timer][0]
            time.timeout.disconnect()
            time.stop()

    def pdbset(self):
        pyqtrm()
        pdb.set_trace()
