import sys
import time
import serial
import math
from PyQt5 import uic, QtWidgets, QtCore   # Import the uic module to load the UI file
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
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(2336, 1363)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.gridLayoutWidget = QtWidgets.QWidget(self.tab)
        self.gridLayoutWidget.setGeometry(QtCore.QRect(50, 880, 691, 371))
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.gridLayoutWidget)
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.AltitudeGraph = QtWidgets.QWidget(self.gridLayoutWidget)
        self.AltitudeGraph.setObjectName("AltitudeGraph")
        self.gridLayout_2.addWidget(self.AltitudeGraph, 0, 0, 1, 1)
        self.gridLayoutWidget_2 = QtWidgets.QWidget(self.tab)
        self.gridLayoutWidget_2.setGeometry(QtCore.QRect(810, 880, 691, 371))
        self.gridLayoutWidget_2.setObjectName("gridLayoutWidget_2")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.gridLayoutWidget_2)
        self.gridLayout_3.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.TempGraph = QtWidgets.QWidget(self.gridLayoutWidget_2)
        self.TempGraph.setObjectName("TempGraph")
        self.gridLayout_3.addWidget(self.TempGraph, 0, 0, 1, 1)
        self.gridLayoutWidget_3 = QtWidgets.QWidget(self.tab)
        self.gridLayoutWidget_3.setGeometry(QtCore.QRect(1560, 880, 721, 371))
        self.gridLayoutWidget_3.setObjectName("gridLayoutWidget_3")
        self.gridLayout_4 = QtWidgets.QGridLayout(self.gridLayoutWidget_3)
        self.gridLayout_4.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.GPSGraph = QtWidgets.QWidget(self.gridLayoutWidget_3)
        self.GPSGraph.setObjectName("GPSGraph")
        self.gridLayout_4.addWidget(self.GPSGraph, 0, 0, 1, 1)
        self.groupBox_2 = QtWidgets.QGroupBox(self.tab)
        self.groupBox_2.setGeometry(QtCore.QRect(550, 240, 971, 181))
        self.groupBox_2.setStyleSheet("background-color: rgb(227, 227, 227);\n"
"background-color: rgb(241, 241, 241);\n"
"font: 87 9pt \"Segoe UI Black\";")
        self.groupBox_2.setObjectName("groupBox_2")
        self.label_7 = QtWidgets.QLabel(self.groupBox_2)
        self.label_7.setGeometry(QtCore.QRect(30, 29, 191, 41))
        self.label_7.setStyleSheet("font: 87 11pt \"Segoe UI Black\";\n"
"font: 11pt \"MS Shell Dlg 2\";")
        self.label_7.setAlignment(QtCore.Qt.AlignCenter)
        self.label_7.setObjectName("label_7")
        self.LongitudeLCD = QtWidgets.QLCDNumber(self.groupBox_2)
        self.LongitudeLCD.setGeometry(QtCore.QRect(310, 70, 191, 81))
        self.LongitudeLCD.setSmallDecimalPoint(False)
        self.LongitudeLCD.setDigitCount(7)
        self.LongitudeLCD.setObjectName("LongitudeLCD")
        self.LatitudeLCD = QtWidgets.QLCDNumber(self.groupBox_2)
        self.LatitudeLCD.setGeometry(QtCore.QRect(30, 69, 181, 81))
        self.LatitudeLCD.setMinimumSize(QtCore.QSize(111, 31))
        self.LatitudeLCD.setAutoFillBackground(False)
        self.LatitudeLCD.setSmallDecimalPoint(False)
        self.LatitudeLCD.setDigitCount(7)
        self.LatitudeLCD.setMode(QtWidgets.QLCDNumber.Dec)
        self.LatitudeLCD.setSegmentStyle(QtWidgets.QLCDNumber.Filled)
        self.LatitudeLCD.setObjectName("LatitudeLCD")
        self.label_11 = QtWidgets.QLabel(self.groupBox_2)
        self.label_11.setGeometry(QtCore.QRect(310, 30, 191, 41))
        self.label_11.setStyleSheet("font: 87 11pt \"Segoe UI Black\";\n"
"font: 11pt \"MS Shell Dlg 2\";")
        self.label_11.setAlignment(QtCore.Qt.AlignCenter)
        self.label_11.setObjectName("label_11")
        self.textBrowser = QtWidgets.QTextBrowser(self.groupBox_2)
        self.textBrowser.setGeometry(QtCore.QRect(220, 70, 61, 81))
        self.textBrowser.setObjectName("textBrowser")
        self.textBrowser_2 = QtWidgets.QTextBrowser(self.groupBox_2)
        self.textBrowser_2.setGeometry(QtCore.QRect(510, 70, 61, 81))
        self.textBrowser_2.setObjectName("textBrowser_2")
        self.label_43 = QtWidgets.QLabel(self.groupBox_2)
        self.label_43.setGeometry(QtCore.QRect(600, 30, 191, 41))
        self.label_43.setStyleSheet("font: 87 11pt \"Segoe UI Black\";\n"
"font: 11pt \"MS Shell Dlg 2\";")
        self.label_43.setAlignment(QtCore.Qt.AlignCenter)
        self.label_43.setObjectName("label_43")
        self.SattelitesLCD_2 = QtWidgets.QLCDNumber(self.groupBox_2)
        self.SattelitesLCD_2.setGeometry(QtCore.QRect(600, 70, 191, 81))
        self.SattelitesLCD_2.setSmallDecimalPoint(False)
        self.SattelitesLCD_2.setDigitCount(7)
        self.SattelitesLCD_2.setObjectName("SattelitesLCD_2")
        self.SattelitesLCD = QtWidgets.QLCDNumber(self.groupBox_2)
        self.SattelitesLCD.setGeometry(QtCore.QRect(800, 70, 161, 81))
        self.SattelitesLCD.setSmallDecimalPoint(False)
        self.SattelitesLCD.setDigitCount(7)
        self.SattelitesLCD.setObjectName("SattelitesLCD")
        self.label_6 = QtWidgets.QLabel(self.groupBox_2)
        self.label_6.setGeometry(QtCore.QRect(800, 30, 161, 41))
        self.label_6.setStyleSheet("font: 87 11pt \"Segoe UI Black\";\n"
"font: 11pt \"MS Shell Dlg 2\";")
        self.label_6.setAlignment(QtCore.Qt.AlignCenter)
        self.label_6.setObjectName("label_6")
        self.groupBox_4 = QtWidgets.QGroupBox(self.tab)
        self.groupBox_4.setGeometry(QtCore.QRect(800, 30, 721, 181))
        self.groupBox_4.setStyleSheet("background-color: rgb(227, 227, 227);\n"
"background-color: rgb(241, 241, 241);\n"
"font: 87 9pt \"Segoe UI Black\";")
        self.groupBox_4.setObjectName("groupBox_4")
        self.label_10 = QtWidgets.QLabel(self.groupBox_4)
        self.label_10.setGeometry(QtCore.QRect(490, 29, 191, 41))
        self.label_10.setStyleSheet("font: 87 11pt \"Segoe UI Black\";\n"
"font: 11pt \"MS Shell Dlg 2\";")
        self.label_10.setAlignment(QtCore.Qt.AlignCenter)
        self.label_10.setObjectName("label_10")
        self.label_20 = QtWidgets.QLabel(self.groupBox_4)
        self.label_20.setGeometry(QtCore.QRect(70, 149, 161, 31))
        font = QtGui.QFont()
        font.setFamily("MS Shell Dlg 2")
        font.setPointSize(10)
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(9)
        self.label_20.setFont(font)
        self.label_20.setStyleSheet("font: 75 10pt \"MS Shell Dlg 2\";")
        self.label_20.setAlignment(QtCore.Qt.AlignCenter)
        self.label_20.setObjectName("label_20")
        self.label_12 = QtWidgets.QLabel(self.groupBox_4)
        self.label_12.setGeometry(QtCore.QRect(60, 29, 191, 41))
        self.label_12.setStyleSheet("font: 87 11pt \"Segoe UI Black\";\n"
"font: 11pt \"MS Shell Dlg 2\";")
        self.label_12.setAlignment(QtCore.Qt.AlignCenter)
        self.label_12.setObjectName("label_12")
        self.TemperatureLCD_3 = QtWidgets.QLCDNumber(self.groupBox_4)
        self.TemperatureLCD_3.setGeometry(QtCore.QRect(270, 69, 191, 81))
        self.TemperatureLCD_3.setSmallDecimalPoint(False)
        self.TemperatureLCD_3.setDigitCount(7)
        self.TemperatureLCD_3.setObjectName("TemperatureLCD_3")
        self.label_21 = QtWidgets.QLabel(self.groupBox_4)
        self.label_21.setGeometry(QtCore.QRect(280, 150, 161, 21))
        font = QtGui.QFont()
        font.setFamily("MS Shell Dlg 2")
        font.setPointSize(10)
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(9)
        self.label_21.setFont(font)
        self.label_21.setStyleSheet("font: 75 10pt \"MS Shell Dlg 2\";")
        self.label_21.setAlignment(QtCore.Qt.AlignCenter)
        self.label_21.setObjectName("label_21")
        self.AltitudeLCD_3 = QtWidgets.QLCDNumber(self.groupBox_4)
        self.AltitudeLCD_3.setGeometry(QtCore.QRect(60, 69, 181, 81))
        self.AltitudeLCD_3.setMinimumSize(QtCore.QSize(111, 31))
        self.AltitudeLCD_3.setAutoFillBackground(False)
        self.AltitudeLCD_3.setSmallDecimalPoint(False)
        self.AltitudeLCD_3.setDigitCount(7)
        self.AltitudeLCD_3.setMode(QtWidgets.QLCDNumber.Dec)
        self.AltitudeLCD_3.setSegmentStyle(QtWidgets.QLCDNumber.Filled)
        self.AltitudeLCD_3.setObjectName("AltitudeLCD_3")
        self.lcdNumber_13 = QtWidgets.QLCDNumber(self.groupBox_4)
        self.lcdNumber_13.setGeometry(QtCore.QRect(490, 69, 191, 81))
        self.lcdNumber_13.setSmallDecimalPoint(False)
        self.lcdNumber_13.setDigitCount(7)
        self.lcdNumber_13.setObjectName("lcdNumber_13")
        self.label_13 = QtWidgets.QLabel(self.groupBox_4)
        self.label_13.setGeometry(QtCore.QRect(270, 29, 191, 41))
        self.label_13.setStyleSheet("font: 87 11pt \"Segoe UI Black\";\n"
"font: 11pt \"MS Shell Dlg 2\";")
        self.label_13.setAlignment(QtCore.Qt.AlignCenter)
        self.label_13.setObjectName("label_13")
        self.label_22 = QtWidgets.QLabel(self.groupBox_4)
        self.label_22.setGeometry(QtCore.QRect(500, 150, 161, 21))
        font = QtGui.QFont()
        font.setFamily("MS Shell Dlg 2")
        font.setPointSize(10)
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(9)
        self.label_22.setFont(font)
        self.label_22.setStyleSheet("font: 75 10pt \"MS Shell Dlg 2\";")
        self.label_22.setAlignment(QtCore.Qt.AlignCenter)
        self.label_22.setObjectName("label_22")
        self.groupBox_5 = QtWidgets.QGroupBox(self.tab)
        self.groupBox_5.setGeometry(QtCore.QRect(1560, 30, 721, 181))
        self.groupBox_5.setStyleSheet("background-color: rgb(227, 227, 227);\n"
"background-color: rgb(241, 241, 241);\n"
"font: 87 9pt \"Segoe UI Black\";")
        self.groupBox_5.setObjectName("groupBox_5")
        self.label_23 = QtWidgets.QLabel(self.groupBox_5)
        self.label_23.setGeometry(QtCore.QRect(490, 29, 191, 41))
        self.label_23.setStyleSheet("font: 87 11pt \"Segoe UI Black\";\n"
"font: 11pt \"MS Shell Dlg 2\";")
        self.label_23.setAlignment(QtCore.Qt.AlignCenter)
        self.label_23.setObjectName("label_23")
        self.label_32 = QtWidgets.QLabel(self.groupBox_5)
        self.label_32.setGeometry(QtCore.QRect(70, 149, 161, 31))
        font = QtGui.QFont()
        font.setFamily("MS Shell Dlg 2")
        font.setPointSize(10)
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(9)
        self.label_32.setFont(font)
        self.label_32.setStyleSheet("font: 75 10pt \"MS Shell Dlg 2\";")
        self.label_32.setAlignment(QtCore.Qt.AlignCenter)
        self.label_32.setObjectName("label_32")
        self.label_33 = QtWidgets.QLabel(self.groupBox_5)
        self.label_33.setGeometry(QtCore.QRect(60, 29, 191, 41))
        self.label_33.setStyleSheet("font: 87 11pt \"Segoe UI Black\";\n"
"font: 11pt \"MS Shell Dlg 2\";")
        self.label_33.setAlignment(QtCore.Qt.AlignCenter)
        self.label_33.setObjectName("label_33")
        self.TemperatureLCD_4 = QtWidgets.QLCDNumber(self.groupBox_5)
        self.TemperatureLCD_4.setGeometry(QtCore.QRect(270, 69, 191, 81))
        self.TemperatureLCD_4.setSmallDecimalPoint(False)
        self.TemperatureLCD_4.setDigitCount(7)
        self.TemperatureLCD_4.setObjectName("TemperatureLCD_4")
        self.label_34 = QtWidgets.QLabel(self.groupBox_5)
        self.label_34.setGeometry(QtCore.QRect(280, 150, 161, 21))
        font = QtGui.QFont()
        font.setFamily("MS Shell Dlg 2")
        font.setPointSize(10)
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(9)
        self.label_34.setFont(font)
        self.label_34.setStyleSheet("font: 75 10pt \"MS Shell Dlg 2\";")
        self.label_34.setAlignment(QtCore.Qt.AlignCenter)
        self.label_34.setObjectName("label_34")
        self.AltitudeLCD_4 = QtWidgets.QLCDNumber(self.groupBox_5)
        self.AltitudeLCD_4.setGeometry(QtCore.QRect(60, 69, 181, 81))
        self.AltitudeLCD_4.setMinimumSize(QtCore.QSize(111, 31))
        self.AltitudeLCD_4.setAutoFillBackground(False)
        self.AltitudeLCD_4.setSmallDecimalPoint(False)
        self.AltitudeLCD_4.setDigitCount(7)
        self.AltitudeLCD_4.setMode(QtWidgets.QLCDNumber.Dec)
        self.AltitudeLCD_4.setSegmentStyle(QtWidgets.QLCDNumber.Filled)
        self.AltitudeLCD_4.setObjectName("AltitudeLCD_4")
        self.lcdNumber_14 = QtWidgets.QLCDNumber(self.groupBox_5)
        self.lcdNumber_14.setGeometry(QtCore.QRect(490, 69, 191, 81))
        self.lcdNumber_14.setSmallDecimalPoint(False)
        self.lcdNumber_14.setDigitCount(7)
        self.lcdNumber_14.setObjectName("lcdNumber_14")
        self.label_35 = QtWidgets.QLabel(self.groupBox_5)
        self.label_35.setGeometry(QtCore.QRect(270, 29, 191, 41))
        self.label_35.setStyleSheet("font: 87 11pt \"Segoe UI Black\";\n"
"font: 11pt \"MS Shell Dlg 2\";")
        self.label_35.setAlignment(QtCore.Qt.AlignCenter)
        self.label_35.setObjectName("label_35")
        self.label_36 = QtWidgets.QLabel(self.groupBox_5)
        self.label_36.setGeometry(QtCore.QRect(500, 150, 161, 21))
        font = QtGui.QFont()
        font.setFamily("MS Shell Dlg 2")
        font.setPointSize(10)
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(9)
        self.label_36.setFont(font)
        self.label_36.setStyleSheet("font: 75 10pt \"MS Shell Dlg 2\";")
        self.label_36.setAlignment(QtCore.Qt.AlignCenter)
        self.label_36.setObjectName("label_36")
        self.groupBox_6 = QtWidgets.QGroupBox(self.tab)
        self.groupBox_6.setGeometry(QtCore.QRect(1560, 450, 721, 181))
        self.groupBox_6.setStyleSheet("background-color: rgb(227, 227, 227);\n"
"background-color: rgb(241, 241, 241);\n"
"font: 87 9pt \"Segoe UI Black\";")
        self.groupBox_6.setObjectName("groupBox_6")
        self.label_37 = QtWidgets.QLabel(self.groupBox_6)
        self.label_37.setGeometry(QtCore.QRect(490, 29, 191, 41))
        self.label_37.setStyleSheet("font: 87 11pt \"Segoe UI Black\";\n"
"font: 11pt \"MS Shell Dlg 2\";")
        self.label_37.setAlignment(QtCore.Qt.AlignCenter)
        self.label_37.setObjectName("label_37")
        self.label_38 = QtWidgets.QLabel(self.groupBox_6)
        self.label_38.setGeometry(QtCore.QRect(70, 149, 161, 31))
        font = QtGui.QFont()
        font.setFamily("MS Shell Dlg 2")
        font.setPointSize(10)
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(9)
        self.label_38.setFont(font)
        self.label_38.setStyleSheet("font: 75 10pt \"MS Shell Dlg 2\";")
        self.label_38.setAlignment(QtCore.Qt.AlignCenter)
        self.label_38.setObjectName("label_38")
        self.label_39 = QtWidgets.QLabel(self.groupBox_6)
        self.label_39.setGeometry(QtCore.QRect(60, 29, 191, 41))
        self.label_39.setStyleSheet("font: 87 11pt \"Segoe UI Black\";\n"
"font: 11pt \"MS Shell Dlg 2\";")
        self.label_39.setAlignment(QtCore.Qt.AlignCenter)
        self.label_39.setObjectName("label_39")
        self.TemperatureLCD_5 = QtWidgets.QLCDNumber(self.groupBox_6)
        self.TemperatureLCD_5.setGeometry(QtCore.QRect(270, 69, 191, 81))
        self.TemperatureLCD_5.setSmallDecimalPoint(False)
        self.TemperatureLCD_5.setDigitCount(7)
        self.TemperatureLCD_5.setObjectName("TemperatureLCD_5")
        self.label_40 = QtWidgets.QLabel(self.groupBox_6)
        self.label_40.setGeometry(QtCore.QRect(280, 150, 161, 21))
        font = QtGui.QFont()
        font.setFamily("MS Shell Dlg 2")
        font.setPointSize(10)
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(9)
        self.label_40.setFont(font)
        self.label_40.setStyleSheet("font: 75 10pt \"MS Shell Dlg 2\";")
        self.label_40.setAlignment(QtCore.Qt.AlignCenter)
        self.label_40.setObjectName("label_40")
        self.AltitudeLCD_5 = QtWidgets.QLCDNumber(self.groupBox_6)
        self.AltitudeLCD_5.setGeometry(QtCore.QRect(60, 69, 181, 81))
        self.AltitudeLCD_5.setMinimumSize(QtCore.QSize(111, 31))
        self.AltitudeLCD_5.setAutoFillBackground(False)
        self.AltitudeLCD_5.setSmallDecimalPoint(False)
        self.AltitudeLCD_5.setDigitCount(7)
        self.AltitudeLCD_5.setMode(QtWidgets.QLCDNumber.Dec)
        self.AltitudeLCD_5.setSegmentStyle(QtWidgets.QLCDNumber.Filled)
        self.AltitudeLCD_5.setObjectName("AltitudeLCD_5")
        self.lcdNumber_15 = QtWidgets.QLCDNumber(self.groupBox_6)
        self.lcdNumber_15.setGeometry(QtCore.QRect(490, 69, 191, 81))
        self.lcdNumber_15.setSmallDecimalPoint(False)
        self.lcdNumber_15.setDigitCount(7)
        self.lcdNumber_15.setObjectName("lcdNumber_15")
        self.label_41 = QtWidgets.QLabel(self.groupBox_6)
        self.label_41.setGeometry(QtCore.QRect(270, 29, 191, 41))
        self.label_41.setStyleSheet("font: 87 11pt \"Segoe UI Black\";\n"
"font: 11pt \"MS Shell Dlg 2\";")
        self.label_41.setAlignment(QtCore.Qt.AlignCenter)
        self.label_41.setObjectName("label_41")
        self.label_42 = QtWidgets.QLabel(self.groupBox_6)
        self.label_42.setGeometry(QtCore.QRect(500, 150, 161, 21))
        font = QtGui.QFont()
        font.setFamily("MS Shell Dlg 2")
        font.setPointSize(10)
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(9)
        self.label_42.setFont(font)
        self.label_42.setStyleSheet("font: 75 10pt \"MS Shell Dlg 2\";")
        self.label_42.setAlignment(QtCore.Qt.AlignCenter)
        self.label_42.setObjectName("label_42")
        self.groupBox_7 = QtWidgets.QGroupBox(self.tab)
        self.groupBox_7.setGeometry(QtCore.QRect(50, 240, 471, 181))
        self.groupBox_7.setStyleSheet("background-color: rgb(227, 227, 227);\n"
"background-color: rgb(241, 241, 241);\n"
"font: 87 9pt \"Segoe UI Black\";")
        self.groupBox_7.setObjectName("groupBox_7")
        self.label_44 = QtWidgets.QLabel(self.groupBox_7)
        self.label_44.setGeometry(QtCore.QRect(70, 149, 161, 31))
        font = QtGui.QFont()
        font.setFamily("MS Shell Dlg 2")
        font.setPointSize(10)
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(9)
        self.label_44.setFont(font)
        self.label_44.setStyleSheet("font: 75 10pt \"MS Shell Dlg 2\";")
        self.label_44.setAlignment(QtCore.Qt.AlignCenter)
        self.label_44.setObjectName("label_44")
        self.label_45 = QtWidgets.QLabel(self.groupBox_7)
        self.label_45.setGeometry(QtCore.QRect(60, 29, 191, 41))
        self.label_45.setStyleSheet("font: 87 11pt \"Segoe UI Black\";\n"
"font: 11pt \"MS Shell Dlg 2\";")
        self.label_45.setAlignment(QtCore.Qt.AlignCenter)
        self.label_45.setObjectName("label_45")
        self.TemperatureLCD_6 = QtWidgets.QLCDNumber(self.groupBox_7)
        self.TemperatureLCD_6.setGeometry(QtCore.QRect(270, 69, 191, 81))
        self.TemperatureLCD_6.setSmallDecimalPoint(False)
        self.TemperatureLCD_6.setDigitCount(7)
        self.TemperatureLCD_6.setObjectName("TemperatureLCD_6")
        self.AltitudeLCD_6 = QtWidgets.QLCDNumber(self.groupBox_7)
        self.AltitudeLCD_6.setGeometry(QtCore.QRect(60, 69, 181, 81))
        self.AltitudeLCD_6.setMinimumSize(QtCore.QSize(111, 31))
        self.AltitudeLCD_6.setAutoFillBackground(False)
        self.AltitudeLCD_6.setSmallDecimalPoint(False)
        self.AltitudeLCD_6.setDigitCount(7)
        self.AltitudeLCD_6.setMode(QtWidgets.QLCDNumber.Dec)
        self.AltitudeLCD_6.setSegmentStyle(QtWidgets.QLCDNumber.Filled)
        self.AltitudeLCD_6.setObjectName("AltitudeLCD_6")
        self.label_47 = QtWidgets.QLabel(self.groupBox_7)
        self.label_47.setGeometry(QtCore.QRect(270, 29, 191, 41))
        self.label_47.setStyleSheet("font: 87 11pt \"Segoe UI Black\";\n"
"font: 11pt \"MS Shell Dlg 2\";")
        self.label_47.setAlignment(QtCore.Qt.AlignCenter)
        self.label_47.setObjectName("label_47")
        self.groupBox_8 = QtWidgets.QGroupBox(self.tab)
        self.groupBox_8.setGeometry(QtCore.QRect(50, 660, 931, 181))
        self.groupBox_8.setStyleSheet("background-color: rgb(227, 227, 227);\n"
"background-color: rgb(241, 241, 241);\n"
"font: 87 9pt \"Segoe UI Black\";")
        self.groupBox_8.setObjectName("groupBox_8")
        self.label_46 = QtWidgets.QLabel(self.groupBox_8)
        self.label_46.setGeometry(QtCore.QRect(490, 29, 191, 41))
        self.label_46.setStyleSheet("font: 87 11pt \"Segoe UI Black\";\n"
"font: 11pt \"MS Shell Dlg 2\";")
        self.label_46.setAlignment(QtCore.Qt.AlignCenter)
        self.label_46.setObjectName("label_46")
        self.label_49 = QtWidgets.QLabel(self.groupBox_8)
        self.label_49.setGeometry(QtCore.QRect(60, 29, 191, 41))
        self.label_49.setStyleSheet("font: 87 11pt \"Segoe UI Black\";\n"
"font: 11pt \"MS Shell Dlg 2\";")
        self.label_49.setAlignment(QtCore.Qt.AlignCenter)
        self.label_49.setObjectName("label_49")
        self.TemperatureLCD_7 = QtWidgets.QLCDNumber(self.groupBox_8)
        self.TemperatureLCD_7.setGeometry(QtCore.QRect(270, 69, 191, 81))
        self.TemperatureLCD_7.setSmallDecimalPoint(False)
        self.TemperatureLCD_7.setDigitCount(7)
        self.TemperatureLCD_7.setObjectName("TemperatureLCD_7")
        self.AltitudeLCD_7 = QtWidgets.QLCDNumber(self.groupBox_8)
        self.AltitudeLCD_7.setGeometry(QtCore.QRect(60, 69, 181, 81))
        self.AltitudeLCD_7.setMinimumSize(QtCore.QSize(111, 31))
        self.AltitudeLCD_7.setAutoFillBackground(False)
        self.AltitudeLCD_7.setSmallDecimalPoint(False)
        self.AltitudeLCD_7.setDigitCount(7)
        self.AltitudeLCD_7.setMode(QtWidgets.QLCDNumber.Dec)
        self.AltitudeLCD_7.setSegmentStyle(QtWidgets.QLCDNumber.Filled)
        self.AltitudeLCD_7.setObjectName("AltitudeLCD_7")
        self.lcdNumber_16 = QtWidgets.QLCDNumber(self.groupBox_8)
        self.lcdNumber_16.setGeometry(QtCore.QRect(490, 69, 191, 81))
        self.lcdNumber_16.setSmallDecimalPoint(False)
        self.lcdNumber_16.setDigitCount(7)
        self.lcdNumber_16.setObjectName("lcdNumber_16")
        self.label_51 = QtWidgets.QLabel(self.groupBox_8)
        self.label_51.setGeometry(QtCore.QRect(270, 29, 191, 41))
        self.label_51.setStyleSheet("font: 87 11pt \"Segoe UI Black\";\n"
"font: 11pt \"MS Shell Dlg 2\";")
        self.label_51.setAlignment(QtCore.Qt.AlignCenter)
        self.label_51.setObjectName("label_51")
        self.lcdNumber_17 = QtWidgets.QLCDNumber(self.groupBox_8)
        self.lcdNumber_17.setGeometry(QtCore.QRect(710, 70, 191, 81))
        self.lcdNumber_17.setSmallDecimalPoint(False)
        self.lcdNumber_17.setDigitCount(7)
        self.lcdNumber_17.setObjectName("lcdNumber_17")
        self.label_54 = QtWidgets.QLabel(self.groupBox_8)
        self.label_54.setGeometry(QtCore.QRect(710, 30, 191, 41))
        self.label_54.setStyleSheet("font: 87 11pt \"Segoe UI Black\";\n"
"font: 11pt \"MS Shell Dlg 2\";")
        self.label_54.setAlignment(QtCore.Qt.AlignCenter)
        self.label_54.setObjectName("label_54")
        self.groupBox_9 = QtWidgets.QGroupBox(self.tab)
        self.groupBox_9.setGeometry(QtCore.QRect(50, 450, 721, 181))
        self.groupBox_9.setStyleSheet("background-color: rgb(227, 227, 227);\n"
"background-color: rgb(241, 241, 241);\n"
"font: 87 9pt \"Segoe UI Black\";")
        self.groupBox_9.setObjectName("groupBox_9")
        self.label_24 = QtWidgets.QLabel(self.groupBox_9)
        self.label_24.setGeometry(QtCore.QRect(490, 29, 191, 41))
        self.label_24.setStyleSheet("font: 87 11pt \"Segoe UI Black\";\n"
"font: 11pt \"MS Shell Dlg 2\";")
        self.label_24.setAlignment(QtCore.Qt.AlignCenter)
        self.label_24.setObjectName("label_24")
        self.label_26 = QtWidgets.QLabel(self.groupBox_9)
        self.label_26.setGeometry(QtCore.QRect(60, 29, 191, 41))
        self.label_26.setStyleSheet("font: 87 11pt \"Segoe UI Black\";\n"
"font: 11pt \"MS Shell Dlg 2\";")
        self.label_26.setAlignment(QtCore.Qt.AlignCenter)
        self.label_26.setObjectName("label_26")
        self.TemperatureLCD_8 = QtWidgets.QLCDNumber(self.groupBox_9)
        self.TemperatureLCD_8.setGeometry(QtCore.QRect(270, 69, 191, 81))
        self.TemperatureLCD_8.setSmallDecimalPoint(False)
        self.TemperatureLCD_8.setDigitCount(7)
        self.TemperatureLCD_8.setObjectName("TemperatureLCD_8")
        self.AltitudeLCD_8 = QtWidgets.QLCDNumber(self.groupBox_9)
        self.AltitudeLCD_8.setGeometry(QtCore.QRect(60, 69, 181, 81))
        self.AltitudeLCD_8.setMinimumSize(QtCore.QSize(111, 31))
        self.AltitudeLCD_8.setAutoFillBackground(False)
        self.AltitudeLCD_8.setSmallDecimalPoint(False)
        self.AltitudeLCD_8.setDigitCount(7)
        self.AltitudeLCD_8.setMode(QtWidgets.QLCDNumber.Dec)
        self.AltitudeLCD_8.setSegmentStyle(QtWidgets.QLCDNumber.Filled)
        self.AltitudeLCD_8.setObjectName("AltitudeLCD_8")
        self.lcdNumber_18 = QtWidgets.QLCDNumber(self.groupBox_9)
        self.lcdNumber_18.setGeometry(QtCore.QRect(490, 69, 191, 81))
        self.lcdNumber_18.setSmallDecimalPoint(False)
        self.lcdNumber_18.setDigitCount(7)
        self.lcdNumber_18.setObjectName("lcdNumber_18")
        self.label_28 = QtWidgets.QLabel(self.groupBox_9)
        self.label_28.setGeometry(QtCore.QRect(270, 29, 191, 41))
        self.label_28.setStyleSheet("font: 87 11pt \"Segoe UI Black\";\n"
"font: 11pt \"MS Shell Dlg 2\";")
        self.label_28.setAlignment(QtCore.Qt.AlignCenter)
        self.label_28.setObjectName("label_28")
        self.groupBox_10 = QtWidgets.QGroupBox(self.tab)
        self.groupBox_10.setGeometry(QtCore.QRect(800, 450, 721, 181))
        self.groupBox_10.setStyleSheet("background-color: rgb(227, 227, 227);\n"
"background-color: rgb(241, 241, 241);\n"
"font: 87 9pt \"Segoe UI Black\";")
        self.groupBox_10.setObjectName("groupBox_10")
        self.label_25 = QtWidgets.QLabel(self.groupBox_10)
        self.label_25.setGeometry(QtCore.QRect(490, 29, 191, 41))
        self.label_25.setStyleSheet("font: 87 11pt \"Segoe UI Black\";\n"
"font: 11pt \"MS Shell Dlg 2\";")
        self.label_25.setAlignment(QtCore.Qt.AlignCenter)
        self.label_25.setObjectName("label_25")
        self.label_27 = QtWidgets.QLabel(self.groupBox_10)
        self.label_27.setGeometry(QtCore.QRect(60, 29, 191, 41))
        self.label_27.setStyleSheet("font: 87 11pt \"Segoe UI Black\";\n"
"font: 11pt \"MS Shell Dlg 2\";")
        self.label_27.setAlignment(QtCore.Qt.AlignCenter)
        self.label_27.setObjectName("label_27")
        self.TemperatureLCD_9 = QtWidgets.QLCDNumber(self.groupBox_10)
        self.TemperatureLCD_9.setGeometry(QtCore.QRect(270, 69, 191, 81))
        self.TemperatureLCD_9.setSmallDecimalPoint(False)
        self.TemperatureLCD_9.setDigitCount(7)
        self.TemperatureLCD_9.setObjectName("TemperatureLCD_9")
        self.AltitudeLCD_9 = QtWidgets.QLCDNumber(self.groupBox_10)
        self.AltitudeLCD_9.setGeometry(QtCore.QRect(60, 69, 181, 81))
        self.AltitudeLCD_9.setMinimumSize(QtCore.QSize(111, 31))
        self.AltitudeLCD_9.setAutoFillBackground(False)
        self.AltitudeLCD_9.setSmallDecimalPoint(False)
        self.AltitudeLCD_9.setDigitCount(7)
        self.AltitudeLCD_9.setMode(QtWidgets.QLCDNumber.Dec)
        self.AltitudeLCD_9.setSegmentStyle(QtWidgets.QLCDNumber.Filled)
        self.AltitudeLCD_9.setObjectName("AltitudeLCD_9")
        self.lcdNumber_19 = QtWidgets.QLCDNumber(self.groupBox_10)
        self.lcdNumber_19.setGeometry(QtCore.QRect(490, 69, 191, 81))
        self.lcdNumber_19.setSmallDecimalPoint(False)
        self.lcdNumber_19.setDigitCount(7)
        self.lcdNumber_19.setObjectName("lcdNumber_19")
        self.label_29 = QtWidgets.QLabel(self.groupBox_10)
        self.label_29.setGeometry(QtCore.QRect(270, 29, 191, 41))
        self.label_29.setStyleSheet("font: 87 11pt \"Segoe UI Black\";\n"
"font: 11pt \"MS Shell Dlg 2\";")
        self.label_29.setAlignment(QtCore.Qt.AlignCenter)
        self.label_29.setObjectName("label_29")
        self.groupBox_11 = QtWidgets.QGroupBox(self.tab)
        self.groupBox_11.setGeometry(QtCore.QRect(1140, 660, 1141, 181))
        self.groupBox_11.setStyleSheet("background-color: rgb(227, 227, 227);\n"
"background-color: rgb(241, 241, 241);\n"
"font: 87 9pt \"Segoe UI Black\";")
        self.groupBox_11.setObjectName("groupBox_11")
        self.label_55 = QtWidgets.QLabel(self.groupBox_11)
        self.label_55.setGeometry(QtCore.QRect(490, 29, 191, 41))
        self.label_55.setStyleSheet("font: 87 11pt \"Segoe UI Black\";\n"
"font: 11pt \"MS Shell Dlg 2\";")
        self.label_55.setAlignment(QtCore.Qt.AlignCenter)
        self.label_55.setObjectName("label_55")
        self.label_57 = QtWidgets.QLabel(self.groupBox_11)
        self.label_57.setGeometry(QtCore.QRect(60, 29, 191, 41))
        self.label_57.setStyleSheet("font: 87 11pt \"Segoe UI Black\";\n"
"font: 11pt \"MS Shell Dlg 2\";")
        self.label_57.setAlignment(QtCore.Qt.AlignCenter)
        self.label_57.setObjectName("label_57")
        self.TemperatureLCD_10 = QtWidgets.QLCDNumber(self.groupBox_11)
        self.TemperatureLCD_10.setGeometry(QtCore.QRect(270, 69, 191, 81))
        self.TemperatureLCD_10.setSmallDecimalPoint(False)
        self.TemperatureLCD_10.setDigitCount(7)
        self.TemperatureLCD_10.setObjectName("TemperatureLCD_10")
        self.AltitudeLCD_10 = QtWidgets.QLCDNumber(self.groupBox_11)
        self.AltitudeLCD_10.setGeometry(QtCore.QRect(60, 69, 181, 81))
        self.AltitudeLCD_10.setMinimumSize(QtCore.QSize(111, 31))
        self.AltitudeLCD_10.setAutoFillBackground(False)
        self.AltitudeLCD_10.setSmallDecimalPoint(False)
        self.AltitudeLCD_10.setDigitCount(7)
        self.AltitudeLCD_10.setMode(QtWidgets.QLCDNumber.Dec)
        self.AltitudeLCD_10.setSegmentStyle(QtWidgets.QLCDNumber.Filled)
        self.AltitudeLCD_10.setObjectName("AltitudeLCD_10")
        self.lcdNumber_20 = QtWidgets.QLCDNumber(self.groupBox_11)
        self.lcdNumber_20.setGeometry(QtCore.QRect(490, 69, 191, 81))
        self.lcdNumber_20.setSmallDecimalPoint(False)
        self.lcdNumber_20.setDigitCount(7)
        self.lcdNumber_20.setObjectName("lcdNumber_20")
        self.label_59 = QtWidgets.QLabel(self.groupBox_11)
        self.label_59.setGeometry(QtCore.QRect(270, 29, 191, 41))
        self.label_59.setStyleSheet("font: 87 11pt \"Segoe UI Black\";\n"
"font: 11pt \"MS Shell Dlg 2\";")
        self.label_59.setAlignment(QtCore.Qt.AlignCenter)
        self.label_59.setObjectName("label_59")
        self.lcdNumber_21 = QtWidgets.QLCDNumber(self.groupBox_11)
        self.lcdNumber_21.setGeometry(QtCore.QRect(710, 70, 191, 81))
        self.lcdNumber_21.setSmallDecimalPoint(False)
        self.lcdNumber_21.setDigitCount(7)
        self.lcdNumber_21.setObjectName("lcdNumber_21")
        self.label_62 = QtWidgets.QLabel(self.groupBox_11)
        self.label_62.setGeometry(QtCore.QRect(710, 30, 191, 41))
        self.label_62.setStyleSheet("font: 87 11pt \"Segoe UI Black\";\n"
"font: 11pt \"MS Shell Dlg 2\";")
        self.label_62.setAlignment(QtCore.Qt.AlignCenter)
        self.label_62.setObjectName("label_62")
        self.lcdNumber_22 = QtWidgets.QLCDNumber(self.groupBox_11)
        self.lcdNumber_22.setGeometry(QtCore.QRect(930, 70, 191, 81))
        self.lcdNumber_22.setSmallDecimalPoint(False)
        self.lcdNumber_22.setDigitCount(7)
        self.lcdNumber_22.setObjectName("lcdNumber_22")
        self.label_64 = QtWidgets.QLabel(self.groupBox_11)
        self.label_64.setGeometry(QtCore.QRect(930, 30, 191, 41))
        self.label_64.setStyleSheet("font: 87 11pt \"Segoe UI Black\";\n"
"font: 11pt \"MS Shell Dlg 2\";")
        self.label_64.setAlignment(QtCore.Qt.AlignCenter)
        self.label_64.setObjectName("label_64")
        self.groupBox_3 = QtWidgets.QGroupBox(self.tab)
        self.groupBox_3.setGeometry(QtCore.QRect(50, 30, 721, 181))
        self.groupBox_3.setStyleSheet("background-color: rgb(227, 227, 227);\n"
"selection-color: rgb(0, 170, 0);\n"
"background-color: rgb(241, 241, 241);\n"
"font: 87 9pt \"Segoe UI Black\";")
        self.groupBox_3.setObjectName("groupBox_3")
        self.label_8 = QtWidgets.QLabel(self.groupBox_3)
        self.label_8.setGeometry(QtCore.QRect(490, 29, 191, 41))
        self.label_8.setStyleSheet("font: 87 11pt \"Segoe UI Black\";\n"
"font: 11pt \"MS Shell Dlg 2\";")
        self.label_8.setAlignment(QtCore.Qt.AlignCenter)
        self.label_8.setObjectName("label_8")
        self.label_17 = QtWidgets.QLabel(self.groupBox_3)
        self.label_17.setGeometry(QtCore.QRect(70, 149, 161, 31))
        font = QtGui.QFont()
        font.setFamily("MS Shell Dlg 2")
        font.setPointSize(10)
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(9)
        self.label_17.setFont(font)
        self.label_17.setStyleSheet("font: 75 10pt \"MS Shell Dlg 2\";")
        self.label_17.setAlignment(QtCore.Qt.AlignCenter)
        self.label_17.setObjectName("label_17")
        self.label_9 = QtWidgets.QLabel(self.groupBox_3)
        self.label_9.setGeometry(QtCore.QRect(60, 29, 191, 41))
        self.label_9.setStyleSheet("font: 87 11pt \"Segoe UI Black\";\n"
"font: 11pt \"MS Shell Dlg 2\";")
        self.label_9.setAlignment(QtCore.Qt.AlignCenter)
        self.label_9.setObjectName("label_9")
        self.TemperatureLCD_2 = QtWidgets.QLCDNumber(self.groupBox_3)
        self.TemperatureLCD_2.setGeometry(QtCore.QRect(270, 69, 191, 81))
        self.TemperatureLCD_2.setSmallDecimalPoint(False)
        self.TemperatureLCD_2.setDigitCount(7)
        self.TemperatureLCD_2.setObjectName("TemperatureLCD_2")
        self.label_18 = QtWidgets.QLabel(self.groupBox_3)
        self.label_18.setGeometry(QtCore.QRect(280, 150, 161, 21))
        font = QtGui.QFont()
        font.setFamily("MS Shell Dlg 2")
        font.setPointSize(10)
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(9)
        self.label_18.setFont(font)
        self.label_18.setStyleSheet("font: 75 10pt \"MS Shell Dlg 2\";")
        self.label_18.setAlignment(QtCore.Qt.AlignCenter)
        self.label_18.setObjectName("label_18")
        self.AltitudeLCD_2 = QtWidgets.QLCDNumber(self.groupBox_3)
        self.AltitudeLCD_2.setGeometry(QtCore.QRect(60, 69, 181, 81))
        self.AltitudeLCD_2.setMinimumSize(QtCore.QSize(111, 31))
        self.AltitudeLCD_2.setAutoFillBackground(False)
        self.AltitudeLCD_2.setSmallDecimalPoint(False)
        self.AltitudeLCD_2.setDigitCount(7)
        self.AltitudeLCD_2.setMode(QtWidgets.QLCDNumber.Dec)
        self.AltitudeLCD_2.setSegmentStyle(QtWidgets.QLCDNumber.Filled)
        self.AltitudeLCD_2.setObjectName("AltitudeLCD_2")
        self.lcdNumber_12 = QtWidgets.QLCDNumber(self.groupBox_3)
        self.lcdNumber_12.setGeometry(QtCore.QRect(490, 69, 191, 81))
        self.lcdNumber_12.setSmallDecimalPoint(False)
        self.lcdNumber_12.setDigitCount(7)
        self.lcdNumber_12.setObjectName("lcdNumber_12")
        self.label_3 = QtWidgets.QLabel(self.groupBox_3)
        self.label_3.setGeometry(QtCore.QRect(270, 29, 191, 41))
        self.label_3.setStyleSheet("font: 87 11pt \"Segoe UI Black\";\n"
"font: 11pt \"MS Shell Dlg 2\";")
        self.label_3.setAlignment(QtCore.Qt.AlignCenter)
        self.label_3.setObjectName("label_3")
        self.label_19 = QtWidgets.QLabel(self.groupBox_3)
        self.label_19.setGeometry(QtCore.QRect(500, 150, 161, 21))
        font = QtGui.QFont()
        font.setFamily("MS Shell Dlg 2")
        font.setPointSize(10)
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(9)
        self.label_19.setFont(font)
        self.label_19.setStyleSheet("font: 75 10pt \"MS Shell Dlg 2\";")
        self.label_19.setAlignment(QtCore.Qt.AlignCenter)
        self.label_19.setObjectName("label_19")
        self.groupBox = QtWidgets.QGroupBox(self.tab)
        self.groupBox.setGeometry(QtCore.QRect(1560, 240, 721, 181))
        self.groupBox.setStyleSheet("background-color: rgb(227, 227, 227);\n"
"background-color: rgb(241, 241, 241);\n"
"font: 87 9pt \"Segoe UI Black\";")
        self.groupBox.setObjectName("groupBox")
        self.label_5 = QtWidgets.QLabel(self.groupBox)
        self.label_5.setGeometry(QtCore.QRect(490, 29, 191, 41))
        self.label_5.setStyleSheet("font: 87 11pt \"Segoe UI Black\";\n"
"font: 11pt \"MS Shell Dlg 2\";")
        self.label_5.setAlignment(QtCore.Qt.AlignCenter)
        self.label_5.setObjectName("label_5")
        self.label_15 = QtWidgets.QLabel(self.groupBox)
        self.label_15.setGeometry(QtCore.QRect(70, 149, 161, 31))
        font = QtGui.QFont()
        font.setFamily("MS Shell Dlg 2")
        font.setPointSize(10)
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(9)
        self.label_15.setFont(font)
        self.label_15.setStyleSheet("font: 75 10pt \"MS Shell Dlg 2\";")
        self.label_15.setAlignment(QtCore.Qt.AlignCenter)
        self.label_15.setObjectName("label_15")
        self.label_4 = QtWidgets.QLabel(self.groupBox)
        self.label_4.setGeometry(QtCore.QRect(60, 29, 191, 41))
        self.label_4.setStyleSheet("font: 87 11pt \"Segoe UI Black\";\n"
"font: 11pt \"MS Shell Dlg 2\";")
        self.label_4.setAlignment(QtCore.Qt.AlignCenter)
        self.label_4.setObjectName("label_4")
        self.TemperatureLCD = QtWidgets.QLCDNumber(self.groupBox)
        self.TemperatureLCD.setGeometry(QtCore.QRect(270, 69, 191, 81))
        self.TemperatureLCD.setSmallDecimalPoint(False)
        self.TemperatureLCD.setDigitCount(7)
        self.TemperatureLCD.setObjectName("TemperatureLCD")
        self.label_14 = QtWidgets.QLabel(self.groupBox)
        self.label_14.setGeometry(QtCore.QRect(280, 150, 161, 21))
        font = QtGui.QFont()
        font.setFamily("MS Shell Dlg 2")
        font.setPointSize(10)
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(9)
        self.label_14.setFont(font)
        self.label_14.setStyleSheet("font: 75 10pt \"MS Shell Dlg 2\";")
        self.label_14.setAlignment(QtCore.Qt.AlignCenter)
        self.label_14.setObjectName("label_14")
        self.AltitudeLCD = QtWidgets.QLCDNumber(self.groupBox)
        self.AltitudeLCD.setGeometry(QtCore.QRect(60, 69, 181, 81))
        self.AltitudeLCD.setMinimumSize(QtCore.QSize(111, 31))
        self.AltitudeLCD.setAutoFillBackground(False)
        self.AltitudeLCD.setSmallDecimalPoint(False)
        self.AltitudeLCD.setDigitCount(7)
        self.AltitudeLCD.setMode(QtWidgets.QLCDNumber.Dec)
        self.AltitudeLCD.setSegmentStyle(QtWidgets.QLCDNumber.Filled)
        self.AltitudeLCD.setObjectName("AltitudeLCD")
        self.PressureLCD = QtWidgets.QLCDNumber(self.groupBox)
        self.PressureLCD.setGeometry(QtCore.QRect(490, 69, 191, 81))
        self.PressureLCD.setSmallDecimalPoint(False)
        self.PressureLCD.setDigitCount(7)
        self.PressureLCD.setObjectName("PressureLCD")
        self.label_2 = QtWidgets.QLabel(self.groupBox)
        self.label_2.setGeometry(QtCore.QRect(270, 29, 191, 41))
        self.label_2.setStyleSheet("font: 87 11pt \"Segoe UI Black\";\n"
"font: 11pt \"MS Shell Dlg 2\";")
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_2.setObjectName("label_2")
        self.label_16 = QtWidgets.QLabel(self.groupBox)
        self.label_16.setGeometry(QtCore.QRect(500, 150, 161, 21))
        font = QtGui.QFont()
        font.setFamily("MS Shell Dlg 2")
        font.setPointSize(10)
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(9)
        self.label_16.setFont(font)
        self.label_16.setStyleSheet("font: 75 10pt \"MS Shell Dlg 2\";")
        self.label_16.setAlignment(QtCore.Qt.AlignCenter)
        self.label_16.setObjectName("label_16")
        self.tabWidget.addTab(self.tab, "")
        self.gridLayout.addWidget(self.tabWidget, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 2336, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

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