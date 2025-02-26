import pandas as pd

def append_to_csv(file_path, new_data):
    df = pd.DataFrame([new_data])
    df.to_csv(file_path, mode='a', header=False, index=False)
