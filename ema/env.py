import sys

import dotenv
import microcore as mc
from chromadb.utils import embedding_functions
from microcore import ui
from colorama import Fore, Style

import ema
from ema.db import init_db
from ema.linear_api import LinearApi, LinearConfig


DEFAULT_ENV_FILE = ".env.mi"
linear_api: LinearApi


def print_logo():
    green = Fore.GREEN  # For borders
    bright = Style.BRIGHT
    logo = [
        f"{green}{bright}"
        "╔══════════════════════════════════════════════════╗\n",
        "║                                                  ║\n",
        "║            ███████╗███╗   ███╗ █████╗            ║\n",
        "║            ██╔════╝████╗ ████║██╔══██╗           ║\n",
        "║            █████╗  ██╔████╔██║███████║           ║\n",
        "║            ██╔══╝  ██║╚██╔╝██║██╔══██║           ║\n",
        "║            ███████╗██║ ╚═╝ ██║██║  ██║           ║\n",
        "║            ╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝           ║\n",
        "║                                                  ║\n",
        f"║  --==<[ {Fore.RESET}Engineering Manager Assistant AI{green}{bright} ]>==--  ║\n",
        f"{green}{bright}"
        f"║                      {green}v{ema.__version__}{green}{bright}                      ║\n",
        "║                                                  ║\n",
        f"{green}{bright}"
        "╚══════════════════════════════════════════════════╝",
    ]

    print("".join(logo))


def bootstrap(env_file: str = DEFAULT_ENV_FILE):
    print_logo()
    if env_file:
        dotenv.load_dotenv(env_file)

    global linear_api
    print(f"Bootstrapping... {ui.gray('env: ')}{ui.green(env_file)}")
    if sys.platform == "win32":
        dotenv.load_dotenv(".env.win_override", override=True)
        print(f"\t{ui.gray('env override: ')}{ui.green('.env.win_override')}")

    linear_api = LinearApi(LinearConfig())
    mc.configure(
        USE_DOT_ENV=False,
        USE_LOGGING=True,
        EMBEDDING_DB_FUNCTION=embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="paraphrase-multilingual-MiniLM-L12-v2"
        ),
    )
    init_db()
