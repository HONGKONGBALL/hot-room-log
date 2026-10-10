"""QA section G. Add a reading through the form."""

import json
from datetime import datetime
from urllib.parse import urlparse

from hotroom.validate import MSG_FUTURE, MSG_NOTE, MSG_RH, MSG_TEMP, MSG_TIME
from tests.htmltool import find_all, html_text, one, parse, raw_html


def _json(response):
    return json.loads(response.get_data(as_text=True))


def _follow(client, response):
    return client.get(urlparse(response.headers["Location"]).path)


def test_61_add(client):
    response = client.post(
        "/rooms/3/readings",
        data={
            "temp_c": "31",
            "rh_percent": "79",
            "taken_at": "2026-09-17T15:00",
            "note": "Air-con off",
        },
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/rooms/3")
    page = _follow(client, response)
    assert "Reading added." in html_text(page)
    root = parse(raw_html(page))
    rows = [
        row
        for row in find_all(one(root, "table", attrs={"id": "readings"}), "tr")
        if row.attrs.get("data-reading-id")
    ]
    assert len(rows) == 7
    last = rows[-1]
    assert last.attrs["data-reading-id"] == "19"
    text = last.text()
    for piece in ("2026-09-17 15:00", "26.9", "45.1", "Dangerous", "Air-con off"):
        assert piece in text
    latest = one(root, attrs={"id": "latest"}).text()
    assert "45.1" in latest
    assert "Dangerous" in latest


def test_62_dashboard_card(client):
    root = parse(raw_html(client.get("/")))
    card = [
        item
        for item in find_all(root, "article", cls="room-card")
        if item.attrs.get("data-room-id") == "3"
    ][0]
    assert card.attrs["data-band"] == "dangerous"
    text = card.text()
    assert "45.1" in text
    assert "7 readings" in text
    assert "Great discomfort or above: 1 of 7" in text


def test_63_earlier_reading(client):
    response = client.post(
        "/rooms/3/readings",
        data={"temp_c": "24", "rh_percent": "70", "taken_at": "2026-09-13 09:00"},
    )
    assert response.status_code == 302
    root = parse(raw_html(client.get("/rooms/3")))
    table = one(root, "table", attrs={"id": "readings"})
    rows = [row for row in find_all(table, "tr") if row.attrs.get("data-reading-id")]
    assert "2026-09-13 09:00" in rows[0].text()
    assert "30.0" in rows[0].text()
    assert "Some discomfort" in rows[0].text()
    chart = one(root, "svg", cls="chart")
    point = find_all(chart, "circle", cls="point")[0]
    assert point.attrs["data-taken-at"] == "2026-09-13 09:00"
    assert point.attrs["data-humidex"] == "30.0"
    assert "band-some" in point.classes()
    stats = one(root, "ul", attrs={"id": "stats"}).text()
    assert "Readings: 8" in stats
    assert "Period: 2026-09-13 to 2026-09-17" in stats
    assert "45.1" in one(root, attrs={"id": "latest"}).text()


def test_64_invalid_temp_kept(client):
    response = client.post(
        "/rooms/2/readings",
        data={"temp_c": "80", "rh_percent": "50", "taken_at": "2026-09-17T15:00"},
    )
    assert response.status_code == 400
    root = parse(raw_html(response))
    error = one(root, "p", attrs={"id": "temp_c-error"})
    assert error.text() == MSG_TEMP
    field = one(root, "input", attrs={"name": "temp_c"})
    assert field.attrs.get("value") == "80"
    assert field.attrs.get("aria-invalid") == "true"
    assert field.attrs.get("aria-describedby") == "temp_c-error"
    humidity = one(root, "input", attrs={"name": "rh_percent"})
    assert humidity.attrs.get("value") == "50"
    rooms = _json(client.get("/api/rooms"))
    assert rooms[1]["reading_count"] == 6


def test_65_more_invalid(client):
    cases = [
        ({"temp_c": "30", "rh_percent": "0"}, MSG_RH),
        ({"temp_c": "30.25", "rh_percent": "50"}, MSG_TEMP),
        ({"temp_c": "abc", "rh_percent": "50"}, MSG_TEMP),
    ]
    for data, message in cases:
        response = client.post("/rooms/2/readings", data=data)
        assert response.status_code == 400
        assert message in html_text(response)
    assert _json(client.get("/api/rooms"))[1]["reading_count"] == 6


def test_66_both_empty(client):
    response = client.post("/rooms/2/readings", data={"temp_c": "", "rh_percent": ""})
    assert response.status_code == 400
    text = html_text(response)
    assert MSG_TEMP in text
    assert MSG_RH in text


def test_67_bad_times(client):
    future = client.post(
        "/rooms/2/readings",
        data={"temp_c": "30", "rh_percent": "50", "taken_at": "2099-01-01T10:00"},
    )
    assert future.status_code == 400
    assert MSG_FUTURE in html_text(future)
    invalid = client.post(
        "/rooms/2/readings",
        data={"temp_c": "30", "rh_percent": "50", "taken_at": "2026-13-01T10:00"},
    )
    assert invalid.status_code == 400
    assert MSG_TIME in html_text(invalid)


def test_68_long_note(client):
    response = client.post(
        "/rooms/2/readings",
        data={"temp_c": "30", "rh_percent": "50", "note": "n" * 141},
    )
    assert response.status_code == 400
    assert MSG_NOTE in html_text(response)


def test_69_empty_time_is_now(client):
    response = client.post(
        "/rooms/2/readings",
        data={"temp_c": "26", "rh_percent": "60", "taken_at": ""},
    )
    assert response.status_code == 302
    rows = _json(client.get("/api/rooms/2/readings"))
    last = rows[-1]
    moment = datetime.strptime(last["taken_at"], "%Y-%m-%d %H:%M")
    now = datetime.now().replace(second=0, microsecond=0)
    assert abs((moment - now).total_seconds()) <= 60
    assert last["humidex"] == 31.6


def test_70_unknown_room(client):
    response = client.post("/rooms/999/readings", data={"temp_c": "30", "rh_percent": "50"})
    assert response.status_code == 404


def test_71_tie_uses_latest(client):
    created = client.post("/rooms", data={"name": "Tie Room"})
    assert created.status_code == 302
    assert created.headers["Location"].endswith("/rooms/4")
    for taken in ("2026-09-17T10:00", "2026-09-17T11:00"):
        response = client.post(
            "/rooms/4/readings",
            data={"temp_c": "30", "rh_percent": "85", "taken_at": taken},
        )
        assert response.status_code == 302
    root = parse(raw_html(client.get("/rooms/4")))
    stats = one(root, "ul", attrs={"id": "stats"}).text()
    assert "Highest: 44.4 (Great discomfort) on 2026-09-17 11:00" in stats
