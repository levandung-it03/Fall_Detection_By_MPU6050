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

def readAndMergeAllCSV(train_url, test_url):
    train_url = os.path.join(root_folder, train_url)
    test_url = os.path.join(root_folder, test_url)

    train_files = [file for file in os.listdir(train_url) if file.endswith(".csv")]
    test_files = [file for file in os.listdir(test_url) if file.endswith(".csv")]

    train_dfs = [pd.read_csv(train_url + file) for file in train_files]
    test_dfs = [pd.read_csv(test_url + file) for file in test_files]

    merged_train_df = pd.concat(train_dfs, ignore_index=True)  # Merge all DataFrames
    merged_test_df = pd.concat(test_dfs, ignore_index=True)  # Merge all DataFrames
    return merged_train_df, merged_test_df
