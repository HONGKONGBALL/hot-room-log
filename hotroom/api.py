"""JSON routes."""

import json

from flask import Blueprint, request

from .calc import compute, json_1, json_meas
from .db import get_db, get_reading, get_room, insert_reading, list_readings, list_rooms
from .http import json_response
from .letter import enrich, great_count, pick_highest
from .validate import MSG_BODY, MSG_RH, MSG_TEMP, parse_rh, parse_temp

bp = Blueprint("api", __name__, url_prefix="/api")


def _readonly_block():
    from flask import current_app

    if current_app.config.get("READONLY"):
        return json_response({"error": "Read-only demo"}, 403)
    return None


def _room_missing():
    return json_response({"error": "Room not found"}, 404)


def _brief(reading):
    if reading is None:
        return None
    return {
        "taken_at": reading["taken_at"],
        "humidex": json_1(reading["humidex"]),
        "band": reading["band"],
        "band_key": reading["band_key"],
    }


def _room_object(room, readings):
    latest = readings[-1] if readings else None
    highest = pick_highest(readings) if readings else None
    return {
        "id": room["id"],
        "name": room["name"],
        "is_sample": bool(room["is_sample"]),
        "reading_count": len(readings),
        "great_or_above_count": great_count(readings),
        "latest": _brief(latest),
        "highest": _brief(highest),
    }


def _reading_object(reading):
    return {
        "id": reading["id"],
        "room_id": reading["room_id"],
        "taken_at": reading["taken_at"],
        "temp_c": json_meas(reading["temp_c"]),
        "rh_percent": json_meas(reading["rh_percent"]),
        "dew_point_c": json_1(reading["dew_point_c"]),
        "humidex": json_1(reading["humidex"]),
        "humidity_effect": json_1(reading["humidity_effect"]),
        "band": reading["band"],
        "band_key": reading["band_key"],
        "note": reading["note"],
    }


def _load(room_id):
    room = get_room(get_db(), room_id)
    if room is None:
        return None, None
    readings = [enrich(row) for row in list_readings(get_db(), room_id)]
    return room, readings


@bp.get("/humidex")
def humidex():
    errors = {}
    temperature = humidity = None
    if "temp_c" not in request.args:
        errors["temp_c"] = MSG_TEMP
    else:
        temperature, error = parse_temp(request.args.get("temp_c"))
        if error:
            errors["temp_c"] = error
    if "rh_percent" not in request.args:
        errors["rh_percent"] = MSG_RH
    else:
        humidity, error = parse_rh(request.args.get("rh_percent"))
        if error:
            errors["rh_percent"] = error
    if errors:
        return json_response({"errors": errors}, 400)
    result = compute(temperature, humidity)
    return json_response(
        {
            "temp_c": json_meas(temperature),
            "rh_percent": json_meas(humidity),
            "humidex": json_1(result["humidex"]),
            "band": result["band"],
            "band_key": result["band_key"],
            "dew_point_c": json_1(result["dew_point_c"]),
            "humidity_effect": json_1(result["humidity_effect"]),
        }
    )


@bp.get("/rooms")
def rooms():
    payload = []
    conn = get_db()
    for room in list_rooms(conn):
        readings = [enrich(row) for row in list_readings(conn, room["id"])]
        payload.append(_room_object(room, readings))
    return json_response(payload)


@bp.get("/rooms/<int:room_id>/readings")
def room_readings(room_id):
    room, readings = _load(room_id)
    if room is None:
        return _room_missing()
    return json_response([_reading_object(reading) for reading in readings])


@bp.post("/rooms/<int:room_id>/readings")
def add_reading(room_id):
    blocked = _readonly_block()
    if blocked:
        return blocked
    room = get_room(get_db(), room_id)
    if room is None:
        return _room_missing()
    raw = request.get_data(cache=False) or b""
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        data = None
    if not isinstance(data, dict):
        return json_response({"errors": {"body": MSG_BODY}}, 400)
    from .validate import validate_reading

    errors, parsed = validate_reading(data)
    if errors:
        return json_response({"errors": errors}, 400)
    new_id = insert_reading(
        get_db(),
        room_id,
        parsed["taken_at"],
        parsed["temp_c"],
        parsed["rh_percent"],
        parsed["note"],
    )
    stored = enrich(get_reading(get_db(), new_id))
    return json_response(_reading_object(stored), 201)
