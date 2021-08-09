"""
Continuously monitor air quality with SDS011 sensor, e.g. for mobile
measurements.

Create a service unit file:
```
sudo nano /etc/systemd/system/py_air_quality.service
```

Place the following configuration in the new service unit file:
```
[Unit]
Description=Python Air Quality Monitor
After=multi-user.target

[Service]
User=pi
Type=simple
Restart=always
ExecStart=/home/pi/py_main/bin/python /home/pi/github/py-air-quality/py_air_quality/measurement/measurement_continuous.py

[Install]
WantedBy=multi-user.target
```

Enable the service, so that it will be started when the system boots:
```
sudo systemctl daemon-reload
sudo systemctl enable py_air_quality.service
sudo systemctl start py_air_quality.service
```

Check the status & system log:
```
sudo systemctl status py_air_quality.service
journalctl -u py_air_quality.service
```

Manually stop the service when done with a measurement:
```
sudo systemctl stop py_air_quality.service
```

Sources:
https://alexandra-zaharia.github.io/posts/stopping-python-systemd-service-cleanly/
https://medium.com/codex/setup-a-python-script-as-a-service-through-systemctl-systemd-f0cc55a42267
"""


import os
import csv
import logging
import signal
import sys
import time
from datetime import datetime, timezone

from sds011 import SDS011

from py_air_quality.internal.settings import settings


class ContinuousMeasurement:
    """
    Continuously monitor air quality with SDS011 sensor.

    To be used for mobile measurements. Can be run as a service.
    """

    def __init__(self):
        self.logger = self._init_logger()

        # Enable graceful shutdown of the service:
        signal.signal(signal.SIGTERM, self._handle_sigterm)

        # Take a sample every x seconds:
        self.sampling_rate = 5.0

        self.continue_measurement = True

        # ----------------------------------------------------------------------
        # *** Load settings from .env file

        # Experimental condition, e.g. 'baseline' or 'with_filter':
        experimental_condition = settings.EXPERIMENTAL_CONDITION

        # Directory where to store data (e.g. '/home/pi/air_quality/'):
        data_directory = settings.DATA_DIRECTORY

        # Path of csv file where to store measurement data:
        self.path_csv = os.path.join(
            data_directory,
            'measurement_{}.csv'.format(experimental_condition)
            )

        # If the csv file does not exist yet, create it and write first line
        # (header):
        if not os.path.isfile(self.path_csv):
            with open(self.path_csv, mode='w') as csv_file:
                csv_write = csv.writer(csv_file, delimiter=',')
                csv_write.writerow(['timestamp', 'pm25', 'pm10'])

        # ----------------------------------------------------------------------
        # *** Initialise sensor

        sensor_initialised = False

        while not sensor_initialised:

            try:

                # Initialise sensor:
                self.sensor = SDS011('/dev/ttyUSB0', use_query_mode=True)
                time.sleep(5)
                self.sensor.sleep(sleep=False)

                # Give sensor time to stabilise:
                time.sleep(30)

                for x in range(5):
                    _, _ = self.sensor.query()
                    time.sleep(1)

                sensor_initialised = True

            except Exception:

                msg = 'Failed to initialise sensor, will try again.'
                self.logger.error(msg)

        self.logger.info('py-air-quality continuous measurement started.')

    def _init_logger(self):
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        stdout_handler = logging.StreamHandler()
        stdout_handler.setLevel(logging.DEBUG)
        stdout_handler.setFormatter(logging.Formatter(
            '%(levelname)8s | %(message)s'
            ))
        logger.addHandler(stdout_handler)
        return logger

    def start(self):
        """Perform measurements."""
        while self.continue_measurement:

            t1 = time.time()

            try:

                utc_now = datetime.now(timezone.utc)

                # Get measurement:
                pm25, pm10 = self.sensor.query()

            except Exception:

                utc_now = datetime.now(timezone.utc)
                pm25 = None
                pm10 = None

            # ------------------------------------------------------------------
            # *** Write data to csv file

            utc_now_str = str(round(utc_now.timestamp()))

            # Append new record to csv file (note the `a` flag):
            with open(self.path_csv, 'a') as csv_file:
                csv_file.write((utc_now_str
                                + ','
                                + str(pm25)
                                + ','
                                + str(pm10)
                                + '\n'))

            # ------------------------------------------------------------------
            # *** Sleep until next measurement

            t2 = time.time()
            td = t2 - t1
            if td < self.sampling_rate:
                sleep_duration = self.sampling_rate - td
                time.sleep(sleep_duration)

    def stop(self):
        self.logger.info('Stopping measurement')
        self.continue_measurement = False
        # Wait for potentially ongoing measurement to finish:
        time.sleep((self.sampling_rate + 0.1))
        self.sensor.sleep(sleep=True)
        sys.exit(0)

    def _handle_sigterm(self, sig, frame):
        msg = 'SIGTERM received, stopping py-air-quality measurement service.'
        self.logger.info(msg)
        self.stop()


if __name__ == '__main__':
    service = ContinuousMeasurement()
    service.start()
