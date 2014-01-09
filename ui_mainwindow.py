# ui_mainwindow.py
# Originally generated with QtCreator and pyuic.

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import pyqtRemoveInputHook as pyqtrm
from messageInfoParse import xmlImport
import threading
from serial.tools.list_ports_posix import comports
import pdb
from backend import *
import filtersTreeWidget
import filterTable
import outmessage
import canport_QT
import time
import os
import xml.etree.ElementTree as ET

FAST_FILENAME = 'newMetaData.xml'
DECODED, RAW_HEX, CSV = range(3)


class Ui_MainWindow(QtCore.QObject):

    def setupUi(self, mainWindow, dataBack):
        self.dataBack = dataBack
       # pyqtrm()
       # pdb.set_trace()
#############################
## Layout code
#############################
        mainWindow.setObjectName("mainindow")
        #mainWindow.resize(659, 565)
        #mainWindow.setWindowTitle("CAN Message Viewer")
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
        self.buttonLogging.setText("Start logging as CSV")
        self.buttonLogging.clicked.connect(self.saveToFile)
        self.logLabel.setBuddy(self.buttonLogging)
        self.fileName = QtWidgets.QLineEdit()
        self.fileName.setObjectName("fileName")
        self.fileName.returnPressed.connect(self.saveToFile)
        self.loggingStatusLabel = QtWidgets.QLabel()
        self.loggingStatusLabel.setText("Status:  not recording")
        self.horizontalLayout_2.addWidget(self.logLabel)
        self.horizontalLayout_2.addWidget(self.fileName)
        self.horizontalLayout_2.addWidget(self.buttonLogging)
        self.horizontalLayout_2.addSpacing(100)
        self.horizontalLayout_2.addWidget(self.loggingStatusLabel)


        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.messagesFrame)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label = QtWidgets.QLabel(self.messagesFrame)
        self.label.setObjectName("messageStreamLabel")
#        self.label.setText("Message Stream")
        self.verticalLayout_2.addWidget(self.label)


