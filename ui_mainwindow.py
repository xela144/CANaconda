# ui_mainwindow.py
# Originally generated with QtCreator and pyuic.
'''
Layout code is executed and GUI will load without any metadata loaded.
When a comport is selected, self.pyserialInit is called, and serial thread
is created. Message streaming will begin.
When a metadata file is loaded, the 'ViewMetadata' tree widget is populated.
When new decoded messages are discovered, the 'newMessageUp' signal is emitted
from the serial thread, self.populateTable.
Message transmission will take place if the 'Activate' pushbutton is pressed
and no error occurs. (error checking not yet implemented)

Recieve queue:  CANacondaRxMsg_queue
transmit queue: CANacondaTxMsg_queue

'''

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QCursor
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import pyqtRemoveInputHook as pyqtrm
from messageInfo import xmlImport, CAN_FORMAT_EXTENDED
import threading
from serial.tools.list_ports import comports
from CanDataTranscoder import encodePayload, generateMessage
from backend import *
import filtersTreeWidget
import filterTable
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

class Ui_MainWindow(QtCore.QObject):
    startHourGlass = pyqtSignal()
    outmsgSignal = pyqtSignal()
    def setupUi(self, mainWindow, dataBack):
        self.dataBack = dataBack
        self.messageCount = 0
#############################
## Layout code
#############################
        mainWindow.setObjectName("mainindow")
        self.centralWidget = QtWidgets.QWidget(mainWindow)
        self.centralWidget.setObjectName("centralWidget")
        self.verticalLayout_top = QtWidgets.QVBoxLayout(self.centralWidget)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout_top.addLayout(self.horizontalLayout)

        self.messagesFrame = QtWidgets.QFrame(self.centralWidget)
        self.messagesFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.messagesFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.messagesFrame.setObjectName("messagesFrame")
        self.messagesFrame.setMinimumWidth(400)
        self.messagesFrame.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                         QtWidgets.QSizePolicy.Expanding)

        #### Logging ####
        self.loggingFrame = QtWidgets.QFrame()
        self.loggingFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.loggingFrame.setObjectName("LOGGINGFRAME")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.loggingFrame)
        self.horizontalLayout_2.setObjectName("HORIZONTAL_LAYOUT_2")
        self.verticalLayout_top.addWidget(self.loggingFrame)

        self.logLabel = QtWidgets.QLabel()
        self.logLabel.setText("Enter filename:")
        self.buttonLogging = QtWidgets.QPushButton()
        self.buttonLogging.setObjectName("save")
        self.buttonLogging.setText("Start logging") 
        self.buttonLogging.clicked.connect(self.saveToFile)
        self.logLabel.setBuddy(self.buttonLogging)
        self.logFileName = QtWidgets.QLineEdit()
        self.logFileName.setObjectName("fileName")
        self.logFileName.returnPressed.connect(self.saveToFile)
        self.loggingStatusLabel = QtWidgets.QLabel()
        self.loggingStatusLabel.setTextFormat(1)
        self.loggingStatusLabel.setText("Status:  <font color=grey><i>not recording</i></font>")
        # Signal handler:
        self.outmsgSignal.connect(self.loggingStatusHandler)
        self.horizontalLayout_2.addWidget(self.logLabel)
        self.horizontalLayout_2.addWidget(self.logFileName)
        self.horizontalLayout_2.addWidget(self.buttonLogging)
        self.horizontalLayout_2.addSpacing(100)
        self.horizontalLayout_2.addWidget(self.loggingStatusLabel)


        #### Transmission ####
        self.txFrame = QtWidgets.QFrame()
        self.txFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.txFrame.setObjectName("TXFRAME")
        self.verticalLayout_top.addWidget(self.txFrame)

        self.txGrid = QtWidgets.QGridLayout(self.txFrame)
        self.txGrid.setHorizontalSpacing(10)
        self.txGrid.setColumnStretch(1, 2)
        self.txGrid.setColumnStretch(3, 2)
        
        # add a vertical layout to the txFrame and put line edits inside it
        # FIXME: Eventually all the firstTx stuff will have to go, as more generic code
        # will have to be written for additional transmission widgets.
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

        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.messagesFrame)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label = QtWidgets.QLabel(self.messagesFrame)
        self.label.setObjectName("messageStreamLabel")
        self.verticalLayout_2.addWidget(self.label)


        #### Display Combobox code ####
        # Choose the format for displaying messages in the Message Stream frame
        # When first launching, default display to 'raw hex' and make inactive
        self.displayLayout = QtWidgets.QHBoxLayout()
        self.verticalLayout_2.addLayout(self.displayLayout)
        self.displayLayout.setObjectName("display combobox layout")
        self.displayLabel = QtWidgets.QLabel()
        self.displayLabel.setText("Display: ")
        self.displayCombo = QtWidgets.QComboBox()
        self.displayLayout.addWidget(self.displayLabel)
        self.displayLayout.addWidget(self.displayCombo)
        
        # Note: displayList must be in order of message stream enum at top of file
        displayList = ["Decoded", "Raw hex", "CSV"]
        self.displayCombo.addItems(displayList)
        self.displayCombo.setDisabled(True)  # FIXME set enabled when metadata loaded
        self.displayCombo.setCurrentIndex(RAW_HEX)
        self.displayCombo.currentIndexChanged.connect(self.setOutput)
        self.displayCombo.currentIndexChanged.connect(self.updateButtonLoggingText) 

        self.messagesTextBrowser = QtWidgets.QTextBrowser(self.messagesFrame)
        self.messagesTextBrowser.setObjectName("messagesTextBrowser")
        #FIXME: set the flag to be able to delete text in the text browser
        self.verticalLayout_2.addWidget(self.messagesTextBrowser)

        if self.dataBack.args.debug:
            self.debug = QtWidgets.QPushButton()
            self.debug.setText("pdb")
            self.debug.clicked.connect(self.debugMode)
            self.buttonsGrid = QtWidgets.QGridLayout()
            self.verticalLayout_2.addLayout(self.buttonsGrid)
            self.buttonsGrid.setObjectName("button grid layout")
            self.buttonsGrid.addWidget(self.debug, 3,1, 1,2)

        self.horizontalLayout.addWidget(self.messagesFrame)
        self.visualizeFrame = QtWidgets.QFrame(self.centralWidget)
        self.visualizeFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.visualizeFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.visualizeFrame.setObjectName("visualizeFrame")
        self.visualizeFrame.setMinimumWidth(555)
        self.visualizeFrame.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                          QtWidgets.QSizePolicy.Expanding)


        ##### Right side #####
        self.verticalLayout = QtWidgets.QVBoxLayout(self.visualizeFrame)
        self.verticalLayout.setObjectName("verticalLayout")

        self.topRightLabels = QtWidgets.QHBoxLayout()
        self.topRightLabels.setObjectName("topRightLabels")
        self.verticalLayout.addLayout(self.topRightLabels)

        self.label_2 = QtWidgets.QLabel(self.visualizeFrame)
        self.label_2.setObjectName("label_2")
        self.topRightLabels.addWidget(self.label_2)

        self.fileNameLabel = QtWidgets.QLabel()
        self.topRightLabels.addWidget(self.fileNameLabel)
        self.fileNameLabel.setText("MetaData file: <font color=grey><i>   None loaded</></font>    ")
