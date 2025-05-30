"""
Python REPL for the EMA CLI with initialized environment and common imports.
"""
# flake8: noqa: F401
import code
from ema.cli import app

# Imports for usage in REPL
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from time import time
from rich.pretty import pprint

import microcore as mc
from microcore import ui

import ema.env as env
import ema.db as db
from ema.db import *
from ema.utils import *
from ema.linear.issue import *

@app.command()
def repl():
    code.interact(local=globals())
