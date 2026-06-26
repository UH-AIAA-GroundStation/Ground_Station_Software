import sys
import serial
import threading
import time
import utm
from serial.tools import list_ports

from PyQt5 import QtWidgets  
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import pyqtSignal, QObject
import pyqtgraph as pg

from ground_app_ui import Ui_MainWindow
from entry_ui import Ui_GroundAppEntry


port = None  # Default port value
baud = 0  # Default baud rate value
launch_zone = 0 # Launch zone for GPS graph
TEXAS_STATE_ZONES = (13,14,15) # Available zones in Texas
connection_successful = False
main_window_time = 0 # Time when main window opens
connection_sem = threading.Semaphore(1)
serial_success = False
data_packet = []


# Constants
START_BYTE = 0x100000000 # Packet start byte
END_BYTE = 0x7F800000 # Packet end byte



class signal_to_LCD(QObject):
    print_lcd_signal = pyqtSignal(list, float)


# Entry window class, prompts user for COM port and baud rate, 
# attempts to open serial connection, and opens main window if successful
class entryWindow(QMainWindow):
    global port
    global baud

    def __init__(self):
        super().__init__()
        # Setup UI
        self.ui = Ui_GroundAppEntry()
        self.ui.setupUi(self)
        self.setWindowTitle("Ground Station Application")
        self.setWindowIcon(QIcon('cropped-aiaaweblogo.png'))
        LogoPixmap = QPixmap('cropped-aiaaweblogo.png')
        self.ui.AIAALogo.setPixmap(LogoPixmap)
        self.ui.AIAALogo.setScaledContents(True) 
        # Add items to lists
        for port in list_ports.comports():
            self.ui.PortList.addItem(port.device)
        for zone in TEXAS_STATE_ZONES:
            self.ui.ZoneList.addItem(str(zone))
        # Button click trigger
        self.ui.ConfirmButton.clicked.connect(self.parse_entry_arguments)
        self.ui.ConfirmButton.clicked.connect(self.io_thread_onetime)


    # Parse selected COM port, baud rate, and launch zone
    def parse_entry_arguments(self):
        # Get the selected port and baud rate from the entry dialog
        port = str(self.ui.PortList.currentText())
        baud = int(self.ui.BaudList.currentText())
        launch_zone = int(self.ui.ZoneList.currentText())

        # Validate the port and baud rate values
        if not port:
            QtWidgets.QMessageBox.warning(self, "Input Error", "Please choose a valid COM port.")
            return
        if not isinstance(baud, int):
            QtWidgets.QMessageBox.warning(self, "Input Error", "Please choose a valid baud rate.")
            return
        if not isinstance(launch_zone, int):
            QtWidgets.QMessageBox.warning(self, "Input Error", "Please choose a valid zone.")
            return
        

    # Attempt to open the serial connection for one time
    # If successful, open the main window and close the entry window
    # If unsuccessful, show an error message
    def io_thread_onetime(self):
        global connection_successful
        connection_sem.acquire()
        try:
            self.serial_connection = serial.Serial(port, baud, timeout=0.1)
            self.serial_connection.close()
            serial_success = True
            self.close()
        except serial.SerialException as e:
            connection_successful = False
            serial_success = False
            QtWidgets.QMessageBox.critical(self, "Error", f"Error: {e}")

        connection_sem.release()
        # Open main window upon successfull connection
        if serial_success:
            self.window = MainWindow()
            self.window.show()


