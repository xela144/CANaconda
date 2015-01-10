"""
This is the GUI script. The general GUI setup is done using the  pyuic5-generated code
that we get from Qt Designer. Once that setup function is called, we proceed to insert our
own widgets, and our logic goes on top of that.
"""


from PyQt5 import QtCore, QtWidgets, QtGui, uic
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QCursor
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import pyqtRemoveInputHook as pyqtrm
from messageInfo import xmlImport, CAN_FORMAT_EXTENDED
import threading
from serial.tools.list_ports import comports
from CanDataTranscoder import generateMessage
from backend import *
import filtersTreeWidget
import filterTable
import transmitGrid
import outmessage
import canport
import time
import os
import xml.etree.ElementTree as ET

from canport import BAUDLIST, BAUDMAP

# displayList
from outmessage import ID, PGN, BODY, RAW

# Message stream enum
DECODED, RAW_HEX, CSV = range(3)



class Ui_CANaconda_GUI(QtCore.QObject):
    startHourGlass = pyqtSignal()
    outmsgSignal = pyqtSignal()
    def __init__(self, dataBack):
        QtCore.QObject.__init__(self) # Without this, the PyQt wrapper is created but the C++ object is not!!!
        from PyQt5.QtWidgets import QApplication, QMainWindow, QStyleFactory
        import sys
        app = QApplication(sys.argv)
        app.setStyle(QStyleFactory.create("Fusion"))
        self.mainWindow = uic.loadUi('canaconda_mainwindow.ui')

        self.dataBack = dataBack
        self.insertWidgets()

        self.mainWindow.show()
        sys.exit(app.exec_())


    def insertWidgets(self):
        """
        Insert the widgets into the mainWindow that we imported in the loadUi() call.
        """
        # First the comports menu
        self.mainWindow.menuChoose_port = QtWidgets.QMenu(self.mainWindow.menuAction) 
        self.mainWindow.menuChoose_port.setObjectName("menuChoose_port")
        self.mainWindow.menuChoose_port.setTitle("Choose Port")
        self.mainWindow.menuAction.addAction(self.mainWindow.menuChoose_port.menuAction())

        # Here we set up one of the tabs
        self.mainWindow.filterTable = filterTable.FilterTable()
        self.mainWindow.filterTable.setup(self.dataBack, self)
        self.mainWindow.filterTable.setObjectName("filterTable")
        self.mainWindow.filterTable.populateTable()
        self.mainWindow.tabWidget.addTab(self.mainWindow.filterTable, "Units and filtering by value")
    
        # set up the other tab
        self.mainWindow.filtersTreeWidget = filtersTreeWidget.FiltersTreeWidget()
        self.mainWindow.filtersTreeWidget.setup(self.mainWindow, self.dataBack)
        self.mainWindow.tabWidget.addTab(self.mainWindow.filtersTreeWidget, "View Meta Data")

        # Now set up the transmit grid
        self.mainWindow.transmitGrid = transmitGrid.TransmitGridWidget(self.mainWindow.transmitWidget)
        # Sending 'self' as an explicit parameter to retain reference to mainWindow, otherwise
        # reference is overwritten and mainWindow cannot be reached from transmitGrid....
        self.mainWindow.transmitGrid.setup(self.mainWindow.transmitWidget, self.dataBack, self)
        self.mainWindow.transmitGrid.setObjectName("transmitGrid")

        if self.dataBack.args.messages != None:
            self.commandLineLoadFilter()
        if self.dataBack.args.port != None:
            self.comportSelect()

        # start connecting signals and slots
        # Load metadata filter on menu item click
        self.mainWindow.actionLoad_Filters_From_File.triggered.connect(self.loadFilter)

        # Log message stream to file on pushbutton click
        self.mainWindow.loggingButton.clicked.connect(self.saveToFile)

        # Change display type in message stream based on combo box index
        self.mainWindow.displayCombo.currentIndexChanged.connect(self.setOutput)

        # Update logging button text based on combo box index
        self.mainWindow.displayCombo.currentIndexChanged.connect(self.updateButtonLoggingText)

        # Cause available serial ports to be scanned when user opens menu
        self.mainWindow.menuAction.aboutToShow.connect(self.setChoose_port_Actions)

        # Clear the message stream window on button push
        self.mainWindow.buttonClearMessageStream.clicked.connect(self.clearTextBrowser)

    def setChoose_port_Actions(self):
        """
        Populate the list of available comports. Called each time user clicks on 'Action' menu
        """
        # If there are already QActions for comports, remove them.
        self.mainWindow.menuChoose_port.clear()

        # Now add the current list of serial ports, obtained from list returned by comports() call.
        for com in comports():
            _port = QtWidgets.QAction(self.mainWindow)
            _port.setText(com[0])
            _port.triggered.connect(self.comportSelect)
            self.mainWindow.menuChoose_port.addAction(_port)

    def updateMessageStream(self):
        """
        Update the message stream. Connected to the 'parsedMsgPut' signal.
        """
        outmsg = self.getMessage(self.dataBack.CANacondaRxMsg_queue)
        if outmsg is not None:
            self.mainWindow.messagesTextBrowser.append("%s" % outmsg)
            self.outmsgSignal.emit()


    def getMessage(self, CANacondaRxMsg_queue):
        """
        Called by updateMessageStream. 'messageInfoFlag' is set to True when the metadata is loaded.
        GUI_rawFlag is set to False when program initalizes, but is set to True only when user
        selects the 'Raw' display option from the combo-box.
        """
        CANacondaMessage = CANacondaRxMsg_queue.get()
        # Switch statement depending on current UI settings
        if self.dataBack.messageInfoFlag is False or self.dataBack.GUI_rawFlag:
            return outmessage.noGuiParse(self.dataBack, CANacondaMessage)
        elif self.dataBack.GUI_CSVflag:
            return outmessage.guiParseCSV(self.dataBack, CANacondaMessage)
        return outmessage.noGuiParse(self.dataBack, CANacondaMessage)

    # FIXME This code didn't get ported over with .ui switch. Need to add QMenu to .ui file
    def setBaud(self):
        """
        Set the baud rate for the CANusb device (does not affect serial connection)
        """
        self.setHourGlass()
        text = self.sender().text()
        baudrate = BAUDMAP[text]
        # Setting this flag to False will cause the canPort serial thread
        # to return, ending the thread. The serial connection will still
        # be open.
        self.dataBack.canPort.live = False
        # Sleep in order to allow serial thread to return
        time.sleep(1)

        # Now it is okay to set the baud
        self.dataBack.canPort.changeCanUSBbaud(self.serialCAN, baudrate)
        
        # Now that the CanUSB baud has changed, we can start a new serial
        # thread using the CANPort class.
        self.serialRxThread = threading.Thread(target=self.dataBack.canPort.getMessages, args=(self.serialCAN,))
        self.serialRxThread.daemon = True

        # Set the canPort.live flag back to True, otherwise the thread 
        # will return immediately after starting it.
        self.dataBack.canPort.live = True

        # Now start the thread
        self.serialRxThread.start()
        self.removeHourGlass()


    def comportSelect(self):
        if self.dataBack.args.port != None:
            self.dataBack.comport = self.dataBack.args.port[0]
        else:
            self.dataBack.comport = self.sender().text()
        self.dataBack.comportsFlag = True

        # There are a few sequential items of business that need to happen when user
        # selects the comport... Make this an init function instead???
        self.setHourGlass()
        if not self.dataBack.messageInfoFlag:
            self.dataBack.GUI_rawFlag = True
        else:
            self.setOutput()
        self.pyserialHandler()
        
        
    # Called when user has selected a comport. Try to create the serial thread, and if successful,
    # run it. Also create a timer for updating the message frequency in the table widget.
    def pyserialHandler(self):
        # Serial connection thread
        # For the first run, everything is fine. However, if user selects
        # comport again, a new thread is created. Bad.
        alreadyStreaming = self.dataBack.alreadyStreaming
        Success = self.pyserialInit()

        # Run the serial thread if it was created successfully
        if not alreadyStreaming and Success:
            self.pyserialRun()

        # Use this timer as a watchdog for when a node on the bus is shut off.
        # Without it, frequency column won't go back to zero.
        self.freqTimer = QtCore.QTimer()
        self.freqTimer.timeout.connect(self.mainWindow.filterTable.updateValueInTable)
        self.freqTimer.start(1000)

    # begin receiving messages and push to CANacondaRxMsg_queue
    def pyserialInit(self):
        self.dataBack.canPort = canport.CANPortGUI(self.dataBack)
        self.serialCAN = self.dataBack.canPort.pyserialInit()

        # The serialCAN thread was initialized without error
        if type(self.serialCAN) != int:
            self.dataBack.canTranscoderGUI.parsedMsgPut.connect(self.updateMessageStream)
            self.dataBack.canTranscoderGUI.parsedMsgPut.connect(
                                               self.mainWindow.filterTable.updateValueInTable)
            self.dataBack.canTranscoderGUI.newMessageUp.connect(self.mainWindow.filterTable.populateTable)
            self.removeHourGlass()
            self.setStreamingFlag()
            return True

        # Error handling here. Create modal dialog windows. Move to another function
        else:
            ErrorType = self.serialCAN
            if ErrorType == self.dataBack.canPort.ERROR_NO_DATA:
                ErrorString = 'There is no data on the CAN bus.\nAre CAN nodes connected?'
            elif ErrorType == self.dataBack.canPort.ERROR_NO_CONNECT:
                ErrorString = 'Could not connect to port  {}'.format(self.dataBack.comport)
            elif ErrorType == self.dataBack.canPort.ERROR_TIMEOUT:
                ErrorString = 'Time-out in sending command \'O\'\n to CANusb device.'
            elif ErrorType == self.dataBack.canPort.ERROR_BAUD:
                ErrorString = 'Could not set the baud rate for CAN bus'

            self.serialWarn(ErrorString)
            self.removeHourGlass()

            # If an incorrect port was given as a command-line argument, it now
            # needs to be deleted
            self.dataBack.args.port = None
            return False


    def pyserialRun(self):
        """
        Creates and starts the serial thread(s). While we're at it, start the 
        decode/encode thread as well.
        """
        self.serialRxThread = threading.Thread(target=self.dataBack.canPort.getMessages, 
                                                args=(self.serialCAN,))
        self.serialRxThread.daemon = True
        self.serialRxThread.name = 'serialRxThread'
        self.serialRxThread.start()