#########################
# Display Combobox code # 
#########################
        self.displayLayout = QtWidgets.QHBoxLayout()
        self.verticalLayout_2.addLayout(self.displayLayout)
        self.displayLayout.setObjectName("display combobox layout")
        self.displayLabel = QtWidgets.QLabel()
        self.displayLabel.setText("Display: ")
        self.displayCombo = QtWidgets.QComboBox()
        self.displayLayout.addWidget(self.displayLabel)
        self.displayLayout.addWidget(self.displayCombo)
        # Note: displayList must be in order of enum at top of file
        displayList = ["Decoded", "Raw hex", "CSV"]
        self.displayCombo.addItems(displayList)
        self.displayCombo.currentIndexChanged.connect(self.setOutput)

        self.messagesTextBrowser = QtWidgets.QTextBrowser(self.messagesFrame)
        self.messagesTextBrowser.setObjectName("messagesTextBrowser")
        self.verticalLayout_2.addWidget(self.messagesTextBrowser)



        '''
##################
# buttonsGrid code
##################
        # Buttons for clearing textbrowser, csv, pgn, body, raw display,
        # and saving textbrowser contents to file.
        self.buttonsGrid = QtWidgets.QGridLayout()
        self.verticalLayout_2.addLayout(self.buttonsGrid)
        self.buttonsGrid.setObjectName("button grid layout")

        self.buttonClear = QtWidgets.QPushButton()
        self.buttonClear.setObjectName("clear")
        self.buttonClear.setText("Clear Message Stream")
        self.buttonClear.clicked.connect(self.clearTextBrowser)
        self.logLabel = QtWidgets.QLabel()
        self.logLabel.setText("Enter filename:")
        self.buttonLogging = QtWidgets.QPushButton()
        self.buttonLogging.setObjectName("save")
        self.buttonLogging.setText("Begin Logging")
        self.buttonLogging.clicked.connect(self.saveToFile)
        self.logLabel.setBuddy(self.buttonLogging)
        self.fileName = QtWidgets.QLineEdit()
        self.fileName.setObjectName("fileName")
        self.fileName.returnPressed.connect(self.saveToFile)

        self.checkBody = QtWidgets.QCheckBox()
        self.checkBody.setObjectName("checkBoxBody")
        self.checkBody.setText("Body")
        self.checkBody.setCheckState(2)
        self.checkBody.stateChanged.connect(self.setOutput)
        self.checkPGN = QtWidgets.QCheckBox()
        self.checkPGN.setObjectName("checkBoxPGN")
        self.checkPGN.setText("PGN")
        self.checkPGN.setCheckState(2)
        self.checkPGN.stateChanged.connect(self.setOutput)
        self.checkID = QtWidgets.QCheckBox()
        self.checkID.setObjectName("checkBoxId")
        self.checkID.setText("ID")
        self.checkID.setCheckState(2)
        self.checkID.stateChanged.connect(self.setOutput)
        self.checkRaw = QtWidgets.QCheckBox()
        self.checkRaw.setObjectName("checkBoxRaw")
        self.checkRaw.setText("Hex")

        self.checkCSV = QtWidgets.QCheckBox()
        self.checkCSV.setObjectName("checkBoxCSV")
        self.checkCSV.setText("CSV")
        self.checkCSV.stateChanged.connect(self.setOutput)
        self.checkCSV.stateChanged.connect(self.csvOutputSet)
        self.displayLabel = QtWidgets.QLabel()
        self.displayLabel.setText("Display opts:")

        self.displayCheckBox = QtWidgets.QHBoxLayout()
        self.displayCheckBox.addWidget(self.displayLabel)
        self.displayCheckBox.addWidget(self.checkBody)
        self.displayCheckBox.addWidget(self.checkPGN)
        self.displayCheckBox.addWidget(self.checkID)
        self.displayCheckBox.addWidget(self.checkRaw)
        self.displayCheckBox.addWidget(self.checkCSV)

        if self.dataBack.args.debug:
            self.debug = QtWidgets.QPushButton()
            self.debug.setText("pdb")
            self.debug.clicked.connect(self.debugMode)


        #self.buttonResetTime.clicked.connect(self.resetTime)
        self.buttonsGrid.addWidget(self.logLabel, 1,0)
#        self.buttonsGrid.addWidget(self.buttonClear, 3,0)
        self.buttonsGrid.addWidget(self.buttonLogging, 0,0, 1,3)
        self.buttonsGrid.addWidget(self.fileName, 1,2)
        self.buttonsGrid.addLayout(self.displayCheckBox, 2,0, 1,3)
#        self.buttonsGrid.addWidget(self.checkCSV, 3,0)
        #self.buttonsGrid.addWidget(self.buttonResetTime, 2,1, 1,2)
        if self.dataBack.args.debug:
            self.buttonsGrid.addWidget(self.debug, 3,1, 1,2)

##################
# End of buttonsGrid code
##################
        '''

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
#        self.metaDataTitleGrid = QtWidgets.QGridLayout()
#        self.metaDataLabel = QtWidgets.QLabel()
#        self.metaDataLabel.setText("MetaData and Filtering")

#        self.verticalLayout.addLayout(self.metaDataTitleGrid)
#        self.statusLabel = QtWidgets.QLabel(self.centralWidget)
#        self.statusLabel.setText("Status: ")
#        self.status = QtWidgets.QLabel()
#        self.status.setText("Not Recording")
#        self.metaDataTitleGrid.addWidget(self.metaDataLabel, 0, 0)
#        self.metaDataTitleGrid.addStretch(0,1)
#        self.metaDataTitleGrid.addWidget(self.statusLabel, 0, 2)
#        self.metaDataTitleGrid.addWidget(self.status, 0, 3)




        # make this QLabel fit inside a grid
        self.label_2 = QtWidgets.QLabel(self.visualizeFrame)
        self.label_2.setObjectName("label_2")
#        self.label_2.setText("Metadata and Filtering")
        self.verticalLayout.addWidget(self.label_2)

#################
# TabWidget, tableWidget, and treeWidget code
#################
        self.tabWidget = QtWidgets.QTabWidget(self.visualizeFrame)
        self.tabWidget.setObjectName("tabWidget")
        self.filterTab = QtWidgets.QWidget()
        self.filterTab.setObjectName("filterTab")
      #  self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.filterTab)
      #  self.verticalLayout_3.setObjectName("verticalLayout_3")
