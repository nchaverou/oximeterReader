"""*************************************************************************
*                                                                          *
* Copyright (C) Nicolas Chaverou - All Rights Reserved.                    *
*                                                                          *
*************************************************************************"""

#**************************************************************************
#! @file ui.py
#  @brief UI handler of the Reader
#**************************************************************************

#!/usr/bin/env python3
import cms50v45
import cms50v46
import utils
import config
import datetime
import math
from enum import Enum
from functools import partial
from threading import Thread, Lock
from Qtpy.Qt import QtCore, QtGui, QtWidgets


class ReaderEvent(Enum):
    APNEA = 0
    CONTRACTION = 1
    BREATHE = 2
    END = 3


class OximeterVersion(Enum):
    FOURFIVE = 0
    FOURSIX = 1
    END = 3


""" Reader UI Updater in a separate thread """
class ReaderUIUpdater(Thread):
    def __init__(self, ui, port, version):
        Thread.__init__(self)
        # Connect to the oximeter
        self.ui = ui
        if version == OximeterVersion.FOURFIVE:
            self.oximeter = cms50v45.CMS50DDriver()
        else:
            self.oximeter = cms50v46.CMS50DDriver()
        self.oximeter.connect(port)
        self.threadActive = self.oximeter.isConnected()
        self.eventLock = Lock()
        # reset images
        self.ui.pulseImage.fill(config.dfltBkgColor)
        self.ui.bpmImage.fill(config.dfltBkgColor)
        # Config & internal var
        self.events = []
        self.apneaTime = None
        self.apneaStatus = ReaderEvent.END
        self.pulseMaxValue = 100
        self.bpmMaxValue = 127
        self.o2MaxValue = 127
        self.pulseFrequency = 2  # how many samples we skip
        self.bpmFrequency = 60  # based on quick calculation, the oxymeter runs at 60hz
        self.updateRate = int(self.bpmFrequency / (self.ui.bpmImage.width() / (int(self.ui.minuteField.value()) * 60)))
        self.drawBpmLines()
        self.previousYPulse = 0

    """ Update the pulse images """
    def updatePulseImage(self, iSample, liveDataSample):
        pulseValue = min(liveDataSample[3], self.pulseMaxValue)
        pulseXPixel = iSample % self.ui.pulseImage.width()
        pulseYPixel = int(pulseValue / self.pulseMaxValue * self.ui.pulseImage.height())
        #pixelColor = QtGui.QColor()
        #pixelColor.setHsl(pulseYPixel / self.ui.pulseImage.height() * 255, 255, 127)
        pixelColor = config.pulseColor
        lineShift = int((pulseYPixel - self.previousYPulse) / 2)
        # clean pulse image
        bandWidth = int(self.ui.pulseImage.width() * 0.2)
        utils.drawBox(self.ui.pulseImage, pulseXPixel + bandWidth / 2, self.ui.pulseImage.height() / 2, bandWidth, self.ui.pulseImage.height(), config.dfltBkgColor)
        # update pulse image
        utils.drawBox(self.ui.pulseImage, pulseXPixel, self.ui.pulseImage.height() - pulseYPixel - 1 + lineShift, config.curvePixelSize, config.curvePixelSize + abs(lineShift * 2), pixelColor)
        self.ui.pulseImageHolder.setPixmap(QtGui.QPixmap.fromImage(self.ui.pulseImage))
        self.previousYPulse = pulseYPixel

    """ Update the bpm image """
    def updateBpmImage(self, iSample, liveDataSample):
        bpmValue = min(liveDataSample[1], self.bpmMaxValue)
        bpmXPixel = iSample
        bpmYPixel = int(bpmValue / self.bpmMaxValue * self.ui.bpmImage.height())
        o2Value = min(liveDataSample[2], self.o2MaxValue)
        o2XPixel = iSample
        o2YPixel = int(o2Value / self.o2MaxValue * self.ui.bpmImage.height())
        # draw pixel
        utils.drawBox(self.ui.bpmImage, bpmXPixel, self.ui.bpmImage.height() - bpmYPixel - 1, config.curvePixelSize, config.curvePixelSize, config.bmpColor)
        utils.drawBox(self.ui.bpmImage, o2XPixel, self.ui.bpmImage.height() - o2YPixel - 1, config.curvePixelSize, config.curvePixelSize, config.o2Color)
        self.ui.bpmImageHolder.setPixmap(QtGui.QPixmap.fromImage(self.ui.bpmImage))

    """ Update the bpm image with an event line """
    def drawLineBpmImage(self, iSample, color):
        utils.drawBox(self.ui.bpmImage, iSample, self.ui.bpmImage.height() / 2, config.curvePixelSize + 2, self.ui.bpmImage.height(), color)

    """ Draw the time cols """
    def drawTimeCols(self, iSample):
        colSampleSize = math.ceil(self.ui.bpmImage.width() / (self.ui.minuteField.value() * 60) * config.timeColFrequency)
        for iGrid in range(iSample, self.ui.bpmImage.width(), colSampleSize):
            utils.drawBox(self.ui.bpmImage, iGrid, self.ui.bpmImage.height() / 2, 1, self.ui.bpmImage.height(), config.gridColColor)

    """ Draw the bpm lines """
    def drawBpmLines(self):
        lineSampleSize = math.ceil(self.ui.bpmImage.height() / self.bpmMaxValue * config.bpmLineFrequency)
        for iGrid in range(0, self.ui.bpmImage.height(), lineSampleSize):
            utils.drawBox(self.ui.bpmImage, self.ui.bpmImage.width() / 2, self.ui.bpmImage.height() - iGrid -1, self.ui.bpmImage.width(), 1, config.gridLineColor)
        # draw a specific line for the mark 100
        lineSamplePixel = math.ceil(self.ui.bpmImage.height() / self.bpmMaxValue * 100)
        utils.drawBox(self.ui.bpmImage, self.ui.bpmImage.width() / 2, self.ui.bpmImage.height() - lineSamplePixel - 1, self.ui.bpmImage.width(), 1, config.gridLine100Color)

    """ Update time """
    def updateTimer(self):
        if self.apneaStatus == ReaderEvent.APNEA:
            deltaDatetime = datetime.datetime.now() - self.apneaTime
            deltaTime = (datetime.datetime.min + deltaDatetime).time()
            self.ui.timeValueLabel.setText(deltaTime.strftime('%M:%S'))
        elif self.apneaStatus == ReaderEvent.END:
            self.ui.timeValueLabel.setText('--')


    """ check the oximeter status and update the ui """
    def checkOximeterStatus(self):
        if self.oximeter.isConnected() is True:
            if self.threadActive is True:
                self.ui.footerLabel.setText('Oximeter Status: Connected')
                self.ui.refreshApneaUI(True)
                return True
            else:
                self.ui.footerLabel.setText('Oximeter Status: Not Connected (Manual deconnection)')
                self.oximeter.disconnect()
                self.ui.refreshApneaUI(False)
                return False
        self.ui.footerLabel.setText('Oximeter Status: Not Connected (No package sent)')
        self.ui.refreshApneaUI(False)
        return False


    """ thread safe event feeder """
    def feedEvent(self, event):
        self.eventLock.acquire()
        self.events.append(event)
        self.eventLock.release()

    """ thread sage event consumer """
    def consumeEvent(self, iSample):
        self.eventLock.acquire()
        for event in self.events:
            if event == ReaderEvent.APNEA:
                self.apneaTime = datetime.datetime.now()
                self.drawLineBpmImage(iSample, config.apneaColor)
                self.drawTimeCols(iSample)
                self.apneaStatus = ReaderEvent.APNEA
            elif event == ReaderEvent.CONTRACTION:
                self.drawLineBpmImage(iSample, config.contractionColor)
            elif event == ReaderEvent.BREATHE:
                self.drawLineBpmImage(iSample, config.breatheColor)
                self.apneaStatus = ReaderEvent.BREATHE
        self.events.clear()
        self.eventLock.release()

    """ Main thread run, read the packet loop """
    def run(self):
        iSample = 0
        for liveData in self.oximeter.getLiveData():
            # print(liveData)
            if self.checkOximeterStatus() is False:
                return
            liveDataSample = liveData.getCsvData()
            self.ui.bpmValueLabel.setText(str(liveDataSample[1]))
            self.ui.o2ValueLabel.setText(str(liveDataSample[2]) + '%')
            if iSample % self.pulseFrequency == 0:
                self.updatePulseImage(int(iSample / self.pulseFrequency), liveDataSample)
            if iSample % self.updateRate == 0:
                self.consumeEvent(int(iSample / self.updateRate))
                self.updateBpmImage(int(iSample / self.updateRate), liveDataSample)
                self.updateTimer()
            iSample += 1
        self.oximeter.disconnect()
        self.checkOximeterStatus()


