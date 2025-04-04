import os

import numpy as np
import pandas as pd

FEATURES = ['accX', 'accY', 'accZ', 'gyroX', 'gyroY', 'gyroZ']
LABEL = "label"
GESTURES = ["fall", "lie", "sit", "run", "stand"]
target_outputs = [
    [1, 0, 0, 0, 0],
    [0, 1, 0, 0, 0],
    [0, 0, 1, 0, 0],
    [0, 0, 0, 1, 0],
    [0, 0, 0, 0, 1]
]
BATCH_SIZE = 10 # Hard-set BATCH_SIZE as the length of each block action.

SAMPLES_PER_GESTURE = 24
NUM_GESTURES = len(GESTURES)

# Normalize data to fit in CNN Model to make model's values lie between [0;1]
def normalize_dataset(df):
    df[FEATURES[0]] = (df[FEATURES[0]] + 8) / 16
    df[FEATURES[1]] = (df[FEATURES[1]] + 8) / 16
    df[FEATURES[2]] = (df[FEATURES[2]] + 8) / 16
    df[FEATURES[3]] = (df[FEATURES[3]] + 2000) / 4000
    df[FEATURES[4]] = (df[FEATURES[4]] + 2000) / 4000
    df[FEATURES[5]] = (df[FEATURES[5]] + 2000) / 4000
    return df


def preProcessDataset(fall_dataf, lie_dataf, sit_dataf, run_dataf, stand_dataf):
    fall = normalize_dataset(fall_dataf)
    lie = normalize_dataset(lie_dataf)
    sit = normalize_dataset(sit_dataf)
    run = normalize_dataset(run_dataf)
    stand = normalize_dataset(stand_dataf)

    fall[LABEL] = [target_outputs[0]] * len(fall)
    lie[LABEL] = [target_outputs[1]] * len(lie)
    sit[LABEL] = [target_outputs[2]] * len(sit)
    run[LABEL] = [target_outputs[3]] * len(sit)
    stand[LABEL] = [target_outputs[4]] * len(sit)

    full_df = pd.concat([fall, lie, sit, run, stand], ignore_index=True)

    X = full_df[FEATURES].values  # Extract feature values
    X = X.reshape(X.shape[0], X.shape[1], 1)  # Change array's orientation from vertical to horizontal.
    y = np.array(full_df[LABEL].tolist())  # Convert labels to NumPy array

    return X, y

# Function: Convert some hex value into an array for C programming
def hex_to_c_array(hex_data, var_name):
    c_str = ''

    # Create header guard
    c_str += '#ifndef ' + var_name.upper() + '_H\n'
    c_str += '#define ' + var_name.upper() + '_H\n\n'

    # Add array length at top of file
    c_str += '\nunsigned int ' + var_name + '_len = ' + str(len(hex_data)) + ';\n'

    # Declare C variable
    c_str += 'unsigned char ' + var_name + '[] = {'
    hex_array = []
    for i, val in enumerate(hex_data):

        # Construct string from hex
        hex_str = format(val, '#04x')

        # Add formatting so each line stays within 80 characters
        if (i + 1) < len(hex_data):
            hex_str += ','
        if (i + 1) % 12 == 0:
            hex_str += '\n '
        hex_array.append(hex_str)

    # Add closing brace
    c_str += '\n ' + format(' '.join(hex_array)) + '\n};\n\n'

    # Close out header guard
    c_str += '#endif //' + var_name.upper() + '_H'

    return c_str