#include <cmath>
#include <Arduino.h>
#include <Wire.h>
#include <MPU6050_tockn.h>

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
MPU6050 mpu6050(Wire);
QueueHandle_t mpuQueue;

// Queue Configuration
#define MAX_BUFFER_SAMPLES 60
#define PREDICT_WINDOW 15
#define SENSOR_DELAY 100  // 100ms per sample
#define ACC_THRESHOLD 1.15

void runInference(float input_data[PREDICT_WINDOW][6]) {
  // Copy data into the input tensor
  for (int i = 0; i < PREDICT_WINDOW * 6; i++) {
    tflInputTensor->data.f[i] = ((float*)input_data)[i];
  }

  // Run inference
  if (tflInterpreter->Invoke() != kTfLiteOk) {
    Serial.println("Inference failed!");
    return;
  }

  // Display predictions
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

    // Retrieve first 30 samples and remove them from buffer
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
  bool isNotReceiving[1];

  while (1) {
    // Read MPU6050 values
    mpu6050.update();

    isNotReceiving[0] = abs(mpu6050.getAccX()) <= ACC_THRESHOLD
      && abs(mpu6050.getAccY()) <= ACC_THRESHOLD
      && abs(mpu6050.getAccZ()) <= ACC_THRESHOLD
      && uxQueueMessagesWaiting(mpuQueue) == 0;

    if (isNotReceiving[0]) {
      vTaskDelay(pdMS_TO_TICKS(SENSOR_DELAY));
      continue;
    } else {
      // Save as Buffer[[accX, accY, accZ, gyroX, gyroY, gyroZ],...]
      // Instead of required predicted datatype of model: [[[accX], [accY], [accZ], [gyroX], [gyroY], [gyroZ]]] - each line.
      // To meet the memory size demand
      sample[0] = mpu6050.getAccX();
      sample[1] = mpu6050.getAccY();
      sample[2] = mpu6050.getAccZ();
      sample[3] = mpu6050.getGyroX();
      sample[4] = mpu6050.getGyroY();
      sample[5] = mpu6050.getGyroZ();
      Serial.print(sample[0]);Serial.print(",");
      Serial.print(sample[1]);Serial.print(",");
      Serial.print(sample[2]);Serial.print(",");
      Serial.print(sample[3]);Serial.print(",");
      Serial.print(sample[4]);Serial.print(",");
      Serial.println(sample[5]);
      // Add sample to queue
      if (xQueueSend(mpuQueue, &sample, portMAX_DELAY) != pdPASS) {
        Serial.println("Queue is full, dropping data!");
      }
    }
    vTaskDelay(pdMS_TO_TICKS(SENSOR_DELAY));  // Delay 100ms
  }
}

void setup() {
  Serial.begin(115200);
  Wire.begin();

  // Load TensorFlow model
  tflModel = tflite::GetModel(gesture_model);
  if (tflModel->version() != TFLITE_SCHEMA_VERSION) {
    Serial.println("Model schema mismatch!");
    while (1);
  }

  // Create an interpreter
  tflInterpreter = new tflite::MicroInterpreter(tflModel, tflOpsResolver, tensorArena, tensorArenaSize, &tflErrorReporter);
  tflInterpreter->AllocateTensors();
  tflInputTensor = tflInterpreter->input(0);
  tflOutputTensor = tflInterpreter->output(0);

  // Initialize MPU6050
  mpu6050.begin();
  mpu6050.calcGyroOffsets(true);

  // Create queue for MPU data (buffer holds max 60 samples)
  mpuQueue = xQueueCreate(MAX_BUFFER_SAMPLES, sizeof(float[6]));

  // Start tasks
  xTaskCreatePinnedToCore(readMPU6050Task, "MPU6050 Task", 4096, NULL, 1, NULL, 0);
  xTaskCreatePinnedToCore(predictWithModel, "Model Predection", 4096, NULL, 1, NULL, 1);
}

void loop() {
  // Keep FreeRTOS active
  vTaskDelay(pdMS_TO_TICKS(1000));
}
