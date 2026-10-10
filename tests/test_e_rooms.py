"""QA section E. Create, validate and delete rooms."""

import csv
import io
import json
from urllib.parse import urlparse

from hotroom.validate import MSG_DUP, MSG_NAME
from tests.htmltool import find_all, html_text, parse, raw_html

CN = "自修室 2F"
EMPTY = "No rooms yet. Add one below, or reset to load the sample data."


def _json(response):
    return json.loads(response.get_data(as_text=True))


def _follow(client, response):
    location = urlparse(response.headers["Location"])
    return client.get(location.path)


def test_42_create_room(client):
    response = client.post("/rooms", data={"name": "My Classroom"})
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/rooms/4")
    page = _follow(client, response)
    assert page.status_code == 200
    text = html_text(page)
    assert "Room added." in text
    assert "No readings yet." in text
    root = parse(raw_html(page))
    assert find_all(root, "svg", cls="chart") == []
    assert find_all(root, cls="banner-sample") == []
    home = parse(raw_html(client.get("/")))
    cards = [
        card
        for card in find_all(home, "article", cls="room-card")
        if card.attrs.get("data-room-id") == "4"
    ]
    assert len(cards) == 1
    assert cards[0].attrs["data-band"] == "none"
    assert "No readings yet" in cards[0].text()
    assert find_all(cards[0], "span", cls="tag-sample") == []
    rooms = _json(client.get("/api/rooms"))
    room = rooms[3]
    assert room["reading_count"] == 0
    assert room["great_or_above_count"] == 0
    assert room["latest"] is None
    assert room["highest"] is None
    assert room["is_sample"] is False


def test_43_blank_name(client):
    response = client.post("/rooms", data={"name": "   "})
    assert response.status_code == 400
    assert MSG_NAME in html_text(response)
    assert len(_json(client.get("/api/rooms"))) == 4


def test_44_length(client):
    too_long = "a" * 61
    response = client.post("/rooms", data={"name": too_long})
    assert response.status_code == 400
    assert MSG_NAME in html_text(response)
    root = parse(raw_html(response))
    field = find_all(root, "input", attrs={"name": "name"})[0]
    assert field.attrs.get("value") == too_long
    ok = client.post("/rooms", data={"name": "b" * 60})
    assert ok.status_code == 302
    assert ok.headers["Location"].endswith("/rooms/5")


def test_45_duplicates(client):
    for name in ("demo estate study room", "  My Classroom  "):
        response = client.post("/rooms", data={"name": name})
        assert response.status_code == 400
        assert MSG_DUP in html_text(response)
    assert len(_json(client.get("/api/rooms"))) == 5


def test_46_trimmed_name(client):
    response = client.post("/rooms", data={"name": "  Lab 2F  "})
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/rooms/6")
    names = [room["name"] for room in _json(client.get("/api/rooms"))]
    assert "Lab 2F" in names


def test_47_chinese_name(client):
    response = client.post("/rooms", data={"name": CN})
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/rooms/7")
    page = parse(raw_html(client.get("/rooms/7")))
    heading = find_all(page, "h1")
    assert len(heading) == 1
    assert CN in heading[0].text()
    assert CN in html_text(client.get("/"))


def test_48_delete_room(client):
    response = client.post("/rooms/1/delete")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    page = _follow(client, response)
    assert "Room deleted." in html_text(page)
    assert [room["id"] for room in _json(client.get("/api/rooms"))] == [2, 3, 4, 5, 6, 7]
    missing = client.get("/api/rooms/1/readings")
    assert missing.status_code == 404
    exported = client.get("/export.csv")
    rows = list(csv.reader(io.StringIO(exported.data.decode("utf-8-sig"))))
    assert len(rows) - 1 == 12


def test_49_missing_and_methods(client):
    missing = client.post("/rooms/999/delete")
    assert missing.status_code == 404
    assert client.get("/rooms/2/delete").status_code == 405
    assert client.get("/rooms").status_code == 405


def test_50_no_sample_banner(client):
    assert client.post("/rooms/2/delete").status_code == 302
    assert client.post("/rooms/3/delete").status_code == 302
    page = client.get("/")
    root = parse(raw_html(page))
    assert find_all(root, cls="banner-sample") == []
    assert "Sample data — fictional rooms and readings for demonstration." not in html_text(page)
    assert len(find_all(root, "article", cls="room-card")) == 4


def test_51_empty_then_reset(client):
    for room_id in (4, 5, 6, 7):
        assert client.post(f"/rooms/{room_id}/delete").status_code == 302
    page = client.get("/")
    assert EMPTY in html_text(page)
    root = parse(raw_html(page))
    assert find_all(root, "form", attrs={"action": "/rooms"})
    reset = client.post("/reset")
    assert reset.status_code == 302
    home = client.get("/")
    text = html_text(home)
    assert "Sample data — fictional rooms and readings for demonstration." in text
    cards = find_all(parse(raw_html(home)), "article", cls="room-card")
    assert len(cards) == 3
