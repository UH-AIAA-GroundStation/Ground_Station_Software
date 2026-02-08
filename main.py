import sys
import time
import serial
from PyQt5 import uic, QtWidgets, QtCore  # Import the uic module to load the UI file
from PyQt5.QtWidgets import QApplication, QMainWindow
import pyqtgraph as pg  # Import pyqtgraph for plotting
from collections import deque  # Import deque for efficient data storage

PORT = "COM3"  # Replace with your serial port
BAUD_RATE = 9600  # Replace with your baud rate (to be improved later)
UI_FILE = "Ground_Station_App_Layout.ui"  # Path to your Qt Designer UI file

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self): # constructor
        super().__init__()  # Initialize the parent class (QMainWindow)

        self._load_ui()  # Load the UI from the .ui file
        self._setup_serial()  # Set up the serial connection
        self._setup_plot()  # Set up the plot for real-time data visualization
        self._setup_timer()  # Set up a timer to read data from the serial port

    def _load_ui(self):
        # Load the UI from the .ui file
        uic.loadUi(UI_FILE, self)
        self.setFixedSize(self.size())  # Set the window to a fixed size based on the UI design
        self.plot_holder = self.AltitudeGraph # Get the plot holder widget from the UI

    def _setup_serial(self):
        self.ser = serial.Serial(PORT, BAUD_RATE, timeout=1)  # Initialize the serial connection

    def _setup_plot(self):
        self.plot = pg.PlotWidget()  # Create a PlotWidget for plotting

        layout = self.plot_holder.layout()  # Get the layout of the plot holder
        if layout is None:
            layout = QtWidgets.QVBoxLayout(self.plot_holder)  # Create a new vertical box layout if none exists
            layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for better fit
            self.plot_holder.setLayout(layout)  # Set the layout for the plot holder
        layout.addWidget(self.plot)  # Add the plot to the layout

        self.plot.setTitle("Real-Time Altitude Plot")  # Set the title of the plot
        self.plot.setLabel('left', 'Altitude (m)')  # Set the label for the y-axis
        self.plot.setLabel('bottom', 'Time (s)')  # Set the label for the x-axis
        self.plot.showGrid(x=True, y=True)  # Show grid lines for better visibility

        self.plot.setYRange(0, 10000)  # Set the initial y-axis range 
        
        # Data storage for plotting
        self.time_data = []
        self.altitude_data = []

        # Create a curve for real-time data plotting
        self.curve = self.plot.plot()

        # Start time for x-axis
        self.time_x = time.perf_counter()

    def _setup_timer(self):
        self.update_timer = QtCore.QTimer(self)  # Create a QTimer for periodic updates
        self.update_timer.timeout.connect(self._tick)  # Connect the timer to the data update method
        self.update_timer.start(100)  # Set the timer to trigger every 100 ms

    def _tick(self):
        line = self.ser.readline().decode("utf-8").strip()  # Read a line from the serial port
        if not line:
            return  # If no data is read, exit the method
        
        try:
            altitude = float(line)  # Convert the read line to a float (altitude value)
        except ValueError:
            return  # If conversion fails, exit the method
        
        # Update Altitude LCD display
        if hasattr(self, "AltitudeLCD"): # Check if the LCD display exists
            self.AltitudeLCD.display(altitude)  # Update the LCD display with the new altitude value

        # Calculate elapsed time since start
        time_sec = time.perf_counter() - self.time_x  

        # Store and plot
        self.time_data.append(time_sec)  # Append the elapsed time to the time data list
        self.altitude_data.append(altitude)  # Append the altitude to the altitude data list
        self.curve.setData(self.time_data, self.altitude_data)  # Update the plot with new data

        # X-axis range adjustment
        self.plot.setXRange(0, time_sec)

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