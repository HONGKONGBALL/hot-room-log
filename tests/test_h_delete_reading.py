"""QA section H. Delete a reading."""

from urllib.parse import urlparse

from tests.htmltool import find_all, html_text, one, parse, raw_html


def test_72_delete_latest(client):
    response = client.post("/readings/6/delete")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/rooms/1")
    page = client.get(urlparse(response.headers["Location"]).path)
    assert "Reading deleted." in html_text(page)
    root = parse(raw_html(page))
    rows = [
        row
        for row in find_all(one(root, "table", attrs={"id": "readings"}), "tr")
        if row.attrs.get("data-reading-id")
    ]
    assert len(rows) == 5
    latest = one(root, attrs={"id": "latest"}).text()
    assert "42.1" in latest
    assert "Great discomfort" in latest
    assert "Taken 2026-09-16 10:00" in latest
    home = parse(raw_html(client.get("/")))
    card = [
        item
        for item in find_all(home, "article", cls="room-card")
        if item.attrs.get("data-room-id") == "1"
    ][0]
    assert card.attrs["data-band"] == "great"


def test_73_unknown_and_method(client):
    assert client.post("/readings/99999/delete").status_code == 404
    assert client.get("/readings/1/delete").status_code == 405