# Main window class, displays incoming data to LCD and graph
class MainWindow(QMainWindow):
    def __init__(self):
        global main_window_time
        super().__init__()
        # Start timer when main window opens
        main_window_time = time.perf_counter()
        # Setup UI
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("Ground Station Application")
        self.setWindowIcon(QIcon('cropped-aiaaweblogo.png'))
        self.load_graphing()
        # Start I/O thread and get data
        threading.Thread(target=self.io_thread_function, daemon=True).start()
        # Print data to LCDs and graph from worker thread to main thread
        self.print_to_LCD = signal_to_LCD()
        self.print_to_LCD.print_lcd_signal.connect(self.main_thread_connection)


    # Setting up data graph
    def load_graphing(self):
        # Enable antialiasing for prettier plots
        pg.setConfigOptions(antialias=True)
        self.time_plot = []

        # Altitude and temp graph and data setup
        self.altitude_plot = pg.PlotWidget()
        self.ui.AltitudeTempGraphLayout.addWidget(self.altitude_plot)
        self.altitude_plot.addLegend()
        self.altitude_plot.addLegend().setLabelTextColor('#FFFFFF')
        self.altitude_plot.setLabel('bottom', 'Time (s)')  
        self.altitude_data = []
        self.temp_data = []

        # ADXL graph and data setup
        self.adxl_graph = pg.PlotWidget()
        self.ui.ADXLAccGraphXYZLayout.addWidget(self.adxl_graph)
        self.adxl_graph.addLegend()
        self.adxl_graph.addLegend().setLabelTextColor('#FFFFFF')
        self.adxl_graph.setLabel('bottom', 'Time (s)')  
        self.adxl_acc_x_data = []
        self.adxl_acc_y_data = []
        self.adxl_acc_z_data = []

        # LSM graph and data setup
        self.lsm_graph = pg.PlotWidget()
        self.ui.LSMAccGraph_XYZLayout.addWidget(self.lsm_graph)
        self.lsm_graph.addLegend()
        self.lsm_graph.addLegend().setLabelTextColor('#FFFFFF')
        self.lsm_graph.setLabel('bottom', 'Time (s)')  
        self.lsm_acc_x_data = []
        self.lsm_acc_y_data = []
        self.lsm_acc_z_data = []

        # GPS graph and data setup
        self.gps_graph = pg.PlotWidget()
        self.ui.GPSGraphLayout.addWidget(self.gps_graph)
        self.gps_graph.showGrid(x=True, y=True)
        
        self.mouse_hover_label = pg.TextItem(text="", color="w", anchor=(0.1,1))
        self.gps_graph.addItem(self.mouse_hover_label)
        self.gps_graph.scene().sigMouseMoved.connect(self.gps_mouse_hover)

        self.longitude_data = []
        self.latitude_data = []

    
    # Connect worker thread to main thread to perform printing and graphing
    def main_thread_connection(self, data_packet, data_avail_time):
        self.parse_data_packet_to_LCD(data_packet)
        self.graph_data(data_packet, data_avail_time)


    # Read from serial port and strip data packet
    def io_thread_function(self):
        global port
        global baud 
        global connection_successful
        global data_packet
        connection_sem.acquire()
        # Attempt to connect to MCU
        try:
            self.serial_connection = serial.Serial(port, baud, timeout=0.1)
            connection_successful = True
        except serial.SerialException as e:
            connection_successful = False
            connection_sem.release()
            # print(self, "Error", f"Error: {e}") # Debug
        
        # If serial connection is good, read data, start timer, and print to LCD 
        while connection_successful:
            try:
                data_packet = self.serial_connection.readline().strip()
                data_packet = data_packet.split(",")
                if len(data_packet) > 0 and data_packet[0] == START_BYTE and data_packet[-1] == END_BYTE:
                    data_avail_time = time.perf_counter()
                    self.print_to_LCD.print_lcd_signal.emit(data_packet,data_avail_time)
            except serial.SerialException as e:
                # print(self, "Error", f"Error: {e}") # Debug
                connection_successful = False
                return
            
            if not connection_successful:
                break

        connection_sem.release()


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

    
    # Signal to enable mouse with x,y coordinates when hovering on GPS graph
    def gps_mouse_hover(self,pos):
        if self.gps_graph.sceneBoundingRect().contains(pos):
            mouse_point = self.gps_graph.plotItem.vb.mapSceneToView(pos)
            self.mouse_hover_label.setText(f"X: {mouse_point.x():.2f}, Y: {mouse_point.y():.2f}")
            self.mouse_hover_label.setPos(mouse_point)


    # Setup data points, graph name/style, Downsampling
    def graph_data(self, data_packet, data_packet_time):
        # Apend time of current packet
        self.time_plot.append(data_packet_time - main_window_time)

        # Altitude and Temperature plot
        self.altitude_data.append(data_packet[7])
        altitude_curve = self.altitude_plot.plot(self.time_plot, self.altitude_data, name="Altitude Plot", pen="r")
        temp_curve = self.altitude_plot.plot(self.time_plot, self.temp_data, name="Temperature Plot", pen="g")
        altitude_curve.setClipToView(True)
        temp_curve.setClipToView(True)
        # 5 data points in, plot 3 points (min-mid-max)
        altitude_curve.setDownsampling(ds=5, auto=True, method='peak')
        temp_curve.setDownsampling(ds=5, auto=True, method='peak')

        # ADXL X/Y/Z plot (red, green, cyan)
        self.adxl_acc_x_data.append(data_packet[9])
        self.adxl_acc_y_data.append(data_packet[10])
        self.adxl_acc_z_data.append(data_packet[11])
        adxl_x_curve = self.adxl_graph.plot(self.time_plot, self.adxl_acc_x_data, name="ADXL Accel X", pen="r")
        adxl_y_curve = self.adxl_graph.plot(self.time_plot, self.adxl_acc_y_data, name="ADXL Accel Y", pen="g")
        adxl_z_curve = self.adxl_graph.plot(self.time_plot, self.adxl_acc_z_data, name="ADXL Accel Z", pen="c")
        adxl_x_curve.setClipToView(True)
        adxl_y_curve.setClipToView(True)
        adxl_z_curve.setClipToView(True)
        # 5 data points in, plot 3 points (min-mid-max)
        adxl_x_curve.setDownsampling(ds=5, auto=True, method='peak')
        adxl_y_curve.setDownsampling(ds=5, auto=True, method='peak')
        adxl_z_curve.setDownsampling(ds=5, auto=True, method='peak')

        # LSM X/Y/Z plot (red, green, cyan)
        self.lsm_acc_x_data.append(data_packet[9])
        self.lsm_acc_y_data.append(data_packet[10])
        self.lsm_acc_z_data.append(data_packet[11])
        lsm_x_curve = self.adxl_graph.plot(self.time_plot, self.adxl_acc_x_data, name="ADXL Accel X", pen="r")
        lsm_y_curve = self.adxl_graph.plot(self.time_plot, self.adxl_acc_y_data, name="ADXL Accel Y", pen="g")
        lsm_z_curve = self.adxl_graph.plot(self.time_plot, self.adxl_acc_z_data, name="ADXL Accel Z", pen="c")
        lsm_x_curve.setClipToView(True)
        lsm_y_curve.setClipToView(True)
        lsm_z_curve.setClipToView(True)
        # 5 data points in, plot 3 points (min-mid-max)
        lsm_x_curve.setDownsampling(ds=5, auto=True, method='peak')
        lsm_y_curve.setDownsampling(ds=5, auto=True, method='peak')
        lsm_z_curve.setDownsampling(ds=5, auto=True, method='peak')

        # Graph GPS
        # x, y = utm.from_latlon(input_lat, input_lon)
        # Return (Easting, Northing, Zone Number, Zone Letter)
        gps_2d = utm.from_latlon(data_packet[35], data_packet[37], force_zone_number=launch_zone)
        self.longitude_data.append(gps_2d[0])
        self.latitude_data.append(gps_2d[1])
        gps_curve = self.gps_graph.plot(self.longitude_data, self.latitude_data, name="GPS", symbol='o')
        gps_curve.setClipToView(True)
        # 5 data points in, plot 3 points (min-mid-max)
        gps_curve.setDownsampling(ds=5, auto=True, method='peak')


            

if __name__ == "__main__":
    # Create the application
    app = QApplication(sys.argv)
    # Entry window
    entry_window = entryWindow()
    entry_window.show()
    # Start event loop
    sys.exit(app.exec_())