import sys
import time
import serial
import math

EARTH_RADIUS = 6371000  # meters, used for distance calculations for GPS Graph
PORT = "COM3"  # Replace with your serial port
BAUD_RATE = 9600  # Replace with your baud rate (to be improved later)



class Sensor_reader:


    def __init__(self):

        # Data storage
        self.altitude_data = []
        self.alt_time_data = []
        self.temp_data = []
        self.temp_time_data = []
        self.x_data = []
        self.y_data = []
        
        self.origin = None
        self.time_x = time.perf_counter()

        
        self._setup_serial()  # Set up the serial connection

    def lat_lon_to_xy(self, lat, lon, lat_ref, lon_ref):
        dlat = math.radians(lat - lat_ref)
        dlon = math.radians(lon - lon_ref)
        x = EARTH_RADIUS * dlon * math.cos(math.radians(lat_ref)) # East
        y = EARTH_RADIUS * dlat # North
        return x, y
    

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
    

    def _tick(self):
        line = self.ser.readline().decode("utf-8").strip()  # Read a line from the serial port
        if not line:
            return  # If no data is read, exit the method
        
        # Parse the serial data into a dictionary
        data = self.parse_serial_data(line) 



        if "ALT" in data:
            # Get the altitude value
            altitude = data["ALT"]  
            # Calculate elapsed time since start
            alt_time_sec = time.perf_counter() - self.time_x  

            # Store
            self.alt_time_data.append(alt_time_sec)  # Append the elapsed time to the time data list
            self.altitude_data.append(altitude)  # Append the altitude to the altitude data list



        if "TEMP" in data:
            bmp_temp = float(data["TEMP"])
            temp_time_sec = time.perf_counter() - self.time_x  
            self.temp_time_data.append(temp_time_sec)  # Append the elapsed time to the time data list
            self.temp_data.append(bmp_temp)  # Append the temperature to the temperature data list

        if "LAT" in data and "LON" in data:
            lat = float(data["LAT"])
            lon = float(data["LON"])

            # Set origin automatically on first GPS data received
            if self.origin is None:
                self.origin = (lat, lon)

            lat_ref, lon_ref = self.origin
            x, y = self.lat_lon_to_xy(lat, lon, lat_ref, lon_ref)  # Convert GPS coordinates to XY

            self.x_data.append(x)  # Append the x-coordinate to the x data list
            self.y_data.append(y)  # Append the y-coordinate to the y data list


    def closeEvent(self, event):
        try:
            if self.ser and self.ser.is_open:
               self.ser.close()  # Close the serial connection when the window is closed
        except Exception:
            pass
        event.accept()  # Accept the close event