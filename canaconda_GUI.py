"""
This is the GUI script. The general GUI setup is done using the  pyuic5-generated code
that we get from Qt Designer. Once that setup function is called, we proceed to insert our
own widgets, and our logic goes on top of that.
"""


from PyQt5 import QtCore, QtWidgets, QtGui
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

from canaconda_mainwindow import *


class Ui_CANaconda_GUI(QtCore.QObject):
    startHourGlass = pyqtSignal()
    outmsgSignal = pyqtSignal()
    def __init__(self, dataBack):
        QtCore.QObject.__init__(self) # Without this, the PyQt wrapper is created but the C++ object is not!!!
        from PyQt5.QtWidgets import QApplication, QMainWindow, QStyleFactory
        import canaconda_mainwindow
        import sys
        app = QApplication(sys.argv)
        app.setStyle(QStyleFactory.create("Fusion"))
        self.mainWindow = QMainWindow()
        #FIXME this ui business might get confusing and hard to maintain
        self.ui = canaconda_mainwindow.Ui_CANaconda_MainWindow()
        self.ui.setupUi(self.mainWindow)
       
        self.dataBack = dataBack
        self.insertWidgets()

        self.mainWindow.show()
        sys.exit(app.exec_())


    def insertWidgets(self):
        # First the comports code
        self.ui.menuChoose_port = QtWidgets.QMenu(self.ui.menuAction) 
        self.ui.menuChoose_port.setObjectName("menuChoose_port")
        self.ui.menuChoose_port.setTitle("Choose Port")
        for com in comports():
            _port = QtWidgets.QAction(self.mainWindow)
            _port.setText(com[0])
            _port.triggered.connect(self.comportSelect)
            self.ui.menuChoose_port.addAction(_port)
        self.ui.menuAction.addAction(self.ui.menuChoose_port.menuAction())

        # Here we set up one of the tabs
        self.ui.filterTable = filterTable.FilterTable()
        self.ui.filterTable.setup(self.dataBack, self)
        self.ui.filterTable.setObjectName("filterTable")
        self.ui.filterTable.populateTable()
        self.ui.tabWidget.addTab(self.ui.filterTable, "Units and filtering by value")
    
        # set up the other tab
        self.ui.filtersTreeWidget = filtersTreeWidget.FiltersTreeWidget()
        self.ui.filtersTreeWidget.setup(self.ui, self.dataBack)
        self.ui.tabWidget.addTab(self.ui.filtersTreeWidget, "View Meta Data")

        # Now set up the transmit grid
        self.ui.transmitGrid = transmitGrid.TransmitGridWidget(self.ui.transmitWidget)
        self.ui.transmitGrid.setup(self.ui.transmitWidget, self.dataBack)
        self.ui.transmitGrid.setObjectName("transmitGrid")

        # start connecting signals and slots
        self.ui.actionLoad_Filters_From_File.triggered.connect(self.loadFilter)
        self.ui.loggingButton.clicked.connect(self.saveToFile)
        self.ui.displayCombo.currentIndexChanged.connect(self.setOutput)
        self.ui.displayCombo.currentIndexChanged.connect(self.updateButtonLoggingText)




    def updateMessageStream(self):
        """
        Update the message stream. Connected to the 'parsedMsgPut' signal.
        """
        outmsg = self.getMessage(self.dataBack.CANacondaRxMsg_queue)
        if outmsg is not None:
            self.ui.messagesTextBrowser.append("%s" % outmsg)
            self.outmsgSignal.emit()


    def getMessage(self, CANacondaRxMsg_queue):
        """
        Called by updateMessageStream. 'messageInfoFlag' is set when the metadata is loaded
        GUI_rawFlag is set to False when program initalizes, but is set to True only when user
        selects the 'Raw' display option from the combo-box.

        """
        CANacondaMessage = CANacondaRxMsg_queue.get()
        if self.dataBack.messageInfoFlag is False or self.dataBack.GUI_rawFlag:
            return outmessage.noGuiParse(self.dataBack, CANacondaMessage)
        elif self.dataBack.GUI_CSVflag:
            return outmessage.guiParseCSV(self.dataBack, CANacondaMessage)
        return outmessage.noGuiParse(self.dataBack, CANacondaMessage)

    def setBaud(self):
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
        self.serialThread = threading.Thread(target=self.dataBack.canPort.getMessages, args=(self.serialCAN,))
        self.serialThread.daemon = True

        # Set the canPort.live flag back to True, otherwise the thread 
        # will return immediately after starting it.
        self.dataBack.canPort.live = True

        # Now start the thread
        self.serialThread.start()
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
        self.freqTimer.timeout.connect(self.ui.filterTable.updateValueInTable)
        self.freqTimer.start(1000)

    # begin receiving messages and push to CANacondaRxMsg_queue
    def pyserialInit(self):
        self.dataBack.canPort = canport.CANPortGUI(self.dataBack)
        self.serialCAN = self.dataBack.canPort.pyserialInit()

        # The serialCAN thread was initialized without error
        if type(self.serialCAN) != int:
            self.dataBack.canTranscoderGUI.parsedMsgPut.connect(self.updateMessageStream)
            self.dataBack.canTranscoderGUI.parsedMsgPut.connect(
                                               self.ui.filterTable.updateValueInTable)
            self.dataBack.canTranscoderGUI.newMessageUp.connect(self.ui.filterTable.populateTable)
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
        self.serialThread = threading.Thread(target=self.dataBack.canPort.getMessages, args=(self.serialCAN,))
        self.serialThread.daemon = True
        self.serialThread.start()
        self.transcoderThread = threading.Thread(target=self.dataBack.canTranscoderGUI.CanTranscoderRun)
        self.transcoderThread.daemon = True
        self.transcoderThread.start()

    def loadFilter(self):
        # These "reset" statements should actually be moved to a
        # reset function that can be called from anywhere in the code.
        self.dataBack.messages = {}
        self.dataBack.messageInfo_to_fields = {}
        self.dataBack.messagesSeenSoFar = {}
        self.dataBack.id_to_name = {}
        self.dataBack.pgn_to_name = {}
        self.dataBack.messageInfoFlag = False
        fileName = None
        while fileName is None:
            fileName = QtWidgets.QFileDialog.getOpenFileName()[0]
        if fileName == '':
            # If user canceled loading file, return
            return

        # Now process our XML file, handling any errors that arise by alerting
        # the user and returning.
        try:
            xmlImport(self.dataBack, fileName)
            # self.dataBack.messageInfoFlag set to true in xmlImport
        except Exception as e:
            self.warnXmlImport(str(e))
            return

        # Save the filename for updating the UI
        self.fileName = fileName

        self.updateFileNameQLabel()
        self.ui.filtersTreeWidget.populateTree()
        self.update_messageInfo_to_fields() # FIXME This is called from filterTable.py
                                            # and may not be necessary here... test this
        # populate the 'transmission' combobox
        self.ui.transmitGrid.populateTxMessageInfoCombo()
        # Enable the combo box that allows user to select message stream format and set to 'decoded'
        self.ui.displayCombo.setDisabled(False)
        self.ui.displayCombo.setCurrentIndex(DECODED)


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
        self.ui.filtersTreeWidget.populateTree()
        self.update_messageInfo_to_fields() # FIXME This is called from filterTable.py
                                            # and may not be necessary here... test this
        # populate the 'transmission' combobox
        self.transmitGrid.populateTxMessageInfoCombo()
        # Enable the combo box that allows user to select message stream format and set to 'decoded'
        self.ui.displayCombo.setDisabled(False)
        self.ui.displayCombo.setCurrentIndex(DECODED)


    # When the metadata file is loaded, the name appears at the upper right corner of UI
    # updateFileNameQLabel handles this.
    def updateFileNameQLabel(self):
        self.fileName = self.fileName.split('/')[-1]
        text = "MetaData file: <font color=grey><i>  " + self.fileName + "</></font>    "
        self.ui.fileNameLabel.setText(text)

    # Connected with displayCombo's currentIndexChanged signal
    def updateButtonLoggingText(self):
        # Before updating the text, make sure we are not currently logging, in which
        # case the button should read "End Logging", and therefore should not be updated.
        if not self.dataBack.logflag:
            self.ui.loggingButton.setText("Start logging as " + self.ui.displayCombo.currentText())
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
    def update_messageInfo_to_fields(self):
        self.dataBack.messageInfo_to_fields = {}
        for row in range(0,self.ui.filterTable.tableWidget.rowCount()):
            if self.ui.filterTable.tableWidget.item(
                    row, filterTable.CHECKBOX).checkState() == QtCore.Qt.Checked:
                name = self.ui.filterTable.tableWidget.item(
                                                row, filterTable.MESSAGE).text()
                field = self.ui.filterTable.tableWidget.item(
                                                row, filterTable.FIELD).text()
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
        currentIndex = self.ui.displayCombo.currentIndex()
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
        self.ui.messagesTextBrowser.clear()


    # This function handles the logging functionality. When the "start logging as..." 
    # button is pressed, this function is called and all messages that were in the
    # message browser are erased and subsequent messages get written to a file. When
    # recording is done, this function is called again to flip the state back to normal.
    def saveToFile(self):
        if self.dataBack.logflag:
            self.ui.loggingButton.setText("Start logging as " + self.ui.displayCombo.currentText()) 
            self.file.write(self.ui.messagesTextBrowser.toPlainText())
            self.file.close()
            # Revert label back to original text
            self.ui.loggingStatusLabel.setText("<font color = grey><i>not recording</i><font>")
            self.dataBack.logflag = False
            # Disable the display combo box so that the user doesn't change anything 
            # by mistake while logging
            self.ui.displayCombo.setDisabled(True)
            self.ui.filterTable.enableItemsAfterLogging()
        else:
            if self.ui.loggingFileName.text() == '':
                self.warnLogging()
                return
            if os.path.isfile(self.ui.loggingFileName.text()):
                overWrite = self.warnOverwrite()
                if overWrite == 0x400000:  # 'don't overwrite'
                    return
                elif overWrite == 0x400:   # 'okay to overwrite'
                   os.remove(self.ui.loggingFileName.text())

            # OK to log. Clear text browser, disable the display combo box, and open a file
            # for writing.
            self.clearTextBrowser()
            self.ui.displayCombo.setDisabled(True)
            self.ui.filterTable.disableItemsForLogging()
            self.file = open(self.ui.loggingFileName.text(), 'w')
            # A header for use with Matlab or other programs:
            if self.dataBack.GUI_CSVflag:
                header = 'time,' + ','.join(self.dataBack.guiCSVDisplayList)
                self.file.write(header)
                self.file.write('\n')
            self.ui.loggingButton.setText("End Logging")
    # Move this functionality to another spot:
            self.ui.loggingStatusLabel.setText("<font color=red><b>\
                                            recording</b></font>    ")
            self.dataBack.logflag = True

    def loggingStatusHandler(self):
        # If we are not logging, then the accompanying text should say so
        if self.dataBack.logflag == False:
            self.ui.loggingStatusLabel.setText("Status:  <font color = grey><i>not recording</i></font>")
            self.messageCount = 0
            return

        # Otherwise, change the text and update the messageCount
        self.statusText = "<font color=red><b><i>recording  </i>" + str(self.messageCount) + "</b></font>"
        self.messageCount += 1
        self.ui.loggingStatusLabel.setText(self.statusText)

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
