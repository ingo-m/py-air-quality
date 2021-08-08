# -*- coding: utf-8 -*-
"""
Analyse mobile air quality measurement.

Process air pollution data and corresponding GPS location data (from "GPS 
Logger" Android App), and plot data on a map from openstreetmap.org.

pip install tilemapbase                                                                

"""

from datetime import datetime, timezone

import numpy as np
import pandas as pd
import tilemapbase
import matplotlib.pyplot as plt

from py_air_quality.crud.read_csv_data import read_csv_data

# -----------------------------------------------------------------------------
# *** Parameters

# Path of csv file with Nova Fitness SDS011 particulate sensor data, measured
# with py-air-quality.
path_air_data = '/media/ssd_dropbox/Dropbox/Raspberry_Pi/air_pollution_data/measurement_mobile.csv'

# Path of csv file with GPS coordinates, from "GPS Logger" App.
path_gps = '/media/ssd_dropbox/Dropbox/Raspberry_Pi/air_pollution_data/20210808-125802-Wanderung_Irmenseule_1.txt'

# Output file path for plot:
path_plot = '/home/john/Desktop/plot.png'

# Which pollutant to plot ('pm25' or 'pm10').
pollutant = 'pm25'

# -----------------------------------------------------------------------------
# *** Load air quality data

print('Analyse mobile air quality measurement')

print('Load air quality data')

df_air = read_csv_data(path_air_data)
df_air = df_air[['timestamp', pollutant]]
df_air = df_air.rename(columns={'timestamp':'timestamp_air'})

# -----------------------------------------------------------------------------
# *** Load GPS data

print('Load GPS data')

df_gps = pd.read_csv(path_gps)

# We assume that the datetime of the GPS data is in UTC.
utc_zone = timezone.utc

datetime = [datetime.strptime(x, '%Y-%m-%d %H:%M:%S').replace(tzinfo=utc_zone)
            for x in df_gps['date time'].to_list()
            ]

timestamp = [round(x.timestamp()) for x in datetime]

df_gps['timestamp_gps'] = timestamp

df_gps = df_gps[['timestamp_gps', 'latitude', 'longitude']]

# -----------------------------------------------------------------------------
# *** Merge pollution & GPS data

print('Merge pollution & GPS data')

# Data must be sorted before merge.
df_air = df_air.sort_values('timestamp_air')
df_gps = df_gps.sort_values('timestamp_gps')

df = pd.merge_asof(
    df_gps,
    df_air,
    left_on='timestamp_gps',
    right_on='timestamp_air',
    direction='nearest',
    )

# Remove datapoints where the timestamps of the particulate concentration and
# the GPS measurements are above some threshold.
time_diff_thr = 10.0
timestamp_gps = [float(x) for x in df['timestamp_gps'].to_list()]
timestamp_air = [float(x) for x in df['timestamp_air'].to_list()]
time_diff = np.absolute(np.subtract(timestamp_gps, timestamp_air))
time_diff_bool = np.less(time_diff, time_diff_thr)

n_valid = np.sum(time_diff_bool)

msg = 'Including {} valid datapoints'.format(n_valid)
print(msg)

msg = ('Excluding {} invalid datapoints (no air pollution datapoints matching'
       + ' GPS timestamp).')
msg = msg.format((len(time_diff_bool) - n_valid))
print(msg)








df_gps.dtypes


long_min = 51.9265
long_max = 52.0050
lat_min = 9.8084
lat_max = 10.0209

tilemapbase.start_logging()
tilemapbase.init(create=True)
t = tilemapbase.tiles.build_OSM()

#degree_range = 0.003
extent = tilemapbase.Extent.from_lonlat(
        lat_min, 
        lat_max,                  
        long_min, 
        long_max
        )
# extent = extent.to_aspect(1.0)

fig, ax = plt.subplots(figsize=(8, 8), dpi=100)
ax.xaxis.set_visible(False)
ax.yaxis.set_visible(False)

plotter = tilemapbase.Plotter(extent, t, width=600)
plotter.plot(ax, t)

x, y = tilemapbase.project(*my_office)
ax.scatter(x,y, marker=".", color="black", linewidth=20)

