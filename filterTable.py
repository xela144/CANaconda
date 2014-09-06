# The FilterTable class gets instantiated in ui_mainwindow.py
# This table gets populated each time a new message is seen for the first time
# on the bus.
# Changing units and filtering by value is done here.

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QHeaderView
import pdb
import backend
from PyQt5.QtCore import pyqtRemoveInputHook as pyqtrm
import time

# Columns:
CHECKBOX, MESSAGE, FIELD, VALUE, FILTER, UNITS, RATE = range(7)


class FilterTable(QtWidgets.QWidget):
    comboChanged = QtCore.pyqtSignal(int)

    def setup(self, dataBack, parent, singleshot=False):
        super(FilterTable, self).__init__()
        self.dataBack = dataBack
        self.parent = parent
        self.singleshot = singleshot

        tableLabel = QtWidgets.QLabel("Messages seen so far:")
        self.tableWidget = QtWidgets.QTableWidget()
        self.tableWidget.setObjectName("tablewidget")
        # Hide row numbers:
        self.tableWidget.verticalHeader().setVisible(False)
        tableLabel.setBuddy(self.tableWidget)

        if self.dataBack.args.debug:
            self.buttonPdb = QtWidgets.QPushButton()
            self.buttonPdb.setText("pdb")
            self.buttonPdb.clicked.connect(self.pdbset)
            self.buttonPopulate = QtWidgets.QPushButton()
            self.buttonPopulate.setText("populateTable()")
            self.buttonPopulate.clicked.connect(self.populateTable)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(tableLabel)
        vbox.addWidget(self.tableWidget)

        if self.dataBack.args.debug:
            vbox.addWidget(self.buttonPopulate)
            vbox.addWidget(self.buttonPdb)

        self.setLayout(vbox)
        if singleshot:
            self.populateTable()

    def populateTable(self):
        try:
            self.tableWidget.itemChanged.disconnect(self.filterByValue)
            self.tableWidget.itemChanged.disconnect(
                                   self.parent.update_messageInfo_to_fields)
        except:
            pass
        self.tableWidget.clear()
        self.tableWidget.setSortingEnabled(False)
        # a list of all 'filter', 'field' pairs to be displayed in table:
        displayList = self.getDisplayList()
        self.tableWidget.setRowCount(len(displayList))
        headerList = ['', 'Message', 'Field', 'Latest value',
                      'Filter', 'Units', 'Rate']
        self.tableWidget.setColumnCount(len(headerList))
        self.tableWidget.setHorizontalHeaderLabels(headerList)
        # a map from (filter,field) to row
        self.tableMap = {}
        for row, tuple in enumerate(displayList):
            messageInfoName, fieldName = tuple
            checkBoxItem = QtWidgets.QTableWidgetItem()
            checkBoxItem.setCheckState(QtCore.Qt.Unchecked)
            checkBoxItem.setToolTip("<font color=black>Check box to display message</font>")
            self.tableWidget.setItem(row, CHECKBOX, checkBoxItem)
            ##
            nameItem = QtWidgets.QTableWidgetItem(messageInfoName)
            nameItem.setFlags(QtCore.Qt.ItemFlags(~QtCore.Qt.ItemIsEditable))
            nameItem.setFlags(QtCore.Qt.ItemFlags(QtCore.Qt.ItemIsEnabled))
            self.tableWidget.setItem(row, MESSAGE, nameItem)
            ##
            fieldItem = QtWidgets.QTableWidgetItem(fieldName)
            fieldItem.setFlags(QtCore.Qt.ItemFlags(~QtCore.Qt.ItemIsEditable))
            fieldItem.setFlags(QtCore.Qt.ItemFlags(QtCore.Qt.ItemIsEnabled))
            self.tableWidget.setItem(row, FIELD, fieldItem)
            ##
            valueItem = QtWidgets.QTableWidgetItem()
            valueItem.setFlags(QtCore.Qt.ItemFlags(~QtCore.Qt.ItemIsEditable))
            valueItem.setFlags(QtCore.Qt.ItemFlags(QtCore.Qt.ItemIsEnabled))
            self.tableWidget.setItem(row, VALUE, valueItem)
            ##
            fieldData = self.dataBack.messages[messageInfoName].fields[fieldName]
            ##
            if len(fieldData.byValue) == 0:
                byValueText = ''
            else:
                byValueText = str(fieldData.byValue)[1:-1]
            byValue = QtWidgets.QTableWidgetItem(byValueText)
            byValue.setToolTip("<font color=black>Enter a value to match, or choose an inequality with &lt; or &gt;.</font>")
            self.tableWidget.setItem(row, FILTER, byValue)
            ##

            # If there is a valid conversion, its units will show up in 
            # conversionMap
            if fieldData.units in backend.conversionMap:
                unitsComboBox = QtWidgets.QComboBox()
                for key in list(backend.conversionMap[fieldData.units].keys()):
                    unitsComboBox.addItem(key)
                unitsComboBox.setCurrentText(fieldData.units)
                self.tableWidget.setCellWidget(row, UNITS, unitsComboBox)
                unitsComboBox.currentTextChanged.connect(self.changeUnits)
            else:
                _units = QtWidgets.QTableWidgetItem(fieldData.units)
                _units.setFlags(QtCore.Qt.ItemFlags(~QtCore.Qt.ItemIsEditable))
                _units.setFlags(QtCore.Qt.ItemFlags(QtCore.Qt.ItemIsEnabled))
                self.tableWidget.setItem(row, UNITS, _units)
                
            # Update table map dict. This is used to display the latest message
            # in the tableWidget
            self.tableMap[(messageInfoName, fieldName)] = row

            ## rate column
            rateItem = QtWidgets.QTableWidgetItem()
            rateItem.setFlags(QtCore.Qt.ItemFlags(~QtCore.Qt.ItemIsEditable))
            rateItem.setFlags(QtCore.Qt.ItemFlags(QtCore.Qt.ItemIsEnabled))
            self.tableWidget.setItem(row, RATE, rateItem)

        # Before returning, finish off with signals and table flags/geometry
        self.tableWidget.itemChanged.connect(self.filterByValue)
        self.tableWidget.itemChanged.connect(
                                     self.parent.update_messageInfo_to_fields)
        self.tableWidget.itemChanged.connect(self.parent.csvOutputSet)
        #self.tableWidget.setSortingEnabled(True)  #  Not working
        #self.tableWidget.sortByColumn(0,0)        # 
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.setColumnWidth(VALUE, 120)

        # STRETCHY CODE
        #self.tableWidget.horizontalHeader().setSizePolicy(3,3)
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        #self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)  
        #self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)  


    # Change units based on comboBox widget and update dataBack
    def changeUnits(self, text):
        widgyWidge = QtWidgets.QApplication.focusWidget()
        if widgyWidge:
            index = self.tableWidget.indexAt(widgyWidge.pos())
        row = index.row()
        messageInfoName = self.tableWidget.item(row, MESSAGE).text()
        fieldName = self.tableWidget.item(row, FIELD).text()
        newUnits = text
        self.dataBack.messages[messageInfoName].fields[fieldName]\
                                              .unitsConversion = newUnits


    # Populate the "Latest value" and "Rate" columns by calling update() on table.
    def updateValueInTable(self):
        # Use tableMap as {('filter','field'): row)}
        for tuple in self.tableMap:
            # first break apart the tuples:
            messageInfo, field = tuple
            # next get the row:
            row = self.tableMap[tuple]

            # Get the latest freqency value
            frequencyQueue = self.dataBack.frequencyMap[messageInfo]
            newRate = 0
            try:
                # If we haven't seen a new messages in the last 3 seconds,
                # set the frequency to 0.
                if time.time() - frequencyQueue.queue[-1] > 3:
                    newRate = 0
                else:
                    newRate = self.dataBack.latest_frequencies[messageInfo]
            # Will throw exception for first few runs; ignore.
            except IndexError:
                pass

            # If newRate < 1Hz, take reciprocal to give time period in seconds
            if newRate < 1 and newRate > 0:
                newRate = "{:5.1f}s".format(1.0/newRate)
            else:
                newRate = "{:5.1f}Hz".format(newRate)

            try:
                # get the update values from dataBack.latest_CANacondaMessages
                newValue = self.dataBack.latest_CANacondaMessages[
                                                            messageInfo][field]
                self.tableWidget.item(row, VALUE).setText(str(newValue))
                self.tableWidget.item(row, RATE).setText(newRate)
            except KeyError:
                pass
        # if viewport() is not called, update is slow
        self.tableWidget.viewport().update()


    # Get a list of format ('filter', 'field') to be displayed
    # in the tableWidget
    def getDisplayList(self):
        messages_dict = self.dataBack.messagesSeenSoFar
        displayList = []
        for messageInfo in messages_dict:
            for field in messages_dict[messageInfo]:
                displayList.append((messageInfo, field))
        return displayList

    # This function needs to be modified so that if an invalid
    # entry occurs, a dialog window warns the user.
    def filterByValue(self, item):
        if item.column() != FILTER:
            return
        if self.dataBack.logflag:
            # FIXME
            # This prevents the user from editing the 'byValue' filter while logging
            # is happening, but it doesn't have the intended effect of disabling the
            # entire tableWidget.
            self.tableWidget.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
            return
        valueString = item.text()
        currentRow = item.row()
        messageInfoName = self.tableWidget.item(currentRow, MESSAGE).data(0)
        fieldName = self.tableWidget.item(currentRow, FIELD).data(0)
        self.dataBack.messages[messageInfoName].fields[fieldName].byValue = []
        byValueList = self.dataBack.messages[messageInfoName]\
                                                .fields[fieldName].byValue
        for value in valueString.split(','):
            try:
                byValueList.append(float(value))
                self.tableWidget.item(currentRow, FILTER).setBackground(QtCore.Qt.cyan)
            except ValueError:
                # The filter was a string, in which case the user is notified by seeing
                # the text change to 'None'
                # This is also how the user clears a filter. FIXME: add this to a mouseover.
                self.dataBack.messages[messageInfoName].fields[fieldName].byValue = []
                self.tableWidget.item(currentRow, FILTER).setText('None')
                self.tableWidget.item(currentRow, FILTER).setBackground(QtCore.Qt.white)

    # Disable items that are normally editable in the tableWidget. 
    def enableItemsAfterLogging(self):
        i = 0
        count = self.tableWidget.rowCount()
        while i < count:
            # First make a QtWidgetItem.flags() object.
            currentFilterFlags = self.tableWidget.item(i,FILTER).flags()
            # Mask the flag object and set the item to 'uneditable'
            self.tableWidget.item(i,FILTER).setFlags(currentFilterFlags | QtCore.Qt.ItemIsEnabled)

            currentCheckboxFlags = self.tableWidget.item(i,CHECKBOX)
            self.tableWidget.item(i,CHECKBOX).setFlags(currentFilterFlags | QtCore.Qt.ItemIsEnabled)

            # Note that for the Units column, there are no flags for the items
            # there, since we have used 'setCellWidget' and inserted a combobox
            # there.
            i += 1

    # Disable items that are normally editable in the tableWidget. 
    def disableItemsForLogging(self):
        i = 0
        count = self.tableWidget.rowCount()
        while i < count:
            # First make a QtWidgetItem.flags() object.
            currentFilterFlags = self.tableWidget.item(i,FILTER).flags()
            # Mask the flag object and set the item to 'uneditable'
            self.tableWidget.item(i,FILTER).setFlags(currentFilterFlags & ~QtCore.Qt.ItemIsEnabled)

            currentCheckboxFlags = self.tableWidget.item(i,CHECKBOX)
            self.tableWidget.item(i,CHECKBOX).setFlags(currentFilterFlags & ~QtCore.Qt.ItemIsEnabled)

            # Note that for the Units column, there are no flags for the items
            # there, since we have used 'setCellWidget' and inserted a combobox
            # there.
            # FIXME: won't work. self.tableWidget.itemAt(i,UNITS).setDisabled(True)
            i += 1


    def pdbset(self):
        pyqtrm()
        pdb.set_trace()


# For debug purposes -- delete later
def main():
    import backend
    import CANaconda
    import argparse
    import sys
    import filtersTreeWidget
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    args.nogui = None
    args.fast = None
    args.debug = False
    dataBack = backend.CanData(args)
    CANaconda.xmlImport(dataBack, 'exampleMetaData.xml')
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
    singleshot = True
    tree = filtersTreeWidget.FiltersTreeWidget()
    tree.setup(None, dataBack, singleshot)
    ui = FilterTable()
    ui.setup(dataBack, singleshot)
    tree.show()
    ui.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
