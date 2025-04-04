#include <cmath>
#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

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
constexpr int tensorArenaSize = 64 * 1024;
byte tensorArena[tensorArenaSize] __attribute__((aligned(16)));

// Gesture names
const char* GESTURES[] = { "fall", "lie", "sit", "run", "stand" };
#define NUM_GESTURES (sizeof(GESTURES) / sizeof(GESTURES[0]))

// MPU6050 Sensor
Adafruit_MPU6050 mpu;
QueueHandle_t mpuQueue;

// Queue Configuration
#define MAX_BUFFER_SAMPLES 60
#define PREDICT_WINDOW 15
#define SENSOR_DELAY 100  // 100ms per sample
#define ACC_THRESHOLD 12.5

void runInference(float input_data[PREDICT_WINDOW][6]) {
  for (int i = 0; i < PREDICT_WINDOW * 6; i++) {
    tflInputTensor->data.f[i] = ((float*)input_data)[i];
  }

  if (tflInterpreter->Invoke() != kTfLiteOk) {
    Serial.println("Inference failed!");
    return;
  }

  Serial.println("Prediction Output:");
  for (int i = 0; i < NUM_GESTURES; i++) {
    Serial.print(GESTURES[i]);
    Serial.print(": ");
    Serial.println(tflOutputTensor->data.f[i], 6);
  }
}

void predictWithModel(void* pvParameters) {
  float input_data[PREDICT_WINDOW][6];
  while (1) {
    if (uxQueueMessagesWaiting(mpuQueue) < PREDICT_WINDOW) {
      vTaskDelay(pdMS_TO_TICKS(SENSOR_DELAY));
      continue;
    }

    for (int i = 0; i < PREDICT_WINDOW; i++) {
      if (xQueueReceive(mpuQueue, &input_data[i], 0) == pdFALSE) {
        Serial.println("Queue underflow, insufficient data!");
        return;
      }
    }

    Serial.println("Running TensorFlow Lite Model...");
    runInference(input_data);
    vTaskDelay(pdMS_TO_TICKS(500));
  }
}

void readMPU6050Task(void* pvParameters) {
  float sample[6];
  sensors_event_t a, g, temp;

  while (1) {
    mpu.getEvent(&a, &g, &temp);

    if ((abs(a.acceleration.x) + 10) <= ACC_THRESHOLD
      && (abs(a.acceleration.y) + 10) <= ACC_THRESHOLD
      && (abs(a.acceleration.z) + 10) <= ACC_THRESHOLD
      && (abs(a.acceleration.x) - 10) <= ACC_THRESHOLD
      && (abs(a.acceleration.y) - 10) <= ACC_THRESHOLD
      && (abs(a.acceleration.z) - 10) <= ACC_THRESHOLD
      && uxQueueMessagesWaiting(mpuQueue) == 0) {
      vTaskDelay(pdMS_TO_TICKS(SENSOR_DELAY));
      continue;
    }

    sample[0] = a.acceleration.x;
    sample[1] = a.acceleration.y;
    sample[2] = a.acceleration.z;
    sample[3] = g.gyro.x;
    sample[4] = g.gyro.y;
    sample[5] = g.gyro.z;
    
    Serial.printf("%f, %f, %f, %f, %f, %f\n", sample[0], sample[1], sample[2], sample[3], sample[4], sample[5]);

    if (xQueueSend(mpuQueue, &sample, portMAX_DELAY) != pdPASS) {
      Serial.println("Queue is full, dropping data!");
    }

    vTaskDelay(pdMS_TO_TICKS(SENSOR_DELAY));
  }
}

void setup() {
  Serial.begin(115200);
  Wire.begin();

  if (!mpu.begin()) {
    Serial.println("MPU6050 initialization failed!");
    while (1);
  }
  
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
  
  tflModel = tflite::GetModel(gesture_model);
  if (tflModel->version() != TFLITE_SCHEMA_VERSION) {
    Serial.println("Model schema mismatch!");
    while (1);
  }

  tflInterpreter = new tflite::MicroInterpreter(tflModel, tflOpsResolver, tensorArena, tensorArenaSize, &tflErrorReporter);
  tflInterpreter->AllocateTensors();
  tflInputTensor = tflInterpreter->input(0);
  tflOutputTensor = tflInterpreter->output(0);

  mpuQueue = xQueueCreate(MAX_BUFFER_SAMPLES, sizeof(float[6]));

  xTaskCreatePinnedToCore(readMPU6050Task, "MPU6050 Task", 4096, NULL, 1, NULL, 0);
  xTaskCreatePinnedToCore(predictWithModel, "Model Prediction", 4096, NULL, 1, NULL, 1);
}

void loop() {
  vTaskDelay(pdMS_TO_TICKS(1000));
}