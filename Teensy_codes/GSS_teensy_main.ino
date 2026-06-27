#include <SPI.h>
#include <LoRa.h>
#include <SD.h>
#include <limits> 
#include <AceCRC.h>

/// Pins definition
#define CLK 13
#define MISO 12
#define MOSI 11
#define CS 10
#define INT 2
#define RST 9
/// Lora Frequency
#define LORA_FREQ 915E6
/// Data constant scaling 
#define SCALE_1000(x) ((x) / 1000.0)
/// Name space to use pycrc CRC16-CCITT
using namespace ace_crc::crc16ccitt_nibblem;

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

/// @brief Expected packet size from Lora of the Flight Comp
const size_t EXPECTED_PACKET_SIZE = sizeof(OutputData_t);
/// @brief Counter for received packets, used for logging and debugging
uint32_t rxCounter = 0;
/// @brief Time from the moment of receiving data from the Lora
uint32_t packet_time = 0;
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
/// @brief Increment of 1 to ensure headerbyte bigger than max values of uint32_t counter 
/// (0x100000000 = std::numeric_limits<uint32_t>::max() + 1.0;)
const uint64_t PACKAGE_HEADER_BYTE = 0x100000000;
/// @brief Serial data packet storage to calculate checksum
uint8_t serial_packet[
    sizeof(PACKAGE_HEADER_BYTE)
    + sizeof(rxCounter)
    + sizeof(failureType)
    + sizeof(packet_time)
    + sizeof(OutputData_t)
] = {0};



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