#        self.progressBar = QtWidgets.QProgressBar(self.treeViewTab)
#        self.progressBar.setProperty("value", 24)
#        self.progressBar.setObjectName("progressBar")
#        self.verticalLayout_3.addWidget(self.progressBar)
        self.filterTable = filterTable.FilterTable()
        self.filterTable.setup(self.dataBack, self)
        self.filterTable.setObjectName("filterTable")
        self.filterTable.populateTable()
        self.treeWidgetTab = QtWidgets.QWidget()
        self.treeWidgetTab.setObjectName("treeWidgetTab")
       # self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.treeWidgetTab)
       # self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.filtersTreeWidget = filtersTreeWidget.FiltersTreeWidget()
        self.filtersTreeWidget.setup(self, self.dataBack)
       # self.verticalLayout_4.addWidget(self.filtersTreeWidget)
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
        self.menuShow = QtWidgets.QMenu(self.menuBar)
        self.menuShow.setObjectName("menuShow")
        self.menuChoose_port = QtWidgets.QMenu(self.menuShow)
        self.menuChoose_port.setObjectName("menuChoose_port")
        mainWindow.setMenuBar(self.menuBar)
        self.actionBegin_Logging = QtWidgets.QAction(mainWindow)
        self.actionBegin_Logging.setObjectName("actionBegin_Logging")
        self.actionEnd_Logging = QtWidgets.QAction(mainWindow)
        self.actionEnd_Logging.setObjectName("actionEnd_Logging")
        self.actionCAN_Messages = QtWidgets.QAction(mainWindow)
        self.actionCAN_Messages.setObjectName("actionCAN_Messages")
        self.actionCAN_Headers = QtWidgets.QAction(mainWindow)
        self.actionCAN_Headers.setObjectName("actionCAN_Headers")
        self.actionCAN_PGNs = QtWidgets.QAction(mainWindow)
        self.actionCAN_PGNs.setObjectName("actionCAN_PGNs")
        self.actionLoad_filters_from_file = QtWidgets.QAction(mainWindow)
        self.actionLoad_filters_from_file.setObjectName(
                                        "actionLoad_filters_from_file")
        self.actionLoad_filters_from_file.triggered.connect(self.newLoadFilter)
        self.actionComports = QtWidgets.QAction(mainWindow)
        self.actionComports.setObjectName("actionComports")
        # comports code:
        ##########
        self.menuChoose_port.addAction(self.actionComports)
        for port in comports():
            #pyqtrm()
            #pdb.set_trace()
            _port = QtWidgets.QAction(port[0], mainWindow)
            self.menuChoose_port.addAction(_port)
            _port.triggered.connect(self.comportSelect)
        ##########
        self.actionTab1 = QtWidgets.QAction(mainWindow)
        self.actionTab1.setObjectName("actionTab1")
        self.actionTab2 = QtWidgets.QAction(mainWindow)
        self.actionTab2.setObjectName("actionTab2")
        self.menuShow.addAction(self.actionCAN_Messages)
        self.menuShow.addAction(self.actionCAN_Headers)
        self.menuShow.addAction(self.actionCAN_PGNs)
        self.menuShow.addSeparator()
        self.menuShow.addAction(self.actionLoad_filters_from_file)
        self.menuShow.addAction(self.menuChoose_port.menuAction())
        self.menuBar.addAction(self.menuShow.menuAction())
        # QtDesigner code:
        self.retranslateUi(mainWindow)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(mainWindow)

        if self.dataBack.args.fast:
            #xmlImport(self.dataBack, self.dataBack.args, FAST_FILENAME)
            #self.filtersTreeWidget.populateTree()
            # Is this still necessary?
            self.filterTable.populateTable()
            self.update_messageInfo_to_fields()
            self.dataBack.comport = '/dev/ttyUSB0'
            self.dataBack.comportsFlag = True
            self.dataBack.displayList['pgn'] = True
            self.dataBack.displayList['raw'] = False
            self.dataBack.displayList['ID'] = True
            self.dataBack.displayList['body'] = True
            self.receiveMessage()  # <-- The serial thread is created here

            self.dataBack.messageInfoFlag = True


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
        self.menuShow.setTitle(_translate("MainWindow", "&Action"))
        self.menuChoose_port.setTitle(_translate("MainWindow", "&Choose port"))
        self.actionBegin_Logging.setText(_translate(
                                                "MainWindow", "Begin Logging"))
        self.actionEnd_Logging.setText(_translate("MainWindow", "End Logging"))
        self.actionCAN_Messages.setText(_translate(
                                            "MainWindow", "Show CAN &Messages"))
        self.actionCAN_Headers.setText(_translate(
                                            "MainWindow", "Show CAN &Headers"))
        self.actionCAN_PGNs.setText(_translate("MainWindow", "Show CAN &PGNs"))
        self.actionLoad_filters_from_file.setText(_translate(
                                    "MainWindow", "Load &Filters from file"))
        #self.actionComports.setText(_translate("MainWindow", "comports()"))
        self.actionTab1.setText(_translate("MainWindow", "Tab 1"))
        self.actionTab2.setText(_translate("MainWindow", "Tab 2"))

    def updateUi(self):
        outmsg = self.getMessage(self.dataBack.CANacondaMessage_queue)

        if outmsg is not None:
            self.messagesTextBrowser.append("%s" % outmsg)

    def getMessage(self, CANacondaMessage_queue):
        CANacondaMessage = CANacondaMessage_queue.get()
        if self.dataBack.messageInfoFlag is False:
            return CANacondaMessage.raw
        elif self.dataBack.GUI_CSVflag:
            return outmessage.guiParseCSV(self.dataBack, CANacondaMessage)
        return outmessage.noGuiParse(self.dataBack, CANacondaMessage)


    def comportSelect(self):
        self.dataBack.comport = self.sender().text()
        self.dataBack.comportsFlag = True
        self.setOutput()
        self.receiveMessage()  # <-- The serial thread is created here

