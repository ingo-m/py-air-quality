#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyse the effect of an air filter on indoor air quality.

...

"""

# import numpy as np
# import statsmodels as sm

from datetime import datetime, timedelta, timezone
import pandas as pd
import seaborn as sns

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

# Datetime comparisons are error-prone with pandas; rather use epoch timestamp.
df_external['timestamp'] = \
    [round(x.timestamp()) for x in df_external['Date'].tolist()]

df_external = df_external[['timestamp', 'median']]
df_external = df_external.rename(columns={'median': (pollutant + '_external')})

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
df_internal = df_internal[['timestamp', pollutant, 'filter', 'weekend']]
df_internal = df_internal.rename(columns={pollutant: (pollutant + '_internal')})


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


# WIP


# ar_mod = AutoReg(signal)
# ar_res = ar_mod.fit()

# https://www.statsmodels.org/stable/generated/statsmodels.tsa.ar_model.AutoReg.html#statsmodels.tsa.ar_model.AutoReg
# ar_model = sm.tsa.AutoReg(df['spend'], freq='1')
