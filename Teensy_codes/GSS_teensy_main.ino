#include <SPI.h>
#include <LoRa.h>
#include <SD.h>
#define CLK 13
#define MISO 12
#define MOSI 11
#define CS 10
#define INT 2
#define RST 9

/// RX Data struct
typedef struct{
    uint32_t BMP_time;
    uint16_t BMP_temp, BMP_pressure, BMP_altitude;

    uint32_t LSM_time;
    uint16_t LSM_accel[3];
    uint16_t LSM_gyro[3];

    uint32_t ADXL_time;
    uint16_t ADXL_accel[3];

    uint32_t BNO_time;
    uint16_t BNO_quat[4];
    uint16_t BNO_euler[3];
    uint16_t BNO_magnet[3];
    uint16_t BNO_accel[3];

    uint32_t GPS_time;
    uint8_t GPS_sat;
    uint16_t GPS_lon, GPS_lat;
    char GPS_lon_dir, GPS_lat_dir;
    uint16_t GPS_alt;

    uint8_t flightState = 0;
    float bmp_apogee_record = 0;
} OutputData_t;

/// Expect packet constant
const int EXPECTED_PACKET_SIZE = sizeof(OutputData_t);

/// Instatiate data packet counter
uint32_t rxCounter = 0;

/// Instatiate data struct for parsing
OutputData_t rxData;

/// Instantiate SD card saving
File flightData;

/// Failure type holder
/*
Bit Position: (0=false,1=true). LSB first.
    1 = SD fails init,
    2 = Lora fails init,
    3 = Packet missing,
    4 = Extracting data fails,
    5 = SD file opening fails.
    8 = Bit is enabled for full printout
*/
uint8_t failureType = 0b10000000;

/// Dynamic file name variables
char fileName[15];
/// File Counter
int fileNum = 0;

/// Parse received data to struct
bool readBytesInto(void *datastruct, int len) { 
    uint8_t *data_pointer = (uint8_t*)datastruct;
    for (int counter = 0; counter < len; ++counter) {
        int data_byte = LoRa.read();
        if (data_byte < 0) {
            return false; // not enough data
        }
        data_pointer[counter] = (uint8_t)data_byte;
    }
    return true;
}

void setup() {
    Serial.begin(9600);
    while (!Serial);
    SPI.begin();
    LoRa.setSPI(SPI);
    LoRa.setPins(CS, RST, INT);

    /// Check SD init
    if (!SD.begin(BUILTIN_SDCARD)) {
        failureType |= (0x1);
    }
    /// Check Lora init
    if (!LoRa.begin(915E6)) {
        failureType |= (1 << 1);
        while (1);
    }
    /// File name increment logic
    while (1){
        snprintf(fileName, sizeof(fileName), "FlightData%02.txt", fileNum);
        if (!SD.exists(fileName)) break;
        fileNum++;
    }
}

