"""
Commit new measurement data to mongodb database.
"""


import os
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from pymongo

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
        {'_id': False},
        ).sort('timestamp', direction=pymongo.DESCENDING)

    newest_db_timestamp = search_results.get('timestamp')
    if not newest_db_timestamp:
        newest_db_timestamp = 0





    df.dtypes


    df = df[['timestamp', 'pm25', 'pm10', 'datetime']]
    df['experimental_condition'] = experimental_condition
    df['measurement_location'] = measurement_location
    df['sensor_type'] = sensor_type
    df['record_time_utc'] = utc_now

    df_list = df.to_dict(orient='records')

    db_response = collection.insert_many(df_list)

