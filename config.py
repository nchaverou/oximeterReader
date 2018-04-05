"""*************************************************************************
*                                                                          *
* Copyright (C) Nicolas Chaverou - All Rights Reserved.                    *
*                                                                          *
*************************************************************************"""

#**************************************************************************
#! @file config.py
#  @brief Various config parameters
#**************************************************************************

#!/usr/bin/env python3
from Qtpy.Qt import QtGui

# Color of the background of the bpm and pulse images
dfltBkgColor = QtGui.QColor(0, 0, 0)
# Color of the bmpColor
bmpColor = QtGui.QColor(227, 35, 15)
# Color of the o2 curve
o2Color = QtGui.QColor(0, 215, 234)
# Color of the apnea line / button
apneaColor = QtGui.QColor(0, 146, 14)
# Color of the contraction line / button
contractionColor = QtGui.QColor(234, 204, 0)
# Color of the breatheline / button
breatheColor = QtGui.QColor(234, 121, 0)
# Color of the grid lines
gridColor = QtGui.QColor(125, 125, 125)
# Frequency of the grid (a line every X seconds)
gridFrequency = 20  # seconds
# Width of the curves
curvePixelSize = 3
# Width of the pulse image
widthPulseImage = 30
# Number of minutes to monitor
dfltMinutes = 5
