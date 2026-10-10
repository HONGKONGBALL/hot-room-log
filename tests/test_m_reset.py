"""QA section M. Reset on a fresh database."""

from tests.htmltool import html_text


def test_110_reset_restores_seed(client):
    assert client.post("/rooms", data={"name": "Extra"}).status_code == 302
    added = client.post(
        "/rooms/1/readings",
        data={"temp_c": "30", "rh_percent": "85", "taken_at": "2026-09-17T10:00"},
    )
    assert added.status_code == 302
    deleted = client.post("/readings/1/delete")
    assert deleted.status_code == 302
    response = client.post("/reset")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    page = client.get("/")
    assert "Sample data restored." in html_text(page)
    rooms = client.get("/api/rooms").get_json()
    assert [room["id"] for room in rooms] == [1, 2, 3]
    assert [room["reading_count"] for room in rooms] == [6, 6, 6]
    readings = client.get("/api/rooms/1/readings").get_json()
    assert [row["id"] for row in readings] == [1, 2, 3, 4, 5, 6]


def test_111_get_reset(client):
    response = client.get("/reset")
    assert response.status_code == 405
