#include <WiFiManager.h>
#include <Preferences.h>
#include <WebServer.h>
#include <cmath>
#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>

#include <HTTPClient.h>
#include <WiFi.h>
#include <WiFiMulti.h>

#include "gesture_model.h"
#include <TensorFlowLite_ESP32.h>
#include "tensorflow/lite/micro/all_ops_resolver.h"
#include "tensorflow/lite/micro/micro_error_reporter.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/system_setup.h"
#include "tensorflow/lite/schema/schema_generated.h"

#include "freertos/queue.h"

// TensorFlow Lite Globals
tflite::MicroErrorReporter tflErrorReporter;
tflite::AllOpsResolver tflOpsResolver;

const tflite::Model* tflModel = nullptr;
tflite::MicroInterpreter* tflInterpreter = nullptr;
TfLiteTensor* tflInputTensor = nullptr;
TfLiteTensor* tflOutputTensor = nullptr;

// Allocate tensor memory
constexpr int tensorArenaSize = 32 * 1024;
byte tensorArena[tensorArenaSize] __attribute__((aligned(16)));

// Gesture names
const char* GESTURES[] = { "fall", "lie", "sit", "run", "stand" };
#define NUM_GESTURES (sizeof(GESTURES) / sizeof(GESTURES[0]))

// MPU6050 Sensor
Adafruit_MPU6050 mpu;
QueueHandle_t mpuQueue;

// WiFi Client configuration
WiFiMulti WiFiMulti;
bool isReceiving = false;
bool isLocking = false;

// Queue Configuration
#define MAX_BUFFER_SAMPLES 60
#define PREDICT_WINDOW 20
#define SENSOR_DELAY 100  // 100ms per sample 

// Connection Configuration
String WIFI_SSID, WIFI_PASSWORD, FASTAPI_HOST, FASTAPI_PORT, USER_ID;
Preferences preferences;
WebServer server(80);
const char* custom_html = R"rawliteral(
  <!DOCTYPE html>
  <html lang="en">
  <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Configuration</title>
  </head>
  <body>
      <form>
          <fieldset style="width: 100%;e="margin-top: 20px;">
              <legend>Server Address</legend>
              <input style="border: none; outline: none; width: 100%;" name="serverAddress" type="text" />
          </fieldset>
          <fieldset style="margin-top: 20px;">
              <legend>Server Port</legend>
              <input style="border: none; outline: none; width: 100%;" name="serverPort" type="text" />
          </fieldset>
          <fieldset style="margin-top: 20px;">
              <legend>Registered Email</legend>
              <input style="border: none; outline: none; width: 100%;" name="registeredEmail" type="text" />
          </fieldset>
          <button type="submit" style="padding: 10px 0; width: 100%; margin-top: 20px;">Submit</button>
      </form>

      <script>
          const form = document.querySelector("form");
          form.addEventListener("submit", e => {
              e.preventDefault();

              const server = form.serverAddress.value;
              const port = form.serverPort.value;
              const email = form.registeredEmail.value;

              fetch(`http://${server}:${port}/api/public/v1/find-user-id-by-email?email=${email}`)
                  .then(res => res.ok ? res.json() : Promise.reject("Invalid Email"))
                  .then(data => {
                      const userId = data["user_id"];
                      
                      const formData = new URLSearchParams();
                      formData.append("serverAddress", server);
                      formData.append("serverPort", port);
                      formData.append("userId", userId);

                      fetch("/save", {
                          method: "POST",
                          headers: {
                              "Content-Type": "application/x-www-form-urlencoded"
                          },
                          body: formData.toString()
                      }).then(() => alert("Configuration Saved! Please reboot ESP32."));
                  })
                  .catch(err => alert(err));
          });
      </script>
  </body>
  </html>
)rawliteral";
void saveConfigToPrefs() {
  preferences.begin("config", false);
  preferences.putString("FASTAPI_HOST", FASTAPI_HOST);
  preferences.putString("FASTAPI_PORT", FASTAPI_PORT);
  preferences.putString("USER_ID", USER_ID);
  preferences.end();
}
void loadConfigFromPrefs() {
  preferences.begin("config", true);
  FASTAPI_HOST = preferences.getString("FASTAPI_HOST", "");
  FASTAPI_PORT = preferences.getString("FASTAPI_PORT", "");
  USER_ID = preferences.getString("USER_ID", "");
  Serial.println("Loaded Config: " + FASTAPI_HOST + "," + FASTAPI_PORT + "," + USER_ID);
  preferences.end();
}
void handleSave() {
  Serial.println("Saving Preferences...");
  FASTAPI_HOST = server.arg("serverAddress");
  FASTAPI_PORT = server.arg("serverPort");
  USER_ID = server.arg("userId");

  saveConfigToPrefs();
  server.send(200, "text/html", "<h2>Configuration Saved. Restart ESP32</h2>");
  delay(1000);
  ESP.restart();
}

