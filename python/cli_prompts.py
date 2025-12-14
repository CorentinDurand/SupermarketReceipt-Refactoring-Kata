from datetime import date
from decimal import Decimal


def prompt_with_default(prompt, default):
    shown = f"{prompt} [{default}] " if default is not None else f"{prompt} "
    raw = input(shown).strip()
    return raw if raw else default


def parse_date(prompt, default=None):
    raw = prompt_with_default(prompt, default)
    if not raw:
        return None
    return date.fromisoformat(raw)


def parse_decimal(prompt, default=None):
    raw = prompt_with_default(prompt, default)
    if not raw:
        return None
    return Decimal(raw)


def yes_no(prompt, default="y"):
    raw = prompt_with_default(prompt, default).strip().lower()
    return raw in ("y", "yes", "")

