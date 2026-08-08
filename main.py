# Author: Thanh Pham (Tony Pham)

# Import lib
import sys
import serial
import threading
import time
import utm
from serial.tools import list_ports
import subprocess
from PyQt5 import QtWidgets  
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import pyqtSignal, QObject
import pyqtgraph as pg
import struct

# File import
from dependencies_modules.ground_app_ui import Ui_MainWindow
from dependencies_modules.entry_ui import Ui_GroundAppEntry

# Helper globals
port = None  # Default port value
baud = 0  # Default baud rate value
launch_zone = 0 # Launch zone for GPS graph
connection_successful = False
connection_sem = threading.Semaphore(1)
serial_success = False
data_packet = []


# Constants
START_BYTE = 0x100000000 # Packet start byte
EXPECTED_PAYLOAD_SIZE = 121 # Total Payload size in bytes (Refer to Teensy serial_packet)
EXPECTED_PACKET_SIZE = EXPECTED_PAYLOAD_SIZE + 2 # Payload size + CRC16 in bytes
TEXAS_STATE_ZONES = (13,14,15) # Available zones in Texas



# Main thread signaling to print data to LCD
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
        global port
        global baud
        global launch_zone
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
    # If unsuccessful, show an error message and return to entry window
    def io_thread_onetime(self):
        global connection_successful
        global serial_success
        # Acquire serial semaphore
        connection_sem.acquire()
        try:
            self.serial_connection = serial.Serial(port, baud, timeout=0.1)
            self.serial_connection.close()
            serial_success = True
            QtWidgets.QMessageBox.information(
                self,
                "Success",
                "Serial connection successful!"
            )
            self.close()
        except serial.SerialException as e:
            connection_successful = False
            serial_success = False
            QtWidgets.QMessageBox.critical(self, "Error", f"Error: {e}")
            return
        # Release serial semaphore upon successful connection
        connection_sem.release()
        # Open main window upon successfull connection
        if serial_success:
            self.window = MainWindow()
            self.window.show()