/// @brief Calculate check sum of the data packet sending to the app
/// @param buffer Data packet storage
/// @param counter Packet counter
/// @param FailureType Failure type redundant checks
/// @param packet_time Time when the data was read from the Lora
/// @param data_packet Data packet on the receiving side
/// @return CRC16
uint16_t pack_packet(uint8_t *buffer, uint32_t &counter, uint8_t &FailureType, uint32_t &packet_time, OutputData_t &data_packet) 
{
    size_t index = 0;
    memcpy(&buffer[index], &PACKAGE_HEADER_BYTE, sizeof(PACKAGE_HEADER_BYTE));
    index += sizeof(PACKAGE_HEADER_BYTE);
    /// Pack counter 
    memcpy(&buffer[index], &counter, sizeof(counter));
    index += sizeof(counter);
    /// Pack FailureType
    memcpy(&buffer[index], &FailureType, sizeof(FailureType));
    index += sizeof(FailureType);
    /// Pack packet time
    memcpy(&buffer[index], &packet_time, sizeof(packet_time));
    index += sizeof(packet_time);
    /// Pack data packet
    memcpy(&buffer[index], &data_packet, sizeof(data_packet));
    index += sizeof(data_packet);
    /// Calculate and append CRC16
    crc_t crc = crc_init();
    crc = crc_update(crc, buffer, index);
    crc = crc_finalize(crc);

    return crc;
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
void logDataToSD(File &file, const OutputData_t &FlightData, uint32_t &counter, uint8_t &failBits) {
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
void printToSerial(const OutputData_t &FlightData, uint32_t &counter, uint8_t &failBits, uint32_t &packet_time, uint16_t &checksum) {
    Serial.print(PACKAGE_HEADER_BYTE); Serial.print(",");//0
    Serial.print(counter); Serial.print(",");//1
    Serial.print(failBits, BIN); Serial.print(",");//2
    Serial.print(packet_time); Serial.print(",");//3

    Serial.print(FlightData.BMP_time); Serial.print(","); //4
    Serial.print(SCALE_1000(FlightData.BMP_temp)); Serial.print(","); //5
    Serial.print(SCALE_1000(FlightData.BMP_pressure)); Serial.print(",");//6
    Serial.print(SCALE_1000(FlightData.BMP_altitude)); Serial.print(",");//7

    Serial.print(FlightData.ADXL_time); Serial.print(",");//8
    Serial.print(SCALE_1000(FlightData.ADXL_accel[0])); Serial.print(",");//9 x
    Serial.print(SCALE_1000(FlightData.ADXL_accel[1])); Serial.print(",");//10 y
    Serial.print(SCALE_1000(FlightData.ADXL_accel[2])); Serial.print(",");//11 z

    Serial.print(FlightData.LSM_time); Serial.print(","); //12
    Serial.print(SCALE_1000(FlightData.LSM_accel[0])); Serial.print(",");//13 x
    Serial.print(SCALE_1000(FlightData.LSM_accel[1])); Serial.print(",");//14 y
    Serial.print(SCALE_1000(FlightData.LSM_accel[2])); Serial.print(",");//15 z
    Serial.print(SCALE_1000(FlightData.LSM_gyro[0])); Serial.print(",");//16 x
    Serial.print(SCALE_1000(FlightData.LSM_gyro[1])); Serial.print(",");//17 y
    Serial.print(SCALE_1000(FlightData.LSM_gyro[2])); Serial.print(",");//18 z

    Serial.print(FlightData.BNO_time); Serial.print(",");//19
    Serial.print(SCALE_1000(FlightData.BNO_quat[0])); Serial.print(",");//20 w
    Serial.print(SCALE_1000(FlightData.BNO_quat[1])); Serial.print(",");//21 x
    Serial.print(SCALE_1000(FlightData.BNO_quat[2])); Serial.print(",");//22 y
    Serial.print(SCALE_1000(FlightData.BNO_quat[3])); Serial.print(",");//23 z

    Serial.print(SCALE_1000(FlightData.BNO_accel[0])); Serial.print(",");//24 x
    Serial.print(SCALE_1000(FlightData.BNO_accel[1])); Serial.print(",");//25 y
    Serial.print(SCALE_1000(FlightData.BNO_accel[2])); Serial.print(",");//26 z

    Serial.print(SCALE_1000(FlightData.BNO_magnet[0])); Serial.print(",");//27 x
    Serial.print(SCALE_1000(FlightData.BNO_magnet[1])); Serial.print(",");//28 y
    Serial.print(SCALE_1000(FlightData.BNO_magnet[2])); Serial.print(",");//29 z

    Serial.print(SCALE_1000(FlightData.BNO_euler[0])); Serial.print(",");//30 x
    Serial.print(SCALE_1000(FlightData.BNO_euler[1])); Serial.print(",");//31 y
    Serial.print(SCALE_1000(FlightData.BNO_euler[2])); Serial.print(",");//32 z

    Serial.print(FlightData.GPS_time); Serial.print(",");//33 
    Serial.print(FlightData.GPS_sat); Serial.print(",");//34
    Serial.print(SCALE_1000(FlightData.GPS_lat)); Serial.print(",");//35
    Serial.print(FlightData.GPS_lat_dir); Serial.print(",");//36
    Serial.print(SCALE_1000(FlightData.GPS_lon)); Serial.print(",");//37
    Serial.print(FlightData.GPS_lon_dir); Serial.print(",");//38
    Serial.print(SCALE_1000(FlightData.GPS_alt)); Serial.print(",");//39

    Serial.print(FlightData.flightState); Serial.print(",");//40
    Serial.print(FlightData.apogeeEstimate); Serial.print(",");//41
    Serial.print((uint8_t)(checksum >> 8)); Serial.print(","); //42
    Serial.print((uint8_t)(checksum));//43

    Serial.println();
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
    } else {
        packet_time = millis();
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
    /// Calculate crc16 of the data packet being sent over the serial line
    uint16_t crc16 = pack_packet(serial_packet, rxCounter, failureType, packet_time, rxData);
    /// Print the data packet to serial line so the app can pick them up
    printToSerial(rxData, rxCounter, failureType, packet_time, crc16);
    /// Increment counter
    rxCounter++;
    /// Small delay so packet is not repeated (can be optimized more)
    delay(100);
}