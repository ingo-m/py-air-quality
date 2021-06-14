"""
Plot air polution measurement data from mongodb database.

Requires database credentials to be set in
py-air-quality/py_air_quality/internal/.credentials

Can be run as a cron job:
*/5 * * * * /home/pi/py_main/bin/python /home/pi/github/py-air-quality/py_air_quality/server/plot_pollution_from_db.py >> /home/pi/air_quality/crontab_log_plot.txt 2>&1

"""

from time import sleep

import pandas as pd
import pymongo
from datetime import datetime, timedelta
from dateutil import tz

from py_air_quality.internal.credentials import credentials
from py_air_quality.server.plot import plot_pollution


# ------------------------------------------------------------------------------
# *** Define parameters

# Experimental condition, e.g. 'baseline' or 'with_filter':
experimental_conditions = ['with_filter', 'outdoors_front']

measurement_locations = ['Berlin Kreuzberg']

sensor_types = ['Nova Fitness SDS011']

# Output path for plots ('indoors' / 'outdoors' directory, experimental
# condition and plot name left open;  plot name will be filled in by the child
# plotting function, e.g. 'last_24h'):
path_plot = '/home/pi/gitlab/utilities/technical_notes/mkdocs/website_air_quality/site/{}/{}_{}.png'

# When querying data for aggregate plots, include data from last x days:
last_x_days = 365

# Time zone used for plots:
local_time_zone_name = 'Europe/Berlin'


# ------------------------------------------------------------------------------
# *** Load database credentials from .credentials file

mongodb_username = credentials.MONGODB_USERNAME

mongodb_url = credentials.MONGODB_CONNECTION_URL

mongodb_tsl_cert = credentials.PATH_MONGODB_TSL_CERTIFICATE


# ------------------------------------------------------------------------------
# *** Query data from mongodb

# Wait for the measurement to finish (assuming that the measurement is done at
# the same frequency, through cron tab).
sleep(70)

# Get current UTC, and add time zone info (so it can be transformed to local
# time).
utc_zone = tz.tzutc()
utc_now = datetime.utcnow()

# Current, local time:
local_time_zone = tz.gettz(local_time_zone_name)
local_now = utc_now.replace(tzinfo=utc_zone).astimezone(local_time_zone)

local_now_hour = (
    float(local_now.hour)
    + (float(local_now.minute) / 60.0)
    )

start_epoch = int(round((utc_now - timedelta(days=last_x_days)).timestamp()))

with pymongo.MongoClient(mongodb_url,
                         username=mongodb_username,
                         authMechanism='MONGODB-X509',
                         tls=True,
                         tlsCertificateKeyFile=mongodb_tsl_cert,
                         ) as client:

    db = client.air_quality

    db_collection = db['air_quality']

    for experimental_condition in experimental_conditions:

        for measurement_location in measurement_locations:

            for sensor_type in sensor_types:

                dict_search = {
                    'timestamp': {'$gt': start_epoch},
                    'experimental_condition': experimental_condition,
                    'measurement_location': measurement_location,
                    'sensor_type': sensor_type,
                    }

                search_results = db_collection.find(dict_search)

                # --------------------------------------------------------------
                # *** Transform data

                data = [x for x in search_results]

                df = pd.DataFrame(data)

                # 'datetime' and 'timestamp' from database should match, but
                # use epoch timestamp as single source of truth and apply time
                # zone conversion.
                df = df[['timestamp', 'pm25', 'pm10']]

                df['datetime'] = [
                    datetime.fromtimestamp(x) for x in df['timestamp'].tolist()
                    ]

                # Tell the datetime object that it's in UTC time zone:
                df['datetime'] = [
                    x.replace(tzinfo=utc_zone) for x in df['datetime'].tolist()
                    ]

                # Convert datetime to local time:
                df['datetime'] = [
                    x.astimezone(local_time_zone) for x in df['datetime'].tolist()
                    ]

                # Add column for hour of the day:

                # Add column for weekday (where Monday is 0 and Sunday is 6):
                df['weekday'] = [x.weekday() for x in df['datetime'].tolist()]

                # Add column for weekend (binary; 0 = weekday, 1 = weekend):
                df['weekend'] = [(5 <= x) for x in df['weekday'].tolist()]

                # Fill in experimental condition into plot name, but leave name
                # for time condition (e.g. 'last_24h') open.
                if experimental_condition == 'with_filter':
                    path_tmp = path_plot.format(
                        'indoors',
                        experimental_condition,
                        '{}'
                        )
                elif experimental_condition == 'outdoors_front':
                    path_tmp = path_plot.format(
                        'outdoors',
                        experimental_condition,
                        '{}'
                        )
                else:
                    raise ValueError

                # Create plots:
                plot_pollution(df=df,
                               utc_now=utc_now,
                               local_now_hour=local_now_hour,
                               path_plot=path_tmp)
