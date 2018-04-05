"""*************************************************************************
*                                                                          *
* Copyright (C) Nicolas Chaverou - All Rights Reserved.                    *
*                                                                          *
*************************************************************************"""

#**************************************************************************
#! @file utils.py
#  @brief Misc utils function
#**************************************************************************

#!/usr/bin/env python3
import os
import sys
import glob
import serial

""" Lists serial port names

    @raises EnvironmentError: On unsupported or unknown platforms
    @returns A list of the serial ports available on the system
    @source https://stackoverflow.com/questions/12090503/listing-available-com-ports-with-python
"""
def listSerialPorts():
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


""" clamp """
def clamp(minValue, value, maxValue):
    return max(minValue, min(value, maxValue))


""" Return the current file directory """
def getScriptPath():
    return (os.path.dirname(os.path.abspath(__file__)) + '/')


""" Return the icons directory """
def getIconsDir():
    return (getScriptPath() + 'icons/')


""" Draw a 2d box """
def drawBox(image, xValue, yValue, xSize, ySize, color):
    #image.setPixelColor(min(image.width() - 1, xValue), min(image.height() - 1, yValue), color)
    for iX in range(int(xValue - (xSize - 1) / 2), int(xValue + (xSize - 1) / 2) + 1):
        for iY in range(int(yValue - (ySize - 1) / 2), int(yValue + (ySize - 1) / 2) + 1):
            image.setPixelColor(clamp(0, iX, image.width() - 1), clamp(0, iY, image.height() - 1), color)


""" Set the border color of a push button """
def setBorderColor(pushButton, color):
    palette = pushButton.palette()
    role = pushButton.backgroundRole()  # choose whatever you like
    palette.setColor(role, color)
    pushButton.setPalette(palette)
    pushButton.setAutoFillBackground(True)
