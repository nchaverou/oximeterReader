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
import sys
from Qtpy.Qt import QtWidgets
import ui

""" Launcher """
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    mainWin = ui.ReaderUI()
    mainWin.show()
    sys.exit(app.exec_())
