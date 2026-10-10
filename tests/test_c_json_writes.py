"""QA section C. JSON writes, in order."""

import json
from datetime import datetime

from hotroom.validate import MSG_FUTURE, MSG_NOTE, MSG_TEMP, MSG_TIME


def _json(response):
    return json.loads(response.get_data(as_text=True))


def _post(client, room_id, payload, content_type="application/json", raw=None):
    if raw is None:
        raw = json.dumps(payload).encode("utf-8")
    return client.post(
        f"/api/rooms/{room_id}/readings",
        data=raw,
        content_type=content_type,
    )


def _close(value):
    moment = datetime.strptime(value, "%Y-%m-%d %H:%M")
    now = datetime.now().replace(second=0, microsecond=0)
    assert abs((moment - now).total_seconds()) <= 60


def test_28_add_known_time(client):
    response = _post(
        client,
        3,
        {
            "temp_c": 31,
            "rh_percent": 79,
            "taken_at": "2026-09-17 15:00",
            "note": "Air-con off",
        },
    )
    assert response.status_code == 201
    body = _json(response)
    assert body["id"] == 19
    assert body["room_id"] == 3
    assert body["taken_at"] == "2026-09-17 15:00"
    assert body["humidex"] == 45.1
    assert body["band"] == "Dangerous"
    assert body["dew_point_c"] == 26.9
    assert body["humidity_effect"] == 14.1
    assert body["note"] == "Air-con off"
    rooms = _json(client.get("/api/rooms"))
    room = rooms[2]
    assert room["reading_count"] == 7
    assert room["latest"]["taken_at"] == "2026-09-17 15:00"
    assert room["latest"]["humidex"] == 45.1
    assert room["latest"]["band"] == "Dangerous"
    assert room["highest"]["humidex"] == 45.1
    assert room["great_or_above_count"] == 1


def test_29_strings_and_now(client):
    response = _post(client, 3, {"temp_c": "28", "rh_percent": "84"})
    assert response.status_code == 201
    body = _json(response)
    assert body["id"] == 20
    assert body["humidex"] == 40.0
    assert body["band"] == "Great discomfort"
    _close(body["taken_at"])
    rooms = _json(client.get("/api/rooms"))
    assert rooms[2]["reading_count"] == 8


def test_30_invalid_temp_saves_nothing(client):
    response = _post(client, 3, {"temp_c": 80, "rh_percent": 50})
    assert response.status_code == 400
    assert _json(response) == {"errors": {"temp_c": MSG_TEMP}}
    rooms = _json(client.get("/api/rooms"))
    assert rooms[2]["reading_count"] == 8


def test_31_more_temp_errors(client):
    payloads = [
        {"temp_c": 30.25, "rh_percent": 50},
        {"temp_c": True, "rh_percent": 50},
        {"rh_percent": 50},
    ]
    for payload in payloads:
        response = _post(client, 3, payload)
        assert response.status_code == 400
        assert _json(response)["errors"]["temp_c"] == MSG_TEMP


def test_32_future(client):
    response = _post(
        client,
        3,
        {"temp_c": 30, "rh_percent": 50, "taken_at": "2099-01-01 10:00"},
    )
    assert response.status_code == 400
    assert _json(response)["errors"]["taken_at"] == MSG_FUTURE


def test_33_bad_times(client):
    for taken in ("2026-02-30 10:00", "17/09/2026 15:00"):
        response = _post(
            client,
            3,
            {"temp_c": 30, "rh_percent": 50, "taken_at": taken},
        )
        assert response.status_code == 400
        assert _json(response)["errors"]["taken_at"] == MSG_TIME


def test_34_note_length(client):
    too_long = _post(
        client,
        3,
        {"temp_c": 30, "rh_percent": 50, "note": "n" * 141},
    )
    assert too_long.status_code == 400
    assert _json(too_long)["errors"]["note"] == MSG_NOTE
    ok = _post(
        client,
        3,
        {
            "temp_c": 30,
            "rh_percent": 50,
            "taken_at": "2026-09-17 09:00",
            "note": "n" * 140,
        },
    )
    assert ok.status_code == 201
    assert _json(ok)["id"] == 21


def test_35_unknown_room(client):
    response = _post(client, 999, {"temp_c": 30, "rh_percent": 50})
    assert response.status_code == 404
    assert _json(response) == {"error": "Room not found"}


def test_36_bad_body(client):
    plain = _post(client, 3, None, content_type="text/plain", raw=b"not json")
    assert plain.status_code == 400
    assert _json(plain) == {"errors": {"body": "Send a JSON object."}}
    listed = _post(client, 3, None, content_type="application/json", raw=b"[1, 2]")
    assert listed.status_code == 400
    assert _json(listed) == {"errors": {"body": "Send a JSON object."}}


def test_37_order(client):
    rows = _json(client.get("/api/rooms/3/readings"))
    assert len(rows) == 9
    assert [row["id"] for row in rows] == [13, 14, 15, 16, 17, 18, 21, 19, 20]
    _close(rows[-1]["taken_at"])
