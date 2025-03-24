import textwrap

import microcore as mc

from ema.utils import format_dt_human


def issue_view(issue: dict) -> str:
    """
    Args:
        issue: dict, fields should correspond to the issues table columns
    """
    return mc.tpl(
        "issue_view.j2",
        issue=issue,
        indent=textwrap.indent,
        date_format=format_dt_human,
    )