void sendPostRequest(String api, String jsonData) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin("http://" + String(FASTAPI_HOST) + ":" + String(FASTAPI_PORT) + api);
    http.addHeader("Content-Type", "application/json");
    int httpResponseCode = http.POST(jsonData);

    if (httpResponseCode <= 0) {
      Serial.printf(http.errorToString(httpResponseCode).c_str());
    }
    http.end();
  }
}

String runInference(float input_data[PREDICT_WINDOW][6]) {
  for (int i = 0; i < PREDICT_WINDOW * 6; i++) {
    tflInputTensor->data.f[i] = ((float*)input_data)[i];
  }

  if (tflInterpreter->Invoke() != kTfLiteOk) {
    Serial.println("Inference failed!");
    return "error-prediction";
  }

  int indOfMaxScore = 0;
  Serial.println("Prediction Output:");
  for (int i = 0; i < NUM_GESTURES; i++) {
    Serial.print(GESTURES[i]);
    Serial.print(": ");
    Serial.println(tflOutputTensor->data.f[i], 6);
    if (tflOutputTensor->data.f[i] > tflOutputTensor->data.f[indOfMaxScore])
      indOfMaxScore = i;
  }
  return GESTURES[indOfMaxScore];
}

void predictWithModel(void* pvParameters) {
  float input_data[PREDICT_WINDOW][6];
  while (1) {
    if (uxQueueMessagesWaiting(mpuQueue) >= PREDICT_WINDOW) {
      isLocking = true;
      Serial.println("Running TensorFlow Lite Model...");
      // "isReceiving" just stop adding new data into current block (to avoid 1_block has 11_lines, instead of default 10_lines)
      // If acceleration is high, it still adds new data into buffer, but as data of the new block.
      isReceiving = false;
      for (int i = 0; i < PREDICT_WINDOW; i++) {
        if (xQueueReceive(mpuQueue, &input_data[i], 0) == pdFALSE) {
          Serial.println("Queue underflow, insufficient data!");
          return;
        }
      }
      
      sendPostRequest(
        "/api/public/v1/mpu-pred-cls",
        "{\"mpu_best_class\":\"" + runInference(input_data) + "\",\"user_id\":" + String(USER_ID) + "}"
        );
      Serial.println("Locking in 2s...");
      vTaskDelay(pdMS_TO_TICKS(2000));
      isLocking = false;
    }
    vTaskDelay(pdMS_TO_TICKS(SENSOR_DELAY));
  }
}

