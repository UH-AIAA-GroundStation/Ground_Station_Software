import sys
import serial
from PyQt5 import uic, QtWidgets, QtCore  # Import the uic module to load the UI file
from PyQt5.QtWidgets import QApplication, QMainWindow

PORT = "COM3"  # Replace with your serial port
BAUD_RATE = 9600  # Replace with your baud rate (to be improved later)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self): # constructor
        super().__init__()  # Initialize the parent class (QMainWindow)

        # Load Qt Designer UI file
        uic.loadUi("Ground_Station_App_Layout.ui", self)  # Load the UI file into this class
        self.setFixedSize(self.size())  # Set a fixed size for the window

        # Open the serial port
        self.ser = serial.Serial(PORT, BAUD_RATE, timeout=0.1);

        # Timer to read serial data periodically
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.read_serial_data)
        self.timer.start(50)  # Read every 50 ms (20Hz)

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