# Main window class, displays incoming data to LCD and graph
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Start timer when main window opens
        self.main_window_time = time.perf_counter()
        # Setup UI
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("Ground Station Application")
        self.setWindowIcon(QIcon('cropped-aiaaweblogo.png'))
        # Flag to toggle pause graphing
        self.graph_paused = False
        # Setup graphing
        self.load_graphing()
        # Start I/O thread and get data
        threading.Thread(target=self.io_thread_function, daemon=True).start()
        # Print data to LCDs and graph from worker thread to main thread
        self.print_to_LCD = signal_to_LCD()
        self.print_to_LCD.print_lcd_signal.connect(self.main_thread_connection)
        # Reset graph button
        self.ui.ResetGraphButton.clicked.connect(self.reset_graph)
        # Reset serial connection
        self.ui.ResetSerialButton.clicked.connect(self.reset_serial_connection)
        # Pause graph button
        self.ui.PauseGraphButton.clicked.connect(self.toggle_graph_pause)


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


    # Unpack data packet to helper values and sensors data
    def unpack_packet(self, payload):
        offset = 0
        # Unpack data packet
        header, counter, failureType, packet_time = struct.unpack_from("<QIBI", payload, offset)
        offset += struct.calcsize("<QIBI")

        # Unpack sensors data
        # BMP
        BMP_time, BMP_temp, BMP_pressure, BMP_altitude = struct.unpack_from(
            "<Qhhh",
            payload,
            offset
        )
        offset += struct.calcsize("<Qhhh")

        # LSM
        LSM_time = struct.unpack_from("<Q", payload, offset)[0]
        offset += 8

        LSM_accel = struct.unpack_from("<3h", payload, offset)
        offset += struct.calcsize("<3h")

        LSM_gyro = struct.unpack_from("<3h", payload, offset)
        offset += struct.calcsize("<3h")

        # ADXL
        ADXL_time = struct.unpack_from("<Q", payload, offset)[0]
        offset += 8

        ADXL_accel = struct.unpack_from("<3h", payload, offset)
        offset += struct.calcsize("<3h")

        # BNO
        BNO_time = struct.unpack_from("<Q", payload, offset)[0]
        offset += 8

        BNO_quat = struct.unpack_from("<4h", payload, offset)
        offset += struct.calcsize("<4h")

        BNO_euler = struct.unpack_from("<3h", payload, offset)
        offset += struct.calcsize("<3h")

        BNO_magnet = struct.unpack_from("<3h", payload, offset)
        offset += struct.calcsize("<3h")

        BNO_accel = struct.unpack_from("<3h", payload, offset)
        offset += struct.calcsize("<3h")

        # GPS
        GPS_time = struct.unpack_from("<Q", payload, offset)[0]
        offset += 8

        GPS_sat = struct.unpack_from("<b", payload, offset)[0]
        offset += 1

        GPS_lon, GPS_lat = struct.unpack_from("<hh", payload, offset)
        offset += struct.calcsize("<hh")

        GPS_lon_dir = struct.unpack_from("<c", payload, offset)[0].decode()
        offset += 1

        GPS_lat_dir = struct.unpack_from("<c", payload, offset)[0].decode()
        offset += 1

        GPS_alt = struct.unpack_from("<h", payload, offset)[0]
        offset += 2

        # Flight
        flightState = struct.unpack_from("<B", payload, offset)[0]
        offset += 1

        apogeeEstimate = struct.unpack_from("<f", payload, offset)[0]
        offset += 4

        return [
            header, counter, failureType, packet_time,
            # BMP
            BMP_time, BMP_temp / 1000.0, BMP_pressure / 1000.0, BMP_altitude / 1000.0,
            # ADXL
            ADXL_time, ADXL_accel[0] / 1000.0, ADXL_accel[1] / 1000.0, ADXL_accel[2] / 1000.0,
            # LSM
            LSM_time, LSM_accel[0] / 1000.0, LSM_accel[1] / 1000.0, LSM_accel[2] / 1000.0,
            LSM_gyro[0] / 1000.0, LSM_gyro[1] / 1000.0, LSM_gyro[2] / 1000.0,
            # BNO
            BNO_time, BNO_quat[0] / 1000.0, BNO_quat[1] / 1000.0,
            BNO_quat[2] / 1000.0, BNO_quat[3] / 1000.0,
            BNO_accel[0] / 1000.0, BNO_accel[1] / 1000.0, BNO_accel[2] / 1000.0,
            BNO_magnet[0] / 1000.0, BNO_magnet[1] / 1000.0, BNO_magnet[2] / 1000.0,
            BNO_euler[0] / 1000.0, BNO_euler[1] / 1000.0, BNO_euler[2] / 1000.0,
            # GPS
            GPS_time, GPS_sat, GPS_lat / 100000.0, GPS_lat_dir,
            GPS_lon / 100000.0, GPS_lon_dir, GPS_alt / 1000.0,
            # Flight info
            flightState,
            apogeeEstimate
        ]
    

    # Connect worker thread to main thread to perform printing and graphing
    def main_thread_connection(self, data_packet, data_avail_time):
        self.parse_data_packet_to_LCD(data_packet)
        if not self.graph_paused:
            self.graph_data(data_packet, data_avail_time)


    # Read from serial port and strip data packet
    def io_thread_function(self):
        global connection_successful
        global data_packet
        connection_sem.acquire()
        # Attempt to connect to MCU
        try:
            self.serial_connection = serial.Serial(port, baud, timeout=0.1)
            connection_successful = True
        except serial.SerialException:
            connection_successful = False
            connection_sem.release()
            # print(self, "Error", f"Error: {e}") # Debug
        
        # If serial connection is good, read data, start timer, and print to LCD 
        while connection_successful:
            try:
                # Read a data line and unpack header, data, crc16
                line = self.serial_connection.readline().decode(errors="ignore").strip()
                try:
                    packet = bytes.fromhex(line)
                    if len(packet) != EXPECTED_PACKET_SIZE:
                        continue
                except ValueError:
                    continue
                if len(packet) < 2:
                    continue

                payload = packet[:-2]
                rx_crc = (packet[-2] << 8) | packet[-1]
                # Read from byte 0 of the payload to get header byte at position 0 in a return tuple (<Q = little-endian,uint64_t)
                # if len is not valid, skip packet
                if len(payload) < 8:
                    continue
                header_payload = struct.unpack_from("<Q", payload, 0)[0] 
                
                if len(payload) > 0 and header_payload == START_BYTE:
                    # Checksum recalculation
                    result = subprocess.run(
                        ["pycrc", "--model", "crc-16-ccitt", "--check-hexstring", payload.hex()],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    # Get the raw checksum values without flag, \n, error, ...
                    checksum_string = result.stdout.strip() # "0x..."
                    calc_checksum = int(checksum_string, 16)

                    # Verify checksum from the data packet 
                    if calc_checksum == rx_crc:
                        # Unpack payload, if len is invalid, skip packet
                        if len(payload) != EXPECTED_PAYLOAD_SIZE:
                            continue
                        data_packet = self.unpack_packet(payload)
                        # Record packet time
                        data_avail_time = time.perf_counter()
                        # Print to LCD and graph data
                        self.print_to_LCD.print_lcd_signal.emit(data_packet,data_avail_time)
                    else: # Bad checksum, skip packet
                        continue
                    
            except serial.SerialException as e:
                # print(self, "Error", f"Error: {e}") # Debug
                connection_successful = False
                connection_sem.release()
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
        self.time_plot.append(data_packet_time - self.main_window_time)

        # Altitude and Temperature plot
        self.altitude_data.append(float(data_packet[7]))
        self.temp_data.append(float(data_packet[5]))
        altitude_curve = self.altitude_plot.plot(self.time_plot, self.altitude_data, name="Altitude Plot", pen="r")
        temp_curve = self.altitude_plot.plot(self.time_plot, self.temp_data, name="Temperature Plot", pen="g")
        altitude_curve.setClipToView(True)
        temp_curve.setClipToView(True)
        # 5 data points in, plot 3 points (min-mid-max)
        altitude_curve.setDownsampling(ds=5, auto=True, method='peak')
        temp_curve.setDownsampling(ds=5, auto=True, method='peak')

        # ADXL X/Y/Z plot (red, green, cyan)
        self.adxl_acc_x_data.append(float(data_packet[9]))
        self.adxl_acc_y_data.append(float(data_packet[10]))
        self.adxl_acc_z_data.append(float(data_packet[11]))
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
        self.lsm_acc_x_data.append(float(data_packet[13]))
        self.lsm_acc_y_data.append(float(data_packet[14]))
        self.lsm_acc_z_data.append(float(data_packet[15]))
        lsm_x_curve = self.lsm_graph.plot(self.time_plot, self.lsm_acc_x_data, name="LSM Accel X", pen="r")
        lsm_y_curve = self.lsm_graph.plot(self.time_plot, self.lsm_acc_y_data, name="LSM Accel Y", pen="g")
        lsm_z_curve = self.lsm_graph.plot(self.time_plot, self.lsm_acc_z_data, name="LSM Accel Z", pen="c")
        lsm_x_curve.setClipToView(True)
        lsm_y_curve.setClipToView(True)
        lsm_z_curve.setClipToView(True)
        # 5 data points in, plot 3 points (min-mid-max)
        lsm_x_curve.setDownsampling(ds=5, auto=True, method='peak')
        lsm_y_curve.setDownsampling(ds=5, auto=True, method='peak')
        lsm_z_curve.setDownsampling(ds=5, auto=True, method='peak')

        # Graph GPS (Easting = x, Northing = y)
        # x, y = utm.from_latlon(input_lat, input_lon)
        # Return (Easting, Northing, Zone Number, Zone Letter)
        gps_2d = utm.from_latlon(float(data_packet[35]), float(data_packet[37]), force_zone_number=launch_zone)
        self.longitude_data.append(gps_2d[0])
        self.latitude_data.append(gps_2d[1])
        gps_curve = self.gps_graph.plot(self.longitude_data, self.latitude_data, name="GPS", symbol='o')
        gps_curve.setClipToView(True)
        # 5 data points in, plot 3 points (min-mid-max)
        gps_curve.setDownsampling(ds=5, auto=True, method='peak')


    # Reset timer and data of graph to reset graph
    def reset_graph(self):
        # Reset data for graph
        self.altitude_data.clear()
        self.temp_data.clear()
        self.adxl_acc_x_data.clear()
        self.adxl_acc_y_data.clear()
        self.adxl_acc_z_data.clear()
        self.lsm_acc_x_data.clear()
        self.lsm_acc_y_data.clear()
        self.lsm_acc_z_data.clear()
        self.longitude_data.clear()
        self.latitude_data.clear()

        # Reset initial graph timer to 0
        self.time_plot.clear()
        self.main_window_time = time.perf_counter()


    # Reset serial connection
    def reset_serial_connection(self):
        global connection_successful
        # Disconnect 
        connection_successful = False
        self.serial_connection.close()
        # Acquire serial semaphore and reconnect
        connection_sem.acquire()
        try:
            self.serial_connection = serial.Serial(port, baud, timeout=0.1)
            connection_successful = True
            QtWidgets.QMessageBox.information(
                self,
                "Success",
                "Serial reconnection successful!"
            )
        except serial.SerialException as e:
            connection_successful = False
            QtWidgets.QMessageBox.information(
                self,
                "Failure",
                f"Error: {e}"
            )
            # Failure to reconnect, release semaphore
            connection_sem.release()
        # If successful, release semaphore
        connection_sem.release()


    # Toggle pause/resume graphing
    def toggle_graph_pause(self):
        self.graph_paused = not self.graph_paused

        if self.graph_paused:
            self.ui.PauseGraphButton.setText("Resume Graph")
        else:
            self.ui.PauseGraphButton.setText("Pause Graph")

            

if __name__ == "__main__":
    # Create the application
    app = QApplication(sys.argv)
    # Entry window
    entry_window = entryWindow()
    entry_window.show()
    # Start event loop
    sys.exit(app.exec_())