#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WORK IN PROGRESS

Test for the effect of an air purifier (filter) on indoor air quality.

To assess the effect of the filter, we combine data from external & internal
sources for analysis. The external data is the air quality index based on
measurements at outdoor measurement stations (obtained from aqicn.org). The
internal data source is an SDS011 particulate sensor.

The data is read data from csv files, processed, and plots are created.
Processed data is exported for further analysis in R.

"""

import os

import pandas as pd
import seaborn as sns
from datetime import datetime, timedelta, time

from read_csv_data import read_csv_data


# ------------------------------------------------------------------------------
# *** Define paths

# Path of indoor air quality measurement - baseline without air filter:
path_csv_indoor_baseline = '/home/john/PhD/GitHub/py-air-quality/py_air_quality/data/baseline_measurement.csv'

# Path of indoor air quality measurement - with air filter:
path_csv_indoor_filter = '/home/john/PhD/GitHub/py-air-quality/py_air_quality/data/measurement_with_filter.csv'

# Path of external air quality measurement data, obtained from
# https://aqicn.org/data-platform/covid19/
path_csv_external = '/media/ssd_dropbox/Dropbox/Raspberry_Pi/air_quality_external_data/waqi-covid19-airqualitydata-2020.csv'

# Output directory for plot & processed csv files (to be imported into R for
# analysis):
path_out = '/home/john/PhD/GitHub/py-air-quality/py_air_quality/data/'

# Which pollutant to analyse ('pm25' or 'pm10'):
pollutant = 'pm25'


# ------------------------------------------------------------------------------
# *** Read data from external data source

# Read and process data from external source (official outdoor measurement
# station).
df_external = pd.read_csv(path_csv_external, sep=',', comment='#')

# Select relevant data:
df_external = df_external.loc[df_external['City'] == 'Berlin']
# df_external = df_external.loc[df_external['Specie'].isin(['pm25', 'pm10'])]
df_external = df_external.loc[df_external['Specie'] == pollutant]

date_format = '%Y-%m-%d'
df_external['Date'] = \
    [datetime.strptime(x, date_format) for x in df_external['Date'].tolist()]

# The data from aqicn.org has one data point per day. The datetime defaults to
# midnight (e.g. `2021-03-26 00:00:00`), but the corresponding measurement is
# average for the entrie day (and the original data is without time, e.g.
# '2021-03-26'). Add 12 hours, so that the epoch timestamp will correspond to
# the (temporal) centre of the measurement period.
df_external['Date'] = \
    [(x + timedelta(hours=12.0)) for x in df_external['Date'].tolist()]

# Datetime comparisons are error-prone with pandas; rather use epoch timestamp.
df_external['timestamp'] = \
    [round(x.timestamp()) for x in df_external['Date'].tolist()]

df_external = df_external[['Date', 'timestamp', 'median']]
df_external = df_external.rename(
    columns={'median': (pollutant + '_external'),
             'Date': 'date'}
    )

# Remove hours, minutes, and seconds from date:
df_external['date'] = [x.date() for x in df_external['date'].tolist()]


# ------------------------------------------------------------------------------
# *** Read data from internal data source

# Read internal measurement data from csv file:
df_baseline = read_csv_data(path_csv_indoor_baseline)
df_filter = read_csv_data(path_csv_indoor_filter)

# Concatenate data from internal source (i.e. both control condition without
# filter, and experimental condition with filter:
df_baseline['filter'] = False
df_filter['filter'] = True
df_internal = pd.concat([df_baseline, df_filter], axis=0, ignore_index=True)

df_internal = \
    df_internal[['timestamp', 'datetime', pollutant, 'filter', 'weekend']]
df_internal = df_internal.rename(columns={pollutant: (pollutant + '_internal')})


# ------------------------------------------------------------------------------
# ***

# Get date without hours, minutes, and seconds, so that we can calculate mean
# pollutant concentration per day:
df_internal['date'] = [x.date() for x in df_internal['datetime'].tolist()]

# The external data (from aqicn.org) only has a temporal resolution of one
# measurement per day (median pollutant concentration per day). For comparison,
# take the mean across each day for the internal data.
df_internal_daily = df_internal.groupby(['date']).mean()
df_internal_daily = df_internal_daily.reset_index(level=0, drop=False)

# Remove day where condition changed from no filter to filter:
df_internal_daily = \
    df_internal_daily.loc[df_internal_daily['filter'].isin([0.0, 1.0])]

# Set the epoch timestamp to noon of the corresponding day, so as to be able to
# match internal and external data:
df_internal_daily['date'] = \
    [datetime.combine(x, time(12)) for x in df_internal_daily['date'].tolist()]
df_internal_daily['timestamp'] = \
    [round(x.timestamp()) for x in df_internal_daily['date'].tolist()]

# Merge internal and external data (with daily temporal resolution):
df_internal_daily = df_internal_daily.sort_values('timestamp')
df_external = df_external.sort_values('timestamp')
df_daily = pd.merge_asof(
    df_internal_daily,
    df_external[['timestamp', 'pm25_external']],
    on='timestamp',
    direction='nearest',
    )

# External and internal data are not on the same scale; divide each by its
# maximum.
df_daily['pm25_external'] = (
    df_daily['pm25_external']
    / df_daily.loc[df_daily['filter'] == 0.0]['pm25_external'].mean()
    )

df_daily['pm25_internal'] = (
    df_daily['pm25_internal']
    / df_daily.loc[df_daily['filter'] == 0.0]['pm25_internal'].mean()
    )

# Wide to long format:

df_tmp_ext = \
    df_daily[['date', 'timestamp', 'pm25_external', 'filter', 'weekend']]
df_tmp_ext = df_tmp_ext.rename(columns={'pm25_external': pollutant})
df_tmp_ext['source'] = 'external'

df_tmp_int = \
    df_daily[['date', 'timestamp', 'pm25_internal', 'filter', 'weekend']]
df_tmp_int = df_tmp_int.rename(columns={'pm25_internal': pollutant})
df_tmp_int['source'] = 'internal'

df_daily = pd.concat([df_tmp_ext, df_tmp_int], axis=0, ignore_index=True)




# ------------------------------------------------------------------------------
# ***

colours = [
    [float(x) / 255.0 for x in [255, 0, 102, 255]],
    [float(x) / 255.0 for x in [44, 178, 252, 255]],
    ]


graph = sns.catplot(
    data=df_daily,
    kind='bar',
    x='source',
    y='pm25',
    hue='filter',
    ci='sd',
    palette=colours,
    )

# Axis layout:
graph.axes[0][0].set_xlabel(None)
graph.axes[0][0].set_ylabel('Air pollutiuon [a.u.]', fontsize=18)
graph.axes[0][0].set_yticks([0.0, 0.5, 1.0, 1.5])
graph.axes[0][0].set_xticklabels(['Outdoors', 'Indoors'])
graph.axes[0][0].tick_params(labelsize=16)

# Adjust legend:
graph.legend.set_title('Filter', prop={'size': 16})
for i in range(2):
    legend_text = graph.legend.texts[i].get_text()
    if legend_text == '0.0':
        graph.legend.texts[i].set_text('Off')
        graph.legend.texts[i].set_fontsize(16)
    elif legend_text == '1.0':
        graph.legend.texts[i].set_text('On')
        graph.legend.texts[i].set_fontsize(16)

# Save figure:
graph.savefig(os.path.join(path_out, 'filter_bar_plot.png'),
               dpi=200.0,
               bbox_inches='tight',
               )





# ------------------------------------------------------------------------------
# *** Merge data from external & internal data source

df_internal = df_internal.sort_values('timestamp')
df_external = df_external.sort_values('timestamp')

# Merge data from external & internal data source on epoch timestamp, using the
# nearest available datapoint from external measurement (which has lower
# temporal resolution).
df = pd.merge_asof(
    df_internal,
    df_external,
    on='timestamp',
    direction='nearest',
    )

# Exclude nan:
df = df[df['pm25_internal'].notna()]
df = df[df['pm25_external'].notna()]

df.to_csv(
    os.path.join(path_out, 'preprocessed.csv'),
    sep=';',
    index=False,
    )
