#include <SPI.h>
#include <LoRa.h>
#include <SD.h>
#include <limits> 

#define CLK 13
#define MISO 12
#define MOSI 11
#define CS 10
#define INT 2
#define RST 9
#define LORA_FREQ 915E6
#define SCALE_1000(x) ((x) / 1000.0)

/// Data struct for incoming data package 
/// 1 byte padding
#pragma pack(push, 1)
typedef struct LORAMessage {
    uint64_t BMP_time;
    int16_t BMP_temp, BMP_pressure, BMP_altitude;

    uint64_t LSM_time;
    int16_t LSM_accel[3];
    int16_t LSM_gyro[3];

    uint64_t ADXL_time;
    int16_t ADXL_accel[3];

    uint64_t BNO_time;
    int16_t BNO_quat[4];
    int16_t BNO_euler[3];
    int16_t BNO_magnet[3];
    int16_t BNO_accel[3];

    uint64_t GPS_time;
    int8_t GPS_sat;
    int16_t GPS_lon, GPS_lat;
    char GPS_lon_dir, GPS_lat_dir;
    int16_t GPS_alt;

    uint8_t flightState;
    float apogeeEstimate;
} OutputData_t;
#pragma pack(pop)

/// Expected packet size
const size_t EXPECTED_PACKET_SIZE = sizeof(OutputData_t);

/// @brief Counter for received packets, used for logging and debugging
uint32_t rxCounter = 0;
/// @brief Struct instantiation for storing received data, used for logging and debugging
OutputData_t rxData;
/// @brief File handle for SD card logging, used for logging and debugging
File flightData;
// -----------------------------
// Failure bit meanings
// bit 0 = SD init fail
// bit 1 = LoRa init fail
// bit 2 = packet size wrong
// bit 3 = parsing fail
// bit 4 = SD file open fail
// bit 7 = debug enabled
// -----------------------------
uint8_t failureType = 0b10000000; 
/// @brief Buffer for file name, used for logging and debugging
char fileName[20];
/// @brief Counter for file naming, used for logging and debugging
int fileNum = 0;
/// @brief Number of packets after which to flush SD file buffer, used for logging and debugging
const uint16_t FLUSH_EVERY = 10;
/// @brief Increment of 1 to ensure headerbyte bigger than max values of uint32_t counter (0x100000000)
const uint64_t PACKAGE_HEADER_BYTE = std::numeric_limits<uint32_t>::max() + 1.0; 
/// @brief Increment of 1 to ensure endbyte bigger than max values of float apogee (0x7F800000)
const double PACKAGE_END_BYTE = std::numeric_limits<float>::max() + 1.0; 



/// @brief  Reads bytes from LoRa into a provided struct pointer, returns false if not enough bytes or if read error occurs
/// @param dataStruct Pointer to struct where data should be stored, used for logging and debugging
/// @param len Length of data to read in bytes, used for logging and debugging
/// @return True if read successful, false if not enough bytes or if read error occurs
bool readBytesInto(void *dataStruct, size_t len) {
    if ((size_t)LoRa.available() < len) {
        return false;
    }
    uint8_t *dataPtr = (uint8_t *)dataStruct;
    for (size_t counter = 0; counter < len; counter++) {
        int dataByte = LoRa.read();
        if (dataByte < 0) {
            return false;
        }
        dataPtr[counter] = (uint8_t)dataByte;
    }
    return true;
}



/// @brief Writes the CSV header row to the specified file
/// @param file 
void writeCSVHeader(File &file) {
    file.println(
        "rxCounter,failureType,"
        "BMP_time,BMP_temp,BMP_pressure,BMP_altitude,"
        "ADXL_time,ADXL_accel_x,ADXL_accel_y,ADXL_accel_z,"
        "LSM_time,LSM_accel_x,LSM_accel_y,LSM_accel_z,LSM_gyro_x,LSM_gyro_y,LSM_gyro_z,"
        "BNO_time,BNO_quat_x,BNO_quat_y,BNO_quat_z,BNO_quat_w,"
        "BNO_accel_x,BNO_accel_y,BNO_accel_z,"
        "BNO_magnet_x,BNO_magnet_y,BNO_magnet_z,"
        "BNO_euler_x,BNO_euler_y,BNO_euler_z,"
        "GPS_time,GPS_sat,GPS_lat,GPS_lat_dir,GPS_lon,GPS_lon_dir,GPS_alt,"
        "flightState,apogeeEstimate"
    );
}



