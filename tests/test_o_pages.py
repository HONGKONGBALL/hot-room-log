"""QA section O. Pages, static files, security and accessibility."""

from tests.htmltool import find_all, html_text, one, parse

PAGES = ["/", "/rooms/1", "/rooms/1/sheet", "/calc", "/import", "/about"]
FOOTER = "Humidex bands are a comfort guide, not medical advice."
BANDS = {"Comfortable", "Some discomfort", "Great discomfort", "Dangerous"}


def test_117_page_shell(client):
    for path in PAGES:
        response = client.get(path)
        assert response.status_code == 200, path
        assert response.headers["Content-Type"] == "text/html; charset=utf-8"
        root = parse(response.get_data(as_text=True))
        assert one(root, "html").attrs.get("lang") == "en"
        viewport = [
            tag
            for tag in find_all(root, "meta")
            if tag.attrs.get("name") == "viewport"
        ]
        assert viewport
        assert len(find_all(root, "h1")) == 1
        assert len(find_all(root, "main")) == 1
        hrefs = {link.attrs.get("href") for link in find_all(one(root, "nav"), "a")}
        assert {"/", "/calc", "/import", "/about"} <= hrefs
        assert FOOTER in html_text(response)


def test_118_no_external_resources(client):
    for path in PAGES:
        root = parse(client.get(path).get_data(as_text=True))
        for tag, attr in (
            ("script", "src"),
            ("link", "href"),
            ("img", "src"),
            ("iframe", "src"),
        ):
            for element in find_all(root, tag):
                value = element.attrs.get(attr, "")
                assert not value.startswith(("http:", "https:", "//")), (path, tag, value)


def test_119_about_copy(client):
    text = html_text(client.get("/about"))
    for phrase in (
        "not medical advice",
        "fictional",
        "not deployed",
        "Below 30",
        "30 to 39.9",
        "40 to 45",
        "Above 45",
        "6.105",
        "17.27",
        "237.7",
        "0.5555",
        "Masterton",
        "Flask",
        "pytest",
    ):
        assert phrase in text
    root = parse(client.get("/about").get_data(as_text=True))
    headings = [node.text() for node in find_all(root, "h2")]
    assert "AI tools and third-party resources" in headings


def test_120_static_and_404(client):
    css = client.get("/static/style.css")
    assert css.status_code == 200
    assert css.content_type.startswith("text/css")
    assert b"@media print" in css.data
    script = client.get("/static/app.js")
    assert script.status_code == 200
    assert "javascript" in script.content_type
    assert client.get("/static/missing.css").status_code == 404
    missing = client.get("/no-such-page")
    assert missing.status_code == 404
    assert "Page not found" in html_text(missing)


def test_121_escaping(client):
    name = "<script>alert(1)</script>"
    created = client.post("/rooms", data={"name": name})
    assert created.status_code == 302
    assert created.headers["Location"].endswith("/rooms/4")
    added = client.post(
        "/rooms/4/readings",
        data={
            "temp_c": "30",
            "rh_percent": "50",
            "taken_at": "2026-09-17T10:00",
            "note": "<b>hi</b>",
        },
    )
    assert added.status_code == 302
    for path in ("/", "/rooms/4"):
        raw = client.get(path).get_data(as_text=True)
        assert "&lt;script&gt;alert(1)&lt;/script&gt;" in raw
        assert "<script>alert(1)</script>" not in raw
    room = client.get("/rooms/4").get_data(as_text=True)
    assert "&lt;b&gt;hi&lt;/b&gt;" in room
    assert "<b>hi</b>" not in room


def test_122_stored_as_data(client):
    name = "x'); DROP TABLE rooms;--"
    assert client.post("/rooms", data={"name": name}).status_code == 302
    rooms = client.get("/api/rooms").get_json()
    assert any(room["name"] == name for room in rooms)
    for room_id in (1, 2, 3):
        room = next(item for item in rooms if item["id"] == room_id)
        assert room["reading_count"] == 6


def test_123_labels_and_bands(client):
    for path in ("/", "/rooms/1", "/calc", "/import"):
        root = parse(client.get(path).get_data(as_text=True))
        controls = find_all(root, "input") + find_all(root, "select") + find_all(root, "textarea")
        for control in controls:
            if control.tag == "input" and control.attrs.get("type", "").lower() in {
                "hidden",
                "submit",
                "button",
            }:
                continue
            control_id = control.attrs.get("id", "")
            assert control_id
            labels = [
                label
                for label in find_all(root, "label")
                if label.attrs.get("for") == control_id
            ]
            assert len(labels) == 1, (path, control_id, len(labels))
        for band in find_all(root, "span", cls="band"):
            assert band.text() in BANDS
