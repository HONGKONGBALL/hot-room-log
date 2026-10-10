"""QA section L. CSV import. State carries from case 98 through 109."""

import csv
import io
from datetime import datetime, timedelta

from tests.htmltool import find_all, html_text, one, parse
from hotroom.validate import MSG_NAME, MSG_TEMP

CN = "自修室 2F"

F1 = (
    "room,taken_at,temp_c,rh_percent,note\n"
    "demo classroom 3f,2026-09-17 15:00,30,88,Projector on\n"
    f"{CN},2026-09-17 16:00,28,84,\n"
    f"{CN},2026-09-17 16:00,28,84,\n"
    "Demo Library Corner,2026-09-14 10:00,23.5,55,\n"
    "Demo Classroom 3F,2026-09-17 16:00,80,50,\n"
    ",2026-09-17 16:00,25,50,\n"
).encode("utf-8")


def _post_file(client, raw, filename="import.csv"):
    return client.post(
        "/import",
        data={"file": (io.BytesIO(raw), filename)},
        content_type="multipart/form-data",
    )


def _summary(response):
    root = parse(response.get_data(as_text=True))
    items = [item.text() for item in find_all(one(root, "ul", attrs={"id": "import-summary"}), "li")]
    errors = [item.text() for item in find_all(one(root, "ul", attrs={"id": "import-errors"}), "li")]
    return items, errors


def _rooms(client):
    return client.get("/api/rooms").get_json()


def _room(rooms, room_id):
    return next(room for room in rooms if room["id"] == room_id)


def _bulk(count, name="Bulk Room"):
    lines = ["room,taken_at,temp_c,rh_percent"]
    start = datetime(2026, 1, 1, 0, 0)
    for index in range(count):
        moment = start + timedelta(minutes=index)
        lines.append(f"{name},{moment:%Y-%m-%d %H:%M},25,50")
    return ("\n".join(lines) + "\n").encode("utf-8")


def test_98_import_form(client):
    response = client.get("/import")
    assert response.status_code == 200
    root = parse(response.get_data(as_text=True))
    form = one(root, "form")
    assert form.attrs.get("method", "").lower() == "post"
    assert "multipart/form-data" in form.attrs.get("enctype", "")
    field = one(root, "input", attrs={"type": "file", "name": "file"})
    labels = [label for label in find_all(root, "label") if label.attrs.get("for") == field.attrs["id"]]
    assert len(labels) == 1
    text = html_text(response)
    for word in ("room", "taken_at", "temp_c", "rh_percent"):
        assert word in text


def test_99_import_f1(client):
    response = _post_file(client, F1, "f1.csv")
    assert response.status_code == 200
    items, errors = _summary(response)
    assert items == [
        "Readings added: 2",
        "New rooms: 1",
        "Duplicates skipped: 2",
        "Invalid rows skipped: 2",
    ]
    assert f"Row 6: {MSG_TEMP}" in errors
    assert f"Row 7: {MSG_NAME}" in errors


def test_100_import_f1_state(client):
    rooms = _rooms(client)
    assert len(rooms) == 4
    room2 = _room(rooms, 2)
    assert room2["reading_count"] == 7
    assert room2["latest"]["taken_at"] == "2026-09-17 15:00"
    assert room2["latest"]["humidex"] == 45.1
    assert room2["latest"]["band"] == "Dangerous"
    room4 = _room(rooms, 4)
    assert room4["name"] == CN
    assert room4["is_sample"] is False
    assert room4["reading_count"] == 1
    assert room4["latest"]["taken_at"] == "2026-09-17 16:00"
    assert room4["latest"]["humidex"] == 40.0
    assert room4["latest"]["band"] == "Great discomfort"
    assert _room(rooms, 3)["reading_count"] == 6
    readings = client.get("/api/rooms/2/readings").get_json()
    assert readings[-1]["note"] == "Projector on"


def test_101_import_f1_again(client):
    before = [(room["id"], room["reading_count"]) for room in _rooms(client)]
    response = _post_file(client, F1, "f1.csv")
    assert response.status_code == 200
    items, _errors = _summary(response)
    assert items == [
        "Readings added: 0",
        "New rooms: 0",
        "Duplicates skipped: 4",
        "Invalid rows skipped: 2",
    ]
    after = [(room["id"], room["reading_count"]) for room in _rooms(client)]
    assert after == before


def test_102_missing_column(client):
    raw = "room,taken_at,temp_c\nDemo Classroom 3F,2026-09-17 18:00,30\n".encode()
    response = _post_file(client, raw, "missing.csv")
    assert response.status_code == 400
    assert "Missing column(s): rh_percent" in html_text(response)
    assert _room(_rooms(client), 2)["reading_count"] == 7


