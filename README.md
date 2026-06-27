# Ground_Station_Software
Ground station software (Application Software and Control Software)
<br><br>

#  Coding standard AIAA:

  -  snake_case() function name
  -  Comment on code
  -  Write as few line as possible
  -  Avoid Deep nesting (avoid double loop function that increases time complexity)
  -  Avoid long lines
  -  Explicit naming (no i,j,etc... Ex: time)
  -  ReadMe for your code

# Features
```
-Control Software: (C++)
+ Define hardware GPIOs.
+ Read 104 bytes of data from the Lora.
+ Perform data check, initialization of serial protocol/SD card/Lora.
+ Pack data and calculate crc16 checksum with a custom header, failures check byte.
+ Print hex data over serial. (8N1)
+ Save 40 telemetry types to an on board SD card.


- Application software: (Python)
+ Allow users to connect to master over serial connection with custom baud/port/zone selection.
+ Read hex data over the serial line and performs data verification.
+ Display 38 data to the LCDs.
+ Graph 9 sensors data in real-time. (Altitude, Temperature, ADXL acceleration X/Y/Z, LSM acceleration X/Y/Z, rocket distance relative to original launch location)
+ Capabilities to reset graph and serial connection.
```


# Build .exe 
```
pyinstaller --onefile --add-data ".\cropped-aiaaweblogo.png;." .\main.py
```


# Usage
```bash
# 1st method: Run the exe
```

```bash
# 2nd method: Running the script:
python main.py
```


# Software 
```
-pyQtDesigner (https://pypi.org/project/PyQt5Designer/)
-Arduino IDE
```

# Author 
Thanh Pham (UH 2024 - 2027)

# Credit
```
-Huge thank you to these people who made this project possible
+ Jake Rodriguez
+ Nathan Samuel
+ 892768447 for the pyQtDesigner library
+ Tobias Bieniek and Bart van Andel for an awesome utm library
+ tpircher for the pycrc library
+ Sandeep Mistry for the Lora library
And everyone who was not mentioned above! Thank you...
```
