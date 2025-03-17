import os

import dotenv

from ema.linear_api import LinearApi, LinearConfig
import microcore as mc
from microcore import ui
from ema.db import init_db

DEFAULT_ENV_FILE = ".env.mi"
linear_api: LinearApi


def bootstrap(env_file: str = DEFAULT_ENV_FILE):
    if env_file:
        dotenv.load_dotenv(env_file)
    global linear_api
    print(f"Bootstrapping... {ui.gray('env: ')}{ui.green(env_file)}")
    linear_api = LinearApi(LinearConfig())
    mc.configure(
        USE_DOT_ENV=True,
        DOT_ENV_FILE=env_file,
        USE_LOGGING=True,
    )
    init_db()

