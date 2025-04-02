# COMMAND_LINES: pip install tensorflow keras numpy pandas scikit-learn
import os

import tensorflow as tf

from helpers.csv_interaction import readAndMergeAllCSVsFromDatasetFolderWithTrainTest
from machine.machine_base import preProcessDataset, NUM_GESTURES, BATCH_SIZE, hex_to_c_array

fall_train_df, fall_test_df = readAndMergeAllCSVsFromDatasetFolderWithTrainTest("dataset/fall/", train_rate=0.8)
lie_train_df, lie_test_df = readAndMergeAllCSVsFromDatasetFolderWithTrainTest("dataset/lie/", train_rate=0.8)
sit_train_df, sit_test_df = readAndMergeAllCSVsFromDatasetFolderWithTrainTest("dataset/sit/", train_rate=0.8)
run_train_df, run_test_df = readAndMergeAllCSVsFromDatasetFolderWithTrainTest("dataset/run/", train_rate=0.8)
stand_train_df, stand_test_df = readAndMergeAllCSVsFromDatasetFolderWithTrainTest("dataset/stand/", train_rate=0.8)

# Train-Test splitting
X_train, y_train = preProcessDataset(fall_train_df, lie_train_df, sit_train_df, run_train_df, stand_train_df)
X_val, y_val = preProcessDataset(fall_test_df, lie_test_df, sit_test_df, run_test_df, stand_test_df)

# Create Model infrastructure with Sequence Layers (1 InpLay, 1 HidLay, 1 OutLay)
model = tf.keras.Sequential()
"""
    ReLU Option -> Decline Negative Values and rise non-linear feature (Anther option is sigmoid,...).
    input_shape -> (length_data, feature)
    kernel_size -> Each Filters has size(3) weights with 1 bias.
                -> y = σ(w1.a1 + w2.a2 + w3.a3 + b).
                -> Num of Weights: 3 + 1(bias)
    Filters(16) -> This feature directly affect to feature determination's model.
                -> Ex: Filter_1(acc_increase), Filter_2(acc_increase_and_drop), Filter_3(acc_drop),...
                -> Total Weights = (weights x features + 1_bias) x filters_num = (3x6 + 1)x16 = 304.
    pool_size(feature of CNN more than NeuralNetwork):
    -> Get 1 greatest value of each 2 values in a block to decrease calculating time.
"""
model.add(tf.keras.layers.Conv1D(filters=16, kernel_size=4, activation='relu',
                                 input_shape=(X_train.shape[1], X_train.shape[2])))
model.add(tf.keras.layers.MaxPooling1D(pool_size=2, strides=1, padding='same'))
model.add(tf.keras.layers.Conv1D(filters=16, kernel_size=2, activation='relu'))
model.add(tf.keras.layers.MaxPooling1D(pool_size=2, strides=1, padding='same'))
"""
    - layers.Flatten
    -> flatting 3D data from previous calculation to 1D.
    -> (batch_size, 176, 16) to (batch_size, 176*16) = (batch_size, 2816)
"""
model.add(tf.keras.layers.Flatten())
"""
    - This is Output Layer (Fully Connected Layer with "NUM_GESTURES" Neurons).
    - Ex: Predicted Values of each action: [0.1, 0.05, 0.05, 0.7, 0.1]
        -> It belongs to the 4'th action which has the greatest value 0.7
"""
model.add(tf.keras.layers.Dense(NUM_GESTURES, activation='softmax'))
model.compile(optimizer='Adam', loss='mse', metrics=['mae'])  # Compiling Model with some testing configuration.
model.summary()  # Show built model

history = model.fit(X_train, y_train, epochs=75, batch_size=BATCH_SIZE, validation_data=(X_val, y_val))

# Convert the model to the TensorFlow Lite format without quantization
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()

# Save the model to disk
open("gesture_model.tflite", "wb").write(tflite_model)

basic_model_size = os.path.getsize("gesture_model.tflite")
print("Model is %d bytes" % basic_model_size)

c_model_name = 'gesture_model'
with open(c_model_name + '.h', 'w') as file:
    file.write(hex_to_c_array(tflite_model, c_model_name))