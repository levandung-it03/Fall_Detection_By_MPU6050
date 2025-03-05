#include <Arduino.h>
#include <WiFi.h>
#include <WiFiMulti.h>
#include <MPU6050_tockn.h>
#include <Wire.h>
#include <WiFiClientSecure.h>
#include <WebSocketsClient.h>
#include <NTPClient.h>
#include <WiFiUdp.h>

// Thông tin WiFi
const char* ssid = "MSIBS";
const char* password = "n21dccn021";

// Địa chỉ WebSocket
const char* ws_host = "192.168.79.116";
const uint16_t ws_port = 8000;
const char* ws_url = "/total-acceleration-by-mpu";

// Khai báo WebSocket client
WiFiMulti WiFiMulti;
WebSocketsClient webSocket;
MPU6050 mpu6050(Wire);
WiFiUDP ntpUDP;
bool isSending = false;
int currentTime = 0, delayTime = 100, limitedTime = 3000;

void setup() {
  Serial.begin(115200);
  Wire.begin();
  mpu6050.begin();
  mpu6050.calcGyroOffsets(true);
	WiFiMulti.addAP(ssid, password);

	//WiFi.disconnect();
  Serial.print("WiFi connecting");
	while(WiFiMulti.run() != WL_CONNECTED) {
		delay(100);Serial.print(".");
	}
  Serial.println("WiFi connected successsfully!");

	// server address, port and URL
	webSocket.begin(ws_host, ws_port, ws_url);
	webSocket.onEvent(webSocketEvent);
	webSocket.setReconnectInterval(1000);
}

void loop() {
  mpu6050.update();
  webSocket.loop();
  String jsonData = "ping";
  
  // Create JSON payload
  if (isSending) {
    currentTime += delayTime;
    jsonData = "{\"ax\": " + String(mpu6050.getAccX()) +
                    ", \"ay\": " + String(mpu6050.getAccY()) +
                    ", \"az\": " + String(mpu6050.getAccZ()) +
                    ", \"gx\": " + String(mpu6050.getGyroAngleX()) +
                    ", \"gy\": " + String(mpu6050.getGyroAngleY()) +
                    ", \"gz\": " + String(mpu6050.getGyroAngleZ()) +
                    ", \"m\": " + String(millis());

    if (currentTime > limitedTime) {
      jsonData += ", \"offStatus\": 1}";
      isSending = false;
    } else {
      jsonData += "}";
    }
  } else {
    currentTime = 0;
  }
  Serial.println("Is sending: " + String(isSending) + ", Current time: " + String(currentTime));
  webSocket.sendTXT(jsonData);
  delay(delayTime);
}

// Xử lý sự kiện WebSocket
void webSocketEvent(WStype_t type, uint8_t* payload, size_t length) {
  switch (type) {
    case WStype_CONNECTED:
      Serial.println("WebSocket connected");
      break;
    case WStype_DISCONNECTED:
      Serial.println("WebSocket disconnected");
      break;
    case WStype_TEXT:
      if (strcmp((char*)payload, "on") == 0) {
        isSending = true;
      } else if (strcmp((char*)payload, "off") == 0) {
        isSending = false;
      }
      break;
    default:
      break;
  }
}