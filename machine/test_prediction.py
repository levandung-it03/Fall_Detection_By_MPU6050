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

def predict(url):
    # Load and preprocess the dataset
    data = readSpecifiedTypeCSV(url)  # Load CSV file
    data = normalize_dataset(data)  # Normalize the dataset

    # Assign the correct label (assuming target_outputs[0] corresponds to "fall")
    data[LABEL] = [target_outputs[0]] * len(data)

    # Extract features and labels
    X_predict = data[FEATURES].values.astype(np.float32)  # Get feature values as a NumPy array

    # Run inference for each sample
    appearances = [0] * len(GESTURES)
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
    print("From: ", url, ", appearances: ", appearances, " - Predicted Labels:", GESTURES[np.argmax(appearances)])


def run_prediction():
    predict("testing/fall_forward.csv")
    predict("testing/fall_forward2.csv")
    predict("testing/fall_back.csv")
    predict("testing/fall_back2.csv")
    predict("testing/stand.csv")
    predict("testing/stand2.csv")
    predict("testing/chill.csv")
    predict("testing/chill2.csv")

