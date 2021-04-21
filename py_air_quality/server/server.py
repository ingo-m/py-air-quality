#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serve air polution plots via local network.

Assumes that the respective image files are created by
`py_air_quality/analysis/plot_pollution.py`

Install dependencies:
pip install fastapi aiofiles uvicorn

Start the server like this, adjusting the IP address to the raspberry pi's
address:
tmux
cd /home/pi/github/py-air-quality/py_air_quality/server/
uvicorn server:app --host 123.456.7.890

You can now find the plots from another device on your local network at these
URLs (adjust the IP to the raspberry pi's address):
http://123.456.7.890:8000/last_24_h
http://123.456.7.890:8000/weekday
http://123.456.7.890:8000/weekend

"""

from fastapi import FastAPI
from fastapi.responses import FileResponse

img_path_last_24_h = '/home/pi/air_quality/baseline_last_24_h.png'
img_path_weekday = '/home/pi/air_quality/baseline_weekday.png'
img_path_weekend = '/home/pi/air_quality/baseline_weekend.png'

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
