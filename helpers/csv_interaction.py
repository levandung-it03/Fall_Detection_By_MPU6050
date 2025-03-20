import os
import random

import pandas as pd

root_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def append_to_csv(file_path, new_data, columns):
    file_exists = os.path.exists(file_path)

    df = pd.DataFrame([new_data], columns=columns)

    df.to_csv(file_path, mode='a', header=not file_exists, index=False)


def readSpecifiedTypeCSV(url):
    return pd.read_csv(os.path.join(root_folder, url), skip_blank_lines=True)


def readAndMergeAllCSVsFromDatasetFolder(url):
    all_dfs = []  # List to store individual DataFrames

    # Iterate through all files in the given folder
    for file in os.listdir(url):
        if file.endswith(".csv"):  # Check if file is a CSV
            df = readSpecifiedTypeCSV(file)  # Read CSV into DataFrame
            all_dfs.append(df)  # Add DataFrame to the list

    if all_dfs:
        merged_df = pd.concat(all_dfs, ignore_index=True)  # Merge all DataFrames
        return merged_df
    else:
        return None  # Return None if no CSV files are found

def readAndMergeAllCSVsFromDatasetFolderWithTrainTest(url, train_rate=1):
    url = os.path.join(root_folder, url)

    all_files = [file for file in os.listdir(url) if file.endswith(".csv")]

    selected_indices = set(random.sample(range(len(all_files)), int(train_rate * len(all_files))))

    merged_test_files = []   # Selected `n` files for testing
    merged_train_files = []  # Remaining files for training

    for index, file in enumerate(all_files):
        file_path = os.path.join(url, file)
        df = pd.read_csv(file_path)  # Read CSV

        if index in selected_indices:
            merged_train_files.append(df)
        else:
            merged_test_files.append(df)

    print(url, "selected indices: ", selected_indices)
    if (train_rate == 1 and merged_train_files) or (merged_test_files and merged_train_files):
        merged_train_df = pd.concat(merged_train_files, ignore_index=True)  # Merge all DataFrames
        merged_test_df = pd.concat(merged_test_files, ignore_index=True)  # Merge all DataFrames
        return merged_train_df, merged_test_df
    else:
        return None, None
