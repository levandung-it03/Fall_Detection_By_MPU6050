import numpy as np
import pandas as pd

FEATURES = ['accX', 'accY', 'accZ', 'gyroX', 'gyroY', 'gyroZ']
LABEL = "label"
GESTURES = [
    "fall_backward",
    "fall_forward",
    "stand",
    "chill"
]
CLASS_WEIGHTS = {
    0: 2.0,
    1: 1.5,
    2: 1.0,
    3: 1.0
}
target_outputs = [
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 1, 0],
    [0, 0, 0, 1],
]
BATCH_SIZE = 15  # Hard-set BATCH_SIZE as the length of each block action.

NUM_GESTURES = len(GESTURES)


# Normalize data to fit in CNN Model to make model's values lie between [0;1]
def normalize_dataset(df):
    df[FEATURES[0]] = (df[FEATURES[0]] + 40) / 80
    df[FEATURES[1]] = (df[FEATURES[1]] + 40) / 80
    df[FEATURES[2]] = (df[FEATURES[2]] + 40) / 80
    df[FEATURES[3]] = (df[FEATURES[3]] + 40) / 80
    df[FEATURES[4]] = (df[FEATURES[4]] + 40) / 80
    df[FEATURES[5]] = (df[FEATURES[5]] + 40) / 80
    return df


def preProcessDataset(
        fall_back_train_df,
        fall_forward_train_df,
        stand_train_df,
        chill_train_df,
):
    fall_back_train_df = normalize_dataset(fall_back_train_df)
    fall_forward_train_df = normalize_dataset(fall_forward_train_df)
    stand = normalize_dataset(stand_train_df)
    chill = normalize_dataset(chill_train_df)

    fall_back_train_df[LABEL] = [target_outputs[0]] * len(fall_back_train_df)
    fall_forward_train_df[LABEL] = [target_outputs[1]] * len(fall_forward_train_df)
    stand[LABEL] = [target_outputs[2]] * len(stand)
    chill[LABEL] = [target_outputs[3]] * len(chill)

    full_df = pd.concat([
        fall_back_train_df,
        fall_forward_train_df,
        stand,
        chill
    ], ignore_index=True)

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
