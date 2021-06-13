import os

from dotenv import load_dotenv
from pydantic import BaseSettings


dotenv_path = os.path.join(os.path.dirname(__file__), '.credentials')
load_dotenv(dotenv_path)


load_dotenv()


class Credentials(BaseSettings):
    MONGODB_USERNAME: str
    MONGODB_CONNECTION_URL: str
    PATH_MONGODB_TSL_CERTIFICATE: str


credentials = Credentials()