# begin receiving messages and push to CANacondaMessage_queue
    def receiveMessage(self):
        self.dataBack.canPort = canport_QT.CANPort_QT(self.dataBack)
        self.dataBack.canPort.parsedMsgPut.connect(self.updateUi)
        self.dataBack.canPort.parsedMsgPut.connect(
                                           self.filterTable.updateValueInTable)
        self.dataBack.canPort.messageUp.connect(self.filterTable.populateTable)
        serialThread = threading.Thread(target=self.dataBack.canPort.getmessage)
    
        # setting daemon to true lets program quit successfully
        serialThread.daemon = True
        serialThread.start()

        # Use this timer as a watchdog for when a node on the bus is shut off.
        # Without it, frequency column won't go back to zero.
        self.freqTimer = QtCore.QTimer()
        self.freqTimer.timeout.connect(self.filterTable.updateValueInTable)
        self.freqTimer.start(1000)



    def newLoadFilter(self):
        # These "reset" statements should actually be moved to a
        # reset function that can be called from anywhere in the code.
        self.dataBack.messages = {}
        self.dataBack.messageInfo_to_fields = {}
        self.dataBack.messagesSeenSoFar = {}
        self.dataBack.id_to_name = {}
        self.dataBack.pgn_to_name = {}
        self.dataBack.messageInfoFlag = True
        fileName = None
        while fileName is None:
            fileName = QtWidgets.QFileDialog.getOpenFileName()[0]
        warn = False
        try:
            xmlImport(self.dataBack, self.dataBack.args, fileName)
        except:
            warn = True
        if warn:
            self.warnFilterImport()
            return
        self.filtersTreeWidget.populateTree()
        # Is this still necessary?
        self.update_messageInfo_to_fields()



