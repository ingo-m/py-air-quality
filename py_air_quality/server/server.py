#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serve air polution plots via local network.

Assumes that the respective image files are created by
`py_air_quality/analysis/plot_pollution.py`
"""

import os
from fastapi import FastAPI
from fastapi.responses import FileResponse

from py_air_quality.internal.settings import settings


# Load settings from .env file

# Experimental condition, e.g. 'baseline' or 'with_filter':
experimental_condition = settings.EXPERIMENTAL_CONDITION

# Directory where to find data, and save plots (e.g. '/home/pi/air_quality/'):
data_directory = settings.DATA_DIRECTORY

img_path_last_24_h = os.path.join(
    data_directory,
    '{}_last_24_h.png'.format(experimental_condition)
    )

img_path_combined = os.path.join(
    data_directory,
    '{}_combined.png'.format(experimental_condition)
    )

img_path_weekday = os.path.join(
    data_directory,
    '{}_weekday.png'.format(experimental_condition)
    )

img_path_weekend = os.path.join(
    data_directory,
    '{}_weekend.png'.format(experimental_condition)
    )

app = FastAPI()


@app.get('/last_24_h')
async def last_24_h():
    return FileResponse(img_path_last_24_h)


@app.get('/combined')
async def combined():
    return FileResponse(img_path_combined)


@app.get('/weekday')
async def weekday():
    return FileResponse(img_path_weekday)


@app.get('/weekend')
async def weekend():
    return FileResponse(img_path_weekend)
