# FiltersTreeWidget class is instantiated in ui_mainwindow.py
# Each time this widget is modified, the messageInfoTable widget gets updated.

from PyQt5 import QtCore, QtWidgets
# from PyQt5.QtWidgets import QMessageBox
import pdb

from messageInfo import CAN_FORMAT_EXTENDED


class FiltersTreeWidget(QtWidgets.QDialog):
    
    def setup(self, parent, dataBack, realParent=None, singleshot=False):
        super(FiltersTreeWidget, self).__init__()
        self.dataBack = dataBack
        self.parent = parent
        self.realParent = realParent  # An explicit reference to the UI_CANaconda_GUI widget
        self.singleshot = singleshot
        treeLabel = QtWidgets.QLabel("Select message data for display")
        self.treeWidget = QtWidgets.QTreeWidget()
        self.treeWidget.setObjectName("filtersTreeWidget")
        treeLabel.setBuddy(self.treeWidget)
        if self.dataBack.args.debug:
            self.buttonPdb = QtWidgets.QPushButton()
            self.buttonPdb.setText("pdb")
            self.buttonPdb.clicked.connect(self.pdbset)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(treeLabel)
        vbox.addWidget(self.treeWidget)
        if self.dataBack.args.debug:
            vbox.addWidget(self.buttonPdb)
        self.setLayout(vbox)

        # for running this class solo
        if singleshot:
            QtCore.QTimer.singleShot(0, self.populateTree)

        # Give the tree headers even if not populated
        self.treeWidget.clear()
        self.treeWidget.setColumnCount(2)
        self.treeWidget.setHeaderLabels(["Message Name", "ID/PGN", "Payload size (bytes)", "Description"])
        self.treeWidget.setItemsExpandable(True)

    def populateTree(self, selectedFilter=None):
        self.messages = self.dataBack.messages
        self.treeWidget.clear()
        self.treeWidget.setItemsExpandable(True)
        for messageName in sorted(self.messages):
            # We don't want to use anonymous messages, so skip them.
            if self.messages[messageName].anonymous:
                continue
            # Create a top-level widget for the  message name
            messageNameWidget = QtWidgets.QTreeWidgetItem(self.treeWidget)
            messageNameWidget.setText(0, self.messages[messageName].name)
            if self.messages[messageName].pgn:
                messageNameWidget.setText(1, "PGN: {}".format(self.messages[messageName].pgn))
            else:
                if self.messages[messageName].format == CAN_FORMAT_EXTENDED:
                    messageNameWidget.setText(1, "ID: 0x{:08X}".format(self.messages[messageName].id))
                else:
                    messageNameWidget.setText(1, "ID: 0x{:03X}".format(self.messages[messageName].id))
            # Include the size of the payload, in bytes
            messageNameWidget.setText(2, str(self.messages[messageName].size))
            # Set the description
            messageNameWidget.setText(3, self.messages[messageName].desc)
    # container will be a map from messageInfo name to its widgetmessageNames.
            self.dataBack.container[messageNameWidget.text(0)] = []
            orderedList = self.getFieldsByOffset(self.messages[messageName])
            #for field in self.messages[messageName]:
            for fieldName in orderedList:
                # Create a mid-level node 
                fieldInfo = self.messages[messageName].fields[fieldName]
                child = QtWidgets.QTreeWidgetItem(messageNameWidget)
                child.setText(0, fieldName)
                self.insertFieldAttributes(self.messages[messageName].fields[fieldName],
                                                                        child)
                self.dataBack.container[messageNameWidget.text(0)].append(child)
            messageNameWidget.sortChildren(2, 0) 
            self.treeWidget.expandItem(messageNameWidget)
        self.treeWidget.resizeColumnToContents(0)
        if not self.singleshot:
            self.parent.filterTable.populateTable()

    def getFieldsByOffset(self, messageInfo):
        return self.realParent.getFieldsByOffset(messageInfo)

    def insertFieldAttributes(self, field, child):
        attr = QtWidgets.QTreeWidgetItem(child)
        attr.setText(0, "Type:   " + str(field.type))
        attr = QtWidgets.QTreeWidgetItem(child)
        attr.setText(0, "Length: " + str(field.length))
        attr = QtWidgets.QTreeWidgetItem(child)
        attr.setText(0, "Offset: " + str(field.offset))
        if field.type == 'int':
            attr = QtWidgets.QTreeWidgetItem(child)
            try:
                attr.setText(0, "Signed: " + field.signed)
            except TypeError:  # Couldn't convert 'NoneType' to string
                attr.setText(0, "Signed: no")
            if field.units == None:
                attr = QtWidgets.QTreeWidgetItem(child)
                attr.setText(0, "Units: " + field.units)
            attr = QtWidgets.QTreeWidgetItem(child)
            attr.setText(0, "Scaling: " + str(field.scaling))

    def pdbset(self):
        QtCore.pyqtRemoveInputHook()
        pdb.set_trace()


