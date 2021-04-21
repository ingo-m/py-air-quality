"""
Monitor air quality with SDS011 sensor.
"""


import os
import csv
import time
from datetime import datetime
from sds011 import SDS011


# ------------------------------------------------------------------------------
# *** Define parameters

path_csv = '/home/pi/air_quality/baseline_measurement.csv'


# ------------------------------------------------------------------------------
# *** Measure air quality

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

    utc_now = datetime.utcnow()

    # Get measurement:
    pm25, pm10 = sensor.query()

    sensor.sleep(sleep=True)

except Exception:

    utc_now = datetime.utcnow()
    pm25 = None
    pm10 = None

    try:
        sensor.sleep(sleep=True)
    except Exception:
        pass


# ------------------------------------------------------------------------------
# *** Write data to csv file

utc_now_str = str(round(utc_now.timestamp()))

# If the csv file does not exist yet, create it and write first line (header):
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
