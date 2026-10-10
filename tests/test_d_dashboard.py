"""QA section D. Dashboard."""

from tests.htmltool import find_all, html_text, parse, raw_html

FOOTER = "Humidex bands are a comfort guide, not medical advice."
BANNER = "Sample data — fictional rooms and readings for demonstration."


def test_38_cards(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.content_type.startswith("text/html")
    assert "charset=utf-8" in response.content_type
    assert BANNER in html_text(response)
    root = parse(raw_html(response))
    cards = find_all(root, "article", cls="room-card")
    assert len(cards) == 3
    assert [card.attrs["data-room-id"] for card in cards] == ["1", "2", "3"]
    assert [card.attrs["data-band"] for card in cards] == ["dangerous", "some", "comfortable"]
    for card in cards:
        tags = find_all(card, "span", cls="tag-sample")
        assert len(tags) == 1
        assert tags[0].text() == "Sample"


def test_39_card_text(client):
    root = parse(raw_html(client.get("/")))
    cards = find_all(root, "article", cls="room-card")
    first = cards[0].text()
    assert "Demo Estate Study Room" in first
    assert "47.6" in first
    assert "Dangerous" in first
    assert "Latest 2026-09-16 15:00" in first
    assert "6 readings" in first
    assert "Great discomfort or above: 6 of 6" in first
    second = cards[1].text()
    assert "35.0" in second
    assert "Some discomfort" in second
    assert "Great discomfort or above: 1 of 6" in second
    third = cards[2].text()
    assert "28.2" in third
    assert "Comfortable" in third
    assert "Great discomfort or above: 0 of 6" in third
    for card, room_id in zip(cards, ("1", "2", "3")):
        links = [
            link
            for link in find_all(card, "a")
            if link.attrs.get("href") == f"/rooms/{room_id}"
        ]
        assert links


def test_40_forms_and_links(client):
    root = parse(raw_html(client.get("/")))
    forms = find_all(root, "form", attrs={"method": "post", "action": "/rooms"})
    assert len(forms) == 1
    names = find_all(forms[0], "input", attrs={"name": "name"})
    assert names[0].attrs.get("maxlength") == "60"
    labels = [
        label
        for label in find_all(root, "label")
        if label.attrs.get("for") == names[0].attrs.get("id")
    ]
    assert len(labels) == 1
    hrefs = {link.attrs.get("href") for link in find_all(root, "a")}
    assert "/export.csv" in hrefs
    assert "/import" in hrefs
    assert "/calc" in hrefs
    assert "/about" in hrefs
    resets = find_all(root, "form", attrs={"method": "post", "action": "/reset"})
    assert len(resets) == 1


def test_41_footer(client):
    assert FOOTER in html_text(client.get("/"))
