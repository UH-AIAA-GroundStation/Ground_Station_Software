import pyqtgraph.examples
# pyqtgraph.examples.run()
from scratch_ui import Ui_MainWindow
import sys
import serial
import threading
import time
from serial.tools import list_ports

from PyQt5 import QtWidgets  
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtGui import QIcon, QPixmap
import pyqtgraph as pg



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("Scratch app")

        data_x = [1,2,3,4,5]
        data_y_1 = [1,2,3,4,5]

        data_y_2 = data_y_1[::-1]

        self.plot = pg.PlotWidget()
        self.plot.addLegend()
        self.plot.addLegend().setLabelTextColor('#FFFFFF')
        self.ui.gridLayout.addWidget(self.plot)
        self.plot.plot(data_x, data_y_1, name="Plot 1", pen="r")
        self.plot.plot(data_x, data_y_2, name="Plot 2", pen="g")





if __name__ == "__main__":
    # Create the application
    app = QApplication(sys.argv)

    # Create the main window
    entry_window = MainWindow()

    # Show the window
    entry_window.show()

    # Start event loop
    sys.exit(app.exec_())


