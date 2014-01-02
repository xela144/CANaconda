# FiltersTreeWidget class is instantiated in ui_mainwindow.py
# Each time this widget is modified, the messageInfoTable widget gets updated.

from PyQt5 import QtCore, QtWidgets
# from PyQt5.QtWidgets import QMessageBox
import pdb


class FiltersTreeWidget(QtWidgets.QDialog):

    def setup(self, parent, dataBack, singleshot=False):
        super(FiltersTreeWidget, self).__init__()
        self.dataBack = dataBack
        self.parent = parent
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
        self.treeWidget.setHeaderLabels(["Filter Name", "ID or PGN"])
        self.treeWidget.setItemsExpandable(True)

    def populateTree(self, selectedFilter=None):
        self.messages = self.dataBack.messages
        self.treeWidget.clear()
        self.treeWidget.setItemsExpandable(True)

        for messageInfo in self.messages:
            # Create a top-level messageName
            messageName = QtWidgets.QTreeWidgetItem(self.treeWidget)
            messageName.setText(0, self.messages[messageInfo].name)
            if self.messages[messageInfo].pgn:
                messageName.setText(1, "PGN: " + self.messages[messageInfo].pgn)
            else:
                messageName.setText(1, "ID: " + self.messages[messageInfo].id)
            # container will be a map from messageInfo name to its widgetmessageNames.
            self.dataBack.container[messageName.text(0)] = []
            for field in self.messages[messageInfo]:
                # Create a mid-level node that is checkable and
                # expanded.
                child = QtWidgets.QTreeWidgetItem(messageName)
                child.setText(0, field)
                #child.setCheckState(0, QtCore.Qt.Checked)
                self.insertFieldAttributes(self.messages[messageInfo].fields[field],
                                                                        child)
                self.dataBack.container[messageName.text(0)].append(child)
            self.treeWidget.expandItem(messageName)
        self.treeWidget.resizeColumnToContents(0)
        if not self.singleshot:
            self.parent.filterTable.populateTable()

    def insertFieldAttributes(self, field, child):
        attr = QtWidgets.QTreeWidgetItem(child)
        attr.setText(0, "Length: " + field.length)
        attr = QtWidgets.QTreeWidgetItem(child)
        attr.setText(0, "Offset: " + field.offset)
        attr = QtWidgets.QTreeWidgetItem(child)
        attr.setText(0, "Signed: " + field.signed)
        attr = QtWidgets.QTreeWidgetItem(child)
        attr.setText(0, "Units: " + field.units)
        attr = QtWidgets.QTreeWidgetItem(child)
        attr.setText(0, "Scaling: " + field.scaling)
        attr = QtWidgets.QTreeWidgetItem(child)
        attr.setText(0, "Endian: " + field.endian)

    def pdbset(self):
        QtCore.pyqtRemoveInputHook()
        pdb.set_trace()


def main():
    import backend
    import canpython
    import argparse
    import sys
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    args.nogui = None
    args.fast = None
    args.debug = False
    dataBack = backend.CanData(args)
    canpython.xmlimport(dataBack, args, 'xmltest.xml')
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
    ui = FiltersTreeWidget()
    singleshot = True
    ui.setup(None, dataBack, singleshot)
    ui.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
