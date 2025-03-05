import pandas as pd

import os
import pandas as pd


def append_to_csv(file_path, new_data, columns):
    file_exists = os.path.exists(file_path)

    df = pd.DataFrame([new_data], columns=columns)

    df.to_csv(file_path, mode='a', header=not file_exists, index=False)
