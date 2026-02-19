class Sensor_reader:


    def __init__(self):
        #fill this in later
        pass

    
    
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

        # Update LCD displays with parsed data 
        for key, lcd in self.lcd_map.items():
            if key in data:
                lcd.display(f"{float(data[key]):.2f}")  # Update LCD with values

        if "ALT" in data:
            # Get the altitude value
            altitude = data["ALT"]  
            # Calculate elapsed time since start
            alt_time_sec = time.perf_counter() - self.time_x  

            # Store and plot
            self.alt_time_data.append(alt_time_sec)  # Append the elapsed time to the time data list
            self.altitude_data.append(altitude)  # Append the altitude to the altitude data list
            self.curve.setData(self.alt_time_data, self.altitude_data)  # Update the plot with new data

        if "TEMP" in data:
            bmp_temp = float(data["TEMP"])
            temp_time_sec = time.perf_counter() - self.time_x  
            self.temp_time_data.append(temp_time_sec)  # Append the elapsed time to the time data list
            self.temp_data.append(bmp_temp)  # Append the temperature to the temperature data list
            self.temp_curve.setData(self.temp_time_data, self.temp_data)  # Update the temperature plot with new data