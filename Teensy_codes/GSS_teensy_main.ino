#include <SPI.h>
#include <LoRa.h>
#include <SD.h>

#define CLK 13
#define MISO 12
#define MOSI 11
#define CS 10
#define INT 2
#define RST 9
#define LORA_FREQ 915E6
#define SCALE_1000(x) ((x) / 1000.0)

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


const size_t EXPECTED_PACKET_SIZE = sizeof(OutputData_t);

uint32_t rxCounter = 0;
OutputData_t rxData;
File flightData;

uint8_t failureType = 0b10000000;  // bit 7 = debug enabled

char fileName[20];
int fileNum = 0;

// optional: flush every N packets instead of every packet
const uint16_t FLUSH_EVERY = 10;

// -----------------------------
// Failure bit meanings
// bit 0 = SD init fail
// bit 1 = LoRa init fail
// bit 2 = packet size wrong
// bit 3 = parsing fail
// bit 4 = SD file open fail
// bit 7 = debug enabled
// -----------------------------

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

void printToSerial(const OutputData_t &FlightData, uint32_t counter, uint8_t failBits) {
    Serial.print("PACKET_COUNTER:"); Serial.print(counter); Serial.print(",");
    Serial.print("FAILURE:");        Serial.print(failBits, BIN); Serial.print(",");
    Serial.print("TIMEMS:");         Serial.print(millis()); Serial.print(",");

    Serial.print("BMP_TIME:");       Serial.print(FlightData.BMP_time); Serial.print(",");
    Serial.print("TEMP:");           Serial.print(SCALE_1000(FlightData.BMP_temp)); Serial.print(",");
    Serial.print("PRESS:");          Serial.print(SCALE_1000(FlightData.BMP_pressure)); Serial.print(",");
    Serial.print("BMP_ALT:");        Serial.print(SCALE_1000(FlightData.BMP_altitude)); Serial.print(",");

    Serial.print("ADXL_TIME:");      Serial.print(FlightData.ADXL_time); Serial.print(",");
    Serial.print("ADXL_ACCEL_X:");   Serial.print(SCALE_1000(FlightData.ADXL_accel[0])); Serial.print(",");
    Serial.print("ADXL_ACCEL_Y:");   Serial.print(SCALE_1000(FlightData.ADXL_accel[1])); Serial.print(",");
    Serial.print("ADXL_ACCEL_Z:");   Serial.print(SCALE_1000(FlightData.ADXL_accel[2])); Serial.print(",");

    Serial.print("LSM_TIME:");       Serial.print(FlightData.LSM_time); Serial.print(",");
    Serial.print("LSM_ACCEL_X:");    Serial.print(SCALE_1000(FlightData.LSM_accel[0])); Serial.print(",");
    Serial.print("LSM_ACCEL_Y:");    Serial.print(SCALE_1000(FlightData.LSM_accel[1])); Serial.print(",");
    Serial.print("LSM_ACCEL_Z:");    Serial.print(SCALE_1000(FlightData.LSM_accel[2])); Serial.print(",");
    Serial.print("LSM_GYRO_X:");     Serial.print(SCALE_1000(FlightData.LSM_gyro[0])); Serial.print(",");
    Serial.print("LSM_GYRO_Y:");     Serial.print(SCALE_1000(FlightData.LSM_gyro[1])); Serial.print(",");
    Serial.print("LSM_GYRO_Z:");     Serial.print(SCALE_1000(FlightData.LSM_gyro[2])); Serial.print(",");

    Serial.print("BNO_TIME:");       Serial.print(FlightData.BNO_time); Serial.print(",");
    Serial.print("BNO_QUAT_W:");     Serial.print(SCALE_1000(FlightData.BNO_quat[0])); Serial.print(",");
    Serial.print("BNO_QUAT_X:");     Serial.print(SCALE_1000(FlightData.BNO_quat[1])); Serial.print(",");
    Serial.print("BNO_QUAT_Y:");     Serial.print(SCALE_1000(FlightData.BNO_quat[2])); Serial.print(",");
    Serial.print("BNO_QUAT_Z:");     Serial.print(SCALE_1000(FlightData.BNO_quat[3])); Serial.print(",");

    Serial.print("BNO_ACCEL_X:");    Serial.print(SCALE_1000(FlightData.BNO_accel[0])); Serial.print(",");
    Serial.print("BNO_ACCEL_Y:");    Serial.print(SCALE_1000(FlightData.BNO_accel[1])); Serial.print(",");
    Serial.print("BNO_ACCEL_Z:");    Serial.print(SCALE_1000(FlightData.BNO_accel[2])); Serial.print(",");

    Serial.print("BNO_MAG_X:");      Serial.print(SCALE_1000(FlightData.BNO_magnet[0])); Serial.print(",");
    Serial.print("BNO_MAG_Y:");      Serial.print(SCALE_1000(FlightData.BNO_magnet[1])); Serial.print(",");
    Serial.print("BNO_MAG_Z:");      Serial.print(SCALE_1000(FlightData.BNO_magnet[2])); Serial.print(",");

    Serial.print("BNO_EULER_X:");    Serial.print(SCALE_1000(FlightData.BNO_euler[0])); Serial.print(",");
    Serial.print("BNO_EULER_Y:");    Serial.print(SCALE_1000(FlightData.BNO_euler[1])); Serial.print(",");
    Serial.print("BNO_EULER_Z:");    Serial.print(SCALE_1000(FlightData.BNO_euler[2])); Serial.print(",");

    Serial.print("GPS_TIME:");       Serial.print(FlightData.GPS_time); Serial.print(",");
    Serial.print("GPS_SAT:");        Serial.print(FlightData.GPS_sat); Serial.print(",");
    Serial.print("LAT:");            Serial.print(SCALE_1000(FlightData.GPS_lat)); Serial.print(",");
    Serial.print("LAT_DIR:");        Serial.print(FlightData.GPS_lat_dir); Serial.print(",");
    Serial.print("LON:");            Serial.print(SCALE_1000(FlightData.GPS_lon)); Serial.print(",");
    Serial.print("LON_DIR:");        Serial.print(FlightData.GPS_lon_dir); Serial.print(",");
    Serial.print("GPS_ALT:");        Serial.print(SCALE_1000(FlightData.GPS_alt)); Serial.print(",");

    Serial.print("FLIGHT_STATE:");   Serial.print(FlightData.flightState); Serial.print(",");
    Serial.print("APOGEE:");         Serial.print(FlightData.apogeeEstimate);

    Serial.println();
}

