import sys
import serial
import threading
import time
from serial.tools import list_ports

from PyQt5 import QtWidgets  
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtGui import QIcon, QPixmap
import pyqtgraph as pg

from ground_app_ui import Ui_MainWindow
from entry_ui import Ui_GroundAppEntry


port = None  # Default port value
baud = 0  # Default baud rate value
connection_successful = False
main_window_time = 0 # Time when main window opens


# Constants
START_BYTE = 0x100000000 # Packet start byte
END_BYTE = 0x7F800000 # Packet end byte


# Entry window class, prompts user for COM port and baud rate, 
# attempts to open serial connection, and opens main window if successful
class entryWindow(QMainWindow):
    global port
    global baud

    def __init__(self):
        super().__init__()
        self.ui = Ui_GroundAppEntry()
        self.ui.setupUi(self)
        self.setWindowTitle("Ground Station Application")
        self.setWindowIcon(QIcon('cropped-aiaaweblogo.png'))
        LogoPixmap = QPixmap('cropped-aiaaweblogo.png')
        self.ui.AIAALogo.setPixmap(LogoPixmap)
        self.ui.AIAALogo.setScaledContents(True)  

        for port in list_ports.comports():
            self.ui.PortList.addItem(port.device)

        self.ui.ConfirmButton.clicked.connect(self.parse_port_baud)
        self.ui.ConfirmButton.clicked.connect(self.io_thread_onetime)


    # Parse selected COM port and baud rate
    def parse_port_baud(self):
        # Get the selected port and baud rate from the entry dialog
        port = str(self.ui.PortList.currentText())
        baud = int(self.ui.BaudList.currentText())

        # Validate the port and baud rate values
        if not port:
            QtWidgets.QMessageBox.warning(self, "Input Error", "Please select a valid COM port.")
            return
        if not isinstance(baud, int):
            QtWidgets.QMessageBox.warning(self, "Input Error", "Please enter a valid baud rate.")
            return
        

    # Attempt to open the serial connection for one time
    # If successful, open the main window and close the entry window
    # If unsuccessful, show an error message
    def io_thread_onetime(self):
        global connection_successful
        try:
            self.serial_connection = serial.Serial(port, baud, timeout=0.1)
            # self.serial_connection.close()
            self.window = MainWindow(self.serial_connection)
            self.window.show()
            self.close()
        except serial.SerialException as e:
            connection_successful = False
            QtWidgets.QMessageBox.critical(f"Error: {e}")
        


