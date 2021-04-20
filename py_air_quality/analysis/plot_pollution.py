#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
To continuously refresh plots via cron tab:

*/5 * * * * /home/pi/py_main/bin/python /home/pi/github/py-air-quality/py_air_quality/analysis/plot_pollution.py

"""


import numpy as np
import pandas as pd
import seaborn as sns
from dateutil import tz
from datetime import datetime, timedelta
from time import sleep


# ------------------------------------------------------------------------------
# *** Define parameters

path_csv = '/home/pi/air_quality/baseline_measurement.csv'

path_plot = '/home/pi/air_quality/baseline_{}.png'


# ------------------------------------------------------------------------------
# *** Read & preprocess data

# Wait for the measurement to finish (assuming that the measurement is done at
# the same frequency, through cron tab).
sleep(60)

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

# Current, local time:
local_now = datetime.now(tz=to_zone)
local_now_hour = (
    float(local_now.hour)
    + (float(local_now.minute) / 60.0)
    )

# Add column for most recent datapoints (True for all datapoints that were
# measured within the last 24 hours):
utc_now = datetime.utcnow()
yesterday_epoch = int(round((utc_now - timedelta(hours=24.0)).timestamp()))
df['last_24_h'] = np.greater_equal(df['timestamp'].values, yesterday_epoch)

# Create a timestamp ranging between 0 and 24:
hour = [float(x.hour) for x in df['datetime'].tolist()]
minute = [float(x.minute) for x in df['datetime'].tolist()]
daytime = np.add(hour, np.divide(minute, 60.0))
daytime = np.around(daytime, decimals=3)
df['daytime'] = daytime

# Currently, there is one row per measurement, with separate columns for the two
# y variables. We need to change this to 'long format', with one row per
# datapoint.
df_pm25 = df[['daytime', 'weekend', 'last_24_h', 'pm25']]
df_pm10 = df[['daytime', 'weekend', 'last_24_h', 'pm10']]
df_pm25 = df_pm25.rename(columns={'pm25': 'pollution'})
df_pm10 = df_pm10.rename(columns={'pm10': 'pollution'})
df_pm25['type'] = 'pm25'
df_pm10['type'] = 'pm10'
df = pd.concat([df_pm25, df_pm10], axis=0, ignore_index=True)


# ------------------------------------------------------------------------------
# *** Create plots

df_weekend = df.loc[df['weekend'] == True]
df_weekday = df.loc[df['weekend'] == False]
df_last_24_h = df.loc[df['last_24_h'] == True]

dict_plot = {'weekend': df_weekend,
             'weekday': df_weekday,
             'last_24_h': df_last_24_h,
             }

colours = [
    [float(x) / 255.0 for x in [255, 212, 42, 255]],
    [float(x) / 255.0 for x in [42, 206, 252, 255]],
    ]

# Create separate plots for weekdays (Monday to Friday) and weekend (Saturday
# and Sunday), which will be saved in separate figures.
for plot_name, df_plot in dict_plot.items():

    graph = sns.lineplot(
        x='daytime',
        y='pollution',
        hue='type',
        data=df_plot,
        estimator='mean',
        ci='sd',
        #palette=colours,
        err_style='band',
        err_kws={'alpha': 0.05,
                 'linewidth': 0.0,
                 }
        )

    graph.axes.set_xlim(-0.5, 24.5)
    graph.axes.set_ylim(0.0, 21.0)

    # Axis layout:
    graph.axes.set_xlabel('Time [hour]', fontsize=14)
    graph.axes.set_ylabel('Pollutant concentration [μg/m3]', fontsize=14)
    graph.axes.set_xticks([0.0, 6.0, 12.0, 18.0, 24.0])
    graph.axes.tick_params(labelsize=14)
    graph.axes.spines['top'].set_visible(False)
    graph.axes.spines['right'].set_visible(False)

    # Vertical line representing current time:
    if plot_name == 'last_24_h':
        graph.axvline(x=local_now_hour,
                      ymin=0,
                      ymax=1,
                      color=[0.75, 0.75, 0.75],
                      linewidth=0.75,
                      )

    # Adjust legend:
    graph.legend_.set_title(None)
    graph.legend_.set_frame_on(False)
    for i in range(2):
        legend_text = graph.legend_.texts[i].get_text()
        if legend_text == 'pm25':
            graph.legend_.texts[i].set_text('$PM_{2.5}$')
        elif legend_text == 'pm10':
            graph.legend_.texts[i].set_text('$PM_{10}$')

    # Save figure:
    figure = graph.get_figure()
    figure.savefig(path_plot.format(plot_name),
                   dpi=160.0,
                   bbox_inches='tight',
                   )

    figure.clf()