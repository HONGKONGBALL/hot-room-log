"""QA section O. Pages, static files, security and accessibility."""

import ast
import re
from pathlib import Path

from tests.htmltool import find_all, html_text, one, parse

ROOT = Path(__file__).resolve().parents[1]
CJK_RANGES = re.compile(
    "[\u3000-\u303f\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff00-\uffef]"
)
ONE_PAGE = re.compile(r"one[- ]page", re.IGNORECASE)
JS_BANNED = (
    "fetch(",
    "XMLHttpRequest",
    "WebSocket",
    "EventSource",
    "sendBeacon",
    "import(",
    "eval(",
    "new Function",
    "innerHTML",
    "outerHTML",
    "insertAdjacentHTML",
    "document.write",
    ".submit(",
    "requestSubmit",
    "localStorage",
    "sessionStorage",
    "document.cookie",
    "http:",
    "https:",
)
IMPORT_BANNED = (
    "urllib",
    "http.client",
    "requests",
    "httpx",
    "aiohttp",
    "socket",
    "dashscope",
    "openai",
)

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
        "Grok",
        "Claude",
        "qwen3-tts-flash",
        "AI-generated voice",
        "does not call",
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


def _imported_module_names(tree):
    """Real import targets. Relative imports such as hotroom.http are skipped."""
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                continue
            module = node.module or ""
            if module:
                names.append(module)
            for alias in node.names:
                if alias.name == "*":
                    continue
                names.append(f"{module}.{alias.name}" if module else alias.name)
    return names


def _import_is_banned(name):
    for banned in IMPORT_BANNED:
        if name == banned or name.startswith(banned + "."):
            return banned
    return None


def test_147_no_cjk_in_readme_and_docs():
    paths = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]
    assert paths
    for path in paths:
        text = path.read_text(encoding="utf-8")
        match = CJK_RANGES.search(text)
        assert match is None, (str(path.relative_to(ROOT)), hex(ord(match.group())))


def test_148_no_one_page_wording(client):
    bodies = {
        "/about": client.get("/about").get_data(as_text=True),
        "README.md": (ROOT / "README.md").read_text(encoding="utf-8"),
        "docs/devpost.md": (ROOT / "docs" / "devpost.md").read_text(encoding="utf-8"),
    }
    for label, body in bodies.items():
        assert ONE_PAGE.search(body) is None, label


def test_149_script_whitelist(client):
    script = (ROOT / "hotroom" / "static" / "app.js").read_text(encoding="utf-8")
    for needle in JS_BANNED:
        assert needle not in script, needle
    for path in PAGES:
        root = parse(client.get(path).get_data(as_text=True))
        scripts = find_all(root, "script")
        assert len(scripts) == 1, (path, len(scripts))
        assert scripts[0].attrs.get("src") == "/static/app.js", path


def test_150_flask_only_no_network_imports():
    lines = []
    for raw in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        lines.append(stripped)
    assert len(lines) == 1
    assert lines[0].startswith("Flask")
    python_files = [ROOT / "app.py", *sorted((ROOT / "hotroom").rglob("*.py"))]
    assert python_files
    for path in python_files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for name in _imported_module_names(tree):
            banned = _import_is_banned(name)
            assert banned is None, (str(path.relative_to(ROOT)), name, banned)
