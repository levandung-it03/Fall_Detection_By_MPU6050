import tensorflow.lite as tflite
import numpy as np

from helpers.csv_interaction import readSpecifiedTypeCSV
from machine.machine_base import normalize_dataset, LABEL, target_outputs, FEATURES, GESTURES

# Load the TensorFlow Lite model
interpreter = tflite.Interpreter(model_path="gesture_model.tflite")
interpreter.allocate_tensors()

# Get input and output tensor details
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
input_index = input_details[0]['index']
output_index = output_details[0]['index']

# Load and preprocess the dataset
fall_predict = readSpecifiedTypeCSV("dataset/fall/fall11.csv")  # Load CSV file
fall_predict = normalize_dataset(fall_predict)  # Normalize the dataset

# Assign the correct label (assuming target_outputs[0] corresponds to "fall")
fall_predict[LABEL] = [target_outputs[0]] * len(fall_predict)

# Extract features and labels
X_predict = fall_predict[FEATURES].values.astype(np.float32)  # Get feature values as a NumPy array

# Run inference for each sample
appearances = [0] * len(FEATURES)
output_data_arr = []

for i in range(len(X_predict)):
    sample = X_predict[i].reshape(1, 6, 1)

    # Set model input tensor
    interpreter.set_tensor(input_details[0]['index'], sample)

    # Run inference
    interpreter.invoke()

    # Get output tensor
    output_data = interpreter.get_tensor(output_details[0]['index'])
    output_data_arr.append(output_data[0])

    # Store prediction
    appearances[np.argmax(output_data[0])] += 1


# Print results
print("output arr: ", output_data_arr)
print("appearances: ", appearances)
print("Predicted Labels:", GESTURES[np.argmax(appearances)])


