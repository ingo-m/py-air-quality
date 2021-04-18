#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import numpy as np
import pandas as pd
import seaborn as sns
from dateutil import tz
from datetime import datetime


# ------------------------------------------------------------------------------
# *** Define parameters

path_csv = '/home/john/PhD/GitHub/py-air-quality/py_air_quality/data/baseline_measurement.csv'

path_plot = '/media/ssd_dropbox/Dropbox/Raspberry_Pi/air_pollution_plots/baseline_{}.png'


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

# Currently, there is one row per measurement, with separate columns for the two
# y variables. We need to change this to 'long format', with one row per
# datapoint.
df_pm25 = df[['daytime', 'weekend', 'pm25']]
df_pm10 = df[['daytime', 'weekend', 'pm10']]
df_pm25 = df_pm25.rename(columns={'pm25': 'pollution'})
df_pm10 = df_pm25.rename(columns={'pm10': 'pollution'})
df_pm25['type'] = 'pm25'
df_pm10['type'] = 'pm10'
df = pd.concat([df_pm25, df_pm10], axis=0, ignore_index=True)


# ------------------------------------------------------------------------------
# *** Create plots

df_weekend = df.loc[df['weekend'] == True]
df_weekday = df.loc[df['weekend'] == False]

dict_plot = {'weekend': df_weekend,
             'weekday': df_weekday,
             }

# Create separate plots for weekdays (Monday to Friday) and weekend (Saturday
# and Sunday), which will be saved in separate figures.
for plot_name, df_plot in dict_plot.items():

    graph = sns.lineplot(
        x='daytime',
        y='pollution',
        hue='type',
        data=df_plot,
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
