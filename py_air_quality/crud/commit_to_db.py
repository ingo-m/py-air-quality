"""
Commit new measurement data to mongodb database.

Requires database credentials to be set in
py-air-quality/py_air_quality/internal/.credentials

Can be run as a cron job:
*/5 * * * * /home/pi/py_main/bin/python /home/pi/github/py-air-quality/py_air_quality/crud/commit_to_db.py >> /home/pi/air_quality/crontab_log_db.txt 2>&1

"""


import os
from datetime import datetime, timezone
from time import sleep

sleep(55)

import pymongo

from py_air_quality.crud.read_csv_data import read_csv_data
from py_air_quality.internal.credentials import credentials
from py_air_quality.internal.settings import settings



# ------------------------------------------------------------------------------
# *** Load settings from .env file

# Experimental condition, e.g. 'baseline' or 'with_filter':
experimental_condition = settings.EXPERIMENTAL_CONDITION

# Measurement location, e.g. 'berlin':
measurement_location = settings.MEASUREMENT_LOCATION

# Sensor type (e.g. "Nova Fitness SDS011"):
sensor_type = settings.SENSOR_TYPE

# Directory where to find data:
data_directory = settings.DATA_DIRECTORY

# Path of csv file from which to load measurement data:
path_csv = os.path.join(
    data_directory,
    'measurement_{}.csv'.format(experimental_condition)
    )


# ------------------------------------------------------------------------------
# *** Load credentials from .credentials file

mongodb_username = credentials.MONGODB_USERNAME

mongodb_url = credentials.MONGODB_CONNECTION_URL

mongodb_tsl_cert = credentials.PATH_MONGODB_TSL_CERTIFICATE


# ------------------------------------------------------------------------------
# *** Commit new data to mongodb database

utc_now = datetime.now(timezone.utc)

print('Commit new data to mongodb database at {}'.format(utc_now))

# Read measurement data from csv file:
df = read_csv_data(path_csv)

with pymongo.MongoClient(mongodb_url,
                         username=mongodb_username,
                         authMechanism='MONGODB-X509',
                         tls=True,
                         tlsCertificateKeyFile=mongodb_tsl_cert,
                         ) as client:

    db = client.air_quality

    db_collection = db['air_quality']

    # Get the newest datapoint (from the same measurement conditions) from the
    # mongodb database:
    dict_search = {'experimental_condition': experimental_condition,
                   'measurement_location': measurement_location,
                   'sensor_type': sensor_type,
                   }

    search_results = db_collection.find_one(
        dict_search,
        sort=[('timestamp', pymongo.DESCENDING)],
        )

    if search_results:
        newest_db_timestamp = search_results.get('timestamp')
        if not newest_db_timestamp:
            newest_db_timestamp = 0
    else:
        print('Found no previous data from same condition in database')
        newest_db_timestamp = 0

    # Select new measurement that is not yet in database:
    df = df.loc[df['timestamp'] > newest_db_timestamp]

    if 0 < len(df):

        print('Insert {} new datapoints into database'.format(len(df)))

        # Select & annotate data to be committed to database:
        df = df[['timestamp', 'pm25', 'pm10', 'datetime']]
        df['experimental_condition'] = experimental_condition
        df['measurement_location'] = measurement_location
        df['sensor_type'] = sensor_type
        df['record_time_utc'] = utc_now

        # Commit new measurement data to database:
        df_list = df.to_dict(orient='records')
        db_response = db_collection.insert_many(df_list)

        if db_response.acknowledged:
            print('Database insertion acknowledged.')
        else:
            print('ERROR: Database insertion failed.')

    else:

        print('No new data to be committed to database.')
