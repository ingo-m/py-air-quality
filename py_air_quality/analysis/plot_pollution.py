#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import numpy as np
import pandas as pd
import seaborn as sns
from dateutil import tz
from datetime import datetime


# ------------------------------------------------------------------------------
# *** Define parameters

path_csv = 'baseline_measurement.csv'

path_plot = 'baseline.png'


# ------------------------------------------------------------------------------
# *** Read & preprocess data

df = pd.read_csv(path_csv)

df = df.replace(to_replace='None', value=np.nan)

df = df.astype({'pm25': np.float32, 'pm10': np.float32})

df['datetime'] = [datetime.fromtimestamp(x) for x in df['timestamp'].tolist()]


# Convert time from UTC to local time zone:
from_zone = tz.tzutc()
to_zone = tz.tzlocal()
# Tell the datetime object that it's in UTC time zone:
df['datetime'] = [x.replace(tzinfo=from_zone) for x in df['datetime'].tolist()]

# Convert datetime to local time:
df['datetime'] = [x.astimezone(to_zone) for x in df['datetime'].tolist()]

# Add column for hour of the day:

# Add column for weekday (where Monday is 0 and Sunday is 6):
df['weekday'] = [x.weekday() for x in df['datetime'].tolist()]

# Add column for weekend (binary; 0 = weekday, 1 = weekend):
df['weekend'] = [(5 <= x) for x in df['weekday'].tolist()]

# Create a timestamp ranging between 0 and 24:
hour = [float(x.hour) for x in df['datetime'].tolist()]
minute = [float(x.minute) for x in df['datetime'].tolist()]
daytime = np.add(hour, np.divide(minute, 60.0))
daytime = np.around(daytime, decimals=3)
df['daytime'] = daytime

# ------------------------------------------------------------------------------
# *** Create plot

# TODO pm25 and pm10 in one plot, separate plots for weekday / weekend

plot = sns.lineplot(
    x='daytime',
    y='pm10',
    hue='weekend',
    # style="event",
    data=df,
    )


df.dtypes
