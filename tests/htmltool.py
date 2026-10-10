"""Small HTML helpers for the QA cases."""

import re
from html.parser import HTMLParser

VOID_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}


class Node:
    def __init__(self, tag, attrs):
        self.tag = tag
        self.attrs = {}
        for key, value in attrs:
            self.attrs[key] = "" if value is None else value
        self.children = []
        self.parts = []

    def classes(self):
        return self.attrs.get("class", "").split()

    def raw_text(self):
        chunks = []

        def walk(node):
            for part in node.parts:
                if isinstance(part, str):
                    chunks.append(part)
                else:
                    walk(part)

        walk(self)
        return "".join(chunks)

    def text(self):
        raw = self.raw_text().replace("\xa0", " ")
        return re.sub(r"\s+", " ", raw).strip()


class _Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("document", [])
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs)
        self.stack[-1].children.append(node)
        self.stack[-1].parts.append(node)
        if tag not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        node = Node(tag, attrs)
        self.stack[-1].children.append(node)
        self.stack[-1].parts.append(node)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data):
        self.stack[-1].parts.append(data)


def parse(html):
    parser = _Parser()
    parser.feed(html)
    parser.close()
    return parser.root


def find_all(node, tag=None, cls=None, attrs=None):
    attrs = attrs or {}
    found = []

    def matches(element):
        if element.tag == "document":
            return False
        if tag is not None and element.tag != tag:
            return False
        if cls is not None and cls not in element.classes():
            return False
        for key, value in attrs.items():
            if element.attrs.get(key) != value:
                return False
        return True

    def walk(element):
        if matches(element):
            found.append(element)
        for child in element.children:
            walk(child)

    walk(node)
    return found


def one(node, tag=None, cls=None, attrs=None):
    found = find_all(node, tag=tag, cls=cls, attrs=attrs)
    assert len(found) == 1, (tag, cls, attrs, len(found))
    return found[0]


def page_text(html):
    return parse(html).text()


def html_text(response):
    return page_text(response.get_data(as_text=True))


def raw_html(response):
    return response.get_data(as_text=True)
