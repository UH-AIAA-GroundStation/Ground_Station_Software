import sys
import serial
from serial.tools import list_ports

from PyQt5 import QtWidgets  
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtGui import QIcon, QPixmap

from ground_app_ui import Ui_MainWindow
from entry_ui import Ui_GroundAppEntry


port = None  # Default port value
baud = None  # Default baud rate value
EARTH_RADIUS = 6371000  # meters, used for distance calculations for GPS Graph
UI_FILE = "Ground_Station_App_Layout.ui"  # Path to your Qt Designer UI file



class entryWindow(QMainWindow):
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
        
        # Attempt to open the serial connection and handle any exceptions
        try:
            self.serial_connection = serial.Serial(port, baud, timeout=0.1)
            self.window = MainWindow()
            self.window.show()
            self.close()  
        except serial.SerialException as e:
            QtWidgets.QMessageBox.critical(self, "Connection Error", f"Failed to connect to {port} at {baud} baud.\nError: {e}")

        

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("Ground Station Application")
        self.setWindowIcon(QIcon('cropped-aiaaweblogo.png'))


            

if __name__ == "__main__":
    # Create the application
    app = QApplication(sys.argv)

    # Create the main window
    entry_window = entryWindow()

    # Show the window
    entry_window.show()

    # Start event loop
    sys.exit(app.exec_())