/// @brief Logs the provided flight data to the specified file in CSV format, includes counter and failure bits for debugging
/// @param file File handle to log data to
/// @param FlightData Struct containing flight data to log
/// @param counter Counter for received packets
/// @param failBits Bitfield indicating any failures that have occurred
/// @note Header/End bytes may be included in the future if needed for data parsing
void logDataToSD(File &file, const OutputData_t &FlightData, uint32_t counter, uint8_t failBits) {
    file.print(counter);                    file.print(",");
    file.print(failBits, BIN);              file.print(",");

    file.print(FlightData.BMP_time);                 file.print(",");
    file.print(SCALE_1000(FlightData.BMP_temp));     file.print(",");
    file.print(SCALE_1000(FlightData.BMP_pressure)); file.print(",");
    file.print(SCALE_1000(FlightData.BMP_altitude)); file.print(",");

    file.print(FlightData.ADXL_time);                file.print(",");
    file.print(SCALE_1000(FlightData.ADXL_accel[0])); file.print(",");
    file.print(SCALE_1000(FlightData.ADXL_accel[1])); file.print(",");
    file.print(SCALE_1000(FlightData.ADXL_accel[2])); file.print(",");

    file.print(FlightData.LSM_time);                 file.print(",");
    file.print(SCALE_1000(FlightData.LSM_accel[0])); file.print(",");
    file.print(SCALE_1000(FlightData.LSM_accel[1])); file.print(",");
    file.print(SCALE_1000(FlightData.LSM_accel[2])); file.print(",");
    file.print(SCALE_1000(FlightData.LSM_gyro[0]));  file.print(",");
    file.print(SCALE_1000(FlightData.LSM_gyro[1]));  file.print(",");
    file.print(SCALE_1000(FlightData.LSM_gyro[2]));  file.print(",");

    file.print(FlightData.BNO_time);                 file.print(",");
    file.print(SCALE_1000(FlightData.BNO_quat[0]));  file.print(",");
    file.print(SCALE_1000(FlightData.BNO_quat[1]));  file.print(",");
    file.print(SCALE_1000(FlightData.BNO_quat[2]));  file.print(",");
    file.print(SCALE_1000(FlightData.BNO_quat[3]));  file.print(",");

    file.print(SCALE_1000(FlightData.BNO_accel[0]));  file.print(",");
    file.print(SCALE_1000(FlightData.BNO_accel[1]));  file.print(",");
    file.print(SCALE_1000(FlightData.BNO_accel[2]));  file.print(",");

    file.print(SCALE_1000(FlightData.BNO_magnet[0])); file.print(",");
    file.print(SCALE_1000(FlightData.BNO_magnet[1])); file.print(",");
    file.print(SCALE_1000(FlightData.BNO_magnet[2])); file.print(",");

    file.print(SCALE_1000(FlightData.BNO_euler[0]));  file.print(",");
    file.print(SCALE_1000(FlightData.BNO_euler[1]));  file.print(",");
    file.print(SCALE_1000(FlightData.BNO_euler[2]));  file.print(",");

    file.print(FlightData.GPS_time);                 file.print(",");
    file.print(FlightData.GPS_sat);                  file.print(",");
    file.print(SCALE_1000(FlightData.GPS_lat));      file.print(",");
    file.print(FlightData.GPS_lat_dir);              file.print(",");
    file.print(SCALE_1000(FlightData.GPS_lon));      file.print(",");
    file.print(FlightData.GPS_lon_dir);              file.print(",");
    file.print(SCALE_1000(FlightData.GPS_alt));      file.print(",");

    file.print(FlightData.flightState);              file.print(",");
    file.print(FlightData.apogeeEstimate);

    file.println();
}



