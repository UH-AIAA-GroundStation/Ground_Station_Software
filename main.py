import sys
import serial
from PyQt5 import uic, QtWidgets, QtCore  # Import the uic module to load the UI file
from PyQt5.QtWidgets import QApplication, QMainWindow
import pyqtgraph as pg  # Import pyqtgraph for plotting
from collections import deque  # Import deque for efficient data storage

PORT = "COM3"  # Replace with your serial port
BAUD_RATE = 9600  # Replace with your baud rate (to be improved later)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self): # constructor
        super().__init__()  # Initialize the parent class (QMainWindow)

        # Load Qt Designer UI file
        uic.loadUi("Ground_Station_App_Layout.ui", self)  # Load the UI file into this class

        self.setFixedSize(self.size())  # Set a fixed size for the window

        # Open the serial port
        self.ser = serial.Serial(PORT, BAUD_RATE, timeout=0.1)

        # Timer to read serial data periodically
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.read_serial_data)
        self.timer.start(50)  # Read every 50 ms (20Hz)

        self.plot = pg.PlotWidget()  # Create a plot widget

        layout = self.widget.layout()  # Get the layout of the GraphWidget from the UI
        if layout is None:
            layout = QtWidgets.QVBoxLayout(self.widget)  # Create a new vertical layout if none exists
            self.widget.setLayout(layout)  # Set the new layout to the GraphWidget
        layout.addWidget(self.plot)  # Add the plot widget to the layout

         # Configure the plot
        self.plot.setTitle("Real-Time Altitude Plot")
        self.plot.setLabel('left', 'Altitude (m)')
        self.plot.setLabel('bottom', 'Time (s)')
        self.plot.setYRange(0, 10000)  # Set Y-axis range (adjust as needed)
        self.plot_data = deque(maxlen=200)  # Store the last 200 data
        self.plot.showGrid(x=True, y=True)  # Show grid for better visibility
        self.data = deque([0.0]*200, maxlen=200)  # Initialize data deque with zeros

        self.data = []  # List to store incoming data for plotting
        self.curve = self.plot.plot(self.data)  # Create a curve for plotting

        self.start_time = QtCore.QTime.currentTime()  # Record the start time for the X-axis
        self.time_data = deque(maxlen=200)  # Store the last 200 time points for the X-axis
        self.value_data = deque(maxlen=200)  # Store the last 200 values for the Y-axis

        self.timer = QtCore.QTimer() # Timer for updating the graph (sample numbers)
        self.timer.timeout.connect(self.update_graph)
        self.timer.start(100)  # Update the graph every 100 ms (10Hz)

    def update_graph(self):
        line = self.ser.readline().decode('utf-8').strip() # Read a line from the serial port, decode it, and strip whitespace
        if not line:
            return  # Skip if line is empty
            
        try:
            value = float(line)
        except ValueError:
            pass  # Ignore bad lines

        self.data.append(value)  # Append new data point
        self.curve.setData(self.data)  # Update the curve with new data

        elapsed_time = self.start_time.msecsTo(QtCore.QTime.currentTime()) / 1000.0  # Calculate elapsed time in seconds
        self.time_data.append(elapsed_time)  # Append elapsed time to the time data deque
        self.value_data.append(value)  # Append the new value to the value data deque
        self.curve.setData(list(self.time_data), list(self.value_data))  # Update the curve with new time and value data

    def read_serial_data(self):
        try:
            line = self.ser.readline().decode('utf-8').strip()  # Read a line from the serial port
            if line:
                value = float(line)
                self.lcdNumber.display(value)  # Update the LCD display with the new value
        except ValueError:
            pass  # Ignore bad lines


    def closeEvent(self, event):
        if self.ser.is_open:
            self.ser.close()  # Close the serial port when the application is closed
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