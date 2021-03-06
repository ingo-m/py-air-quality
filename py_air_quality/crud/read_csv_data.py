import numpy as np
import pandas as pd
from dateutil import tz
from datetime import datetime, timezone


def read_csv_data(path_csv, newest_db_timestamp=None):
    """
    Read & process measurement data from csv file.
    Load csv data created from `py_air_quality.measurement.measurement.py`, and
    transform date string to datetime object, and return dataframe.
    """

    df = pd.read_csv(path_csv)

    if newest_db_timestamp:
        # Select new measurements that are not yet in database:
        df = df.loc[df['timestamp'] > newest_db_timestamp]

    df = df.replace(to_replace='None', value=np.nan)

    df = df.astype({'pm25': np.float64, 'pm10': np.float64})

    df['datetime'] = [
        datetime.fromtimestamp(x, tz=timezone.utc) for x in
        df['timestamp'].tolist()
        ]

    # Convert datetime to local time:
    df['datetime'] = [
        x.astimezone(tz.tzlocal()) for x in df['datetime'].tolist()
        ]

    # Add column for hour of the day:

    # Add column for weekday (where Monday is 0 and Sunday is 6):
    df['weekday'] = [x.weekday() for x in df['datetime'].tolist()]

    # Add column for weekend (binary; 0 = weekday, 1 = weekend):
    df['weekend'] = [(5 <= x) for x in df['weekday'].tolist()]

    return df
