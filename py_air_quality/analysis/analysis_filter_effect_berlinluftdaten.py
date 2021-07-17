#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WORK IN PROGRESS

Test for the effect of an air purifier (filter) on indoor air quality.

To assess the effect of the filter, we combine data from external & internal
sources for analysis. The external data are hourly measurements from an outdoor
measurement station (obtained from luftdaten.berlin.de). The internal data
source is an SDS011 particulate sensor.

The data is read data from csv files, processed, and plots are created.
Processed data is exported for further analysis in R.

"""

import os

import pandas as pd
import seaborn as sns
from datetime import datetime, timedelta

from read_csv_data import read_csv_data


# ------------------------------------------------------------------------------
# *** Define paths

# Path of indoor air quality measurement - baseline without air filter:
path_csv_indoor_baseline = '/home/john/PhD/GitHub/py-air-quality/py_air_quality/data/measurement_baseline.csv'

# Path of indoor air quality measurement - with air filter:
path_csv_indoor_filter = '/home/john/PhD/GitHub/py-air-quality/py_air_quality/data/measurement_with_filter.csv'

# Path of external air quality measurement data, obtained from
# https://luftdaten.berlin.de/station/overview/active/
path_csv_external = '/media/ssd_dropbox/Dropbox/Raspberry_Pi/air_quality_external_data/ber_mc042_20210414-20210712.csv'

# Output directory for plot & processed csv files (to be imported into R for
# analysis):
path_out = '/home/john/PhD/GitHub/py-air-quality/py_air_quality/data/'

# Which pollutant to analyse ('pm25' or 'pm10'):
pollutant = 'pm25'


# ------------------------------------------------------------------------------
# *** Read data from external data source

# Read and process data from external source (official outdoor measurement
# station).
df_external = pd.read_csv(path_csv_external, sep=';', skiprows=3)

df_external = df_external.rename(
    columns={'Messzeit (Angaben in MESZ bzw. MEZ)': 'time_string',
             'Stundenwerte': 'pm10',
             'Stundenwerte.1': 'pm25',
             }
    )

date_format = '%d.%m.%Y %H:%M'
df_external['datetime'] = [datetime.strptime(x, date_format)
                           for x in df_external['time_string'].tolist()]

# Datetime comparisons are error-prone with pandas; rather use epoch timestamp.
df_external['timestamp'] = \
    [round(x.timestamp()) for x in df_external['datetime'].tolist()]

# Only keep the pollutant to be analysed ('pm25' or 'pm10'):
df_external = df_external[['timestamp', pollutant]]
df_external = df_external.rename(columns={pollutant: (pollutant + '_external')})


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
    df_internal[['timestamp', 'datetime', pollutant, 'filter']]
df_internal = df_internal.rename(columns={pollutant: (pollutant + '_internal')})


# ------------------------------------------------------------------------------
# *** Merge internal & external data

# Round date to hours, so that we can calculate mean pollutant concentration per
# hour; solution from https://stackoverflow.com/a/48938464/13386040
def _hour_rounder(t):
    # Rounds to nearest hour by adding a timedelta hour if minute >= 30
    r = (t.replace(second=0, microsecond=0, minute=0, hour=t.hour)
         +timedelta(hours=t.minute//30)
         )
    return r

df_internal['datetime_hour'] = [
    _hour_rounder(x) for x in df_internal['datetime'].tolist()
    ]

# The external data only has a temporal resolution of one measurement per hour.
# For comparison, take the mean across each hour for the internal data.
df_internal_hourly = df_internal.groupby(['datetime_hour']).mean()
df_internal_hourly = df_internal_hourly.reset_index(level=0, drop=False)

# Remove datapoint where condition changed from no filter to filter:
df_internal_hourly = \
    df_internal_hourly.loc[df_internal_hourly['filter'].isin([0.0, 1.0])]

# Reset the timestamp to integer to be able to merge internal & external data on
# timestamp:
df_internal_hourly['timestamp'] = \
    [round(x.timestamp()) for x in df_internal_hourly['datetime_hour'].tolist()]

# Merge internal and external data (with hourly temporal resolution):
df_internal_hourly = df_internal_hourly.sort_values('timestamp')
df_external = df_external.sort_values('timestamp')
df_hourly = pd.merge_asof(
    df_internal_hourly,
    df_external[['timestamp', 'pm25_external']],
    on='timestamp',
    direction='nearest',
    )

# Wide to long format:

df_tmp_ext = \
    df_hourly[['datetime_hour', 'timestamp', 'pm25_external', 'filter']]
df_tmp_ext = df_tmp_ext.rename(columns={'pm25_external': pollutant})
df_tmp_ext['source'] = 'external'

df_tmp_int = \
    df_hourly[['datetime_hour', 'timestamp', 'pm25_internal', 'filter']]
df_tmp_int = df_tmp_int.rename(columns={'pm25_internal': pollutant})
df_tmp_int['source'] = 'internal'

df_hourly = pd.concat([df_tmp_ext, df_tmp_int], axis=0, ignore_index=True)

# ------------------------------------------------------------------------------
# *** Bar graph

colours = [
    [float(x) / 255.0 for x in [255, 0, 102, 255]],
    [float(x) / 255.0 for x in [44, 178, 252, 255]],
    ]

graph = sns.catplot(
    data=df_hourly,
    kind='bar',
    x='source',
    y='pm25',
    hue='filter',
    ci='sd',
    palette=colours,
    )

# Axis layout:
graph.axes[0][0].set_xlabel(None)
graph.axes[0][0].set_ylabel('Pollutant concentration [μg/m3]', fontsize=18)
graph.axes[0][0].set_yticks([0.0, 5.0, 10.0, 15.0])
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
figure = graph.fig
figure.clf()


# ------------------------------------------------------------------------------
# *** Plot pollution over time

# Calculate rolling average, separately for internal & external measurements
# (otherwise the rolling average would spread form one condition into the
# other).

df_hourly.loc[df_hourly['source'] == 'internal', pollutant] = \
    df_hourly.loc[df_hourly['source'] == 'internal', pollutant
                  ].rolling(24, center=True).mean()

df_hourly.loc[df_hourly['source'] == 'external', pollutant] = \
    df_hourly.loc[df_hourly['source'] == 'external', pollutant
                  ].rolling(24, center=True).mean()

# Exclude nan:
# df_hourly = df_hourly[df_hourly[pollutant].notna()]

graph = sns.lineplot(
    x='datetime_hour',
    y=pollutant,
    hue='source',
    style='filter',
    data=df_hourly,
    palette=colours,
    ci=None,
    )

# Axis layout:
graph.axes.set_xlabel(None)
graph.set_xticks([
    df_internal_hourly['datetime_hour'].iloc[0],
    df_internal_hourly['datetime_hour'].iloc[
        (round(len(df_internal_hourly) / 2))
        ],
    df_internal_hourly['datetime_hour'].iloc[-1],
    ])
graph.set_ylabel('Pollutant concentration [μg/m3]', fontsize=14)
graph.set_yticks([0.0, 5.0, 10.0, 15.0, 20.0])
graph.axes.tick_params(labelsize=14)
graph.axes.spines['top'].set_visible(False)
graph.axes.spines['right'].set_visible(False)

graph.get_legend().remove()

graph.set_aspect(2.7)

figure = graph.get_figure()
figure.savefig(os.path.join(path_out, 'timeplot.png'),
               dpi=200.0,
               bbox_inches='tight',
               )
figure.clf()


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
