import json
import os
from dataclasses import fields, is_dataclass
from datetime import datetime
from json import JSONDecodeError
from types import UnionType
from typing import TypeVar, get_args

from microcore.configuration import TRUE_VALUES

T = TypeVar("T")


def is_optional_int(field_type):
    """Checks if the field is int | None in Python 3.10+"""
    args = get_args(field_type)
    return isinstance(field_type, UnionType) and int in args and type(None) in args


def update_object_from_env(obj: T, prefixes: list[str] | None = None) -> T:
    """
    Update object fields from environment variables

    ENV variable name resolution:
        If "env_var" key exists in field metadata (dataclasses.field.metadata):
            - if empty (False, "", None) then field will not be updated from ENVs
            - otherwise field.metadata.env_var will be used as ENV variable name
        Otherwise:
            - Try ENV var with uppercased and prefixed field name if defined
            - Leave field value as is if no ENV var found
    """
    for f in fields(obj.__class__):
        if is_dataclass(f.type) and (field_obj := getattr(obj, f.name)):
            update_object_from_env(field_obj, getattr(field_obj, "_ENV_PREFIXES", None))
            continue
        if "env_var" in f.metadata:
            name = f.metadata["env_var"]
            if not name:
                continue
        else:
            if prefixes:
                name = None
                for prefix in prefixes:
                    if f"{prefix}{f.name.upper()}" in os.environ:
                        name = f"{prefix}{f.name.upper()}"
                        break
                if not name:
                    continue
            else:
                name = f.name.upper()

        if name not in os.environ:
            continue
        value = os.getenv(name)

        if f.metadata.get("ignore_empty_env") and value == "":
            continue
        if is_optional_int(f.type):
            if value == "":
                value = None
            elif not value.isdigit():
                raise ValueError(f"Incorrect ENV variable: {name} is not an integer")
            else:
                value = int(value)
        elif f.type is bool:
            value = value.upper() in TRUE_VALUES
        elif f.type is int:
            if not value.isdigit():
                raise ValueError(f"Incorrect ENV variable: {name} is not an integer")
            value = int(value)
        elif f.type is list:
            try:
                if not value:
                    value = []
                else:
                    if all(c in value for c in ("[", "]", '"')):
                        value = json.loads(value)
                    else:
                        value = [v.strip() for v in value.split(",") if v.strip()]
            except ValueError | JSONDecodeError:
                raise ValueError(f"Incorrect ENV variable: {name} is not a list")

        setattr(obj, f.name, value)
    return obj


def format_dt(value: str | datetime, fmt: str= "%Y-%m-%d %H:%M:%S") -> str:
    if not value:
        return None
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    return value.strftime(fmt)


def format_dt_human(value: str | datetime) -> str:
    return format_dt(value, "%d %B, %H:%M").replace(" 0", " ")