# Main window class, displays incoming data to LCD and graph
class MainWindow(QMainWindow):
    global main_window_time

    def __init__(self, serial_object):
        super().__init__()
        self.serial_connection = serial_object
        main_window_time = time.perf_counter()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("Ground Station Application")
        self.setWindowIcon(QIcon('cropped-aiaaweblogo.png'))
        self.load_graphing()

        threading.Thread(target=self.io_thread_function, daemon=True).start()


    # Read from serial port and strip data packet
    def io_thread_function(self):
        global port
        global baud 
        global connection_successful
        
        while connection_successful:
            try:
                data_packet = self.serial_connection.readline().strip()
                data_packet = data_packet.split(",")
                if len(data_packet) > 0 and data_packet[0] == START_BYTE and data_packet[-1] == END_BYTE:
                    data_avail_time = time.perf_counter()
                    self.parse_data_packet_to_LCD(data_packet)
                    self.graph_data(data_packet,data_avail_time)
            except serial.SerialException as e:
                QtWidgets.QMessageBox.critical(f"Error: {e}")
                connection_successful = False
                return
            
            if not connection_successful:
                break


        # Graph data values in real time
    def load_graphing(self):
        # Enable antialiasing for prettier plots
        pg.setConfigOptions(antialias=True)
        self.time_plot = []

        self.altitude_plot = pg.PlotWidget()
        self.ui.AltitudeTempGraphLayout.addWidget(self.altitude_plot)
        self.altitude_plot.addLegend()
        self.altitude_plot.addLegend().setLabelTextColor('#FFFFFF')
        self.altitude_plot.setLabel('bottom', 'Time (s)')  
        self.altitude_data = []
        self.temp_data = []


        self.adxl_graph = pg.PlotWidget()
        self.ui.ADXLAccGraphXYZLayout.addWidget(self.adxl_graph)
        self.adxl_graph.addLegend()
        self.adxl_graph.addLegend().setLabelTextColor('#FFFFFF')
        self.adxl_graph.setLabel('bottom', 'Time (s)')  
        self.adxl_acc_x_data = []
        self.adxl_acc_y_data = []
        self.adxl_acc_z_data = []

        self.lsm_graph = pg.PlotWidget()
        self.ui.LSMAccGraph_XYZLayout.addWidget(self.lsm_graph)
        self.lsm_graph.addLegend()
        self.lsm_graph.addLegend().setLabelTextColor('#FFFFFF')
        self.lsm_graph.setLabel('bottom', 'Time (s)')  
        self.lsm_acc_x_data = []
        self.lsm_acc_y_data = []
        self.lsm_acc_z_data = []

        self.gps_graph = pg.PlotWidget()
        self.ui.GPSGraphLayout.addWidget(self.gps_graph)
        self.gps_graph.showGrid(x=True, y=True)
        self.longitude_data = []
        self.latitude_data = []


    # Parse data value into corresponding LCD widgets
    def parse_data_packet_to_LCD(self, data_packet):
        self.ui.BMPTimeLCD.display(data_packet[4])
        self.ui.TemperatureLCD.display(data_packet[5])
        self.ui.PressureLCD.display(data_packet[6])
        self.ui.BMPAltitudeLCD.display(data_packet[7])

        self.ui.ADXLTimeLCD.display(data_packet[8])
        self.ui.ADXLAccelLCD_X.display(data_packet[9])
        self.ui.ADXLAccelLCD_Y.display(data_packet[10])
        self.ui.ADXLAccelLCD_Z.display(data_packet[11])

        self.ui.LSMTimeLCD.display(data_packet[12])
        self.ui.LSMAccelLCD_X.display(data_packet[13])
        self.ui.LSMAccelLCD_Y.display(data_packet[14])
        self.ui.LSMAccelLCD_Z.display(data_packet[15])
        self.ui.LSMGyroLCD_X.display(data_packet[16])
        self.ui.LSMGyroLCD_Y.display(data_packet[17])
        self.ui.LSMGyroLCD_Z.display(data_packet[18])

        self.ui.BNOTimeLCD.display(data_packet[19])
        self.ui.BNOQuarLCD_W.display(data_packet[20])
        self.ui.BNOQuarLCD_X.display(data_packet[21])
        self.ui.BNOQuarLCD_Y.display(data_packet[22])
        self.ui.BNOQuarLCD_Z.display(data_packet[23])
        
        self.ui.BNOAccelLCD_X.display(data_packet[24])
        self.ui.BNOAccelLCD_Y.display(data_packet[25])
        self.ui.BNOAccelLCD_Z.display(data_packet[26])

        self.ui.BNOMagLCD_X.display(data_packet[27])
        self.ui.BNOMagLCD_Y.display(data_packet[28])
        self.ui.BNOMagLCD_Z.display(data_packet[29])
        
        self.ui.BNOEulerLCD_X.display(data_packet[30])
        self.ui.BNOEulerLCD_Y.display(data_packet[31])
        self.ui.BNOEulerLCD_Z.display(data_packet[32])

        self.ui.GPSTimeLCD.display(data_packet[33])
        self.ui.SattelitesLCD.display(data_packet[34])
        self.ui.LatitudeLCD.display(data_packet[35])
        self.ui.LatDirectionLCD.display(data_packet[36])
        self.ui.LongitudeLCD.display(data_packet[37])
        self.ui.LongDirectionLCD.display(data_packet[38])
        self.ui.GPSAltitudeLCD.display(data_packet[39])

        self.ui.FlightStateLCD.display(data_packet[40])
        self.ui.ApogeeLCD.display(data_packet[41])


    def graph_data(self, data_packet, data_packet_time):
        self.time_plot.append(data_packet_time - main_window_time)

        self.altitude_data.append(data_packet[7])
        self.altitude_plot.plot(self.time_plot, self.altitude_data, name="Altitude Plot", pen="r")
        self.altitude_plot.plot(self.time_plot, self.temp_data, name="Temperature Plot", pen="g")
        self.altitude_plot.setClipToView(True)

        self.adxl_acc_x_data.append(data_packet[9])
        self.adxl_acc_y_data.append(data_packet[10])
        self.adxl_acc_z_data.append(data_packet[11])
        self.adxl_graph.plot(self.time_plot, self.adxl_acc_x_data, name="ADXL Accel X", pen="r")
        self.adxl_graph.plot(self.time_plot, self.adxl_acc_y_data, name="ADXL Accel Y", pen="g")
        self.adxl_graph.plot(self.time_plot, self.adxl_acc_z_data, name="ADXL Accel Z", pen="c")


            

if __name__ == "__main__":
    # Create the application
    app = QApplication(sys.argv)

    # Create the main window
    entry_window = entryWindow()

    # Show the window
    entry_window.show()

    # Start event loop
    sys.exit(app.exec_())