def test_103_empty_and_missing_file(client):
    empty = _post_file(client, b"", "empty.csv")
    assert empty.status_code == 400
    assert "The CSV file is empty." in html_text(empty)
    missing = client.post("/import", data={}, content_type="multipart/form-data")
    assert missing.status_code == 400
    assert "Choose a CSV file to import." in html_text(missing)


def test_104_bad_encoding(client):
    before = client.get("/api/rooms").data
    raw = "room,taken_at,temp_c,rh_percent\n\xff\xfe\xfa,2026-09-17 18:00,30,50\n".encode("latin-1")
    response = _post_file(client, raw, "bad.csv")
    assert response.status_code == 400
    assert "The file must be a UTF-8 CSV file." in html_text(response)
    assert client.get("/api/rooms").data == before


def test_105_bom_and_header_case(client):
    body = " Room , TAKEN_AT ,Temp_C,rh_percent\nDemo Library Corner,2026-09-17 18:00,24,70\n"
    raw = b"\xef\xbb\xbf" + body.encode("utf-8")
    response = _post_file(client, raw, "bom.csv")
    assert response.status_code == 200
    items, _errors = _summary(response)
    assert "Readings added: 1" in items
    assert _room(_rooms(client), 3)["reading_count"] == 7


def test_106_row_limit(client):
    too_many = _post_file(client, _bulk(2001), "too-many.csv")
    assert too_many.status_code == 400
    assert "Too many rows (max 2000)." in html_text(too_many)
    names = [room["name"] for room in _rooms(client)]
    assert "Bulk Room" not in names
    accepted = _post_file(client, _bulk(2000), "bulk.csv")
    assert accepted.status_code == 200
    items, _errors = _summary(accepted)
    assert "Readings added: 2000" in items
    assert "New rooms: 1" in items
    bulk = next(room for room in _rooms(client) if room["name"] == "Bulk Room")
    assert bulk["reading_count"] == 2000


def test_107_too_large(client):
    before = client.get("/api/rooms").data
    payload = b"room,taken_at,temp_c,rh_percent\n" + (b"x" * (1500 * 1024))
    response = _post_file(client, payload, "huge.csv")
    assert response.status_code == 413
    assert "File too large (max 1 MB)." in html_text(response)
    assert client.get("/api/rooms").data == before


def test_108_round_trip(client):
    assert client.post("/reset").status_code == 302
    created = client.post("/rooms", data={"name": "My Classroom"})
    assert created.status_code == 302
    assert created.headers["Location"].endswith("/rooms/4")
    added = client.post(
        "/rooms/4/readings",
        data={"temp_c": "30", "rh_percent": "88", "taken_at": "2026-09-17T15:00"},
    )
    assert added.status_code == 302
    noted = client.post(
        "/rooms/3/readings",
        data={
            "temp_c": "31",
            "rh_percent": "79",
            "taken_at": "2026-09-17T16:00",
            "note": 'Fan "max", window shut',
        },
    )
    assert noted.status_code == 302
    exported = client.get("/export.csv")
    text = exported.data.decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(text)))
    assert len(rows) - 1 == 20
    assert client.post("/reset").status_code == 302
    response = _post_file(client, exported.data, "round.csv")
    assert response.status_code == 200
    items, _errors = _summary(response)
    assert items == [
        "Readings added: 2",
        "New rooms: 1",
        "Duplicates skipped: 18",
        "Invalid rows skipped: 0",
    ]
    rooms = _rooms(client)
    assert len(rooms) == 4
    assert _room(rooms, 3)["reading_count"] == 7
    classroom = next(room for room in rooms if room["name"] == "My Classroom")
    assert classroom["reading_count"] == 1
    readings = client.get("/api/rooms/3/readings").get_json()
    match = [row for row in readings if row["note"] == 'Fan "max", window shut']
    assert len(match) == 1


def test_109_ignore_derived_columns(client):
    raw = (
        "room,taken_at,temp_c,rh_percent,humidex,band\n"
        "Demo Library Corner,2026-09-17 19:00,34,65,1.0,Comfortable\n"
    ).encode()
    response = _post_file(client, raw, "derived.csv")
    assert response.status_code == 200
    items, _errors = _summary(response)
    assert "Readings added: 1" in items
    readings = client.get("/api/rooms/3/readings").get_json()
    match = [row for row in readings if row["taken_at"] == "2026-09-17 19:00"]
    assert len(match) == 1
    assert match[0]["humidex"] == 47.6
    assert match[0]["band"] == "Dangerous"