#        self.serialTxThread = threading.Thread(target=self.dataBack.canPort.sendMessages, 
#                                                args=(self.serialCAN,))
#        self.serialTxThread.daemon = True
#        self.serialTxThread.name = 'serialTxThread'
#        self.serialTxThread.start()
        self.transcoderThread = threading.Thread(target=self.dataBack.canTranscoderGUI.CanTranscoderRun)
        self.transcoderThread.daemon = True
        self.transcoderThread.name = 'transcoderThread'
        self.transcoderThread.start()

    # Clear the backend meta data
    def resetAllMetadata(self):
        # Get rid of the messageInfo filter objects, and update UI and backend accordingly
        self.dataBack.messages = {}
        self.dataBack.messageInfoFlag = False
        self.fileName = 'None loaded'   # Normally this gets overwritten immediately
        self.updateFileNameQLabel()  
        
        # The map from message name to the fields contained with that message
        self.dataBack.messageInfo_to_fields = {}
        
        # The set of all messages seen on the bus
        self.dataBack.messagesSeenSoFar = {}

        # A map from message ID to its name
        self.dataBack.id_to_name = {}

        # A map from message PGN to its name
        self.dataBack.pgn_to_name = {}

    # Load metadata after user has selected that option from the menu
    def loadFilter(self):
        fileName = None
        while fileName is None:
            fileName = QtWidgets.QFileDialog.getOpenFileName()[0]
        if fileName == '':
            # If user canceled loading file, return
            return

        # Now process our XML file, handling any errors that arise by alerting
        # the user and returning.
        try:
            self.resetAllMetadata()
            xmlImport(self.dataBack, fileName)
            # self.dataBack.messageInfoFlag set to true in xmlImport
        except Exception as e:
            self.warnXmlImport(str(e))
            return
        # Save the filename for updating the UI
        self.fileName = fileName
        # The current metadata file needs to be displayed in the UI
        self.updateFileNameQLabel()
        self.mainWindow.filtersTreeWidget.populateTree()
        # populate the 'transmission' combobox
        self.mainWindow.transmitGrid.populateTxMessageInfoCombo()
        # Enable the combo box that allows user to select message stream format and set to 'decoded'
        self.mainWindow.displayCombo.setDisabled(False)
        self.mainWindow.displayCombo.setCurrentIndex(DECODED)

    # If --messages argument was given, this function loads the metadata file.
    def commandLineLoadFilter(self):
        self.dataBack.messageInfoFlag = True
        fileName = self.dataBack.args.messages
        try:
            xmlImport(self.dataBack, fileName)
        except Exception as e:
            self.warnXmlImport(str(e))
            return
        # Save the filename for updating the UI
        self.fileName = fileName
        self.updateFileNameQLabel()
        self.mainWindow.filtersTreeWidget.populateTree()
        # populate the 'transmission' combobox
        self.mainWindow.transmitGrid.populateTxMessageInfoCombo()
        # Enable the combo box that allows user to select message stream format and set to 'decoded'
        self.mainWindow.displayCombo.setDisabled(False)
        self.mainWindow.displayCombo.setCurrentIndex(DECODED)

    # Get a list of field names sorted by offset, rather than alphabetical order. Useful for
    # when user needs to find field data within large CAN messages.
    def getFieldsByOffset(self, messageInfo):
        unorderedDict = {}
        # Map the offset to a field name
        for fieldName in messageInfo.fields.keys():
            unorderedDict[messageInfo.fields[fieldName].offset] = fieldName
        # Create a list of the offsets, from least to greatest
        offsetList = sorted(unorderedDict)
        orderedList = []
        # Append the field names, ordered by offset
        for offset in offsetList:
            orderedList.append(unorderedDict[offset])
        # Return a list of field names that are ordered by offset.
        return orderedList

    # When the metadata file is loaded, the name appears at the upper right corner of UI
    # updateFileNameQLabel handles this.
    def updateFileNameQLabel(self):
        self.fileName = self.fileName.split('/')[-1]
        text = "MetaData file: <font color=grey><i>  " + self.fileName + "</></font>    "
        self.mainWindow.fileNameLabel.setText(text)

    # Connected with displayCombo's currentIndexChanged signal
    def updateButtonLoggingText(self):
        # Before updating the text, make sure we are not currently logging, in which
        # case the button should read "End Logging", and therefore should not be updated.
        if not self.dataBack.logflag:
            self.mainWindow.loggingButton.setText("Start logging as " + self.mainWindow.displayCombo.currentText())
            # Also, re-enable the DisplayAs combobox


    def notStreamingWarn(self):
        warn = QtWidgets.QMessageBox()
        warn.setText("Message Transmit Error")
        warn.setInformativeText("Make sure you have already begun streaming messages")
        warn.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        warn.exec()

    def comportUnavailable(self):
        pass
    
    # Set the messageInfo_to_fields for correct message stream output
    # This is done by determining which message/field pair the user has selected in the
    # filterTable widget.
    def update_messageInfo_to_fields(self):
        self.dataBack.messageInfo_to_fields = {}
        # Iterate through all the rows in the table
        for row in range(0,self.mainWindow.filterTable.tableWidget.rowCount()):
            # If the checkbox has been checked, store the name and field associated with row
            if self.mainWindow.filterTable.tableWidget.item(
                    row, filterTable.CHECKBOX).checkState() == QtCore.Qt.Checked:
                name = self.mainWindow.filterTable.tableWidget.item(
                                                row, filterTable.MESSAGE).text()
                field = self.mainWindow.filterTable.tableWidget.item(
                                                row, filterTable.FIELD).text()
                # Update dataBack accordingly
                if name in self.dataBack.messageInfo_to_fields:
                    self.dataBack.messageInfo_to_fields[name].append(field)
                else:
                    self.dataBack.messageInfo_to_fields[name] = []
                    self.dataBack.messageInfo_to_fields[name].append(field)

    # For creating the outmessage.
    # recall: DECODED, RAW_HEX, CSV = range(3)
    def setOutput(self):
        if self.dataBack.logflag:
            return
        currentIndex = self.mainWindow.displayCombo.currentIndex()
        if currentIndex == CSV:
            self.dataBack.GUI_CSVflag = True
            self.dataBack.GUI_rawFlag = False
            self.csvOutputSet()
            return

        elif currentIndex == DECODED:
            self.dataBack.GUI_CSVflag = False
            self.dataBack.GUI_rawFlag = False
            self.dataBack.displayList[ID]   = True
            self.dataBack.displayList[PGN]  = True
            self.dataBack.displayList[BODY] = True
            self.dataBack.displayList[RAW]  = False
            return
            
        elif currentIndex == RAW_HEX:
            self.dataBack.GUI_rawFlag = True
            self.dataBack.GUI_CSVflag = False
            self.dataBack.displayList[ID]   = False
            self.dataBack.displayList[PGN]  = False
            self.dataBack.displayList[BODY] = False
            self.dataBack.displayList[RAW]  = True
            return

    # This function is called whenever the filtering is changed 
    # in filterTable object
    def csvOutputSet(self):
        self.dataBack.guiCSVDisplayList = []
        self.dataBack.fieldIndices = {}
        map = sorted(self.dataBack.messageInfo_to_fields.items())
        # this returns a funky list which has to be access as follows:
        i = 1
        for item in map:
            for field in item[1]:
                self.dataBack.guiCSVDisplayList.append(item[0]+'.'+field.replace(' ', '_'))
                self.dataBack.fieldIndices[field] = i
                i += 1

    def clearTextBrowser(self):
        self.mainWindow.messagesTextBrowser.clear()


    # This function handles the logging functionality. When the "start logging as..." 
    # button is pressed, this function is called and all messages that were in the
    # message browser are erased and subsequent messages get written to a file. When
    # recording is done, this function is called again to flip the state back to normal.
    def saveToFile(self):
        if self.dataBack.logflag:
            self.mainWindow.loggingButton.setText("Start logging as " + self.mainWindow.displayCombo.currentText()) 
            self.file.write(self.mainWindow.messagesTextBrowser.toPlainText())
            self.file.close()
            # Revert label back to original text
            self.mainWindow.loggingStatusLabel.setText("<font color = grey><i>not recording</i><font>")
            self.dataBack.logflag = False
            # Disable the display combo box so that the user doesn't change anything 
            # by mistake while logging
            self.mainWindow.displayCombo.setDisabled(True)
            self.mainWindow.filterTable.enableItemsAfterLogging()
        else:
            if self.mainWindow.loggingFileName.text() == '':
                self.warnLogging()
                return
            if os.path.isfile(self.mainWindow.loggingFileName.text()):
                overWrite = self.warnOverwrite()
                if overWrite == 0x400000:  # 'don't overwrite'
                    return
                elif overWrite == 0x400:   # 'okay to overwrite'
                   os.remove(self.mainWindow.loggingFileName.text())

            # OK to log. Clear text browser, disable the display combo box, and open a file
            # for writing.
            self.clearTextBrowser()
            self.mainWindow.displayCombo.setDisabled(True)
            self.mainWindow.filterTable.disableItemsForLogging()
            self.file = open(self.mainWindow.loggingFileName.text(), 'w')
            # A header for use with Matlab or other programs:
            if self.dataBack.GUI_CSVflag:
                header = 'time,' + ','.join(self.dataBack.guiCSVDisplayList)
                self.file.write(header)
                self.file.write('\n')
            self.mainWindow.loggingButton.setText("End Logging")
    # Move this functionality to another spot:
            self.mainWindow.loggingStatusLabel.setText("<font color=red><b>\
                                            recording</b></font>    ")
            self.dataBack.logflag = True

    def loggingStatusHandler(self):
        # If we are not logging, then the accompanying text should say so
        if self.dataBack.logflag == False:
            self.mainWindow.loggingStatusLabel.setText("Status:  <font color = grey><i>not recording</i></font>")
            self.messageCount = 0
            return

        # Otherwise, change the text and update the messageCount
        self.statusText = "<font color=red><b><i>recording  </i>" + str(self.messageCount) + "</b></font>"
        self.messageCount += 1
        self.mainWindow.loggingStatusLabel.setText(self.statusText)

    def resetTime(self):
        self.dataBack.CSV_START_TIME = time.time()

    def warnXmlImport(self, errorString):
        warn = QtWidgets.QMessageBox()
        warn.setText("XML import error")
        warn.setInformativeText(errorString)
        warn.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        warn.exec()


    def serialWarn(self, errorString):
        warn = QtWidgets.QMessageBox()
        warn.setText("Serial connection error")
        warn.setInformativeText(errorString)
        warn.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        warn.exec()
        

    def warnLogging(self):
        ok = QtWidgets.QMessageBox()
        ok.setText("Please enter a file name")
        ok.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        ok.exec()

    def warnOverwrite(self):
        warn = QtWidgets.QMessageBox()
        warn.setText("File already exists: Overwrite?")
        warn.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        warn.setStandardButtons(QtWidgets.QMessageBox.Ok |
                                QtWidgets.QMessageBox.Cancel)
        return warn.exec()

    def setHourGlass(self):
        alreadyStreaming = self.dataBack.alreadyStreaming
        if not alreadyStreaming:
            QApplication.setOverrideCursor(QCursor(QtCore.Qt.WaitCursor))

    def removeHourGlass(self):
        QApplication.restoreOverrideCursor()

    def setStreamingFlag(self):
        self.dataBack.alreadyStreaming = True

    def debugMode(self):
        pyqtrm()
        import pdb
        pdb.set_trace()