void setup() {
    Serial.begin(9600);
    while (!Serial) {;}

    SPI.begin();
    LoRa.setSPI(SPI);
    LoRa.setPins(CS, RST, INT);

    if (!SD.begin(BUILTIN_SDCARD)) {
        failureType |= (1 << 0);
        // Serial.println("SD init failed");
    }

    if (!LoRa.begin(LORA_FREQ)) {
        failureType |= (1 << 1);
        // Serial.println("LoRa init failed");
        while (1) {;}
    }

    while (1) {
        snprintf(fileName, sizeof(fileName), "FlightData%02d.txt", fileNum);
        if (!SD.exists(fileName)) {
            break;
        }
        fileNum++;
    }

    // Serial.print("Using file: ");
    // Serial.println(fileName);

    flightData = SD.open(fileName, FILE_WRITE);
    if (!flightData) {
        failureType |= (1 << 4);
        // Serial.println("Failed to open log file");
        while (1) {;}
    }

    writeCSVHeader(flightData);
    flightData.flush();

    // Serial.print("Expected packet size: ");
    // Serial.println(EXPECTED_PACKET_SIZE);
}

void loop() {
    int packetSize = LoRa.parsePacket();

    if (packetSize <= 0) {
        return;
    }

    /// AND mask to reset packet size and parsing bits in failureYype
    failureType &= ~((1 << 2) | (1 << 3)); 

    if ((size_t)packetSize != EXPECTED_PACKET_SIZE) {
        failureType |= (1 << 2);
        Serial.print(packetSize);
        // Serial.print(" Expected: ");
        // Serial.println(EXPECTED_PACKET_SIZE);
        while (LoRa.available()) {
            LoRa.read();
        }
        return;
    }

    if (!readBytesInto(&rxData, EXPECTED_PACKET_SIZE)) {
        failureType |= (1 << 3);
        // Serial.println("Parsing data failed");
        while (LoRa.available()) {
            LoRa.read();
        }
        return;
    }

    if (flightData) {
        logDataToSD(flightData, rxData, rxCounter, failureType);
        if ((rxCounter % FLUSH_EVERY) == 0) {
            flightData.flush();
        }
    } else {
        failureType |= (1 << 4);
        // Serial.println("Log file handle invalid");
        return;
    }

    printToSerial(rxData, rxCounter, failureType);

    rxCounter++;

    delay(100);
}