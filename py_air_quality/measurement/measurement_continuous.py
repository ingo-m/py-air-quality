"""
Continuously monitor air quality with SDS011 sensor, e.g. for mobile
measurements.
"""


import os
import csv
import time
from datetime import datetime, timezone

from sds011 import SDS011

from py_air_quality.internal.settings import settings


# ------------------------------------------------------------------------------
# *** Parameters

# Take a sample every x seconds:
sampling_rate = 5.0


# ------------------------------------------------------------------------------
# *** Load settings from .env file

# Experimental condition, e.g. 'baseline' or 'with_filter':
experimental_condition = settings.EXPERIMENTAL_CONDITION

# Directory where to find data, and save plots (e.g. '/home/pi/air_quality/'):
data_directory = settings.DATA_DIRECTORY

# Path of csv file from which to load measurement data:
path_csv = os.path.join(
    data_directory,
    'measurement_{}.csv'.format(experimental_condition)
    )


# ------------------------------------------------------------------------------
# *** Measure air quality

sensor_initialised = False

while not sensor_initialised:

    try:

        # Initialise sensor:
        sensor = SDS011('/dev/ttyUSB0', use_query_mode=True)
        time.sleep(5)
        sensor.sleep(sleep=False)

        # Give sensor time to stabilise:
        time.sleep(30)

        for x in range(5):
            _, _ = sensor.query()
            time.sleep(1)

        sensor_initialised = True

    except Exception:

        print('Failed to initialise sensor, will try again.')

# TODO: end measurement
while True:

    t1 = time.time()

    try:

        utc_now = datetime.now(timezone.utc)

        # Get measurement:
        pm25, pm10 = sensor.query()

    except Exception:

        utc_now = datetime.now(timezone.utc)
        pm25 = None
        pm10 = None

    # --------------------------------------------------------------------------
    # *** Write data to csv file

    utc_now_str = str(round(utc_now.timestamp()))

    # If the csv file does not exist yet, create it and write first line
    # (header):
    if not os.path.isfile(path_csv):
        with open(path_csv, mode='w') as csv_file:
            csv_write = csv.writer(csv_file, delimiter=',')
            csv_write.writerow(['timestamp', 'pm25', 'pm10'])

    # Append new record to csv file (note the `a` flag):
    with open(path_csv, 'a') as csv_file:
        csv_file.write((utc_now_str
                        + ','
                        + str(pm25)
                        + ','
                        + str(pm10)
                        + '\n'))

    # --------------------------------------------------------------------------
    # *** Sleep until next measurement

    t2 = time.time()
    td = t2 - t1
    if td < sampling_rate:
        sleep_duration = sampling_rate - td
        time.sleep(sleep_duration)

sensor.sleep(sleep=True)
