import os
from typing import Any, Dict, List, Optional, Union

from dotenv import load_dotenv
from pydantic import BaseSettings


dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)


load_dotenv()


class Settings(BaseSettings):
    EXPERIMENTAL_CONDITION: str
    DATA_DIRECTORY: str
    MEASUREMENT_LOCATION: str
    SENSOR_TYPE: str


settings = Settings()
