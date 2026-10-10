"""QA section B. Sample data via JSON."""

import json


def _rooms(client):
    response = client.get("/api/rooms")
    assert response.status_code == 200
    return json.loads(response.get_data(as_text=True))


def test_21_rooms(client):
    rooms = _rooms(client)
    assert len(rooms) == 3
    assert [room["id"] for room in rooms] == [1, 2, 3]
    assert [room["name"] for room in rooms] == [
        "Demo Estate Study Room",
        "Demo Classroom 3F",
        "Demo Library Corner",
    ]
    assert all(room["is_sample"] is True for room in rooms)
    assert all(room["reading_count"] == 6 for room in rooms)


def test_22_latest(client):
    rooms = _rooms(client)
    assert rooms[0]["latest"] == {
        "taken_at": "2026-09-16 15:00",
        "humidex": 47.6,
        "band": "Dangerous",
        "band_key": "dangerous",
    }
    assert rooms[1]["latest"]["taken_at"] == "2026-09-16 15:00"
    assert rooms[1]["latest"]["humidex"] == 35.0
    assert rooms[1]["latest"]["band"] == "Some discomfort"
    assert rooms[1]["latest"]["band_key"] == "some"
    assert rooms[2]["latest"]["taken_at"] == "2026-09-16 15:00"
    assert rooms[2]["latest"]["humidex"] == 28.2
    assert rooms[2]["latest"]["band"] == "Comfortable"
    assert rooms[2]["latest"]["band_key"] == "comfortable"


def test_23_highest(client):
    rooms = _rooms(client)
    assert rooms[0]["highest"]["taken_at"] == "2026-09-16 15:00"
    assert rooms[0]["highest"]["humidex"] == 47.6
    assert rooms[0]["highest"]["band"] == "Dangerous"
    assert rooms[1]["highest"]["taken_at"] == "2026-09-15 15:00"
    assert rooms[1]["highest"]["humidex"] == 40.4
    assert rooms[1]["highest"]["band"] == "Great discomfort"
    assert rooms[2]["highest"]["taken_at"] == "2026-09-15 15:00"
    assert rooms[2]["highest"]["humidex"] == 28.3
    assert rooms[2]["highest"]["band"] == "Comfortable"
    assert [room["great_or_above_count"] for room in rooms] == [6, 1, 0]


def _readings(client, room_id):
    response = client.get(f"/api/rooms/{room_id}/readings")
    assert response.status_code == 200
    return json.loads(response.get_data(as_text=True))


def test_24_room_1(client):
    rows = _readings(client, 1)
    assert [row["id"] for row in rows] == [1, 2, 3, 4, 5, 6]
    assert [row["taken_at"] for row in rows] == [
        "2026-09-14 10:00",
        "2026-09-14 15:00",
        "2026-09-15 10:00",
        "2026-09-15 15:00",
        "2026-09-16 10:00",
        "2026-09-16 15:00",
    ]
    assert [row["humidex"] for row in rows] == [40.7, 44.3, 41.3, 45.8, 42.1, 47.6]
    assert [row["dew_point_c"] for row in rows] == [24.8, 25.3, 24.8, 25.8, 25.1, 26.5]
    assert [row["band_key"] for row in rows] == [
        "great",
        "great",
        "great",
        "dangerous",
        "great",
        "dangerous",
    ]
    assert rows[3]["note"] == "Fan on, windows open"
    assert all(row["note"] is None for index, row in enumerate(rows) if index != 3)


def test_25_room_2(client):
    rows = _readings(client, 2)
    assert [row["id"] for row in rows] == [7, 8, 9, 10, 11, 12]
    assert [row["humidex"] for row in rows] == [31.6, 35.6, 32.8, 40.4, 31.2, 35.0]
    assert [row["dew_point_c"] for row in rows] == [17.6, 20.3, 18.6, 23.4, 17.1, 19.5]
    assert rows[3]["band"] == "Great discomfort"
    assert rows[3]["note"] == "Full class after lunch"
    assert all(row["band"] == "Some discomfort" for index, row in enumerate(rows) if index != 3)


def test_26_room_3(client):
    rows = _readings(client, 3)
    assert [row["id"] for row in rows] == [13, 14, 15, 16, 17, 18]
    assert [row["humidex"] for row in rows] == [26.8, 28.0, 26.8, 28.3, 26.3, 28.2]
    assert [row["dew_point_c"] for row in rows] == [13.9, 15.2, 14.8, 14.9, 13.1, 13.8]
    assert [row["humidity_effect"] for row in rows] == [3.3, 4.0, 3.8, 3.8, 2.8, 3.2]
    assert all(row["band"] == "Comfortable" for row in rows)


def test_27_missing(client):
    missing = client.get("/api/rooms/999/readings")
    assert missing.status_code == 404
    assert json.loads(missing.get_data(as_text=True)) == {"error": "Room not found"}
    nope = client.get("/api/nope")
    assert nope.status_code == 404
    assert json.loads(nope.get_data(as_text=True)) == {"error": "Not found"}
