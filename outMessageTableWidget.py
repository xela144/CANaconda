
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
        self.tableWidget.verticalHeader().setVisible(False)
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
        if singleshot:
            self.populateTable()
        #self.tableWidget.viewport().update()

    def populateTable(self):
        displayList = self.getDisplayList()
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

            # The checkBoxItem will control whether the message is being written to serial
            checkBoxItem = QtWidgets.QTableWidgetItem()
            checkBoxItem.setCheckState(QtCore.Qt.Unchecked)
            checkBoxItem.setToolTip("<font color=black>Check to send messages</font>")
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

    def getDisplayList(self):
        displayList = []
        for message in self.dataBack.messagesToSerial:
            displayList.append(self.dataBack.messagesToSerial[message])
        return displayList

    def pdbset(self):
        pyqtrm()
        pdb.set_trace()
