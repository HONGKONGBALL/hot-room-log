"""Shared validation for forms, the JSON API and CSV import."""

import math
import re
from datetime import datetime

MSG_TEMP = (
    "Temperature must be a number from 0 to 50 °C with at most one decimal place."
)
MSG_RH = "Humidity must be a number from 1 to 100 % with at most one decimal place."
MSG_TIME = "Time must be a real date and time in the form YYYY-MM-DD HH:MM."
MSG_FUTURE = "Time cannot be in the future."
MSG_NOTE = "Note must be 140 characters or fewer."
MSG_NAME = "Room name must be 1 to 60 characters."
MSG_DUP = "A room with this name already exists."
MSG_BODY = "Send a JSON object."

_NUMBER = re.compile(r"^-?\d+(\.\d)?$")
_TIME = re.compile(r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}$")


def now_minute(moment=None):
    moment = moment or datetime.now()
    return moment.replace(second=0, microsecond=0)


def _number_text(value):
    """Turn a form string or JSON number into text for the pattern check."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        return repr(value)
    if isinstance(value, str):
        return value.strip()
    return None


def _parse_number(value, low, high, message):
    text = _number_text(value)
    if text is None or _NUMBER.fullmatch(text) is None:
        return None, message
    number = float(text)
    if number < low or number > high:
        return None, message
    return number, None


def parse_temp(value):
    return _parse_number(value, 0, 50, MSG_TEMP)


def parse_rh(value):
    return _parse_number(value, 1, 100, MSG_RH)


def parse_name(value):
    if not isinstance(value, str):
        return None, MSG_NAME
    text = value.strip()
    if not text or len(text) > 60:
        return None, MSG_NAME
    return text, None


def parse_note(value):
    if value is None:
        return None, None
    if not isinstance(value, str):
        return None, MSG_NOTE
    text = value.strip()
    if len(text) > 140:
        return None, MSG_NOTE
    if text == "":
        return None, None
    return text, None


def parse_time(value, now=None):
    """Empty or missing means the current local minute. Future times are rejected."""
    current = now_minute(now)
    if value is None:
        return current, None
    if not isinstance(value, str):
        return None, MSG_TIME
    text = value.strip()
    if text == "":
        return current, None
    if _TIME.fullmatch(text) is None:
        return None, MSG_TIME
    try:
        parsed = datetime.strptime(text.replace("T", " "), "%Y-%m-%d %H:%M")
    except ValueError:
        return None, MSG_TIME
    if parsed > current:
        return None, MSG_FUTURE
    return parsed, None


def format_taken_at(moment):
    return moment.strftime("%Y-%m-%d %H:%M")


def validate_reading(data, now=None):
    """Validate a reading dict. Missing temperature or humidity is an error.

    Missing time means now. Missing note means no note. Every invalid field
    is reported.
    """
    errors = {}
    if "temp_c" not in data:
        temp, temp_error = None, MSG_TEMP
    else:
        temp, temp_error = parse_temp(data.get("temp_c"))
    if temp_error:
        errors["temp_c"] = temp_error

    if "rh_percent" not in data:
        humidity, rh_error = None, MSG_RH
    else:
        humidity, rh_error = parse_rh(data.get("rh_percent"))
    if rh_error:
        errors["rh_percent"] = rh_error

    if "taken_at" not in data:
        taken, time_error = parse_time(None, now=now)
    else:
        taken, time_error = parse_time(data.get("taken_at"), now=now)
    if time_error:
        errors["taken_at"] = time_error
        taken = None

    if "note" not in data:
        note, note_error = None, None
    else:
        note, note_error = parse_note(data.get("note"))
    if note_error:
        errors["note"] = note_error

    parsed = {
        "temp_c": temp,
        "rh_percent": humidity,
        "taken_at": None if taken is None else format_taken_at(taken),
        "note": note,
    }
    return errors, parsed