void loop() {
    int packetSize = LoRa.parsePacket();

    /// Set error type and drain packet
    if (packetSize != EXPECTED_PACKET_SIZE) {
        failureType |= (1 << 2);
        while (LoRa.available()) LoRa.read();
        return;
    }

    /// Set error for fail parsing
    if (!readBytesInto(&rxData, EXPECTED_PACKET_SIZE)) {
        failureType |= (1 << 3);
        return;
    }

    /// Open file
    flightData = SD.open(fileName, FILE_WRITE);

    if (flightData) {
        flightData.print(rxCounter); Serial.print(",");
        flightData.print(failureType, BIN);Serial.print(",");
        flightData.print(rxData.BMP_time); Serial.print(",");
        flightData.print(rxData.BMP_temp); Serial.print(",");
        flightData.print(rxData.BMP_pressure); Serial.print(",");
        flightData.print(rxData.BMP_altitude); Serial.print(",");
        flightData.print(rxData.ADXL_time); Serial.print(",");
        flightData.print(rxData.ADXL_accel[0]); Serial.print(",");
        flightData.print(rxData.ADXL_accel[1]); Serial.print(",");
        flightData.print(rxData.ADXL_accel[2]); Serial.print(",");
        flightData.print(rxData.LSM_time); Serial.print(",");
        flightData.print(rxData.LSM_accel[0]); Serial.print(",");
        flightData.print(rxData.LSM_accel[1]); Serial.print(",");
        flightData.print(rxData.LSM_accel[2]); Serial.print(",");
        flightData.print(rxData.LSM_gyro[0]); Serial.print(",");
        flightData.print(rxData.LSM_gyro[1]); Serial.print(",");
        flightData.print(rxData.LSM_gyro[2]); Serial.print(",");
        flightData.print(rxData.BNO_time); Serial.print(",");
        flightData.print(rxData.BNO_quat[0]); Serial.print(",");
        flightData.print(rxData.BNO_quat[1]); Serial.print(",");
        flightData.print(rxData.BNO_quat[2]); Serial.print(",");
        flightData.print(rxData.BNO_quat[3]); Serial.print(",");
        flightData.print(rxData.BNO_accel[0]); Serial.print(",");
        flightData.print(rxData.BNO_accel[1]); Serial.print(",");
        flightData.print(rxData.BNO_accel[2]); Serial.print(",");
        flightData.print(rxData.BNO_magnet[0]); Serial.print(",");
        flightData.print(rxData.BNO_magnet[1]); Serial.print(",");
        flightData.print(rxData.BNO_magnet[2]); Serial.print(",");
        flightData.print(rxData.BNO_euler[0]); Serial.print(",");
        flightData.print(rxData.BNO_euler[1]); Serial.print(",");
        flightData.print(rxData.BNO_euler[2]); Serial.print(",");
        flightData.print(rxData.GPS_time); Serial.print(",");
        flightData.print(rxData.GPS_lat); Serial.print(",");
        flightData.print(rxData.GPS_lat_dir); Serial.print(",");
        flightData.print(rxData.GPS_lon); Serial.print(",");
        flightData.print(rxData.GPS_lon_dir); Serial.print(",");
        flightData.print(rxData.flightState); Serial.print(",");
        flightData.print(rxData.bmp_apogee_record); 
        flightData.println();
        flightData.close();
    } else {
        failureType |= (1 << 4);
        return;
    }

    /// Packet Counter
    // Debug only. Disable later for better performance
    Serial.print("PACKET_COUNTER:"); Serial.print(rxCounter++); Serial.print(",");
    Serial.print("FAILURE:"); Serial.print(failureType, BIN); Serial.print(",");

    /// Time of each full packet
    Serial.print("TIMEMS:"); Serial.print(millis()); Serial.print(",");

    /// BMP data
    Serial.print("BMP_TIME:"); Serial.print(rxData.BMP_time); Serial.print(",");
    Serial.print("TEMP:"); Serial.print(rxData.BMP_temp); Serial.print(",");
    Serial.print("PRESS:"); Serial.print(rxData.BMP_pressure); Serial.print(",");
    Serial.print("BMP_ALT:"); Serial.print(rxData.BMP_altitude); Serial.print(",");

    /// ADXL data
    Serial.print("ADXL_TIME: ");  Serial.print(rxData.ADXL_time); Serial.print(",");
    Serial.print("ADXL_ACCEL_X:"); Serial.print(rxData.ADXL_accel[0]); Serial.print(",");
    Serial.print("ADXL_ACCEL_Y:"); Serial.print(rxData.ADXL_accel[1]); Serial.print(",");
    Serial.print("ADXL_ACCEL_Z:"); Serial.print(rxData.ADXL_accel[2]); Serial.print(",");

    // LSM data - Accel
    Serial.print("LSM_TIME: ");  Serial.print(rxData.LSM_time);Serial.print(",");
    Serial.print("LSM_ACCEL_X:"); Serial.print(rxData.LSM_accel[0]); Serial.print(",");
    Serial.print("LSM_ACCEL_Y:"); Serial.print(rxData.LSM_accel[1]); Serial.print(",");
    Serial.print("LSM_ACCEL_Z:"); Serial.print(rxData.LSM_accel[2]);Serial.print(",");
    /// Gyro
    Serial.print("LSM_GYRO_X:"); Serial.print(rxData.LSM_gyro[0]); Serial.print(",");
    Serial.print("LSM_GYRO_Y:"); Serial.print(rxData.LSM_gyro[1]); Serial.print(",");
    Serial.print("LSM_GYRO_Z:"); Serial.print(rxData.LSM_gyro[2]); Serial.print(",");

    /// BNO quaternion data
    Serial.print("BNO_TIME:"); Serial.print(rxData.BNO_time); Serial.print(",");
    Serial.print("BNO_QUAT_X:"); Serial.print(rxData.BNO_quat[0]); Serial.print(",");
    Serial.print("BNO_QUAT_Y:"); Serial.print(rxData.BNO_quat[1]); Serial.print(",");
    Serial.print("BNO_QUAT_Z:"); Serial.print(rxData.BNO_quat[2]); Serial.print(",");
    Serial.print("BNO_QUAT_W:"); Serial.print(rxData.BNO_quat[3]); Serial.print(",");

    /// BNO accelerometer data
    Serial.print("BNO_ACCEL_X:"); Serial.print(rxData.BNO_accel[0]); Serial.print(",");
    Serial.print("BNO_ACCEL_Y:"); Serial.print(rxData.BNO_accel[1]); Serial.print(",");
    Serial.print("BNO_ACCEL_Z:"); Serial.print(rxData.BNO_accel[2]); Serial.print(",");

    /// BNO Magnometer data
    Serial.print("BNO_MAG_X:"); Serial.print(rxData.BNO_magnet[0]); Serial.print(",");
    Serial.print("BNO_MAG_Y:"); Serial.print(rxData.BNO_magnet[1]); Serial.print(",");
    Serial.print("BNO_MAG_Z:"); Serial.print(rxData.BNO_magnet[2]); Serial.print(",");

    /// BNO Euler data
    Serial.print("BNO_EULER_X:"); Serial.print(rxData.BNO_euler[0]); Serial.print(",");
    Serial.print("BNO_EULER_Y:"); Serial.print(rxData.BNO_euler[1]); Serial.print(",");
    Serial.print("BNO_EULER_Z:"); Serial.print(rxData.BNO_euler[2]); Serial.print(",");

    /// GPS data
    Serial.print("GPS_TIME:"); Serial.print(rxData.GPS_time); Serial.print(",");
    Serial.print("GPS_SAT:"); Serial.print(rxData.GPS_sat); Serial.print(",");
    Serial.print("LAT:"); Serial.print(rxData.GPS_lat); Serial.print(",");
    Serial.print("LON:"); Serial.print(rxData.GPS_lon); Serial.print(",");
    Serial.print("GPS_ALT:"); Serial.print(rxData.GPS_alt); Serial.print(",");
    Serial.print("LAT_DIR:"); Serial.print(rxData.GPS_lat_dir); Serial.print(",");
    Serial.print("LON_DIR:"); Serial.print(rxData.GPS_lon_dir); Serial.print(",");

    Serial.print("FLIGHT_STATE:"); Serial.print(rxData.flightState); Serial.print(",");
    Serial.print("APOGEE:"); Serial.print(rxData.bmp_apogee_record); Serial.print(",");

    Serial.println();
    

    delay(100); //10Hz Update rate to avoid buffer overflow 
}