/// @brief Prints the provided flight data to the serial monitor in CSV format, includes counter and failure bits for debugging
/// @param FlightData Struct containing flight data to print
/// @param counter Counter for received packets
/// @param failBits Bitfield indicating any failures that have occurred
void printToSerial(const OutputData_t &FlightData, uint32_t counter, uint8_t failBits) {
    Serial.print(PACKAGE_HEADER_BYTE); Serial.print(",");
    Serial.print(counter); Serial.print(",");
    Serial.print(failBits, BIN); Serial.print(",");
    Serial.print(millis()); Serial.print(",");

    Serial.print(FlightData.BMP_time); Serial.print(",");
    Serial.print(SCALE_1000(FlightData.BMP_temp)); Serial.print(",");
    Serial.print(SCALE_1000(FlightData.BMP_pressure)); Serial.print(",");
    Serial.print(SCALE_1000(FlightData.BMP_altitude)); Serial.print(",");

    Serial.print(FlightData.ADXL_time); Serial.print(",");
    Serial.print(SCALE_1000(FlightData.ADXL_accel[0])); Serial.print(",");
    Serial.print(SCALE_1000(FlightData.ADXL_accel[1])); Serial.print(",");
    Serial.print(SCALE_1000(FlightData.ADXL_accel[2])); Serial.print(",");

    Serial.print(FlightData.LSM_time); Serial.print(",");
    Serial.print(SCALE_1000(FlightData.LSM_accel[0])); Serial.print(",");
    Serial.print(SCALE_1000(FlightData.LSM_accel[1])); Serial.print(",");
    Serial.print(SCALE_1000(FlightData.LSM_accel[2])); Serial.print(",");
    Serial.print(SCALE_1000(FlightData.LSM_gyro[0])); Serial.print(",");
    Serial.print(SCALE_1000(FlightData.LSM_gyro[1])); Serial.print(",");
    Serial.print(SCALE_1000(FlightData.LSM_gyro[2])); Serial.print(",");

    Serial.print(FlightData.BNO_time); Serial.print(",");
    Serial.print(SCALE_1000(FlightData.BNO_quat[0])); Serial.print(",");
    Serial.print(SCALE_1000(FlightData.BNO_quat[1])); Serial.print(",");
    Serial.print(SCALE_1000(FlightData.BNO_quat[2])); Serial.print(",");
    Serial.print(SCALE_1000(FlightData.BNO_quat[3])); Serial.print(",");

    Serial.print(SCALE_1000(FlightData.BNO_accel[0])); Serial.print(",");
    Serial.print(SCALE_1000(FlightData.BNO_accel[1])); Serial.print(",");
    Serial.print(SCALE_1000(FlightData.BNO_accel[2])); Serial.print(",");

    Serial.print(SCALE_1000(FlightData.BNO_magnet[0])); Serial.print(",");
    Serial.print(SCALE_1000(FlightData.BNO_magnet[1])); Serial.print(",");
    Serial.print(SCALE_1000(FlightData.BNO_magnet[2])); Serial.print(",");

    Serial.print(SCALE_1000(FlightData.BNO_euler[0])); Serial.print(",");
    Serial.print(SCALE_1000(FlightData.BNO_euler[1])); Serial.print(",");
    Serial.print(SCALE_1000(FlightData.BNO_euler[2])); Serial.print(",");

    Serial.print(FlightData.GPS_time); Serial.print(",");
    Serial.print(FlightData.GPS_sat); Serial.print(",");
    Serial.print(SCALE_1000(FlightData.GPS_lat)); Serial.print(",");
    Serial.print(FlightData.GPS_lat_dir); Serial.print(",");
    Serial.print(SCALE_1000(FlightData.GPS_lon)); Serial.print(",");
    Serial.print(FlightData.GPS_lon_dir); Serial.print(",");
    Serial.print(SCALE_1000(FlightData.GPS_alt)); Serial.print(",");

    Serial.print(FlightData.flightState); Serial.print(",");
    Serial.print(FlightData.apogeeEstimate);
    Serial.print(PACKAGE_END_BYTE); 
}



/* 
@brief Arduino setup function, 
initializes serial, SPI, LoRa, and SD card, 
sets failure bits if initialization fails, and prepares file for logging.
*/
void setup() {
    /// Begin serial initialization
    Serial.begin(9600);
    while (!Serial) {;}
    SPI.begin();

    /// Pin configuration for LoRa and SD
    LoRa.setSPI(SPI);
    LoRa.setPins(CS, RST, INT);

    /// Initialize SD and LoRa, set failure bits if initialization fails
    if (!SD.begin(BUILTIN_SDCARD)) {
        failureType |= (1 << 0);
    }
    if (!LoRa.begin(LORA_FREQ)) {
        failureType |= (1 << 1);
        while (1) {;}
    }

    /// Find the next available file name for logging
    while (1) {
        snprintf(fileName, sizeof(fileName), "FlightData%02d.txt", fileNum);
        if (!SD.exists(fileName)) {
            break;
        }
        fileNum++;
    }

    /// Open the file for writing and set failure bit if failure occurs
    flightData = SD.open(fileName, FILE_WRITE);
    if (!flightData) {
        failureType |= (1 << 4);
        while (1) {;}
    }

    /// Write the CSV header to the file
    writeCSVHeader(flightData);
    flightData.flush();
}


/*
@brief Arduino loop function, 
checks for incoming LoRa packets, 
validates and parses data, 
logs to SD card, and prints to serial monitor, 
sets failure bits for any errors encountered.
*/
void loop() {
    /// Check for data packet and return early if no packet available
    int packetSize = LoRa.parsePacket();
    if (packetSize <= 0) {
        return;
    }

    /// AND mask to reset packet size and parsing bits in failureType
    failureType &= ~((1 << 2) | (1 << 3)); 

    /// Check packet size and return early if size mismatch, set failure bit
    if ((size_t)packetSize != EXPECTED_PACKET_SIZE) {
        failureType |= (1 << 2);
        while (LoRa.available()) {
            LoRa.read();
        }
        return;
    }

    /// Read packet into struct and return early if parsing fails, set failure bit
    if (!readBytesInto(&rxData, EXPECTED_PACKET_SIZE)) {
        failureType |= (1 << 3);
        while (LoRa.available()) {
            LoRa.read();
        }
        return;
    }

    /// Log data to SD card and return early if file handle invalid, set failure bit
    if (flightData) {
        logDataToSD(flightData, rxData, rxCounter, failureType);
        if ((rxCounter % FLUSH_EVERY) == 0) {
            flightData.flush();
        }
    } else {
        failureType |= (1 << 4);
        return;
    }

    printToSerial(rxData, rxCounter, failureType);

    rxCounter++;

    delay(100);
}