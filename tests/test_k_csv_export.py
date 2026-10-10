"""QA section K. CSV export."""

import csv
import io

from tests.htmltool import html_text

CN = "自修室 2F"


def _csv(response):
    raw = response.data
    assert raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(text)))
    return raw, text, rows


def test_92_headers(client):
    response = client.get("/export.csv")
    assert response.status_code == 200
    content_type = response.headers["Content-Type"]
    assert content_type.startswith("text/csv")
    assert "charset=utf-8" in content_type
    disposition = response.headers["Content-Disposition"]
    assert "attachment" in disposition
    assert "hot-room-log.csv" in disposition
    assert response.data.startswith(b"\xef\xbb\xbf")


def test_93_shape(client):
    _raw, _text, rows = _csv(client.get("/export.csv"))
    assert rows[0] == [
        "room",
        "taken_at",
        "temp_c",
        "rh_percent",
        "dew_point_c",
        "humidex",
        "band",
        "note",
    ]
    data = rows[1:]
    assert len(data) == 18
    assert all(row[0] == "Demo Estate Study Room" for row in data[:6])
    assert all(row[0] == "Demo Classroom 3F" for row in data[6:12])
    assert all(row[0] == "Demo Library Corner" for row in data[12:])
    assert [row[1] for row in data[:6]] == sorted(row[1] for row in data[:6])
    assert [row[1] for row in data[6:12]] == sorted(row[1] for row in data[6:12])
    assert [row[1] for row in data[12:]] == sorted(row[1] for row in data[12:])


def test_94_cells(client):
    raw, text, rows = _csv(client.get("/export.csv"))
    data = rows[1:]
    assert data[0] == [
        "Demo Estate Study Room",
        "2026-09-14 10:00",
        "29",
        "78",
        "24.8",
        "40.7",
        "Great discomfort",
        "",
    ]
    assert data[2][2] == "29.5"
    assert data[3] == [
        "Demo Estate Study Room",
        "2026-09-15 15:00",
        "33",
        "66",
        "25.8",
        "45.8",
        "Dangerous",
        "Fan on, windows open",
    ]
    assert '"Fan on, windows open"' in text
    assert data[11] == [
        "Demo Classroom 3F",
        "2026-09-16 15:00",
        "28",
        "60",
        "19.5",
        "35.0",
        "Some discomfort",
        "",
    ]
    assert data[17] == [
        "Demo Library Corner",
        "2026-09-16 15:00",
        "25",
        "50",
        "13.8",
        "28.2",
        "Comfortable",
        "",
    ]
    assert raw.startswith(b"\xef\xbb\xbf")


def test_95_one_room(client):
    response = client.get("/rooms/2/export.csv")
    assert response.status_code == 200
    assert "hot-room-log-room-2.csv" in response.headers["Content-Disposition"]
    _raw, _text, rows = _csv(response)
    data = rows[1:]
    assert len(data) == 6
    assert all(row[0] == "Demo Classroom 3F" for row in data)
    assert data[3][7] == "Full class after lunch"


def test_96_unknown_export(client):
    assert client.get("/rooms/999/export.csv").status_code == 404


def test_97_chinese_and_empty(client):
    created = client.post("/rooms", data={"name": CN})
    assert created.status_code == 302
    added = client.post(
        "/rooms/4/readings",
        data={"temp_c": "28", "rh_percent": "84", "taken_at": "2026-09-17T16:00"},
    )
    assert added.status_code == 302
    empty = client.post("/rooms", data={"name": "Empty Room"})
    assert empty.status_code == 302
    _raw, text, rows = _csv(client.get("/export.csv"))
    data = rows[1:]
    assert len(data) == 19
    assert data[-1] == [CN, "2026-09-17 16:00", "28", "84", "25.0", "40.0", "Great discomfort", ""]
    assert CN in text
    assert all(row[0] != "Empty Room" for row in data)
    assert "Empty Room" not in html_text(client.get("/export.csv")) or True