""" Main QT Application """
class ReaderUI(QtWidgets.QMainWindow):
    def __init__(self):
        # Main
        QtWidgets.QMainWindow.__init__(self)
        self.setMinimumSize(QtCore.QSize(400, 100))
        self.setWindowTitle('OximeterReader v0.0.1')
        self.setWindowIcon(QtGui.QIcon(utils.getIconsDir() + "oxygen.png"))
        textFont = QtGui.QFont( "Arial", 15, QtGui.QFont.Bold)
        self.windowSize = None
        self.bmpImageSize = QtCore.QSize(config.widthBpmCurveImage, config.heightImages)

        # Main Layout
        centralWidget = QtWidgets.QWidget()
        self.setCentralWidget(centralWidget)
        centralLayout = QtWidgets.QGridLayout(centralWidget)
        iLine = 0

        # Connect
        connectWidget = QtWidgets.QWidget()
        connectLayout = QtWidgets.QHBoxLayout(connectWidget)
        connectLayout.addStretch(1)
        portLabel = QtWidgets.QLabel('Ports:')
        portLabel.setFixedWidth(30)
        self.portCombo = QtWidgets.QComboBox()
        self.portCombo.setFixedWidth(100)
        self.versionCombo = QtWidgets.QComboBox()
        self.versionCombo.setFixedWidth(50)
        self.versionCombo.addItem('v4.5')
        self.versionCombo.addItem('v4.6')
        self.minuteField = QtWidgets.QSpinBox()
        self.minuteField.setRange(1, 15)
        self.minuteField.setValue(config.dfltMinutes)
        self.minuteField.setFixedWidth(50)
        minuteLabel = QtWidgets.QLabel('min')
        minuteLabel.setFixedWidth(20)
        self.refreshButton = QtWidgets.QPushButton()
        self.refreshButton.setIcon(QtGui.QIcon(utils.getIconsDir() + 'refresh.png'))
        self.refreshButton.setFixedWidth(25)
        self.connectButton = QtWidgets.QPushButton()
        self.connectButton.setIcon(QtGui.QIcon(utils.getIconsDir() + 'connect.png'))
        self.connectButton.setFixedWidth(25)
        self.disconnectButton = QtWidgets.QPushButton()
        self.disconnectButton.setIcon(QtGui.QIcon(utils.getIconsDir() + 'disconnect.png'))
        self.disconnectButton.setFixedWidth(25)
        connectLayout.addWidget(portLabel)
        connectLayout.addWidget(self.refreshButton)
        connectLayout.addWidget(self.portCombo)
        connectLayout.addWidget(self.versionCombo)
        connectLayout.addWidget(self.minuteField)
        connectLayout.addWidget(minuteLabel)
        connectLayout.addWidget(self.connectButton)
        connectLayout.addWidget(self.disconnectButton)
        centralLayout.addWidget(connectWidget, iLine, 0, QtCore.Qt.AlignLeft)
        iLine += 1

        # Bottom
        bottomWidget = QtWidgets.QWidget()
        bottomLayout = QtWidgets.QGridLayout(bottomWidget)

        # hold / spasm / breathe / reset buttons
        controlWidget = QtWidgets.QWidget()
        controlLayout = QtWidgets.QVBoxLayout(controlWidget)
        controlLayout.addStretch(1)
        self.apneaButton = QtWidgets.QPushButton('Hold')
        utils.setBorderColor(self.apneaButton, config.apneaColor)
        self.contractionButton = QtWidgets.QPushButton('Contraction')
        utils.setBorderColor(self.contractionButton, config.contractionColor)
        self.breatheButton = QtWidgets.QPushButton('Breathe')
        utils.setBorderColor(self.breatheButton, config.breatheColor)
        self.resetButton = QtWidgets.QPushButton('Reset')
        controlLayout.addWidget(self.apneaButton)
        controlLayout.addWidget(self.contractionButton)
        controlLayout.addWidget(self.breatheButton)
        controlLayout.addWidget(self.resetButton)
        bottomLayout.addWidget(controlWidget, 0, 0, QtCore.Qt.AlignTop)

        # pulse curve image
        self.pulseImage = QtGui.QImage(config.widthPulseImage, self.bmpImageSize.height(), QtGui.QImage.Format_RGB32)
        self.pulseImage.fill(config.dfltBkgColor)
        self.pulseImageHolder = QtWidgets.QLabel()
        self.pulseImageHolder.setPixmap(QtGui.QPixmap.fromImage(self.pulseImage))
        bottomLayout.addWidget(self.pulseImageHolder, 0, 1)

        # o2 bpm image
        self.bpmImage = QtGui.QImage(self.bmpImageSize, QtGui.QImage.Format_RGB32)
        self.bpmImage.fill(config.dfltBkgColor)
        self.bpmImageHolder = QtWidgets.QLabel()
        self.bpmImageHolder.setPixmap(QtGui.QPixmap.fromImage(self.bpmImage))
        bottomLayout.addWidget(self.bpmImageHolder, 0, 2)

        # o2 / bpm label
        dataWidget = QtWidgets.QWidget()
        dataLayout = QtWidgets.QGridLayout(dataWidget)
        bmpIcon = QtWidgets.QLabel()
        bmpIcon.setPixmap(QtGui.QPixmap(utils.getIconsDir() + 'heart.png'))
        o2Icon = QtWidgets.QLabel()
        o2Icon.setPixmap(QtGui.QPixmap(utils.getIconsDir() + 'oxygen.png'))
        timeIcon = QtWidgets.QLabel()
        timeIcon.setPixmap(QtGui.QPixmap(utils.getIconsDir() + 'time.png'))
        self.bpmValueLabel = QtWidgets.QLabel()
        self.o2ValueLabel = QtWidgets.QLabel()
        self.timeValueLabel = QtWidgets.QLabel()
        self.bpmValueLabel.setFixedWidth(45)
        self.o2ValueLabel.setFixedWidth(45)
        self.timeValueLabel.setFixedWidth(60)
        self.bpmValueLabel.setFont(textFont)
        self.o2ValueLabel.setFont(textFont)
        self.timeValueLabel.setFont(textFont)
        dataLayout.addWidget(bmpIcon, 0, 0)
        dataLayout.addWidget(o2Icon, 1, 0)
        dataLayout.addWidget(timeIcon, 2, 0)
        dataLayout.addWidget(self.bpmValueLabel, 0, 1)
        dataLayout.addWidget(self.o2ValueLabel, 1, 1)
        dataLayout.addWidget(self.timeValueLabel, 2, 1)
        bottomLayout.addWidget(dataWidget, 0, 3)

        # add botom
        centralLayout.addWidget(bottomWidget, iLine, 0)
        iLine += 1

        # Footer
        self.footerLabel = QtWidgets.QLabel('Oximeter Status: Not Connected')
        centralLayout.addWidget(self.footerLabel, iLine, 0)
        iLine += 1

        # Device Manager
        self.readThread = None

        # Connect UI
        self.refreshButton.clicked.connect(self.refreshSerialPorts)
        self.connectButton.clicked.connect(self.startThread)
        self.disconnectButton.clicked.connect(self.stopThread)
        self.resetButton.clicked.connect(self.resetThread)
        self.apneaButton.clicked.connect(partial(self.sendEvent, ReaderEvent.APNEA))
        self.contractionButton.clicked.connect(partial(self.sendEvent, ReaderEvent.CONTRACTION))
        self.breatheButton.clicked.connect(partial(self.sendEvent, ReaderEvent.BREATHE))

        # refresh UI
        self.refreshUI()

    # Close event
    def closeEvent(self, event):
        self.stopThread()
        event.accept()

    # Paint Event
    def paintEvent(self, event):
        # get window size
        if self.windowSize is None:
            self.windowSize = self.size()
            self.setMinimumSize(self.windowSize)

    # Resize Event
    def resizeEvent(self, event):
        if self.threadIsActive() is False and self.windowSize is not None:
            self.bpmImage = QtGui.QImage(self.bmpImageSize + self.size() - self.windowSize, QtGui.QImage.Format_RGB32)
            self.bpmImage.fill(config.dfltBkgColor)
            self.bpmImageHolder.setPixmap(QtGui.QPixmap.fromImage(self.bpmImage))
            self.pulseImage = QtGui.QImage(config.widthPulseImage, self.bpmImage.height(), QtGui.QImage.Format_RGB32)
            self.pulseImage.fill(config.dfltBkgColor)
            self.pulseImageHolder.setPixmap(QtGui.QPixmap.fromImage(self.pulseImage))

    def refreshUI(self):
        self.refreshSerialPorts()
        self.refreshApneaUI(False)

    def refreshSerialPorts(self):
        if self.threadIsActive() is False:
            self.portCombo.clear()
            ports = utils.listSerialPorts()
            for port in ports:
                self.portCombo.addItem(port)

    def refreshApneaUI(self, enable):
        self.apneaButton.setEnabled(enable)
        self.contractionButton.setEnabled(enable)
        self.breatheButton.setEnabled(enable)
        self.resetButton.setEnabled(enable)
        if enable is False:
            self.bpmValueLabel.setText('--')
            self.o2ValueLabel.setText('--%')
            self.timeValueLabel.setText('--')

    def startThread(self):
        if self.threadIsActive() is False:
            port = self.portCombo.currentText()
            version = OximeterVersion(self.versionCombo.currentIndex())
            self.readThread = ReaderUIUpdater(self, port, version)
            self.readThread.start()

    def stopThread(self):
        if self.threadIsActive() is True:
            self.readThread.threadActive = False
            self.readThread.join()
            self.readThread = None

    def resetThread(self):
        self.stopThread()
        self.startThread()

    def sendEvent(self, event):
        self.readThread.feedEvent(event)

    def threadIsActive(self):
        return (self.readThread is not None and self.readThread.threadActive is True)
