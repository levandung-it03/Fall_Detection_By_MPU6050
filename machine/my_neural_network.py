# COMMAND_LINES: pip install tensorflow keras numpy pandas scikit-learn
import os

import tensorflow as tf
from helpers.csv_interaction import readAndMergeAllCSV
from machine.machine_base import preProcessDataset, NUM_GESTURES, BATCH_SIZE, hex_to_c_array, CLASS_WEIGHTS
from machine.test_prediction import run_prediction

fall_backward_train_df, fall_backward_test_df = readAndMergeAllCSV("dataset/fall_backward/",
                                                                   "dataset_test/fall_backward/")
fall_forward_train_df, fall_forward_test_df = readAndMergeAllCSV("dataset/fall_forward/",
                                                                 "dataset_test/fall_forward/")
stand_train_df, stand_test_df = readAndMergeAllCSV("dataset/stand/",
                                                   "dataset_test/stand/")
chill_train_df, chill_test_df = readAndMergeAllCSV("dataset/chill/",
                                                 "dataset_test/chill/")

# Train-Test splitting
X_train, y_train = preProcessDataset(
    fall_backward_train_df,
    fall_forward_train_df,
    stand_train_df,
    chill_train_df,
)
X_val, y_val = preProcessDataset(
    fall_backward_test_df,
    fall_forward_test_df,
    stand_test_df,
    chill_test_df,
)

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
model.add(tf.keras.layers.Conv1D(filters=48, kernel_size=3, activation='relu',
                                 input_shape=(X_train.shape[1], X_train.shape[2])))
model.add(tf.keras.layers.Conv1D(filters=24, kernel_size=3, activation='relu'))
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
model.compile(optimizer='Adam', loss='categorical_crossentropy', metrics=['mae', 'accuracy'])  # Compiling Model with some testing configuration.
model.summary()  # Show built model

history = model.fit(X_train, y_train,
                    epochs=125, batch_size=BATCH_SIZE,
                    validation_data=(X_val, y_val),
                    class_weight=CLASS_WEIGHTS
                    )

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

import matplotlib.pyplot as plt
loss = history.history['loss']
val_loss = history.history['val_loss']
epochs = range(1, len(loss) + 1)
plt.plot(epochs, loss, 'g.', label='Training loss')
plt.plot(epochs, val_loss, 'b', label='Validation loss')
plt.title('Training and validation loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.show()

print(plt.rcParams["figure.figsize"])
run_prediction()