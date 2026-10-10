"""QA section N. Read-only demo mode on a fresh database."""

import io

import pytest

from hotroom import create_app
from tests.htmltool import find_all, html_text, one, parse

BANNER_RO = (
    "Read-only demo: changes are turned off. "
    "Run the app on your own computer to add readings."
)
CN = "自修室 2F"
F1 = (
    "room,taken_at,temp_c,rh_percent,note\n"
    "demo classroom 3f,2026-09-17 15:00,30,88,Projector on\n"
    f"{CN},2026-09-17 16:00,28,84,\n"
).encode("utf-8")


@pytest.fixture(scope="module")
def ro(tmp_path_factory):
    database = tmp_path_factory.mktemp("readonly") / "test.db"
    app = create_app(
        {
            "DATABASE": str(database),
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "READONLY": True,
        }
    )
    return app.test_client()


def _actions(response):
    root = parse(response.get_data(as_text=True))
    return [form.attrs.get("action", "") for form in find_all(root, "form")]


def test_112_dashboard(ro):
    response = ro.get("/")
    assert response.status_code == 200
    root = parse(response.get_data(as_text=True))
    assert BANNER_RO in one(root, "p", cls="banner-readonly").text()
    actions = _actions(response)
    assert "/rooms" not in actions
    assert "/reset" not in actions
    cards = find_all(root, "article", cls="room-card")
    assert [card.attrs.get("data-room-id") for card in cards] == ["1", "2", "3"]


def test_113_room_page(ro):
    response = ro.get("/rooms/1")
    assert response.status_code == 200
    root = parse(response.get_data(as_text=True))
    assert find_all(root, "svg", cls="chart")
    assert find_all(root, "table", attrs={"id": "readings"})
    for action in _actions(response):
        assert action != "/rooms/1/readings"
        assert action != "/rooms/1/delete"
        assert not action.startswith("/readings/")


def test_114_writes_forbidden(ro):
    posts = [
        ro.post("/rooms", data={"name": "X"}),
        ro.post("/rooms/1/readings", data={"temp_c": "30", "rh_percent": "50"}),
        ro.post("/readings/1/delete"),
        ro.post("/rooms/1/delete"),
        ro.post("/reset"),
        ro.post(
            "/import",
            data={"file": (io.BytesIO(F1), "f1.csv")},
            content_type="multipart/form-data",
        ),
    ]
    for response in posts:
        assert response.status_code == 403
        assert BANNER_RO in html_text(response)
    rooms = ro.get("/api/rooms").get_json()
    assert len(rooms) == 3
    assert [room["reading_count"] for room in rooms] == [6, 6, 6]


def test_115_json_write(ro):
    response = ro.post("/api/rooms/1/readings", json={"temp_c": 30, "rh_percent": 50})
    assert response.status_code == 403
    assert response.get_json() == {"error": "Read-only demo"}


def test_116_reads_still_work(ro):
    calc = ro.get("/calc?temp_c=30&rh_percent=85")
    assert calc.status_code == 200
    assert 'data-humidex="44.4"' in calc.get_data(as_text=True)
    exported = ro.get("/export.csv")
    assert exported.status_code == 200
    text = exported.data.decode("utf-8-sig")
    assert text.count("\n") >= 18
    sheet = ro.get("/rooms/1/sheet")
    assert sheet.status_code == 200
    assert find_all(parse(sheet.get_data(as_text=True)), "textarea", attrs={"id": "letter"})
    form = ro.get("/import")
    assert form.status_code == 200
    root = parse(form.get_data(as_text=True))
    assert BANNER_RO in html_text(form)
    assert find_all(root, "input", attrs={"type": "file"}) == []
