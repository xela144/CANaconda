# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'CANaconda_ui/canaconda_mainwindow.ui'
#
# Created: Thu Nov 27 11:21:11 2014
#      by: PyQt5 UI code generator 5.3.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_CANaconda_MainWindow(object):
    def setupUi(self, CANaconda_MainWindow):
        CANaconda_MainWindow.setObjectName("CANaconda_MainWindow")
        CANaconda_MainWindow.resize(776, 500)
        self.centralWidget = QtWidgets.QWidget(CANaconda_MainWindow)
        self.centralWidget.setObjectName("centralWidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralWidget)
        self.gridLayout.setObjectName("gridLayout")
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_2 = QtWidgets.QLabel(self.centralWidget)
        self.label_2.setObjectName("label_2")
        self.verticalLayout.addWidget(self.label_2)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_6 = QtWidgets.QLabel(self.centralWidget)
        self.label_6.setObjectName("label_6")
        self.horizontalLayout_3.addWidget(self.label_6)
        self.displayCombo = QtWidgets.QComboBox(self.centralWidget)
        self.displayCombo.setEnabled(False)
        self.displayCombo.setObjectName("displayCombo")
        self.displayCombo.addItem("")
        self.displayCombo.addItem("")
        self.displayCombo.addItem("")
        self.horizontalLayout_3.addWidget(self.displayCombo)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.messagesTextBrowser = QtWidgets.QTextBrowser(self.centralWidget)
        self.messagesTextBrowser.setObjectName("messagesTextBrowser")
        self.verticalLayout.addWidget(self.messagesTextBrowser)
        self.horizontalLayout_5.addLayout(self.verticalLayout)
        self.line_2 = QtWidgets.QFrame(self.centralWidget)
        self.line_2.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_2.setObjectName("line_2")
        self.horizontalLayout_5.addWidget(self.line_2)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label = QtWidgets.QLabel(self.centralWidget)
        self.label.setObjectName("label")
        self.horizontalLayout_4.addWidget(self.label)
        self.fileNameLabel = QtWidgets.QLabel(self.centralWidget)
        self.fileNameLabel.setObjectName("fileNameLabel")
        self.horizontalLayout_4.addWidget(self.fileNameLabel)
        self.verticalLayout_2.addLayout(self.horizontalLayout_4)
        self.tabWidget = QtWidgets.QTabWidget(self.centralWidget)
        self.tabWidget.setObjectName("tabWidget")
        self.verticalLayout_2.addWidget(self.tabWidget)
        self.horizontalLayout_5.addLayout(self.verticalLayout_2)
        self.gridLayout.addLayout(self.horizontalLayout_5, 0, 0, 1, 1)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_3 = QtWidgets.QLabel(self.centralWidget)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_2.addWidget(self.label_3)
        spacerItem = QtWidgets.QSpacerItem(14, 20, QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.loggingFileName = QtWidgets.QLineEdit(self.centralWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.loggingFileName.sizePolicy().hasHeightForWidth())
        self.loggingFileName.setSizePolicy(sizePolicy)
        self.loggingFileName.setMinimumSize(QtCore.QSize(200, 0))
        self.loggingFileName.setBaseSize(QtCore.QSize(0, 0))
        self.loggingFileName.setObjectName("loggingFileName")
        self.horizontalLayout_2.addWidget(self.loggingFileName)
        self.loggingButton = QtWidgets.QPushButton(self.centralWidget)
        self.loggingButton.setObjectName("loggingButton")
        self.horizontalLayout_2.addWidget(self.loggingButton)
        spacerItem1 = QtWidgets.QSpacerItem(75, 20, QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.label_4 = QtWidgets.QLabel(self.centralWidget)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_2.addWidget(self.label_4)
        self.loggingStatusLabel = QtWidgets.QLabel(self.centralWidget)
        self.loggingStatusLabel.setObjectName("loggingStatusLabel")
        self.horizontalLayout_2.addWidget(self.loggingStatusLabel)
        self.gridLayout.addLayout(self.horizontalLayout_2, 2, 0, 1, 1)
        self.line = QtWidgets.QFrame(self.centralWidget)
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.gridLayout.addWidget(self.line, 1, 0, 1, 1)
        self.line_3 = QtWidgets.QFrame(self.centralWidget)
        self.line_3.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_3.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_3.setObjectName("line_3")
        self.gridLayout.addWidget(self.line_3, 3, 0, 1, 1)
        self.transmitWidget = QtWidgets.QWidget(self.centralWidget)
        self.transmitWidget.setMinimumSize(QtCore.QSize(0, 39))
        self.transmitWidget.setBaseSize(QtCore.QSize(0, 15))
        self.transmitWidget.setObjectName("transmitWidget")
        self.gridLayout.addWidget(self.transmitWidget, 4, 0, 1, 1)
        CANaconda_MainWindow.setCentralWidget(self.centralWidget)
        self.menuBar = QtWidgets.QMenuBar(CANaconda_MainWindow)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 776, 25))
        self.menuBar.setObjectName("menuBar")
        self.menuAction = QtWidgets.QMenu(self.menuBar)
        self.menuAction.setObjectName("menuAction")
        CANaconda_MainWindow.setMenuBar(self.menuBar)
        self.mainToolBar = QtWidgets.QToolBar(CANaconda_MainWindow)
        self.mainToolBar.setObjectName("mainToolBar")
        CANaconda_MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.mainToolBar)
        self.statusBar = QtWidgets.QStatusBar(CANaconda_MainWindow)
        self.statusBar.setObjectName("statusBar")
        CANaconda_MainWindow.setStatusBar(self.statusBar)
        self.actionLoad_Filters_From_File = QtWidgets.QAction(CANaconda_MainWindow)
        self.actionLoad_Filters_From_File.setObjectName("actionLoad_Filters_From_File")
        self.actionChoose_Port = QtWidgets.QAction(CANaconda_MainWindow)
        self.actionChoose_Port.setCheckable(True)
        self.actionChoose_Port.setObjectName("actionChoose_Port")
        self.actionChange_CanBaud = QtWidgets.QAction(CANaconda_MainWindow)
        self.actionChange_CanBaud.setObjectName("actionChange_CanBaud")
        self.menuAction.addAction(self.actionLoad_Filters_From_File)
        self.menuBar.addAction(self.menuAction.menuAction())

        self.retranslateUi(CANaconda_MainWindow)
        self.tabWidget.setCurrentIndex(-1)
        QtCore.QMetaObject.connectSlotsByName(CANaconda_MainWindow)

    def retranslateUi(self, CANaconda_MainWindow):
        _translate = QtCore.QCoreApplication.translate
        CANaconda_MainWindow.setWindowTitle(_translate("CANaconda_MainWindow", "CANaconda_MainWindow"))
        self.label_2.setText(_translate("CANaconda_MainWindow", "Message Stream"))
        self.label_6.setText(_translate("CANaconda_MainWindow", "Display:"))
        self.displayCombo.setItemText(0, _translate("CANaconda_MainWindow", "Decoded"))
        self.displayCombo.setItemText(1, _translate("CANaconda_MainWindow", "Raw hex"))
        self.displayCombo.setItemText(2, _translate("CANaconda_MainWindow", "CSV"))
        self.label.setText(_translate("CANaconda_MainWindow", "MetaData and Filtering"))
        self.fileNameLabel.setText(_translate("CANaconda_MainWindow", "MetaData file: <font color=grey><i>   None loaded</></font>    "))
        self.label_3.setText(_translate("CANaconda_MainWindow", "Enter Filename"))
        self.loggingButton.setText(_translate("CANaconda_MainWindow", "Start Logging"))
        self.label_4.setText(_translate("CANaconda_MainWindow", "Status:"))
        self.loggingStatusLabel.setText(_translate("CANaconda_MainWindow", "Not recording"))
        self.menuAction.setTitle(_translate("CANaconda_MainWindow", "Action"))
        self.actionLoad_Filters_From_File.setText(_translate("CANaconda_MainWindow", "Load Filters From File"))
        self.actionChoose_Port.setText(_translate("CANaconda_MainWindow", "Choose Port"))
        self.actionChange_CanBaud.setText(_translate("CANaconda_MainWindow", "Change CanBaud"))

