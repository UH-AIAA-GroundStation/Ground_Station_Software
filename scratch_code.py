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
import utm

# x = 0
y_1 = 0
y_2 = 3
flag = False

data_x = []
data_y_1 = []
data_y_2 = []

longitude_init = -95.390488
latitude_init = 29.755568

longitude_target = -97.745338
latitude_target = 30.281140

start = utm.from_latlon(latitude_init,longitude_init)

start_x = start[0]
start_y = start[1]
zone = start[2]
letter = start[3]

longitude = []
latitude = []

# normalize_x = 0
# normalize_y = 0
# normalize_x_init = 0
# normalize_y_init = 0

# counter = 0


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

        # self.curve_1 = self.plot.plot(data_x, data_y_1, name="Plot 1", pen="r")
        # self.curve_2 = self.plot.plot(data_x, data_y_2, name="Plot 2", pen="g")

        # self.curve_1.setClipToView(True)
        # self.curve_2.setClipToView(True)
        # self.curve_1.setDownsampling(ds=10, auto=True, method='peak')
        # self.curve_2.setDownsampling(ds=10, auto=True, method='peak')

        

        self.gps_curve = self.plot.plot(longitude, latitude, name="GPS", pen="g")
        self.gps_curve.setClipToView(True)
        self.gps_curve.setDownsampling(ds=3, auto=True, method='peak')


    def update_data(self):
        # global x, y_1, y_2
        global flag
        global data_x
        global data_y_1, data_y_2
        global longitude_init
        global latitude_init
        # global normalize_x, normalize_y
        # global normalize_x_init, normalize_y_init
        # global counter
        global start_x
        global start_y

        # Closest constant to get to Austin from Houston
        # longitude_init -= 0.0051
        # latitude_init += 0.00115

        longitude_init += (longitude_target - longitude_init) * 0.01
        latitude_init += (latitude_target - latitude_init) * 0.01

        # Force zone so coordinates don't get reset when zone changes
        data_packet = utm.from_latlon(latitude_init,longitude_init, force_zone_number=zone)

        print(f"Easting: {data_packet[0]}")
        print(f"Northing: {data_packet[1]}")

        x = data_packet[0] - start_x
        y = data_packet[1] - start_y

        if longitude_init <= longitude_target and latitude_init >= latitude_target:
            return

        # if counter == 1: # 1st run (no normalization values yet)
        #     normalize_x_init = data_packet[0]
        #     normalize_y_init = data_packet[1]
        #     normalize_x = data_packet[0]/normalize_x_init
        #     normalize_y = data_packet[1]/normalize_y_init
        # elif counter >= 2: # 2nd run (normalization values exist)
        #     normalize_x = data_packet[0]/normalize_x_init
        #     normalize_y = data_packet[1]/normalize_y_init

        # counter += 1

        longitude.append(x)
        latitude.append(y)

        # print(f"Real long: {longitude_init}")
        # print(f"Real lat: {latitude_init}")

        # print(normalize_x)
        # print(normalize_y)

        print(data_packet[2])

        self.gps_curve.setData(longitude, latitude)


        # if flag == 0:
        #     x +=1
        #     y_1 +=1
        #     y_2 +=1

        #     data_x.append(x)
        #     data_y_1.append(y_1)
        #     data_y_2.append(y_2)
        #     flag = True
        #     # print("Flag on")
        # else:
        #     flag = False
        #     # print("Flag off")


        # self.curve_1.setData(data_x, data_y_1)
        # self.curve_2.setData(data_x, data_y_2)



if __name__ == "__main__":
    # Create the application
    app = QApplication(sys.argv)

    # Create the main window
    entry_window = MainWindow()

    # Show the window
    entry_window.show()

    # Start event loop
    sys.exit(app.exec_())


