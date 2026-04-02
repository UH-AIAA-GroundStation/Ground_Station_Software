#include <SPI.h>
#include <LoRa.h>
#define CLK 13
#define MISO 12
#define MOSI 11
#define CS 10
#define INT 2
#define RST 9

static bool toggle = false;

typedef struct{
  uint32_t ADXL_time;
  uint16_t ADXL_accel[3];

  uint32_t BNO_time;
  uint16_t BNO_quat[4];
  uint16_t BNO_euler[3];
  uint16_t BNO_magnet[3];
  uint16_t BNO_accel[3];

  uint32_t LSM_time;
  uint16_t LSM_accel[3];
  uint16_t LSM_gyro[3];

  uint32_t BMP_time;
  uint16_t BMP_temp, BMP_pressure, BMP_altitude;

  uint32_t GPS_time;
  uint8_t GPS_sat;
  uint16_t GPS_lon, GPS_lat;
  char GPS_lon_dir, GPS_lat_dir;
  uint16_t GPS_alt;

  uint8_t flightState = 0;
  float bmp_apogee_record = 0;
} OutputData_t;

OutputData_t rxData;


void dataToSerial(const OutputData_t& data) {
  // /// Now rxData is fully reconstructed
  //   Serial.print("PACKET_COUNTER:"); Serial.print(pktCounter); Serial.print(",");

    /// Time of each full packet
    Serial.print("TIMEMS:"); Serial.print(millis()); Serial.print(",");

    /// BMP data
    Serial.print("BMP_TIME:"); Serial.print(float(rxData.BMP_time)); Serial.print(",");
    Serial.print("TEMP:"); Serial.print(float(rxData.BMP_temp)); Serial.print(",");
    Serial.print("PRESS:"); Serial.print(float(rxData.BMP_pressure)); Serial.print(",");
    Serial.print("BMP_ALT:"); Serial.print(float(rxData.BMP_altitude)); Serial.print(",");

    /// ADXL data
    Serial.print("ADXL_TIME: ");  Serial.print(rxData.ADXL_time); Serial.print(",");
    Serial.print("ADXL_ACCEL_X:"); Serial.print(float(rxData.ADXL_accel[0])); Serial.print(",");
    Serial.print("ADXL_ACCEL_Y:"); Serial.print(float(rxData.ADXL_accel[1])); Serial.print(",");
    Serial.print("ADXL_ACCEL_Z:"); Serial.print(float(rxData.ADXL_accel[2])); Serial.print(",");

    // LSM data - Accel
    Serial.print("LSM_TIME: ");  Serial.print(float(rxData.LSM_time));Serial.print(",");
    Serial.print("LSM_ACCEL_X:"); Serial.print(float(rxData.LSM_accel[0])); Serial.print(",");
    Serial.print("LSM_ACCEL_Y:"); Serial.print(float(rxData.LSM_accel[1])); Serial.print(",");
    Serial.print("LSM_ACCEL_Z:"); Serial.print(float(rxData.LSM_accel[2]));Serial.print(",");
    /// Gyro
    Serial.print("LSM_GYRO_X:"); Serial.print(float(rxData.LSM_gyro[0])); Serial.print(",");
    Serial.print("LSM_GYRO_Y:"); Serial.print(float(rxData.LSM_gyro[1])); Serial.print(",");
    Serial.print("LSM_GYRO_Z:"); Serial.print(float(rxData.LSM_gyro[2])); Serial.print(",");

    /// BNO quaternion data
    Serial.print("BNO_TIME:"); Serial.print(float(rxData.BNO_time)); Serial.print(",");
    Serial.print("BNO_QUAT_X:"); Serial.print(float(rxData.BNO_quat[0])); Serial.print(",");
    Serial.print("BNO_QUAT_Y:"); Serial.print(float(rxData.BNO_quat[1])); Serial.print(",");
    Serial.print("BNO_QUAT_Z:"); Serial.print(float(rxData.BNO_quat[2])); Serial.print(",");
    Serial.print("BNO_QUAT_W:"); Serial.print(float(rxData.BNO_quat[3])); Serial.print(",");

    /// BNO accelerometer data
    Serial.print("BNO_ACCEL_X:"); Serial.print(float(rxData.BNO_accel[0])); Serial.print(",");
    Serial.print("BNO_ACCEL_Y:"); Serial.print(float(rxData.BNO_accel[1])); Serial.print(",");
    Serial.print("BNO_ACCEL_Z:"); Serial.print(float(rxData.BNO_accel[2])); Serial.print(",");

    /// BNO Magnometer data
    Serial.print("BNO_MAG_X:"); Serial.print(float(rxData.BNO_magnet[0])); Serial.print(",");
    Serial.print("BNO_MAG_Y:"); Serial.print(float(rxData.BNO_magnet[1])); Serial.print(",");
    Serial.print("BNO_MAG_Z:"); Serial.print(float(rxData.BNO_magnet[2])); Serial.print(",");

    /// BNO Euler data
    Serial.print("BNO_EULER_X:"); Serial.print(float(rxData.BNO_euler[0])); Serial.print(",");
    Serial.print("BNO_EULER_Y:"); Serial.print(float(rxData.BNO_euler[1])); Serial.print(",");
    Serial.print("BNO_EULER_Z:"); Serial.print(float(rxData.BNO_euler[2])); Serial.print(",");

    /// GPS data
    Serial.print("GPS_TIME:"); Serial.print(float(rxData.GPS_time)); Serial.print(",");
    Serial.print("GPS_SAT:"); Serial.print(float(rxData.GPS_sat)); Serial.print(",");
    Serial.print("LAT:"); Serial.print(float(rxData.GPS_lat)); Serial.print(",");
    Serial.print("LON:"); Serial.print(float(rxData.GPS_lon)); Serial.print(",");
    Serial.print("GPS_ALT:"); Serial.print(float(rxData.GPS_alt)); Serial.print(",");
    Serial.print("LAT_DIR:"); Serial.print(rxData.GPS_lat_dir); Serial.print(",");
    Serial.print("LON_DIR:"); Serial.print(rxData.GPS_lon_dir); Serial.print(",");

    Serial.print("FLIGHT_STATE:"); Serial.print(rxData.flightState); Serial.print(",");
    Serial.print("APOGEE:"); Serial.print(rxData.bmp_apogee_record); Serial.print(",");

    Serial.println();

}

