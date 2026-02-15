import sys
import time
import serial
import math
from PyQt5 import uic, QtWidgets, QtCore  # Import the uic module to load the UI file
from PyQt5.QtWidgets import QApplication, QMainWindow
import pyqtgraph as pg  # Import pyqtgraph for plotting
from collections import deque  # Import deque for efficient data storage

EARTH_RADIUS = 6371000  # meters, used for distance calculations for GPS Graph
PORT = "COM3"  # Replace with your serial port
BAUD_RATE = 9600  # Replace with your baud rate (to be improved later)
UI_FILE = "Ground_Station_App_Layout.ui"  # Path to your Qt Designer UI file

def lat_lon_to_xy(lat, lon, lat_ref, lon_ref):
    dlat = math.radians(lat - lat_ref)
    dlon = math.radians(lon - lon_ref)
    x = EARTH_RADIUS * dlon * math.cos(math.radians(lat_ref)) # East
    y = EARTH_RADIUS * dlat # North
    return x, y

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self): # constructor
        super().__init__()  # Initialize the parent class (QMainWindow)

        self._load_ui()  # Load the UI from the .ui file

        # Dictionary to map data keys to LCD display widgets
        self.lcd_map = {
            "ALT": self.AltitudeLCD,
            "TEMP": self.TemperatureLCD,
            "LAT": self.LatitudeLCD,
            "LON": self.LongitudeLCD,
        }  

        self._setup_serial()  # Set up the serial connection
        self._setup_plot()  # Set up the plot for real-time data visualization
        self._setup_timer()  # Set up a timer to read data from the serial port

    def _load_ui(self):
        # Load the UI from the .ui file
        uic.loadUi(UI_FILE, self)
        self.setFixedSize(self.size())  # Set the window to a fixed size based on the UI design
        self.alt_plot_holder = self.AltitudeGraph # Get the plot holder widget from the UI
        self.temp_plot_holder = self.TempGraph # Get the temperature plot holder widget from the UI

    def _setup_serial(self):
        self.ser = serial.Serial(PORT, BAUD_RATE, timeout=1)  # Initialize the serial connection

    def parse_serial_data(self,line: str) -> dict:
        output = {}
        for item in line.split(","):
            if ":" not in item:
                continue
            key, value = item.split(":",1) # split at first colon
            key = key.strip()
            value = value.strip()
            try:
                output[key] = float(value)  # Try to convert the value to a float
            except ValueError:
                try:
                    output[key] = int(value)  # If float conversion fails, try to convert to an int
                except ValueError:
                    pass  # If both conversions fail, ignore the value
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

        self.AltPlot.setTitle("Real-Time Altitude Plot")  # Set the title of the plot
        self.AltPlot.setLabel('left', 'Altitude (m)')  # Set the label for the y-axis
        self.AltPlot.setLabel('bottom', 'Time (s)')  # Set the label for the x-axis
        self.AltPlot.showGrid(x=True, y=True)  # Show grid lines for better visibility
        self.AltPlot.setYRange(0, 10000)  # Set the initial y-axis range 
        
        # Data storage for plotting
        self.alt_time_data = []
        self.altitude_data = []

        # Create a curve for real-time data plotting
        self.alt_curve = self.AltPlot.plot()


        # Temperature vs Time PLot---------------------------------------
        self.TempPlot = pg.PlotWidget()  # Create a PlotWidget for plotting
        temp_layout = self.temp_plot_holder.layout()  # Get the layout of the temperature plot holder
        if temp_layout is None:
            temp_layout = QtWidgets.QVBoxLayout(self.temp_plot_holder)  # Create a new vertical box layout if none exists
            temp_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for better fit
            self.temp_plot_holder.setLayout(temp_layout)  # Set the layout for the temperature plot holder
        temp_layout.addWidget(self.TempPlot)  # Add the temperature plot to the layout

        self.TempPlot.setTitle("Real-Time Temperature Plot")  # Set the title of the temperature plot
        self.TempPlot.setLabel('left', 'Temperature (°C)')  # Set the label for the y-axis of the temperature plot
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
        self.GPSPlot.setTitle("Real-time tracker")  # Set the title of the GPS plot
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

        # Update LCD displays with parsed data 
        for key, lcd in self.lcd_map.items():
            if key in data:
                lcd.display(f"{float(data[key]):.2f}")  # Update LCD with values

        if "TIMEMS" in data:
            time_ms = float(data["TIMEMS"]) / 1000.0  # Convert milliseconds to seconds
        else:
            time_ms = time.perf_counter() - self.time_x  # Use elapsed time since start if TIMEMS is not available

        if "ALT" in data:
            # Get the altitude value
            altitude = data["ALT"]  

            # Store and plot
            if "TIMEMS" not in data:
                # Calculate elapsed time since start
                alt_time_sec = time.perf_counter() - self.time_x  
                self.alt_time_data.append(alt_time_sec)  # Append the elapsed time to the time data list
                self.altitude_data.append(altitude)  # Append the altitude to the altitude data list
                self.alt_curve.setData(self.alt_time_data, self.altitude_data)  # Update the plot with new data
            else:
                self.alt_time_data.append(time_ms)  # Append the TIMEMS time to the time data list
                self.altitude_data.append(altitude)  # Append the altitude to the altitude data list
                self.alt_curve.setData(self.alt_time_data, self.altitude_data)  # Update the plot with new data

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
            lat = float(data["LAT"])
            lon = float(data["LON"])

            # Set origin automatically on first GPS data received
            if self.origin is None:
                self.origin = (lat, lon)

            lat_ref, lon_ref = self.origin
            x, y = lat_lon_to_xy(lat, lon, lat_ref, lon_ref)  # Convert GPS coordinates to XY

            self.x_data.append(x)  # Append the x-coordinate to the x data list
            self.y_data.append(y)  # Append the y-coordinate to the y data list

            self.gps_curve.setData(self.x_data, self.y_data)  # Update the GPS plot with new data
            self.gps_dot.setData([x], [y])  # Update the GPS plot with the current position as a dot

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