########## deprecated but keep around for default suffix code. ########
#    def loadFilter(self):
#        filename = None
#        dialog = QtWidgets.QFileDialog()
#        dialog.setNameFilter(tr("(*.xml)"))
#        dialog.setDefaultSuffix('xml')
#        dialog.setViewMode(QtWidgets.QFileDialog.Detail)
#        if (dialog.exec()):
#            fileName = dialog.selectedFiles()
##        while filename is None:
#
##            filename = QtWidgets.QFileDialog.getOpenFileName(self, )
##            filename = filename[0]
#        blob = None
#        fallacy = xmlimport(self.dataBack, blob, filename)
#        if fallacy:
#            self.warnFiltersImport()
#            return
#        self.filtersTreeWidget.populateTree()
#        self.update_messageInfo_to_fields()
#######################################################################

    def comportUnavailable(self):
        pass


    # Set the messageInfo_to_fields for correct message stream output
    def update_messageInfo_to_fields(self):
        self.dataBack.messageInfo_to_fields = {}
        for row in range(0,self.filterTable.tableWidget.rowCount()):
            if self.filterTable.tableWidget.item(
                    row, filterTable.MESSAGE).checkState() == QtCore.Qt.Checked:
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
        currentIndex = self.displayCombo.currentIndex()
        # Python switch?
        if currentIndex == CSV:
            self.dataBack.GUI_CSVflag = True
            self.csvOutputSet()
            return

        elif currentIndex == DECODED:
            self.dataBack.GUI_CSVflag = False
            self.dataBack.displayList['ID'] = True
            self.dataBack.displayList['pgn'] = True
            self.dataBack.displayList['body'] = True
            self.dataBack.displayList['raw'] = False
            return
            
        elif currentIndex == RAW_HEX:
            self.dataBack.GUI_CSVflag = False
            self.dataBack.displayList['ID'] = False
            self.dataBack.displayList['pgn'] = False
            self.dataBack.displayList['body'] = False
            self.dataBack.displayList['raw'] = True
            return

    # This function is called whenever the filtering is changed via
    # filtersTreeWidget checkbox signal.
    def csvOutputSet(self):
        self.dataBack.guiCSVDisplayList = []
        self.dataBack.fieldIndices = {}
        map = sorted(self.dataBack.messageInfo_to_fields.items())
        # this returns a funky list which has to be access as follows:
        i = 1
        for item in map:
            for field in item[1]:
                self.dataBack.guiCSVDisplayList.append(item[0]+'_'+field)
                self.dataBack.fieldIndices[field] = i
                i += 1


    def clearTextBrowser(self):
        self.messagesTextBrowser.clear()

    def saveToFile(self):
        #pyqtRemoveInputHook()
        #pdb.set_trace()
        if self.dataBack.logflag:
            self.buttonLogging.setText("Start logging as CSV")
            self.file.write(self.messagesTextBrowser.toPlainText())
            self.file.close()
            self.loggingStatusLabel.setText("Status:  not recording")
            self.dataBack.logflag = False
        else:
            if self.fileName.text() == '':
                self.warnLogging()
                return
            if os.path.isfile(self.fileName.text()):
                overWrite = self.warnOverwrite()
                if overWrite == 0x400000:
                    return
                elif overWrite == 0x400:
                   os.remove(self.fileName.text())
            self.clearTextBrowser()

            self.file = open(self.fileName.text(), 'w')
            # A header for use with Matlab or other programs:
            if self.dataBack.GUI_CSVflag:
                header = 'time,' + ','.join(self.dataBack.guiCSVDisplayList)
                self.file.write(header)
                self.file.write('\n')
            self.buttonLogging.setText("End Logging")
            self.loggingStatusLabel.setText("Status:  recording    ")
            self.dataBack.logflag = True

    def resetTime(self):
        self.dataBack.CSV_START_TIME = time.time()

    def warnFilterImport(self):
        effedUp = QtWidgets.QMessageBox()
        effedUp.setText("Meta Data File Error")
        effedUp.setInformativeText("Check XML file for correct formatting and syntax")
        effedUp.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        effedUp.exec()


    def warnPgnId(self):
        effedUp = QtWidgets.QMessageBox()
        effedUp.setText("Meta Data Error")
        effedUp.setInformativeText("You can't have both PGN and ID in one filter in your meta data file")
        effedUp.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        effedUp.exec()

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

    def debugMode(self):
        pyqtrm()
        pdb.set_trace()
