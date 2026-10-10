"""QA section A. Formulas and bands."""

import json

from hotroom.validate import MSG_RH, MSG_TEMP


def _get(client, query):
    response = client.get("/api/humidex" + query)
    return response


def test_01_to_14_values(client):
    cases = [
        ("?temp_c=34&rh_percent=65", 34, 65, 47.6, "Dangerous", "dangerous", 26.5, 13.6),
        ("?temp_c=23&rh_percent=80", 23, 80, 29.9, "Comfortable", "comfortable", 19.4, 6.9),
        ("?temp_c=24&rh_percent=70", 24, 70, 30.0, "Some discomfort", "some", 18.2, 6.0),
        ("?temp_c=34&rh_percent=39", 34, 39, 39.9, "Some discomfort", "some", 18.1, 5.9),
        ("?temp_c=35&rh_percent=34", 35, 34, 40.0, "Great discomfort", "great", 16.8, 5.0),
        ("?temp_c=35&rh_percent=50", 35, 50, 45.0, "Great discomfort", "great", 23.0, 10.0),
        ("?temp_c=31&rh_percent=79", 31, 79, 45.1, "Dangerous", "dangerous", 26.9, 14.1),
        ("?temp_c=30&rh_percent=85", 30, 85, 44.4, "Great discomfort", "great", 27.2, 14.4),
        ("?temp_c=35&rh_percent=40", 35, 40, 41.9, "Great discomfort", "great", 19.4, 6.9),
        ("?temp_c=25&rh_percent=20", 25, 20, 23.0, "Comfortable", "comfortable", 0.5, -2.0),
        ("?temp_c=30&rh_percent=100", 30, 100, 47.9, "Dangerous", "dangerous", 30.0, 17.9),
        ("?temp_c=29.5&rh_percent=76", 29.5, 76, 41.3, "Great discomfort", "great", 24.8, 11.8),
        ("?temp_c=0&rh_percent=1", 0, 1, -5.5, "Comfortable", "comfortable", -50.0, -5.5),
        ("?temp_c=50&rh_percent=100", 50, 100, 112.7, "Dangerous", "dangerous", 50.0, 62.7),
    ]
    for query, temp, rh, humidex, band, key, dew, effect in cases:
        response = _get(client, query)
        assert response.status_code == 200, query
        assert response.headers["Content-Type"].startswith("application/json")
        data = json.loads(response.get_data(as_text=True))
        assert data["temp_c"] == temp
        assert data["rh_percent"] == rh
        assert data["humidex"] == humidex
        assert data["band"] == band
        assert data["band_key"] == key
        assert data["dew_point_c"] == dew
        assert data["humidity_effect"] == effect


def test_15_temp_above_range(client):
    response = _get(client, "?temp_c=50.1&rh_percent=50")
    assert response.status_code == 400
    assert json.loads(response.get_data(as_text=True)) == {"errors": {"temp_c": MSG_TEMP}}


def test_16_temp_below_range(client):
    response = _get(client, "?temp_c=-0.5&rh_percent=50")
    assert response.status_code == 400
    assert json.loads(response.get_data(as_text=True))["errors"]["temp_c"] == MSG_TEMP


def test_17_humidity_edges(client):
    for query in ("?temp_c=30&rh_percent=0.5", "?temp_c=30&rh_percent=100.1"):
        response = _get(client, query)
        assert response.status_code == 400
        assert json.loads(response.get_data(as_text=True))["errors"]["rh_percent"] == MSG_RH


def test_18_temp_pattern(client):
    for query in (
        "?temp_c=30.25&rh_percent=50",
        "?temp_c=30%2C5&rh_percent=50",
        "?temp_c=abc&rh_percent=50",
    ):
        response = _get(client, query)
        assert response.status_code == 400, query
        assert json.loads(response.get_data(as_text=True))["errors"]["temp_c"] == MSG_TEMP


def test_19_missing_fields(client):
    first = _get(client, "?temp_c=30")
    assert first.status_code == 400
    body = json.loads(first.get_data(as_text=True))
    assert list(body["errors"]) == ["rh_percent"]
    assert body["errors"]["rh_percent"] == MSG_RH

    second = _get(client, "")
    assert second.status_code == 400
    errors = json.loads(second.get_data(as_text=True))["errors"]
    assert errors["temp_c"] == MSG_TEMP
    assert errors["rh_percent"] == MSG_RH


def test_20_trimmed_input(client):
    response = _get(client, "?temp_c=%2030%20&rh_percent=85")
    assert response.status_code == 200
    assert json.loads(response.get_data(as_text=True))["humidex"] == 44.4
