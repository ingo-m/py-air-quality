#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serve air polution plots via local network.

Assumes that the respective image files are created by
`py_air_quality/analysis/plot_pollution.py`
"""

from fastapi import FastAPI
from fastapi.responses import FileResponse

img_path_last_24_h = '/home/pi/air_quality/with_filter_last_24_h.png'
img_path_weekday = '/home/pi/air_quality/with_filter_weekday.png'
img_path_weekend = '/home/pi/air_quality/with_filter_weekend.png'

app = FastAPI()

@app.get('/last_24_h')
async def last_24_h():
    return FileResponse(img_path_last_24_h)

@app.get('/weekday')
async def weekday():
    return FileResponse(img_path_weekday)

@app.get('/weekend')
async def weekend():
    return FileResponse(img_path_weekend)
