import sys
from importlib import import_module
import pkgutil

import typer

import ema.env as env


class CliApp(typer.Typer):
    def __call__(self, *args, **kwargs):
        cli_bootstrap()
        super().__call__(*args, **kwargs)


app = CliApp()


def import_commands():
    for _, name, _ in pkgutil.iter_modules(["ema/commands"]):
        import_module(f"ema.commands.{name}")


def cli_bootstrap():
    # Read .env arg if exists and remove it
    args = sys.argv[1:]  # skip script name
    env_file = args.pop(0) if args and args[0].startswith(".env") else env.DEFAULT_ENV_FILE
    sys.argv = [sys.argv[0]] + args

    env.bootstrap(env_file)