void setup() {
  Serial.begin(9600);
  while (!Serial);
  SPI.begin();
  LoRa.setSPI(SPI);
  LoRa.setPins(CS, RST, INT);

  // Serial.println("LoRa Receiver");
  // Serial.println("Waiting for packets...");
}

void loop() {
  // Serial.print("\n[RX] Packet received, size = ");

  toggle = !toggle;

  rxData.ADXL_time = rxData.ADXL_time + 1;
  rxData.ADXL_accel[0] = toggle ? 100 : 300;
  rxData.ADXL_accel[1] = toggle ? 100 : 300;
  rxData.ADXL_accel[2] = toggle ? 100 : 300;

  rxData.BNO_time = (float(rxData.BNO_time) + 1);
  rxData.BNO_quat[0] = toggle ? 100 : 300;
  rxData.BNO_quat[1] = toggle ? 100 : 300;
  rxData.BNO_quat[2] = toggle ? 100 : 300;
  rxData.BNO_quat[3] = toggle ? 100 : 300;

  rxData.BNO_euler[0] = toggle ? 100 : 300;
  rxData.BNO_euler[1] = toggle ? 100 : 300;
  rxData.BNO_euler[2] = toggle ? 100 : 300;

  rxData.BNO_magnet[0] = toggle ? 100 : 300;
  rxData.BNO_magnet[1] = toggle ? 100 : 300;
  rxData.BNO_magnet[2] = toggle ? 100 : 300;

  rxData.BNO_accel[0] = toggle ? 100 : 300;
  rxData.BNO_accel[1] = toggle ? 100 : 300;
  rxData.BNO_accel[2] = toggle ? 100 : 300;

  rxData.LSM_time = (float(rxData.LSM_time) + 1);
  rxData.LSM_accel[0] = toggle ? 100 : 300;
  rxData.LSM_accel[1] = toggle ? 100 : 300;
  rxData.LSM_accel[2] = toggle ? 100 : 300;

  rxData.LSM_gyro[0] = toggle ? 100 : 300;
  rxData.LSM_gyro[1] = toggle ? 100 : 300;
  rxData.LSM_gyro[2] = toggle ? 100 : 300;

  rxData.BMP_time = (float(rxData.BMP_time) + 1);
  rxData.BMP_temp = toggle ? 23.33 : 16.27;
  rxData.BMP_pressure = toggle ? 100 : 300;
  rxData.BMP_altitude = toggle ? 3333.34567 : 2222.34567;
  
  rxData.GPS_time = (float(rxData.GPS_time) + 1);
  rxData.GPS_sat = toggle ? 2 : 4;
  rxData.GPS_lat = (float(rxData.GPS_lat) + 1);
  rxData.GPS_lon = (float(rxData.GPS_lon) + 1);
  rxData.GPS_lon_dir = toggle ? 'A' : 'B';
  rxData.GPS_lat_dir = toggle ? 'A' : 'B';
  rxData.GPS_alt = toggle ? 1000: 1500;

  rxData.flightState = toggle ? 1 : 2;
  rxData.bmp_apogee_record = toggle ? 1000 : 2000;

  
  dataToSerial(rxData);

  delay(100); //10Hz Update rate to avoid buffer overflow 
}
