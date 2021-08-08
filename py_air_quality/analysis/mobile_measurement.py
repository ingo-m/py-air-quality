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
import seaborn as sns
import tilemapbase
import matplotlib.pyplot as plt
from matplotlib import colorbar
from matplotlib.cm import ScalarMappable
from mpl_toolkits.axes_grid1 import make_axes_locatable

from py_air_quality.crud.read_csv_data import read_csv_data

# -----------------------------------------------------------------------------
# *** Parameters

# Path of csv file with Nova Fitness SDS011 particulate sensor data, measured
# with py-air-quality.
path_air_data = '/media/ssd_dropbox/Dropbox/Raspberry_Pi/air_pollution_data/measurement_mobile.csv'

# Path of csv file with GPS coordinates, from "GPS Logger" App.
path_gps = '/media/ssd_dropbox/Dropbox/Raspberry_Pi/air_pollution_data/20210807-212329-Alfeld-Duingen-artifact-removed.txt'

# Output file path for plot:
path_plot = '/media/ssd_dropbox/Dropbox/Raspberry_Pi/air_pollution_plots/alfeld_duingen_pm25.png'

# Which pollutant to plot ('pm25' or 'pm10').
pollutant = 'pm25'

figure_size = (16, 16)

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

df = df.loc[time_diff_bool]

n_valid = np.sum(time_diff_bool)

msg = 'Including {} valid datapoints'.format(n_valid)
print(msg)

msg = ('Excluding {} invalid datapoints (no air pollution datapoints matching'
       + ' GPS timestamp).')
msg = msg.format((len(time_diff_bool) - n_valid))
print(msg)

# -----------------------------------------------------------------------------
# *** Plot data

print('Plot data')

# Get the minimum and maximum latitude and longitude. Add a margin for
# visualisation purposes.
lat_min = df['latitude'].min()
lat_max = df['latitude'].max()
long_min = df['longitude'].min()
long_max = df['longitude'].max()

plot_margin = 0.075 * max((long_max - long_min), (lat_max - lat_min))

long_min = long_min - plot_margin
long_max = long_max + plot_margin
lat_min = lat_min - plot_margin
lat_max = lat_max + plot_margin

#long_min = 51.9265
#long_max = 52.0050
#lat_min = 9.8084
#lat_max = 10.0209

# Get map from open street maps:
tilemapbase.start_logging()
tilemapbase.init(create=True)
tiles = tilemapbase.tiles.build_OSM()
extent = tilemapbase.Extent.from_lonlat(
        long_min,
        long_max,
        lat_min,
        lat_max,
        )
# extent = extent.to_aspect(1.0)

fig, ax = plt.subplots(figsize=figure_size)
ax.xaxis.set_visible(False)
ax.yaxis.set_visible(False)

plotter = tilemapbase.Plotter(extent, tiles, width=600)
plotter.plot(ax, tiles)

# Convert GPS coordinates to "Web Mercator" projection, normalised between 0
# and 1.
x_coordinates = []
y_coordinates = []

for x, y in zip(df['longitude'].to_list(), df['latitude'].to_list()):
    x_norm, y_norm = tilemapbase.project(x, y)
    x_coordinates.append(x_norm)
    y_coordinates.append(y_norm)

colour_map = sns.color_palette('plasma', as_cmap=True)

# Minimum and maximum of colour map.
vmin = 0.0
vmax = np.ceil(df[pollutant].max())

# Plot air pollution on map.
scatter = ax.scatter(
    x_coordinates,
    y_coordinates,
    s=150.0,
    c=df[pollutant].to_list(),
    marker='.',
    cmap=colour_map,
    vmin=vmin,
    vmax=vmax,
    linewidth=0,
    zorder=2,
    edgecolor='none',
    alpha=0.5,
    )

# Colour space for colour bar.
norm = plt.Normalize(vmin, vmax)
sm = ScalarMappable(norm=norm, cmap=colour_map)
sm.set_array([])

# Create additional axes for colour bar, next to existing plot.
# divider = make_axes_locatable(ax)
# colorbar_axes = divider.append_axes(
#     'right',
#     size='5%',
#     pad=0.2,
#     )

# Create colour bar.
# cbar = fig.colorbar(sm, cax=colorbar_axes, shrink=0.5)
cbar = fig.colorbar(sm, ax=ax, shrink=0.5)
cbar.ax.set_title(pollutant)

ax.spines['top'].set_visible(False)
ax.spines['bottom'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['right'].set_visible(False)

fig.savefig(
    path_plot,
    dpi=128,
    bbox_inches='tight',
    )