#################
# TabWidget, tableWidget, and treeWidget code
#################
        self.tabWidget = QtWidgets.QTabWidget(self.visualizeFrame)
        self.tabWidget.setObjectName("tabWidget")
        self.filterTab = QtWidgets.QWidget()
        self.filterTab.setObjectName("filterTab")
        self.filterTable = filterTable.FilterTable()
        self.filterTable.setup(self.dataBack, self)
        self.filterTable.setObjectName("filterTable")
        self.filterTable.populateTable()
        self.treeWidgetTab = QtWidgets.QWidget()
        self.treeWidgetTab.setObjectName("treeWidgetTab")
        self.filtersTreeWidget = filtersTreeWidget.FiltersTreeWidget()
        self.filtersTreeWidget.setup(self, self.dataBack)
        self.tabWidget.addTab(self.filterTable, "")
        self.tabWidget.addTab(self.filtersTreeWidget, "")
        self.verticalLayout.addWidget(self.tabWidget)
        self.horizontalLayout.addWidget(self.visualizeFrame)
        mainWindow.setCentralWidget(self.centralWidget)

#############################
## Menu code
#############################
        self.menuBar = QtWidgets.QMenuBar(mainWindow)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 659, 20))
        self.menuBar.setObjectName("menuBar")
        self.menuWidget = QtWidgets.QMenu(self.menuBar)
        self.menuWidget.setObjectName("menuWidget")

        self.menuChooseBaud = QtWidgets.QMenu(self.menuWidget)
        self.menuChooseBaud.setObjectName("menuChooseBaud")
        self.menuChooseBaud.addAction("Not supported yet, and these checkboxes should be radio buttons")
        for baudrate in BAUDLIST:
            _baudrate = QtWidgets.QAction(baudrate,  mainWindow)
            _baudrate.setCheckable(True)
            self.menuChooseBaud.addAction(_baudrate)
            _baudrate.triggered.connect(self.setBaud)

        self.menuChoose_port = QtWidgets.QMenu(self.menuWidget)
        self.menuChoose_port.setObjectName("menuChoose_port")
        mainWindow.setMenuBar(self.menuBar)
        self.actionLoad_filters_from_file = QtWidgets.QAction(mainWindow)
        self.actionLoad_filters_from_file.setObjectName(
                                        "actionLoad_filters_from_file")
        self.actionLoad_filters_from_file.triggered.connect(self.loadFilter)
        # comports code:
        ##########
        # Populate the serial port menu with all the available ports.
        for port in comports():
            _port = QtWidgets.QAction(port[0], mainWindow)
            _port.setCheckable(True)
            self.menuChoose_port.addAction(_port)
            _port.triggered.connect(self.comportSelect)
        ##########
        self.actionTab1 = QtWidgets.QAction(mainWindow)
        self.actionTab1.setObjectName("actionTab1")
        self.actionTab2 = QtWidgets.QAction(mainWindow)
        self.actionTab2.setObjectName("actionTab2")
        self.menuWidget.addAction(self.actionLoad_filters_from_file)
        self.menuWidget.addAction(self.menuChooseBaud.menuAction())
        self.menuWidget.addAction(self.menuChoose_port.menuAction())
        self.menuBar.addAction(self.menuWidget.menuAction())
        # QtDesigner code:
        self.retranslateUi(mainWindow)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(mainWindow)

        ## Check for command line arguments: --messages or --port
        if self.dataBack.args.messages != None:
            self.commandLineLoadFilter()

        if self.dataBack.args.port != None:
            self.comportSelect()


    def retranslateUi(self, mainWindow):
        _translate = QtCore.QCoreApplication.translate
        mainWindow.setWindowTitle(_translate(
                                "MainWindow", "CAN Message Viewer"))
        self.label.setText(_translate("MainWindow", "Message Stream"))
        self.label_2.setText(_translate("MainWindow", "MetaData and Filtering"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.filterTable),
                            _translate("MainWindow", "Units and filtering by value"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(
                                      self.filtersTreeWidget),
                                     _translate("MainWindow", "View MetaData"))
        self.menuWidget.setTitle(_translate("MainWindow", "&Action"))
        self.menuChooseBaud.setTitle(_translate("MainWindow", "Choose Can &Baud"))
        self.menuChoose_port.setTitle(_translate("MainWindow", "&Choose port"))
        self.actionLoad_filters_from_file.setText(_translate(
                                    "MainWindow", "Load &Filters from file"))


    #
    def updateUi(self):
        outmsg = self.getMessage(self.dataBack.CANacondaRxMsg_queue)
        if outmsg is not None:
            self.messagesTextBrowser.append("%s" % outmsg)
            self.outmsgSignal.emit()

    def getMessage(self, CANacondaRxMsg_queue):
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
        self.freqTimer.timeout.connect(self.filterTable.updateValueInTable)
        self.freqTimer.start(1000)

    # begin receiving messages and push to CANacondaRxMsg_queue
    def pyserialInit(self):
        self.dataBack.canPort = canport.CANPortGUI(self.dataBack)
        self.serialCAN = self.dataBack.canPort.pyserialInit()

        # The serialCAN thread was initialized without error
        if type(self.serialCAN) != int:
            self.dataBack.canTranscoderGUI.parsedMsgPut.connect(self.updateUi)
            self.dataBack.canTranscoderGUI.parsedMsgPut.connect(
                                               self.filterTable.updateValueInTable)
            self.dataBack.canTranscoderGUI.newMessageUp.connect(self.filterTable.populateTable)
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
        self.filtersTreeWidget.populateTree()
        self.update_messageInfo_to_fields() # FIXME This is called from filterTable.py
                                            # and may not be necessary here... test this
        # populate the 'transmission' combobox
        self.populateTxMessageInfoCombo()
        # Enable the combo box that allows user to select message stream format and set to 'decoded'
        self.displayCombo.setDisabled(False)
        self.displayCombo.setCurrentIndex(DECODED)


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
        self.filtersTreeWidget.populateTree()
        self.update_messageInfo_to_fields() # FIXME This is called from filterTable.py
                                            # and may not be necessary here... test this
        # populate the 'transmission' combobox
        self.populateTxMessageInfoCombo()
        # Enable the combo box that allows user to select message stream format and set to 'decoded'
        self.displayCombo.setDisabled(False)
        self.displayCombo.setCurrentIndex(DECODED)


    # When the metadata file is loaded, the name appears at the upper right corner of UI
    # updateFileNameQLabel handles this.
    def updateFileNameQLabel(self):
        self.fileName = self.fileName.split('/')[-1]
        text = "MetaData file: <font color=grey><i>  " + self.fileName + "</></font>    "
        self.fileNameLabel.setText(text)


    # Called when a metadata file is loaded
    # populate the combobox with messageInfo/field names
    def populateTxMessageInfoCombo(self):
        try:
            self.firstTxMessageInfo.currentTextChanged.disconnect(self.populateTxField)
        except:
            pass
        self.firstTxMessageInfo.clear()            #
        self.firstTxMessageInfo.setDisabled(False) #
        try:
            self.firstTxBody1.clear()                  #
        except RuntimeError:
            # The widget has already been deleted
            pass
        # move to separate function
        self.firstTxFreq.setDisabled(False)       #
        self.firstTxButton.setDisabled(False)     #
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

        # For one iteration, 'key' will be '', and we want to ignore this error.
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

    # Connected with displayCombo's currentIndexChanged signal
    def updateButtonLoggingText(self):
        # Before updating the text, make sure we are not currently logging, in which
        # case the button should read "End Logging", and therefore should not be updated.
        if not self.dataBack.logflag:
            self.buttonLogging.setText("Start logging as " + self.displayCombo.currentText())
            # Also, re-enable the DisplayAs combobox



    # generateMessage: Creates a hex encoded message
    # 'payload' is a dictionary mapping of field names to payload data
    # 'messageName' is a string that came from the QComboBox (GUI) or a command-line argument (CLI)
    # This function will be refactored so that code is in the 'right' place, i.e. not in ui_mainwindow
    # but instead in a file that is common to both CLI and GUI.
        
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
        

    def comportUnavailable(self):
        pass

    # Set the messageInfo_to_fields for correct message stream output
    def update_messageInfo_to_fields(self):
        self.dataBack.messageInfo_to_fields = {}
        for row in range(0,self.filterTable.tableWidget.rowCount()):
            if self.filterTable.tableWidget.item(
                    row, filterTable.CHECKBOX).checkState() == QtCore.Qt.Checked:
                name = self.filterTable.tableWidget.item(
                                                row, filterTable.MESSAGE).text()
                field = self.filterTable.tableWidget.item(
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
        currentIndex = self.displayCombo.currentIndex()
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
        self.messagesTextBrowser.clear()


    # This function handles the logging functionality. When the "start logging as..." 
    # button is pressed, this function is called and all messages that were in the
    # message browser are erased and subsequent messages get written to a file. When
    # recording is done, this function is called again to flip the state back to normal.
    def saveToFile(self):
        if self.dataBack.logflag:
            self.buttonLogging.setText("Start logging as " + self.displayCombo.currentText()) 
            self.file.write(self.messagesTextBrowser.toPlainText())
            self.file.close()
            # Revert label back to original text
            self.loggingStatusLabel.setText("Status:  <font color = grey><i>not recording</i><font>")
            self.dataBack.logflag = False
            # Disable the display combo box so that the user doesn't change anything 
            # by mistake while logging
            self.displayCombo.setDisabled(True)
            self.filterTable.enableItemsAfterLogging()
        else:
            if self.logFileName.text() == '':
                self.warnLogging()
                return
            if os.path.isfile(self.logFileName.text()):
                overWrite = self.warnOverwrite()
                if overWrite == 0x400000:  # 'don't overwrite'
                    return
                elif overWrite == 0x400:   # 'okay to overwrite'
                   os.remove(self.logFileName.text())

            # OK to log. Clear text browser, disable the display combo box, and open a file
            # for writing.
            self.clearTextBrowser()
            self.displayCombo.setDisabled(True)
            self.filterTable.disableItemsForLogging()
            self.file = open(self.logFileName.text(), 'w')
            # A header for use with Matlab or other programs:
            if self.dataBack.GUI_CSVflag:
                header = 'time,' + ','.join(self.dataBack.guiCSVDisplayList)
                self.file.write(header)
                self.file.write('\n')
            self.buttonLogging.setText("End Logging")
# Move this functionality to another spot:
            self.loggingStatusLabel.setText("Status:  <font color=red><b>\
                                            recording</b></font>    ")
            self.dataBack.logflag = True
    
    def loggingStatusHandler(self):
        # If we are not logging, then the accompanying text should say so
        if self.dataBack.logflag == False:
            self.loggingStatusLabel.setText("Status:  <font color = grey><i>not recording</i></font>")
            self.messageCount = 0
            return

        # Otherwise, change the text and update the messageCount
        self.statusText = "Status:  <font color=red><b><i>recording  </i>" + str(self.messageCount) + "</b></font>"
        self.messageCount += 1
        self.loggingStatusLabel.setText(self.statusText)

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


    def transmissionWarn(self, errorString):
        warn = QtWidgets.QMessageBox()
        warn.setText("Transmission Error")
        warn.setInformativeText(errorString)
        warn.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        warn.exec()

    def debugMode(self):
        pyqtrm()
        import pdb
        pdb.set_trace()

    def setHourGlass(self):
        alreadyStreaming = self.dataBack.alreadyStreaming
        if not alreadyStreaming:
            QApplication.setOverrideCursor(QCursor(QtCore.Qt.WaitCursor))

    def removeHourGlass(self):
        QApplication.restoreOverrideCursor()

    def setStreamingFlag(self):
        self.dataBack.alreadyStreaming = True

