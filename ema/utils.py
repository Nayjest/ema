import json
import os
from dataclasses import fields
from json import JSONDecodeError
from typing import TypeVar

from microcore.configuration import TRUE_VALUES

T = TypeVar('T')


def update_object_from_env(
    obj: T,
    prefixes: list[str] | None = None,
    allow_no_prefix: bool = True,
) -> T:
    """
    Update object fields from environment variables

    ENV variable name resolution:
        If "env_var" key exists in field metadata (dataclasses.field.metadata):
            - if empty (False, "", None) then field will not be updated from ENVs
            - otherwise field.metadata.env_var will be used as ENV variable name
        Otherwise:
            - Try ENV var with uppercased and prefixed field name if defined
            - Try ENV var with uppercased field name if exists
            - Leave field value as is if no ENV var found
    """
    for f in fields(obj.__class__):
        # Find corresponding ENV variable or continue
        if "env_var" in f.metadata:
            name = f.metadata["env_var"]
            if not name:
                continue
        else:
            name = f.name.upper()
            if prefixes:
                found = False
                for prefix in prefixes:
                    if f"{prefix}{name}" in os.environ:
                        name = f"{prefix}{name}"
                        break
                if not allow_no_prefix and not found:
                    continue
        if name not in os.environ:
            continue
        value = os.getenv(name)

        # Convert ENV value to the fields type
        if f.type is type(int | None):
            if value == "":
                value = None
            elif not value.isdigit():
                raise ValueError(f"Incorrect ENV variable: {name} is not an integer")
        elif f.type is bool:
            value = value.upper() in TRUE_VALUES
        elif f.type is int:
            if not value.isdigit():
                raise ValueError(f"Incorrect ENV variable: {name} is not an integer")
        elif f.type is list:
            try:
                if not value:
                    value = []
                else:
                    if all(c in value for c in ('[', ']', '\"')):
                        value = json.loads(value)
                    else:
                        value = [v.strip() for v in value.split(',') if v.strip()]
            except ValueError | JSONDecodeError:
                raise ValueError(f"Incorrect ENV variable: {name} is not a list")

        setattr(obj, f.name, value)
    return obj
