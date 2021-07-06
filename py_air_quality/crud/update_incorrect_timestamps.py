#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update incorrect timestamps.

Due to a bug in an earlier version of py-air-quality, timestamps were created
from a datetime object, assuming the datetime to be in local time, although it
was actually in UTC. The mongodb database documents also contain the correct
datetime object, alongside the incorrect epoch timestamp. Convert all timestamps
to the correct value, in accordance with the UTC datetime object.

"""

import pymongo
from datetime import timezone

mongodb_username = ""
mongodb_url = ""
mongodb_tsl_cert = ""

document_update_counter = 0

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
    dict_search = {'status': {'$exists': False},
                   }

    while True:

        search_results = db_collection.find_one(
            dict_search,
            sort=[('timestamp', pymongo.ASCENDING)],
            )

        if not search_results:
            print('Updated {} documents.'.format(document_update_counter))
            print('No more documents to update.')
            break

        document_datetime = search_results['datetime']

        # The datetime is already in utc, add the timezone info (without
        # changing the time):
        document_datetime = document_datetime.replace(tzinfo=timezone.utc)

        correct_timestamp = document_datetime.timestamp()

        dict_id = {'_id': search_results['_id']}

        dict_update = {'$set': {'status': 1,
                                'timestamp': correct_timestamp,
                                }
                       }

        # Update the job status in the mongodb database:
        db_response = db_collection.update_one(dict_id,
                                               dict_update,
                                               upsert=False)

        if db_response.acknowledged:
            document_update_counter += 1
        else:
            print('Failed to update document: {}'.format(search_results['_id']))

print('Done')
