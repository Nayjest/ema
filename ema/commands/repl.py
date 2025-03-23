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



@app.command()
def repl():
    code.interact(local=globals())