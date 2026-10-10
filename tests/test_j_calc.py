"""QA section J. Calculator."""

import json

from hotroom.validate import MSG_RH, MSG_TEMP
from tests.htmltool import find_all, html_text, one, parse, raw_html


def test_84_empty(client):
    response = client.get("/calc")
    assert response.status_code == 200
    root = parse(raw_html(response))
    for name in ("temp_c", "rh_percent", "temp_c_b", "rh_percent_b"):
        field = one(root, "input", attrs={"name": name})
        labels = [
            label
            for label in find_all(root, "label")
            if label.attrs.get("for") == field.attrs.get("id")
        ]
        assert len(labels) == 1
    hrefs = [link.attrs.get("href", "") for link in find_all(root, "a")]
    assert any(
        "temp_c=35" in href and "rh_percent=40" in href and "temp_c_b=30" in href and "rh_percent_b=85" in href
        for href in hrefs
    )
    assert find_all(root, "section", cls="result") == []
    text = html_text(response)
    for piece in ("Below 30", "30 to 39.9", "40 to 45", "Above 45"):
        assert piece in text


def test_85_condition_a(client):
    response = client.get("/calc?temp_c=30&rh_percent=85")
    assert response.status_code == 200
    root = parse(raw_html(response))
    results = find_all(root, "section", cls="result")
    assert len(results) == 1
    assert results[0].attrs["data-condition"] == "a"
    assert results[0].attrs["data-humidex"] == "44.4"
    assert results[0].attrs["data-band"] == "great"
    text = html_text(response)
    for piece in ("Humidex 44.4", "Great discomfort", "Dew point 27.2 °C", "Humidity adds +14.4"):
        assert piece in text
    for piece in ("42.29 hPa", "35.94 hPa", "1.7729"):
        assert piece in text
    assert find_all(root, attrs={"id": "compare"}) == []


def test_86_compare_hotter(client):
    response = client.get("/calc?temp_c=35&rh_percent=40&temp_c_b=30&rh_percent_b=85")
    assert response.status_code == 200
    root = parse(raw_html(response))
    results = {item.attrs["data-condition"]: item for item in find_all(root, "section", cls="result")}
    assert results["a"].attrs["data-humidex"] == "41.9"
    assert results["a"].attrs["data-band"] == "great"
    assert results["b"].attrs["data-humidex"] == "44.4"
    assert results["b"].attrs["data-band"] == "great"
    assert one(root, attrs={"id": "compare"}).text() == (
        "Condition B feels 2.5 humidex points hotter than condition A."
    )


def test_87_cooler_and_equal(client):
    cooler = parse(raw_html(client.get("/calc?temp_c=30&rh_percent=85&temp_c_b=35&rh_percent_b=40")))
    assert one(cooler, attrs={"id": "compare"}).text() == (
        "Condition B feels 2.5 humidex points cooler than condition A."
    )
    same = parse(raw_html(client.get("/calc?temp_c=30&rh_percent=85&temp_c_b=30&rh_percent_b=85")))
    assert one(same, attrs={"id": "compare"}).text() == "Both conditions have the same humidex."


def test_88_invalid_temp(client):
    response = client.get("/calc?temp_c=60&rh_percent=50")
    assert response.status_code == 400
    root = parse(raw_html(response))
    assert one(root, attrs={"id": "temp_c-error"}).text() == MSG_TEMP
    assert one(root, "input", attrs={"name": "temp_c"}).attrs.get("value") == "60"
    assert find_all(root, "section", cls="result") == []


def test_89_partial_b(client):
    response = client.get("/calc?temp_c=30&rh_percent=85&temp_c_b=30&rh_percent_b=")
    assert response.status_code == 400
    root = parse(raw_html(response))
    assert one(root, attrs={"id": "rh_percent_b-error"}).text() == MSG_RH


def test_90_empty_submit(client):
    response = client.get("/calc?temp_c=&rh_percent=")
    assert response.status_code == 400
    text = html_text(response)
    assert MSG_TEMP in text
    assert MSG_RH in text


def test_91_calculator_does_not_write(client):
    rooms = json.loads(client.get("/api/rooms").get_data(as_text=True))
    assert len(rooms) == 3
    assert [room["reading_count"] for room in rooms] == [6, 6, 6]
