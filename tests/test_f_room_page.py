"""QA section F. Room page."""

from datetime import datetime

from tests.htmltool import find_all, html_text, one, parse, raw_html


def _page():
    return None


def test_52_heading(client):
    response = client.get("/rooms/1")
    assert response.status_code == 200
    root = parse(raw_html(response))
    headings = find_all(root, "h1")
    assert len(headings) == 1
    assert "Demo Estate Study Room" in headings[0].text()
    assert find_all(root, cls="banner-sample")
    assert one(root, "span", cls="tag-sample").text() == "Sample"


def test_53_latest(client):
    root = parse(raw_html(client.get("/rooms/1")))
    text = one(root, attrs={"id": "latest"}).text()
    for piece in (
        "47.6",
        "Dangerous",
        "Air 34 °C",
        "Humidity 65 %",
        "Dew point 26.5 °C",
        "Humidity adds +13.6",
        "Taken 2026-09-16 15:00",
    ):
        assert piece in text


def test_54_stats(client):
    root = parse(raw_html(client.get("/rooms/1")))
    text = one(root, "ul", attrs={"id": "stats"}).text()
    for piece in (
        "Readings: 6",
        "Period: 2026-09-14 to 2026-09-16",
        "Highest: 47.6 (Dangerous) on 2026-09-16 15:00",
        "Great discomfort or above: 6 of 6",
    ):
        assert piece in text


def test_55_chart(client):
    root = parse(raw_html(client.get("/rooms/1")))
    charts = find_all(root, "svg", cls="chart")
    assert len(charts) == 1
    assert charts[0].attrs.get("role") == "img"
    assert find_all(charts[0], "title")
    points = find_all(charts[0], "circle", cls="point")
    assert len(points) == 6
    taken = [point.attrs["data-taken-at"] for point in points]
    assert taken == [
        "2026-09-14 10:00",
        "2026-09-14 15:00",
        "2026-09-15 10:00",
        "2026-09-15 15:00",
        "2026-09-16 10:00",
        "2026-09-16 15:00",
    ]
    xs = [float(point.attrs["cx"]) for point in points]
    assert xs == sorted(xs) and len(set(xs)) == 6
    assert [point.attrs["data-humidex"] for point in points] == [
        "40.7",
        "44.3",
        "41.3",
        "45.8",
        "42.1",
        "47.6",
    ]
    assert "band-dangerous" in points[-1].classes()
    strips = find_all(charts[0], "rect", cls="strip")
    assert len(strips) == 4
    classes = [" ".join(strip.classes()) for strip in strips]
    for key in ("band-comfortable", "band-some", "band-great", "band-dangerous"):
        assert any(key in item for item in classes)
    assert len(find_all(charts[0], "polyline", cls="trend")) == 1


def test_56_table(client):
    root = parse(raw_html(client.get("/rooms/1")))
    table = one(root, "table", attrs={"id": "readings"})
    rows = find_all(table, "tr")
    body = [row for row in rows if row.attrs.get("data-reading-id")]
    assert [row.attrs["data-reading-id"] for row in body] == ["1", "2", "3", "4", "5", "6"]
    noted = body[3].text()
    for piece in ("2026-09-15 15:00", "33", "66", "25.8", "45.8", "Dangerous", "Fan on, windows open"):
        assert piece in noted
    for row, reading_id, taken in zip(
        body,
        range(1, 7),
        [
            "2026-09-14 10:00",
            "2026-09-14 15:00",
            "2026-09-15 10:00",
            "2026-09-15 15:00",
            "2026-09-16 10:00",
            "2026-09-16 15:00",
        ],
    ):
        forms = find_all(row, "form", attrs={"method": "post", "action": f"/readings/{reading_id}/delete"})
        assert len(forms) == 1
        button = find_all(forms[0], "button")[0]
        assert button.attrs.get("aria-label") == f"Delete reading from {taken}"


def test_57_room_2(client):
    root = parse(raw_html(client.get("/rooms/2")))
    latest = one(root, attrs={"id": "latest"}).text()
    assert "35.0" in latest
    assert "Some discomfort" in latest
    stats = one(root, "ul", attrs={"id": "stats"}).text()
    assert "Highest: 40.4 (Great discomfort) on 2026-09-15 15:00" in stats
    assert "Great discomfort or above: 1 of 6" in stats


def test_58_room_3(client):
    root = parse(raw_html(client.get("/rooms/3")))
    latest = one(root, attrs={"id": "latest"}).text()
    assert "28.2" in latest
    assert "Comfortable" in latest
    assert "Humidity adds +3.2" in latest
    stats = one(root, "ul", attrs={"id": "stats"}).text()
    assert "Highest: 28.3 (Comfortable) on 2026-09-15 15:00" in stats
    assert "Great discomfort or above: 0 of 6" in stats


def test_59_form(client):
    root = parse(raw_html(client.get("/rooms/1")))
    form = one(root, "form", attrs={"action": "/rooms/1/readings"})
    assert form.attrs.get("method") == "post"
    temp = one(form, "input", attrs={"name": "temp_c"})
    assert temp.attrs.get("type") == "number"
    assert temp.attrs.get("step") == "0.1"
    assert temp.attrs.get("min") == "0"
    assert temp.attrs.get("max") == "50"
    humidity = one(form, "input", attrs={"name": "rh_percent"})
    assert humidity.attrs.get("type") == "number"
    assert humidity.attrs.get("step") == "0.1"
    assert humidity.attrs.get("min") == "1"
    assert humidity.attrs.get("max") == "100"
    taken = one(form, "input", attrs={"name": "taken_at"})
    assert taken.attrs.get("type") == "datetime-local"
    moment = datetime.strptime(taken.attrs["value"], "%Y-%m-%dT%H:%M")
    now = datetime.now().replace(second=0, microsecond=0)
    assert abs((moment - now).total_seconds()) <= 60
    note = one(form, "input", attrs={"name": "note"})
    assert note.attrs.get("maxlength") == "140"
    for field in (temp, humidity, taken, note):
        labels = [
            label
            for label in find_all(root, "label")
            if label.attrs.get("for") == field.attrs.get("id")
        ]
        assert len(labels) == 1
    hrefs = {link.attrs.get("href") for link in find_all(root, "a")}
    assert "/rooms/1/sheet" in hrefs
    assert "/rooms/1/export.csv" in hrefs
    assert find_all(root, "form", attrs={"method": "post", "action": "/rooms/1/delete"})


def test_60_unknown(client):
    missing = client.get("/rooms/999")
    assert missing.status_code == 404
    assert "Room not found" in html_text(missing)
    assert client.get("/rooms/abc").status_code == 404