void readMPU6050Task(void* pvParameters) {
  float sample[6];
  sensors_event_t a, g, temp;

  while (1) {
    mpu.getEvent(&a, &g, &temp);
    // Checking every beginning of the next block(10lines), except the 1fs line (in total 60lines).
    // The current mpu6050 data is beginning of a block = mpuQueue has enough "n" blocks (10lines, 20lines, 30lines...).
    if (isLocking) {
      Serial.print(".");
    } else if (isReceiving
      || abs(a.acceleration.x) <= 8 || 12 <= abs(a.acceleration.x)
      || abs(a.acceleration.y) <= -3 || 3 <= abs(a.acceleration.y)
      || abs(a.acceleration.z) <= -3 || 3 <= abs(a.acceleration.z)) {
      
      if (isReceiving == false) {
        sendPostRequest("/api/public/v1/on-cam-pred-sts", "{\"user_id\":" + String(USER_ID) + "}");
        Serial.println();
      }
      isReceiving = true;

      sample[0] = a.acceleration.x;
      sample[1] = a.acceleration.y;
      sample[2] = a.acceleration.z;
      sample[3] = g.gyro.x;
      sample[4] = g.gyro.y;
      sample[5] = g.gyro.z;

      Serial.printf("x: %f, y: %f, z: %f", sample[0], sample[1], sample[2]);
      Serial.println();

      if (xQueueSend(mpuQueue, &sample, portMAX_DELAY) != pdPASS) {
        Serial.println("MPU6050 Queue is full, dropping data!");
      }
    }

    vTaskDelay(pdMS_TO_TICKS(SENSOR_DELAY));
  }
}

void threadsSetup() {
  mpuQueue = xQueueCreate(MAX_BUFFER_SAMPLES, sizeof(float[6]));

  xTaskCreatePinnedToCore(readMPU6050Task, "MPU6050 Task", 4096, NULL, 1, NULL, 0);
  xTaskCreatePinnedToCore(predictWithModel, "Model Prediction", 4096, NULL, 1, NULL, 1);
}

void predictionModelSetup() {
  // Import Model
  tflModel = tflite::GetModel(gesture_model);
  if (tflModel->version() != TFLITE_SCHEMA_VERSION) {
    Serial.println("Model schema mismatch!");
    while (1)
      ;
  }

  tflInterpreter = new tflite::MicroInterpreter(tflModel, tflOpsResolver, tensorArena, tensorArenaSize, &tflErrorReporter);
  tflInterpreter->AllocateTensors();
  tflInputTensor = tflInterpreter->input(0);
  tflOutputTensor = tflInterpreter->output(0);
}

void mpu6050Setup() {
  Wire.begin();
  if (!mpu.begin()) {
    Serial.println("MPU6050 initialization failed!");
    while (1)
      ;
  }
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
}

void localServerSetup() {
  WiFiManager wm;
  // Open AP if configurations is not existing.
  if (!wm.autoConnect("ESP32-Setup")) {
    Serial.println("Failed to connect");
    ESP.restart();
  }
  Serial.println("WiFi Connected");

  String ipAddress = WiFi.localIP().toString();
  if (!FASTAPI_HOST || String(FASTAPI_HOST).length() == 0) {
    server.on("/", HTTP_GET, []() {
      server.send(200, "text/html", custom_html);
    });

    server.on("/save", HTTP_POST, handleSave);
    server.begin();
    Serial.println("WebServer started, waiting for user config...");

    while (!FASTAPI_HOST || String(FASTAPI_HOST).length() == 0) {
      server.handleClient();
      delay(10);
    }
    server.close();
  }

  // Configurations is ready
  Serial.println("Pre-check loaded Config:");
  Serial.println(FASTAPI_HOST);
  Serial.println(FASTAPI_PORT);
  Serial.println(USER_ID);
}

void setup() {
  Serial.begin(115200);
  loadConfigFromPrefs();  // Load all stored params in preferences

  localServerSetup();
  mpu6050Setup();
  predictionModelSetup();
  threadsSetup();
}

void loop() {
  vTaskDelay(pdMS_TO_TICKS(1000));
  // Serial.println("Loaded Config: " + FASTAPI_HOST + "," + FASTAPI_PORT + "," + USER_ID);
  // delay(2000);
}

// #include <Preferences.h>
// Preferences preferences;
// void setup() {
//   preferences.begin("config", false);
//   preferences.clear();       // Clear all params in Preferences
//   preferences.end();
// }
// void loop() { delay(1000); }
