#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Matplotlib Qt widget

"""
import os, sys
import numpy as np

# Qt import PySide or PyQt4
HAS_PYSIDE = False
if "PySide" in sys.modules:
    HAS_PYSIDE = True
if HAS_PYSIDE:
    os.environ['QT_API'] = 'pyside'
    from PySide import QtGui
else:
    os.environ['QT_API'] = 'pyqt'
    # force API 2
    import sip
    try:
        sip.setapi('QDate', 2)
        sip.setapi('QDateTime', 2)
        sip.setapi('QString', 2)
        sip.setapi('QtextStream', 2)
        sip.setapi('Qtime', 2)
        sip.setapi('QUrl', 2)
        sip.setapi('QVariant', 2)
    except:
        print(sys.exc_info()[1])
        pass
    try:
        from PyQt5 import QtGui
        HAS_QT = True
    except:
        from PyQt4 import QtGui
        HAS_QT = True

# Matplotlib stuff
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas

class MplCanvas(FigureCanvas):
    """ mpl canvas """
    def __init__(self, parent=None, figW=5, figH=4, figDpi=100):
        fig = plt.figure(figsize=(figW, figH), dpi=figDpi)
        self.axes = fig.add_subplot(111)
        # clear axes at every plot()
        self.axes.hold(False)
        super(MplCanvas, self).__init__(fig)
        #self.setParent(parent)
    
class MplWidget(QtGui.QWidget):
    """ mpl widget = canvas plus layout """
    def __init__(self, parent=None, **kws):
        super(MplWidget, self).__init__(parent)

        mpl = MplCanvas(parent, **kws)
        
        # layout
        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(mpl)
    
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    mpl = MplWidget()
    mpl.show()
    sys.exit(app.exec_())
