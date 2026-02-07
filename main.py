import sys
from PyQt5 import uic, QtWidgets  # Import the uic module to load the UI file
from PyQt5.QtWidgets import QApplication, QMainWindow


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self): # constructor
        super().__init__()  # Initialize the parent class (QMainWindow)

        # Load Qt Designer UI file
        uic.loadUi("Ground_Station_App_Layout.ui", self)  # Load the UI file into this class
        self.setFixedSize(self.size())  # Set a fixed size for the window


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