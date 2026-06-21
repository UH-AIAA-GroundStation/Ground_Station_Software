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
from PyQt5.QtCore import QTimer
import pyqtgraph as pg

x = 0
y_1 = 0
y_2 = 3
flag = False

data_x = []
data_y_1 = []
data_y_2 = []


class MainWindow(QMainWindow):
    def __init__(self):
        # global x, y_1, y_2
        # global flag
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("Scratch app")

        self.plot = pg.PlotWidget()
        self.plot.addLegend()
        self.plot.addLegend().setLabelTextColor('#FFFFFF')
        self.ui.gridLayout.addWidget(self.plot)


        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(100)

        self.curve_1 = self.plot.plot(data_x, data_y_1, name="Plot 1", pen="r")
        self.curve_2 = self.plot.plot(data_x, data_y_2, name="Plot 2", pen="g")

        self.curve_1.setClipToView(True)
        self.curve_2.setClipToView(True)
        self.curve_1.setDownsampling(ds=10, auto=True, method='peak')
        self.curve_2.setDownsampling(ds=10, auto=True, method='peak')


    def update_data(self):
        global x, y_1, y_2
        global flag
        global data_x
        global data_y_1, data_y_2

        if flag == 0:
            x +=1
            y_1 +=1
            y_2 +=1

            data_x.append(x)
            data_y_1.append(y_1)
            data_y_2.append(y_2)
            flag = True
            # print("Flag on")
        else:
            flag = False
            # print("Flag off")


        self.curve_1.setData(data_x, data_y_1)
        self.curve_2.setData(data_x, data_y_2)




        





if __name__ == "__main__":
    # Create the application
    app = QApplication(sys.argv)

    # Create the main window
    entry_window = MainWindow()

    # Show the window
    entry_window.show()

    # Start event loop
    sys.exit(app.exec_())


