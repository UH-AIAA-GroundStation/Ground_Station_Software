import sys
import time
import serial
import math
from PyQt5 import uic, QtWidgets, QtCore   # Import the uic module to load the UI file
from PyQt5.QtWidgets import QApplication, QMainWindow
import pyqtgraph as pg  # Import pyqtgraph for plotting
from collections import deque  # Import deque for efficient data storage
from PyQt5.QtGui import QIcon

port = ""  # Default port value
baud = ""  # Default baud rate value
EARTH_RADIUS = 6371000  # meters, used for distance calculations for GPS Graph
UI_FILE = "Ground_Station_App_Layout.ui"  # Path to your Qt Designer UI file

def lat_lon_to_xy(lat, lon, lat_ref, lon_ref):
    # normalize longitude difference to the shortest path across the anti-meridian
    raw_dlon = lon - lon_ref
    norm_dlon = ((raw_dlon + 180) % 360) - 180
    dlat = math.radians(lat - lat_ref)
    dlon = math.radians(norm_dlon)
    x = EARTH_RADIUS * dlon * math.cos(math.radians(lat_ref))  # East positive
    y = EARTH_RADIUS * dlat  # North positive
    return x, y

def nmea_to_decimal(dm: float) -> float:
    """Convert NMEA-style ddmm.mmmm to decimal degrees."""
    try:
        d = int(dm // 100)
        m = float(dm) - d * 100
        return d + m / 60.0
    except Exception:
        return float(dm)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, port_arg=None, baud_arg=None): # constructor
        super().__init__()  # Initialize the parent class (QMainWindow)

        self._load_ui()  # Load the UI from the .ui file
        

        # Dictionary to map data keys to LCD display widgets
        self.lcd_map = {

            # ADXL Acceleration Data
            "ADXL_ACCEL_X": self.ADXLAccelLCD_X,
            "ADXL_ACCEL_Y": self.ADXLAccelLCD_Y,
            "ADXL_ACCEL_Z": self.ADXLAccelLCD_Z,

            # LSM Acceleration Data
            "LSM_ACCEL_X": self.LSMAccelLCD_X,
            "LSM_ACCEL_Y": self.LSMAccelLCD_Y,
            "LSM_ACCEL_Z": self.LSMAccelLCD_Z,

            # BNO Acceleration Data
            "BNO_ACCEL_X": self.BNOAccelLCD_X,
            "BNO_ACCEL_Y": self.BNOAccelLCD_Y,
            "BNO_ACCEL_Z": self.BNOAccelLCD_Z,

            # Rockets data
            "APOGEE": self.ApogeeLCD,
            "FLIGHT_STATE": self.FlightStateLCD,

            # BMP Data
            "BMP_ALT": self.BMPAltitudeLCD,
            "TEMP": self.TemperatureLCD,
            "PRESS": self.PressureLCD,

            # BNO Euler
            "BNO_EULER_X": self.BNOEulerLCD_X,
            "BNO_EULER_Y": self.BNOEulerLCD_Y,
            "BNO_EULER_Z": self.BNOEulerLCD_Z,

            # BNO Magnetometer
            "BNO_MAG_X": self.BNOMagLCD_X,
            "BNO_MAG_Y": self.BNOMagLCD_Y,
            "BNO_MAG_Z": self.BNOMagLCD_Z,

            # BNO Quaternion
            "BNO_QUAT_X": self.BNOQuarLCD_X,
            "BNO_QUAT_Y": self.BNOQuarLCD_Y,
            "BNO_QUAT_Z": self.BNOQuarLCD_Z,
            "BNO_QUAT_W": self.BNOQuarLCD_W,

            # LSM Gyro
            "LSM_GYRO_X": self.LSMGyroLCD_X,
            "LSM_GYRO_Y": self.LSMGyroLCD_Y,
            "LSM_GYRO_Z": self.LSMGyroLCD_Z,

            # Sensors Time
            "GPS_TIME": self.GPSTimeLCD,
            "LSM_TIME": self.LSMTimeLCD,
            "ADXL_TIME": self.ADXLTimeLCD,
            "BNO_TIME": self.BNOTimeLCD,
            "BMP_TIME": self.BMPTimeLCD,

            # GPS Data
            "LAT": self.LatitudeLCD,
            "LAT_DIR": self.LatDirectionLCD,
            "LON": self.LongitudeLCD,
            "LON_DIR": self.LongDirectionLCD,
            "GPS_ALT": self.GPSAltitudeLCD,
            "GPS_SAT": self.SattelitesLCD,
        }  

        # store raw/sanitized args and let _setup_serial handle defaults/validation
        if isinstance(port_arg, str):
            port_arg = port_arg.strip()
        self.port = port_arg if port_arg else None

        if baud_arg is None:
            self.baud = None
        else:
            self.baud = str(baud_arg).strip()

        # GPS helpers: buffer first samples to establish stable origin,
        # remember detected format so we don't flip heuristics mid-run,
        # and keep last smoothed XY to reduce zigzag jitter.
        self._gps_origin_buffer = []
        self._gps_origin_samples = 5
        self._gps_format = None  # 'decimal' | 'nmea' | 'scaled_100' etc.
        self._gps_smoothing_alpha = 0.35
        self._gps_last_xy = None

        self._setup_serial()  # Set up the serial connection (will handle defaults)
        self._setup_plot()  # Set up the plot for real-time data visualization
        self._setup_timer()  # Set up a timer to read data from the serial port
        self.setWindowIcon(QIcon('cropped-aiaaweblogo.png'))  # Set the window icon to the AIAA logo

    def _load_ui(self):
        # Load the UI from the .ui file
        uic.loadUi(UI_FILE, self)
        self.setFixedSize(self.size())  # Set the window to a fixed size based on the UI design
        self.alt_plot_holder = self.AltitudeGraph # Get the plot holder widget from the UI
        self.temp_plot_holder = self.TempGraph # Get the temperature plot holder widget from the UI
        self.adxl_plot_holder_x = self.ADXLAccGraph_X # Get the ADXL Acceleration X plot holder widget from the UI
        self.adxl_plot_holder_y = self.ADXLAccGraph_Y # Get the ADXL Acceleration Y plot holder widget from the UI
        self.adxl_plot_holder_z = self.ADXLAccGraph_Z # Get the ADXL Acceleration Z plot holder widget from the UI

        self.lsm_plot_holder_x = self.LSMAccGraph_X # Get the LSM Acceleration X plot holder widget from the UI
        self.lsm_plot_holder_y = self.LSMAccGraph_Y # Get the LSM Acceleration Y plot holder widget from the UI
        self.lsm_plot_holder_z = self.LSMAccGraph_Z # Get the LSM Acceleration Z plot holder widget from the UI

        self.gps_plot_holder = self.GPSGraph # Get the GPS plot holder widget from the UI

    def _setup_serial(self):
        # Safely determine baud as integer and open serial port, use default rate if input is invalid
        try:
            baud_int = int(self.baud)
        except Exception:
            try:
                baud_int = int(globals().get('baud', '9600'))
            except Exception:
                baud_int = 9600

        try:
            self.ser = serial.Serial(self.port, baud_int, timeout=1)
        except Exception as e:
            # don't crash; keep app running and show a warning
            print(f"Failed to open serial port {self.port} at {baud_int}: {e}")
            self.ser = None
            try:
                QtWidgets.QMessageBox.warning(self, "Serial Error", f"Failed to open serial port {self.port} at {baud_int}: {e}")
            except Exception:
                pass

    def parse_serial_data(self,line: str) -> dict:
        output = {}
        for item in line.split(","):
            if ":" not in item:
                continue
            key, value = item.split(":",1) # split at first colon
            key = key.strip()
            value = value.strip()
            # strip surrounding quotes
            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]

            # try numeric
            try:
                num = float(value)
                # store as int when integer-valued
                if num.is_integer():
                    output[key] = int(num)
                else:
                    output[key] = num
                continue
            except ValueError:
                pass

            # otherwise preserve raw text (directions, state strings, etc.)
            output[key] = value
        return output

    def _setup_plot(self):

        # Altitude vs Time Plot--------------------------------------
        self.AltPlot = pg.PlotWidget()  # Create a PlotWidget for plotting
        altitude_layout = self.alt_plot_holder.layout()  # Get the layout of the plot holder
        if altitude_layout is None:
            altitude_layout = QtWidgets.QVBoxLayout(self.alt_plot_holder)  # Create a new vertical box layout if none exists
            altitude_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for better fit
            self.alt_plot_holder.setLayout(altitude_layout)  # Set the layout for the plot holder
        altitude_layout.addWidget(self.AltPlot)  # Add the plot to the layout

        self.AltPlot.setTitle("Altitude")  # Set the title of the plot
        self.AltPlot.setLabel('left', 'Altitude (m)')  # Set the label for the y-axis
        self.AltPlot.setLabel('bottom', 'Time (s)')  # Set the label for the x-axis
        self.AltPlot.showGrid(x=True, y=True)  # Show grid lines for better visibility
        self.AltPlot.setYRange(0, 10000)  # Set the initial y-axis range 
        
        # Data storage for plotting
        self.bmp_alt_time_data = []
        self.bmp_altitude_data = []

        # Create a curve for BMP Altitude data plotting
        self.bmp_alt_curve = self.AltPlot.plot()


        # ADXL Acceleratation X vs Time Plot--------------------------------------
        self.ADXLAccPlot_x = pg.PlotWidget()  # Create a PlotWidget for plotting
        adxl_acc_x_layout = self.adxl_plot_holder_x.layout()  # Get the layout of the acceleration X plot holder
        if adxl_acc_x_layout is None:  
            adxl_acc_x_layout = QtWidgets.QVBoxLayout(self.adxl_plot_holder_x)  # Create a new vertical box layout if none exists
            adxl_acc_x_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for better fit
            self.adxl_plot_holder_x.setLayout(adxl_acc_x_layout)  # Set the layout for the acceleration X plot holder
        adxl_acc_x_layout.addWidget(self.ADXLAccPlot_x)  # Add the acceleration X plot to the layout

        self.ADXLAccPlot_x.setTitle("ADXL Accel X")  # Set the title of the acceleration X plot
        self.ADXLAccPlot_x.setLabel('left', 'Accel (m/s²)')  # Set the label for the y-axis of the acceleration X plot
        self.ADXLAccPlot_x.setLabel('bottom', 'Time (s)')  # Set the label for the x-axis of the acceleration X plot
        self.ADXLAccPlot_x.showGrid(x=True, y=True)  # Show grid lines for better visibility in the acceleration X plot
        self.ADXLAccPlot_x.setYRange(-5, 1000)  # Set a sensible y-axis range for the acceleration X plot

        # Data storage for ADXL acceleration X plotting
        self.ADXL_x_time_data = []
        self.ADXL_x_data = []

        # Create a curve for ADXL acceleration X data plotting
        self.adxl_x_curve = self.ADXLAccPlot_x.plot()


        # ADXL Acceleratation Y vs Time Plot--------------------------------------
        self.ADXLAccPlot_y = pg.PlotWidget()  # Create a PlotWidget for plotting
        adxl_acc_y_layout = self.ADXLAccGraph_Y.layout()  # Get the layout of the acceleration Y plot holder
        if adxl_acc_y_layout is None:  
            adxl_acc_y_layout = QtWidgets.QVBoxLayout(self.adxl_plot_holder_y)  # Create a new vertical box layout if none exists
            adxl_acc_y_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for better fit
            self.adxl_plot_holder_y.setLayout(adxl_acc_y_layout)  # Set the layout for the acceleration Y plot holder
        adxl_acc_y_layout.addWidget(self.ADXLAccPlot_y)  # Add the acceleration Y plot to the layout

        self.ADXLAccPlot_y.setTitle("ADXL Accel Y")  # Set the title of the acceleration Y plot
        self.ADXLAccPlot_y.setLabel('left', 'Accel (m/s²)')  # Set the label for the y-axis of the acceleration Y plot
        self.ADXLAccPlot_y.setLabel('bottom', 'Time (s)')  # Set the label for the x-axis of the acceleration Y plot
        self.ADXLAccPlot_y.showGrid(x=True, y=True)  # Show grid lines for better visibility in the acceleration Y plot
        self.ADXLAccPlot_y.setYRange(-5, 1000)  # Set a sensible y-axis range for the acceleration Y plot

        # Data storage for ADXL acceleration Y plotting
        self.ADXL_y_time_data = []
        self.ADXL_y_data = []

        # Create a curve for ADXL acceleration Y data plotting
        self.adxl_y_curve = self.ADXLAccPlot_y.plot()


        # ADXL Acceleratation Z vs Time Plot--------------------------------------
        self.ADXLAccPlot_z = pg.PlotWidget()  # Create a PlotWidget for plotting
        adxl_acc_z_layout = self.ADXLAccGraph_Z.layout()  # Get the layout of the acceleration Z plot holder
        if adxl_acc_z_layout is None:  
            adxl_acc_z_layout = QtWidgets.QVBoxLayout(self.adxl_plot_holder_z)  # Create a new vertical box layout if none exists
            adxl_acc_z_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for better fit
            self.adxl_plot_holder_z.setLayout(adxl_acc_z_layout)  # Set the layout for the acceleration Z plot holder
        adxl_acc_z_layout.addWidget(self.ADXLAccPlot_z)  # Add the acceleration Z plot to the layout

        self.ADXLAccPlot_z.setTitle("ADXL Accel Z")  # Set the title of the acceleration Z plot
        self.ADXLAccPlot_z.setLabel('left', 'Accel (m/s²)')  # Set the label for the y-axis of the acceleration Z plot
        self.ADXLAccPlot_z.setLabel('bottom', 'Time (s)')  # Set the label for the x-axis of the acceleration Z plot
        self.ADXLAccPlot_z.showGrid(x=True, y=True)  # Show grid lines for better visibility in the acceleration Z plot
        self.ADXLAccPlot_z.setYRange(-5, 1000)  # Set a sensible y-axis range for the acceleration Z plot

        # Data storage for ADXL acceleration Z plotting
        self.ADXL_z_time_data = []
        self.ADXL_z_data = []

        # Create a curve for ADXL acceleration Z data plotting
        self.adxl_z_curve = self.ADXLAccPlot_z.plot()


        # LSM Acceleratation X vs Time Plot--------------------------------------
        self.LSMAccPlot_x = pg.PlotWidget()  # Create a PlotWidget for plotting
        lsm_acc_x_layout = self.LSMAccGraph_X.layout()  # Get the layout of the acceleration X plot holder
        if lsm_acc_x_layout is None:  
            lsm_acc_x_layout = QtWidgets.QVBoxLayout(self.lsm_plot_holder_x)  # Create a new vertical box layout if none exists
            lsm_acc_x_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for better fit
            self.lsm_plot_holder_x.setLayout(lsm_acc_x_layout)  # Set the layout for the acceleration X plot holder
        lsm_acc_x_layout.addWidget(self.LSMAccPlot_x)  # Add the acceleration X plot to the layout

        self.LSMAccPlot_x.setTitle("LSM Accel X")  # Set the title of the acceleration X plot
        self.LSMAccPlot_x.setLabel('left', 'Accel (m/s²)')  # Set the label for the y-axis of the acceleration X plot
        self.LSMAccPlot_x.setLabel('bottom', 'Time (s)')  # Set the label for the x-axis of the acceleration X plot
        self.LSMAccPlot_x.showGrid(x=True, y=True)  # Show grid lines for better visibility in the acceleration X plot
        self.LSMAccPlot_x.setYRange(-5, 1000)  # Set a sensible y-axis range for the acceleration X plot

        # Data storage for LSM acceleration X plotting
        self.LSM_x_time_data = []
        self.LSM_x_data = []

        # Create a curve for LSM acceleration X data plotting
        self.lsm_x_curve = self.LSMAccPlot_x.plot()


        # LSM Acceleratation Y vs Time Plot--------------------------------------
        self.LSMAccPlot_y = pg.PlotWidget()  # Create a PlotWidget for plotting
        lsm_acc_y_layout = self.LSMAccGraph_Y.layout()  # Get the layout of the acceleration Y plot holder
        if lsm_acc_y_layout is None:  
            lsm_acc_y_layout = QtWidgets.QVBoxLayout(self.lsm_plot_holder_y)  # Create a new vertical box layout if none exists
            lsm_acc_y_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for better fit
            self.lsm_plot_holder_y.setLayout(lsm_acc_y_layout)  # Set the layout for the acceleration Y plot holder
        lsm_acc_y_layout.addWidget(self.LSMAccPlot_y)  # Add the acceleration Y plot to the layout

        self.LSMAccPlot_y.setTitle("LSM Accel Y")  # Set the title of the acceleration Y plot
        self.LSMAccPlot_y.setLabel('left', 'Accel (m/s²)')  # Set the label for the y-axis of the acceleration Y plot
        self.LSMAccPlot_y.setLabel('bottom', 'Time (s)')  # Set the label for the x-axis of the acceleration Y plot
        self.LSMAccPlot_y.showGrid(x=True, y=True)  # Show grid lines for better visibility in the acceleration Y plot
        self.LSMAccPlot_y.setYRange(-5, 1000)  # Set a sensible y-axis range for the acceleration Y plot

        # Data storage for LSM acceleration Y plotting
        self.LSM_y_time_data = []
        self.LSM_y_data = []

        # Create a curve for LSM acceleration Y data plotting
        self.lsm_y_curve = self.LSMAccPlot_y.plot()


        # LSM Acceleratation Z vs Time Plot--------------------------------------
        self.LSMAccPlot_z = pg.PlotWidget()  # Create a PlotWidget for plotting
        lsm_acc_z_layout = self.LSMAccGraph_Z.layout()  # Get the layout of the acceleration Z plot holder
        if lsm_acc_z_layout is None:  
            lsm_acc_z_layout = QtWidgets.QVBoxLayout(self.lsm_plot_holder_z)  # Create a new vertical box layout if none exists
            lsm_acc_z_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for better fit
            self.lsm_plot_holder_z.setLayout(lsm_acc_z_layout)  # Set the layout for the acceleration Z plot holder
        lsm_acc_z_layout.addWidget(self.LSMAccPlot_z)  # Add the acceleration Z plot to the layout

        self.LSMAccPlot_z.setTitle("LSM Accel Z")  # Set the title of the acceleration Z plot
        self.LSMAccPlot_z.setLabel('left', 'Accel (m/s²)')  # Set the label for the y-axis of the acceleration Z plot
        self.LSMAccPlot_z.setLabel('bottom', 'Time (s)')  # Set the label for the x-axis of the acceleration Z plot
        self.LSMAccPlot_z.showGrid(x=True, y=True)  # Show grid lines for better visibility in the acceleration Z plot
        self.LSMAccPlot_z.setYRange(-5, 1000)  # Set a sensible y-axis range for the acceleration Z plot

        # Data storage for LSM acceleration Z plotting
        self.LSM_z_time_data = []
        self.LSM_z_data = []

        # Create a curve for LSM acceleration Z data plotting
        self.lsm_z_curve = self.LSMAccPlot_z.plot()


        # Temperature vs Time PLot---------------------------------------
        self.TempPlot = pg.PlotWidget()  # Create a PlotWidget for plotting
        temp_layout = self.temp_plot_holder.layout()  # Get the layout of the temperature plot holder
        if temp_layout is None:
            temp_layout = QtWidgets.QVBoxLayout(self.temp_plot_holder)  # Create a new vertical box layout if none exists
            temp_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for better fit
            self.temp_plot_holder.setLayout(temp_layout)  # Set the layout for the temperature plot holder
        temp_layout.addWidget(self.TempPlot)  # Add the temperature plot to the layout

        self.TempPlot.setTitle("Temperature")  # Set the title of the temperature plot
        self.TempPlot.setLabel('left', 'Temp(°C)')  # Set the label for the y-axis of the temperature plot
        self.TempPlot.setLabel('bottom', 'Time (s)')  # Set the label for the x-axis of the temperature plot
        self.TempPlot.showGrid(x=True, y=True)  # Show grid lines for better visibility in the temperature plot
        self.TempPlot.setYRange(-20, 40)  # Set the initial y-axis range for the temperature plot

        # Data storage for plotting
        self.temp_time_data = []  
        self.temp_data = []  

        # Create a curve for real-time temperature data plotting
        self.temp_curve = self.TempPlot.plot()  


        # GPS Graph---------------------------------------
        self.GPSPlot = pg.PlotWidget()  # Create a PlotWidget for GPS plotting
        self.GPSPlot.setXRange(-100, 100)  # Set initial x-axis range for GPS plot
        self.GPSPlot.setYRange(-100, 100)  # Set initial y-axis range for GPS plot
        gps_layout = self.GPSGraph.layout()  # Get the layout of the GPS plot holder
        if gps_layout is None:
            gps_layout = QtWidgets.QVBoxLayout(self.GPSGraph)  # Create a new vertical box layout if none exists
            gps_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for better fit
            self.GPSGraph.setLayout(gps_layout)  # Set the layout for the GPS plot holder

        gps_layout.addWidget(self.GPSPlot)  # Add the GPS plot to the layout
        self.GPSPlot.setTitle("GPS")  # Set the title of the GPS plot
        self.GPSPlot.setLabel('left', 'South(-) / North(+) (m)')  # Set the label for the y-axis of the GPS plot
        self.GPSPlot.setLabel('bottom', 'West(-) / East(+) (m)')  # Set the label for the x-axis of the GPS plot
        self.GPSPlot.showGrid(x=True, y=True)  # Show grid lines for better visibility in the GPS plot
        self.GPSPlot.setAspectLocked(True)  # Lock the aspect ratio for accurate representation of GPS data
        self.gps_dot = self.GPSPlot.plot([],[],symbol='o') # Create a dot to represent the current GPS position
        self.origin = None  # Store the reference GPS coordinates for converting to XY

        # Data storage for GPS plotting
        self.x_data = [] 
        self.y_data = []  

        # Create a curve for real-time GPS data plotting
        self.gps_curve = self.GPSPlot.plot() 


        # Start time for x-axis of all plots
        self.time_x = time.perf_counter()


    def _setup_timer(self):
        self.update_timer = QtCore.QTimer(self)  # Create a QTimer for periodic updates
        self.update_timer.timeout.connect(self._tick)  # Connect the timer to the data update method
        self.update_timer.start(100)  # Set the timer to trigger every 100 ms

    def _tick(self):
        line = self.ser.readline().decode("utf-8").strip()  # Read a line from the serial port
        if not line:
            return  # If no data is read, exit the method
        
        # Parse the serial data into a dictionary
        data = self.parse_serial_data(line) 

        # Update LCDs / labels with parsed data
        for key, widget in self.lcd_map.items():
            if key not in data:
                continue
            val = data[key]
            # numeric -> try `display()` (QLCDNumber) first
            if isinstance(val, (int, float)):
                try:
                    widget.display(val)
                    continue
                except Exception:
                    pass
                # fallback to setText if widget supports it
                try:
                    widget.setText(f"{val}")
                    continue
                except Exception:
                    pass

            # non-numeric values: try setText (QLabel/QLineEdit)
            try:
                widget.setText(str(val))
            except Exception:
                # widget doesn't support text; ignore gracefully
                pass

        if "TIMEMS" in data:
            time_ms = float(data["TIMEMS"]) / 1000.0  # Convert milliseconds to seconds
        else:
            time_ms = time.perf_counter() - self.time_x  # Use elapsed time since start if TIMEMS is not available


        if "BMP_ALT" in data:
            # Get the altitude value
            altitude = float(data["BMP_ALT"])

            # Store and plot
            if "TIMEMS" not in data:
                # Calculate elapsed time since start
                alt_time_sec = time.perf_counter() - self.time_x  
                self.bmp_alt_time_data.append(alt_time_sec)  # Append the elapsed time to the time data list
                self.bmp_altitude_data.append(altitude)  # Append the altitude to the altitude data list
                self.bmp_alt_curve.setData(self.bmp_alt_time_data, self.bmp_altitude_data)  # Update the plot with new data
            else:
                self.bmp_alt_time_data.append(time_ms)  # Append the TIMEMS time to the time data list
                self.bmp_altitude_data.append(altitude)  # Append the altitude to the altitude data list
                self.bmp_alt_curve.setData(self.bmp_alt_time_data, self.bmp_altitude_data)  # Update the plot with new data



        if "ADXL_ACCEL_X" in data:
            adxl_acc_x = float(data["ADXL_ACCEL_X"])

            # Store and plot
            if "TIMEMS" not in data:
                adxl_acc_x_time_sec = time.perf_counter() - self.time_x  
                self.ADXL_x_time_data.append(adxl_acc_x_time_sec)  # Append the elapsed time to the time data list
                self.ADXL_x_data.append(adxl_acc_x)  # Append the acceleration to the acceleration data list
                self.adxl_x_curve.setData(self.ADXL_x_time_data, self.ADXL_x_data)  # Update the plot with new data
            else:
                self.ADXL_x_time_data.append(time_ms)  # Append the TIMEMS time to the time data list
                self.ADXL_x_data.append(adxl_acc_x)  # Append the acceleration to the acceleration data list
                self.adxl_x_curve.setData(self.ADXL_x_time_data, self.ADXL_x_data)  # Update the plot with new data


        if "ADXL_ACCEL_Y" in data:
            adxl_acc_y = float(data["ADXL_ACCEL_Y"])

            # Store and plot
            if "TIMEMS" not in data:
                adxl_acc_y_time_sec = time.perf_counter() - self.time_x  
                self.ADXL_y_time_data.append(adxl_acc_y_time_sec)  # Append the elapsed time to the time data list
                self.ADXL_y_data.append(adxl_acc_y)  # Append the acceleration to the acceleration data list
                self.adxl_y_curve.setData(self.ADXL_y_time_data, self.ADXL_y_data)  # Update the plot with new data
            else:
                self.ADXL_y_time_data.append(time_ms)  # Append the TIMEMS time to the time data list
                self.ADXL_y_data.append(adxl_acc_y)  # Append the acceleration to the acceleration data list
                self.adxl_y_curve.setData(self.ADXL_y_time_data, self.ADXL_y_data)  # Update the plot with new data


        if "ADXL_ACCEL_Z" in data:
            adxl_acc_z = float(data["ADXL_ACCEL_Z"])

            # Store and plot
            if "TIMEMS" not in data:
                adxl_acc_z_time_sec = time.perf_counter() - self.time_x  
                self.ADXL_z_time_data.append(adxl_acc_z_time_sec)  # Append the elapsed time to the time data list
                self.ADXL_z_data.append(adxl_acc_z)  # Append the acceleration to the acceleration data list
                self.adxl_z_curve.setData(self.ADXL_z_time_data, self.ADXL_z_data)  # Update the plot with new data
            else:
                self.ADXL_z_time_data.append(time_ms)  # Append the TIMEMS time to the time data list
                self.ADXL_z_data.append(adxl_acc_z)  # Append the acceleration to the acceleration data list
                self.adxl_z_curve.setData(self.ADXL_z_time_data, self.ADXL_z_data)  # Update the plot with new data


        if "LSM_ACCEL_X" in data:
            lsm_acc_x = float(data["LSM_ACCEL_X"])

            # Store and plot
            if "TIMEMS" not in data:
                lsm_acc_x_time_sec = time.perf_counter() - self.time_x  
                self.LSM_x_time_data.append(lsm_acc_x_time_sec)  # Append the elapsed time to the time data list
                self.LSM_x_data.append(lsm_acc_x)  # Append the acceleration to the acceleration data list
                self.lsm_x_curve.setData(self.LSM_x_time_data, self.LSM_x_data)  # Update the plot with new data
            else:
                self.LSM_x_time_data.append(time_ms)  # Append the TIMEMS time to the time data list
                self.LSM_x_data.append(lsm_acc_x)  # Append the acceleration to the acceleration data list
                self.lsm_x_curve.setData(self.LSM_x_time_data, self.LSM_x_data)  # Update the plot with new data


        if "LSM_ACCEL_Y" in data:
            lsm_acc_y = float(data["LSM_ACCEL_Y"])

            # Store and plot
            if "TIMEMS" not in data:
                lsm_acc_y_time_sec = time.perf_counter() - self.time_x  
                self.LSM_y_time_data.append(lsm_acc_y_time_sec)  # Append the elapsed time to the time data list
                self.LSM_y_data.append(lsm_acc_y)  # Append the acceleration to the acceleration data list
                self.lsm_y_curve.setData(self.LSM_y_time_data, self.LSM_y_data)  # Update the plot with new data
            else:
                self.LSM_y_time_data.append(time_ms)  # Append the TIMEMS time to the time data list
                self.LSM_y_data.append(lsm_acc_y)  # Append the acceleration to the acceleration data list
                self.lsm_y_curve.setData(self.LSM_y_time_data, self.LSM_y_data)  # Update the plot with new data


        if "LSM_ACCEL_Z" in data:
            lsm_acc_z = float(data["LSM_ACCEL_Z"])

            # Store and plot
            if "TIMEMS" not in data:
                lsm_acc_z_time_sec = time.perf_counter() - self.time_x  
                self.LSM_z_time_data.append(lsm_acc_z_time_sec)  # Append the elapsed time to the time data list
                self.LSM_z_data.append(lsm_acc_z)  # Append the acceleration to the acceleration data list
                self.lsm_z_curve.setData(self.LSM_z_time_data, self.LSM_z_data)  # Update the plot with new data
            else:
                self.LSM_z_time_data.append(time_ms)  # Append the TIMEMS time to the time data list
                self.LSM_z_data.append(lsm_acc_z)  # Append the acceleration to the acceleration data list
                self.lsm_z_curve.setData(self.LSM_z_time_data, self.LSM_z_data)  # Update the plot with new data


        if "TEMP" in data:
            bmp_temp = float(data["TEMP"])

            # Store and plot
            if "TIMEMS" not in data:
                temp_time_sec = time.perf_counter() - self.time_x  
                self.temp_time_data.append(temp_time_sec)  # Append the elapsed time to the time data list
                self.temp_data.append(bmp_temp)  # Append the temperature to the temperature data list
                self.temp_curve.setData(self.temp_time_data, self.temp_data)  # Update the temperature plot with new data
            else:
                self.temp_time_data.append(time_ms)  # Append the TIMEMS time to the time data list
                self.temp_data.append(bmp_temp)  # Append the temperature to the temperature data list
                self.temp_curve.setData(self.temp_time_data, self.temp_data)  # Update the temperature plot with new data


        if "LAT" in data and "LON" in data:
            lat_raw = data["LAT"]
            lon_raw = data["LON"]

            def _try_formats(raw_lat, raw_lon):
                """Return (lat, lon, format_name) for the first valid interpretation."""
                # 1) decimal degrees
                try:
                    la = float(raw_lat)
                    lo = float(raw_lon)
                    if abs(la) <= 90 and abs(lo) <= 180:
                        return la, lo, 'decimal'
                except Exception:
                    pass

                # 2) NMEA ddmm.mmmm
                try:
                    la = nmea_to_decimal(float(raw_lat))
                    lo = nmea_to_decimal(float(raw_lon))
                    if abs(la) <= 90 and abs(lo) <= 180:
                        return la, lo, 'nmea'
                except Exception:
                    pass

                # 3) simple scaled values (try common divisors)
                scales = [100.0, 1000.0, 10000.0]
                for s in scales:
                    try:
                        la = float(raw_lat) / s
                        lo = float(raw_lon) / s
                        if abs(la) <= 90 and abs(lo) <= 180:
                            return la, lo, f'scaled_{int(s)}'
                    except Exception:
                        continue

                # Fallback: try floats anyway
                try:
                    return float(raw_lat), float(raw_lon), 'decimal'
                except Exception:
                    return None, None, None

            # determine or reuse detected format to avoid mid-run flips
            if self._gps_format is None:
                lat, lon, fmt = _try_formats(lat_raw, lon_raw)
                self._gps_format = fmt
            else:
                fmt = self._gps_format
                try:
                    if fmt == 'decimal' or fmt is None:
                        lat = float(lat_raw)
                        lon = float(lon_raw)
                    elif fmt == 'nmea':
                        lat = nmea_to_decimal(float(lat_raw))
                        lon = nmea_to_decimal(float(lon_raw))
                    elif fmt.startswith('scaled_'):
                        s = float(fmt.split('_', 1)[1])
                        lat = float(lat_raw) / s
                        lon = float(lon_raw) / s
                    else:
                        lat = float(lat_raw)
                        lon = float(lon_raw)
                except Exception:
                    # parsing failed for chosen format: try autodetect
                    lat, lon, fmt = _try_formats(lat_raw, lon_raw)
                    self._gps_format = fmt

            # apply hemisphere fields if provided
            if "LAT_DIR" in data and isinstance(data["LAT_DIR"], str):
                if data["LAT_DIR"].upper() == 'S':
                    lat = -abs(lat)
            if "LON_DIR" in data and isinstance(data["LON_DIR"], str):
                if data["LON_DIR"].upper() == 'W':
                    lon = -abs(lon)

            if lat is None or lon is None:
                return

            # Build a stable origin by averaging the first N samples to avoid first-sample jitter
            if self.origin is None:
                self._gps_origin_buffer.append((lat, lon))
                if len(self._gps_origin_buffer) < self._gps_origin_samples:
                    return
                lat_ref = sum(p[0] for p in self._gps_origin_buffer) / len(self._gps_origin_buffer)
                lon_ref = sum(p[1] for p in self._gps_origin_buffer) / len(self._gps_origin_buffer)
                self.origin = (lat_ref, lon_ref)
            else:
                lat_ref, lon_ref = self.origin

            x, y = lat_lon_to_xy(lat, lon, lat_ref, lon_ref)  # Convert GPS coordinates to XY

            # smoothing to reduce zigzag spikes
            if self._gps_last_xy is None:
                sx, sy = x, y
            else:
                lx, ly = self._gps_last_xy
                a = self._gps_smoothing_alpha
                sx = lx * (1.0 - a) + x * a
                sy = ly * (1.0 - a) + y * a
            self._gps_last_xy = (sx, sy)

            self.x_data.append(sx)  # Append the x-coordinate to the x data list
            self.y_data.append(sy)  # Append the y-coordinate to the y data list

            self.gps_curve.setData(self.x_data, self.y_data)  # Update the GPS plot with new data
            self.gps_dot.setData([sx], [sy])  # Update the GPS plot with the current position as a dot

    def closeEvent(self, event):
        try:
            if self.ser and self.ser.is_open:
               self.ser.close()  # Close the serial connection when the window is closed
        except Exception:
            pass
        event.accept()  # Accept the close event

        

if __name__ == "__main__":
    # Create the application
    app = QApplication(sys.argv)

    # Create the main window
    window = MainWindow()
    window.setWindowTitle("Ground Station Application")

    # resize the window to fit the content
    window.resize(1200, 800)

    # Show the window
    window.show()

    # Start event loop
    sys.exit(app.exec_())