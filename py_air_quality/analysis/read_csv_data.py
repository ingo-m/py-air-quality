import pandas as pd


def read_csv_data(path_csv):
    """
    Read & process measurement data from csv file.

    Load csv data created from `py_air_quality.measurement.measurement.py`, and
    transform date string to datetime object, and return dataframe.

    """

    df = pd.read_csv(path_csv)

    df = df.replace(to_replace='None', value=np.nan)

    df = df.astype({'pm25': np.float32, 'pm10': np.float32})

    df['datetime'] = [
        datetime.fromtimestamp(x) for x in df['timestamp'].tolist()
        ]

    # Convert time from UTC to local time zone:
    from_zone = tz.tzutc()

    # Tell the datetime object that it's in UTC time zone:
    df['datetime'] = [
        x.replace(tzinfo=from_zone) for x in df['datetime'].tolist()
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
