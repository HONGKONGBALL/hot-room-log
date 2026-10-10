"""QA 129–138 in headless Chrome against the fresh sample server.

QA 137 records network requests. It does not unplug a cable.
QA 136 records keyboard focus names and the computed focus outline.
A 320 px datapoint covering the "40" label is recorded, not treated as a failure.
"""

import base64
import json
import subprocess
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

ROOT = Path("/workspace/hot-room-log-rc3")
OUT = ROOT / "review" / "rc4" / "evidence"
SHOTS = OUT / "qa-shots"
SHOTS.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:5050"
CHROME = "/usr/bin/google-chrome"
EXPECTED = {
    "dangerous": "rgb(255, 214, 214)",
    "some": "rgb(255, 243, 191)",
    "comfortable": "rgb(211, 249, 216)",
}


def git_identity():
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    diff = subprocess.check_output("git diff HEAD | sha256sum", cwd=ROOT, shell=True, text=True)
    return {"git_head": head, "git_diff_head_sha256": diff.split()[0]}


def hosts_of(urls):
    hosts = set()
    for url in urls:
        if url.startswith("data:") or url.startswith("blob:") or url.startswith("about:"):
            continue
        host = urlparse(url).hostname
        if host:
            hosts.add(host)
    return sorted(hosts)


LAYOUT_JS = r"""
() => {
  const doc = document.documentElement;
  const scrollers = Array.from(document.querySelectorAll('.table-scroll')).map(box => {
    const rect = box.getBoundingClientRect();
    return {
      scrollWidth: box.scrollWidth,
      clientWidth: box.clientWidth,
      overflows: box.scrollWidth > box.clientWidth + 2,
      left: rect.left,
      right: rect.right,
      withinPage: rect.left >= -1 && rect.right <= doc.clientWidth + 1
    };
  });
  const inside = new Set();
  document.querySelectorAll('.table-scroll *').forEach(el => inside.add(el));
  const offenders = [];
  for (const el of document.body.querySelectorAll('*')) {
    if (inside.has(el)) continue;
    const style = getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden') continue;
    const rect = el.getBoundingClientRect();
    if (rect.width < 1 || rect.height < 1) continue;
    if (rect.right > doc.clientWidth + 1.5 || rect.left < -1.5) {
      offenders.push({
        tag: el.tagName,
        id: el.id || '',
        className: String(el.className).slice(0, 80),
        text: (el.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 50),
        left: Math.round(rect.left),
        right: Math.round(rect.right),
        page: doc.clientWidth
      });
      if (offenders.length >= 8) break;
    }
  }
  return {
    clientWidth: doc.clientWidth,
    scrollWidth: doc.scrollWidth,
    pageOverflow: doc.scrollWidth - doc.clientWidth,
    scrollers,
    offenders
  };
}
"""

POINT_HIT_JS = r"""
() => {
  const svg = document.querySelector('svg.chart');
  if (!svg) return {present: false};
  const label = Array.from(svg.querySelectorAll('text.axis-label')).find(node => node.textContent === '40');
  if (!label) return {present: true, label: false};
  const box = label.getBoundingClientRect();
  const hits = [];
  for (const circle of svg.querySelectorAll('circle.point')) {
    const rect = circle.getBoundingClientRect();
    const overlap = !(rect.right < box.left || rect.left > box.right || rect.bottom < box.top || rect.top > box.bottom);
    if (overlap) {
      hits.push({cx: circle.getAttribute('cx'), r: circle.getAttribute('r'), title: circle.querySelector('title') && circle.querySelector('title').textContent});
    }
  }
  return {
    present: true,
    labelBox: {x: box.x, y: box.y, width: box.width, height: box.height},
    hits
  };
}
"""

OVERLAP_JS = r"""
() => {
  const selector = 'h1,h2,p,a,button,label,li,th,td,legend,summary,span.band,span.tag-sample,.banner-sample';
  const nodes = Array.from(document.querySelectorAll(selector)).filter(el => {
    const style = getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden') return false;
    const rect = el.getBoundingClientRect();
    return rect.width > 2 && rect.height > 2;
  });
  const overlaps = [];
  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      const a = nodes[i];
      const b = nodes[j];
      if (a.contains(b) || b.contains(a)) continue;
      const ra = a.getBoundingClientRect();
      const rb = b.getBoundingClientRect();
      const x = Math.min(ra.right, rb.right) - Math.max(ra.left, rb.left);
      const y = Math.min(ra.bottom, rb.bottom) - Math.max(ra.top, rb.top);
      if (x <= 2 || y <= 2) continue;
      const area = x * y;
      const small = Math.min(ra.width * ra.height, rb.width * rb.height);
      if (area <= small * 0.3) continue;
      overlaps.push({
        a: (a.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 60),
        b: (b.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 60),
        x: Math.round(x),
        y: Math.round(y)
      });
      if (overlaps.length >= 12) return {overlaps, clipped: []};
    }
  }
  const clipped = [];
  for (const el of document.querySelectorAll('h1,h2,p,a,button,label,li,th,td,legend')) {
    const style = getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden') continue;
    if (el.closest('.table-scroll')) continue;
    const hidden = style.overflowX === 'hidden' || style.overflowX === 'clip' || style.textOverflow === 'ellipsis';
    if (hidden && el.scrollWidth > el.clientWidth + 3) {
      clipped.push({
        tag: el.tagName,
        text: (el.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 60),
        scrollWidth: el.scrollWidth,
        clientWidth: el.clientWidth
      });
    }
  }
  return {
    overlaps,
    clipped,
    innerWidth: window.innerWidth,
    devicePixelRatio: window.devicePixelRatio
  };
}
"""

FOCUS_NAME_JS = r"""
(el) => {
  if (!el) return '';
  const aria = el.getAttribute('aria-label');
  if (aria) return aria;
  if (el.id) {
    const label = document.querySelector('label[for="' + el.id + '"]');
    if (label) return label.textContent.trim().replace(/\s+/g, ' ');
  }
  const text = (el.innerText || el.value || el.getAttribute('aria-label') || '').trim().replace(/\s+/g, ' ');
  return text.slice(0, 80) || el.tagName.toLowerCase();
}
"""


def focus_snapshot(page):
    return page.evaluate(
        """(nameOf) => {
          const el = document.activeElement;
          const style = el ? getComputedStyle(el) : null;
          const width = style ? parseFloat(style.outlineWidth) : 0;
          const outlineStyle = style ? style.outlineStyle : '';
          return {
            tag: el ? el.tagName.toLowerCase() : '',
            id: el ? (el.id || '') : '',
            name: nameOf(el),
            outlineWidth: style ? style.outlineWidth : '',
            outlineStyle: outlineStyle,
            outlineColor: style ? style.outlineColor : '',
            visibleOutline: !!style && outlineStyle !== 'none' && width >= 2
          };
        }""",
        None,
    )


def tab_through(page, limit=80, shot_path=None):
    # The evaluate above can't take a function. Do it inline.
    page.evaluate("() => { if (document.activeElement && document.activeElement.blur) document.activeElement.blur(); }")
    seen = []
    shot_done = False
    for _ in range(limit):
        page.keyboard.press("Tab")
        snap = page.evaluate(
            """() => {
              const el = document.activeElement;
              if (!el || el === document.body || el === document.documentElement) {
                return {tag: el ? el.tagName.toLowerCase() : '', id: '', name: '', outlineWidth: '', outlineStyle: '', outlineColor: '', visibleOutline: false, stop: true};
              }
              let name = el.getAttribute('aria-label') || '';
              if (!name && el.id) {
                const label = document.querySelector('label[for="' + CSS.escape(el.id) + '"]');
                if (label) name = label.textContent;
              }
              if (!name) name = el.innerText || el.value || '';
              name = String(name).trim().replace(/\\s+/g, ' ').slice(0, 80);
              const style = getComputedStyle(el);
              const width = parseFloat(style.outlineWidth) || 0;
              return {
                tag: el.tagName.toLowerCase(),
                id: el.id || '',
                name: name,
                outlineWidth: style.outlineWidth,
                outlineStyle: style.outlineStyle,
                outlineColor: style.outlineColor,
                visibleOutline: style.outlineStyle !== 'none' && width >= 2,
                stop: false
              };
            }"""
        )
        if snap.get("stop"):
            break
        if shot_path and not shot_done and snap["name"] in ("Rooms", "Add room", "Calculate"):
            page.screenshot(path=str(shot_path))
            shot_done = True
        key = (snap["tag"], snap["id"], snap["name"])
        if seen and key == (seen[0]["tag"], seen[0]["id"], seen[0]["name"]):
            break
        seen.append(snap)
    if shot_path and not shot_done and seen:
        page.screenshot(path=str(shot_path))
    return seen


def expected_focusables(page):
    return page.evaluate(
        """() => {
          const nodes = Array.from(document.querySelectorAll('a[href], button, input, textarea, select, summary'));
          return nodes.filter(el => {
            const style = getComputedStyle(el);
            if (style.display === 'none' || style.visibility === 'hidden') return false;
            return true;
          }).map(el => {
            let name = el.getAttribute('aria-label') || '';
            if (!name && el.id) {
              const label = document.querySelector('label[for="' + CSS.escape(el.id) + '"]');
              if (label) name = label.textContent;
            }
            if (!name) name = el.innerText || '';
            return {
              tag: el.tagName.toLowerCase(),
              id: el.id || '',
              name: String(name).trim().replace(/\\s+/g, ' ').slice(0, 80)
            };
          });
        }"""
    )


def main():
    identity = git_identity()
    requests = []
    report = {**identity, "qa": {}, "failures": [], "requests_sample": []}
    failures = []

    def record(number, ok, detail):
        report["qa"][str(number)] = {"pass": bool(ok), "detail": detail}
        if not ok:
            failures.append(number)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=CHROME,
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            device_scale_factor=1,
        )
        context.grant_permissions(["clipboard-read", "clipboard-write"])
        page = context.new_page()
        page.on("request", lambda req: requests.append(req.url))

        # 129 dashboard
        page.goto(BASE + "/", wait_until="networkidle")
        page.screenshot(path=str(SHOTS / "129-dashboard-1280.png"), full_page=True)
        cards = page.evaluate(
            """() => {
              const banner = document.querySelector('.banner-sample');
              return {
                banner: banner ? banner.textContent.trim() : '',
                bannerBg: banner ? getComputedStyle(banner).backgroundColor : '',
                cards: Array.from(document.querySelectorAll('.room-card')).map(card => ({
                  name: card.querySelector('h2').innerText.replace(/\\s+/g, ' ').trim(),
                  band: card.dataset.band,
                  bg: getComputedStyle(card).backgroundColor,
                  humidex: card.querySelector('.humidex-big').textContent.trim(),
                  bandText: card.querySelector('.band').textContent.trim(),
                  bandColor: getComputedStyle(card.querySelector('.band')).color,
                  bandBg: getComputedStyle(card.querySelector('.band')).backgroundColor
                }))
              };
            }"""
        )
        ok129 = (
            cards["banner"].startswith("Sample data")
            and [c["humidex"] for c in cards["cards"]] == ["47.6", "35.0", "28.2"]
            and [c["bandText"] for c in cards["cards"]] == ["Dangerous", "Some discomfort", "Comfortable"]
            and [c["bg"] for c in cards["cards"]] == [EXPECTED["dangerous"], EXPECTED["some"], EXPECTED["comfortable"]]
            and all(c["bandText"] and c["bandColor"] != c["bg"] for c in cards["cards"])
        )
        record(129, ok129, cards)

        # 130 tooltip
        page.goto(BASE + "/rooms/1", wait_until="networkidle")
        titles = page.evaluate(
            """() => Array.from(document.querySelectorAll('circle.point title')).map(n => n.textContent)"""
        )
        tips = []
        points = page.locator("circle.point")
        for i in range(points.count()):
            points.nth(i).hover()
            page.wait_for_timeout(80)
            tip = page.locator("p.chart-tip")
            tips.append(
                {
                    "hidden": tip.get_attribute("hidden") is not None,
                    "text": tip.inner_text(),
                }
            )
        page.screenshot(path=str(SHOTS / "130-tooltip.png"))
        ok130 = (
            len(tips) == 6
            and all(not item["hidden"] and item["text"] == titles[i] for i, item in enumerate(tips))
            and "humidex 47.6" in tips[-1]["text"]
            and "Dangerous" in tips[-1]["text"]
        )
        record(130, ok130, {"titles": titles, "tips": tips})

        # 131 copy edited letter
        page.goto(BASE + "/rooms/1/sheet", wait_until="networkidle")
        original = page.input_value("#letter")
        edited = original.replace("[recipient]", "Room manager")
        page.fill("#letter", edited)
        page.click("#copy-letter")
        page.wait_for_function("() => document.querySelector('#copy-letter').textContent === 'Copied'")
        copied_now = page.inner_text("#copy-letter")
        clipboard = page.evaluate("() => navigator.clipboard.readText()")
        page.wait_for_timeout(2200)
        copied_later = page.inner_text("#copy-letter")
        page.screenshot(path=str(SHOTS / "131-after-copy.png"))
        ok131 = (
            copied_now == "Copied"
            and copied_later == "Copy letter"
            and clipboard == edited
            and clipboard.startswith("Dear Room manager,")
        )
        record(
            131,
            ok131,
            {
                "button_immediate": copied_now,
                "button_after": copied_later,
                "clipboard_starts": clipboard[:80],
                "clipboard_equals_textarea": clipboard == edited,
            },
        )

        # 132 print edited letter
        page.evaluate("() => { document.getElementById('letter-print').textContent = 'STALE MARKER'; }")
        session = context.new_cdp_session(page)
        data = session.send(
            "Page.printToPDF",
            {"printBackground": True, "paperWidth": 8.27, "paperHeight": 11.69, "preferCSSPageSize": True},
        )
        pdf_path = OUT / "qa132-edited-letter.pdf"
        pdf_path.write_bytes(base64.b64decode(data["data"]))
        session.detach()
        info = subprocess.check_output(["pdfinfo", str(pdf_path)], text=True)
        text = subprocess.check_output(["pdftotext", "-layout", str(pdf_path), "-"], text=True)
        pages = None
        for line in info.splitlines():
            if line.startswith("Pages:"):
                pages = int(line.split()[1])
        absent = ["Copy letter", "Print / Save as PDF", "Skip to content", "Calculator", "Reset demo data", "[recipient]", "STALE MARKER"]
        present = ["Dear Room manager,", "Fan on, windows open", "47.6"]
        flat = " ".join(text.split())
        missing = [item for item in present if item not in flat]
        leaked = [item for item in absent if item in text]
        ok132 = pages is not None and pages <= 2 and pages >= 1 and not missing and not leaked and "A4" in info
        record(
            132,
            ok132,
            {
                "pdf": str(pdf_path.relative_to(ROOT)),
                "pages": pages,
                "page_size": next((line.split(":", 1)[1].strip() for line in info.splitlines() if line.startswith("Page size:")), ""),
                "missing": missing,
                "leaked": leaked,
            },
        )

        # 133 confirm then cancel
        dialogs = []

        def on_dialog(dialog):
            dialogs.append(dialog.message)
            dialog.dismiss()

        page.on("dialog", on_dialog)
        page.goto(BASE + "/rooms/1", wait_until="networkidle")
        before_rows = page.locator("#readings tbody tr").count()
        page.locator("form[action^='/readings/'] button").first.click()
        page.wait_for_timeout(200)
        after_rows = page.locator("#readings tbody tr").count()
        page.locator("form[action='/rooms/1/delete'] button").click()
        page.wait_for_timeout(200)
        still_room = "Demo Estate Study Room" in page.inner_text("h1")
        page.goto(BASE + "/", wait_until="networkidle")
        page.locator("form[action='/reset'] button").click()
        page.wait_for_timeout(200)
        card_count = page.locator(".room-card").count()
        ok133 = (
            dialogs
            == [
                "Delete this reading?",
                "Delete this room and all its readings?",
                "Replace all rooms and readings with the sample data?",
            ]
            and before_rows == after_rows == 6
            and still_room
            and card_count == 3
        )
        record(
            133,
            ok133,
            {"dialogs": dialogs, "rows_before": before_rows, "rows_after": after_rows, "still_room": still_room, "cards": card_count},
        )

        # 135 narrow widths
        narrow = {}
        for width in (320, 375):
            page.set_viewport_size({"width": width, "height": 800})
            per_page = {}
            for name, path in (
                ("dashboard", "/"),
                ("room", "/rooms/1"),
                ("sheet", "/rooms/1/sheet"),
                ("calculator", "/calc"),
            ):
                page.goto(BASE + path, wait_until="networkidle")
                layout = page.evaluate(LAYOUT_JS)
                hit = page.evaluate(POINT_HIT_JS) if name == "room" else None
                page.screenshot(path=str(SHOTS / f"135-{name}-{width}.png"), full_page=False)
                per_page[name] = {"layout": layout, "point_on_40": hit}
            # forms usable on the room page
            page.goto(BASE + "/rooms/1", wait_until="networkidle")
            page.fill("#temp_c", "31")
            page.fill("#note", "narrow")
            typed = {"temp": page.input_value("#temp_c"), "note": page.input_value("#note")}
            narrow[str(width)] = {"pages": per_page, "typed": typed}
        ok135 = True
        for width, payload in narrow.items():
            if payload["typed"] != {"temp": "31", "note": "narrow"}:
                ok135 = False
            for name, item in payload["pages"].items():
                layout = item["layout"]
                if layout["pageOverflow"] > 1 or layout["offenders"]:
                    ok135 = False
                if name in ("room", "sheet"):
                    if not layout["scrollers"] or not all(s["overflows"] and s["withinPage"] for s in layout["scrollers"]):
                        ok135 = False
        point_limit = {
            width: payload["pages"]["room"]["point_on_40"]
            for width, payload in narrow.items()
        }
        record(135, ok135, {"widths": narrow, "known_limit_point_covers_40": point_limit})

        # 136 keyboard, back at 1280
        page.set_viewport_size({"width": 1280, "height": 900})
        keyboard = {}
        for name, path in (
            ("dashboard", "/"),
            ("room", "/rooms/1"),
            ("sheet", "/rooms/1/sheet"),
            ("calculator", "/calc"),
        ):
            page.goto(BASE + path, wait_until="networkidle")
            expected = expected_focusables(page)
            order = tab_through(page, limit=80, shot_path=SHOTS / f"136-{name}-focus.png")
            # one Shift+Tab
            page.keyboard.press("Shift+Tab")
            back = page.evaluate(
                """() => {
                  const el = document.activeElement;
                  const style = getComputedStyle(el);
                  const width = parseFloat(style.outlineWidth) || 0;
                  return {
                    name: (el.getAttribute('aria-label') || el.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 80),
                    visibleOutline: style.outlineStyle !== 'none' && width >= 2
                  };
                }"""
            )
            got = [(item["tag"], item["id"], item["name"]) for item in order if item["tag"] != "body"]
            want = [(item["tag"], item["id"], item["name"]) for item in expected]
            outline_by_control = {}
            for item in order:
                if item["tag"] == "body":
                    continue
                key = (item["tag"], item["id"], item["name"])
                outline_by_control[key] = outline_by_control.get(key, False) or item["visibleOutline"]
            missing_outline = [list(key) for key, visible in outline_by_control.items() if not visible]
            keyboard[name] = {
                "focused": [{"name": item["name"], "tag": item["tag"], "id": item["id"], "outline": item["outlineWidth"], "color": item["outlineColor"], "visible": item["visibleOutline"]} for item in order],
                "expected_count": len(expected),
                "missing_from_tab": list((Counter(want) - Counter(got)).elements()),
                "extra_tab": list((Counter(got) - Counter(want)).elements()),
                "missing_outline": [{"name": item["name"], "tag": item["tag"]} for item in missing_outline],
                "shift_tab": back,
            }
        # Enter submits the calculator
        page.goto(BASE + "/calc", wait_until="networkidle")
        page.fill("#temp_c", "30")
        page.fill("#rh_percent", "85")
        with page.expect_navigation():
            page.locator("#temp_c").press("Enter")
        page.wait_for_load_state("networkidle")
        entered = {
            "url": page.url,
            "humidex": page.locator("[data-condition='a']").get_attribute("data-humidex") if page.locator("[data-condition='a']").count() else None,
        }
        keyboard["enter_submits_calculator"] = entered
        outlines_ok = all(
            not payload["missing_outline"] and not payload["missing_from_tab"] and payload["shift_tab"]["visibleOutline"]
            for payload in keyboard.values()
            if "focused" in payload
        )
        ok136 = outlines_ok and entered["humidex"] == "44.4" and "temp_c=30" in entered["url"]
        record(136, ok136, keyboard)

        # 138 browser zoom 200% on a 1280x900 window: layout viewport halves, DPR doubles
        zoom_context = browser.new_context(
            viewport={"width": 640, "height": 450},
            device_scale_factor=2,
        )
        zoom_page = zoom_context.new_page()
        zoom_page.on("request", lambda req: requests.append(req.url))
        zoom = {}
        zoom_ok = True
        for name, path in (
            ("dashboard", "/"),
            ("room", "/rooms/1"),
            ("sheet", "/rooms/1/sheet"),
            ("calculator", "/calc"),
        ):
            zoom_page.goto(BASE + path, wait_until="networkidle")
            metrics = zoom_page.evaluate(OVERLAP_JS)
            layout = zoom_page.evaluate(LAYOUT_JS)
            zoom_page.screenshot(path=str(SHOTS / f"138-{name}-zoom200.png"), full_page=True)
            zoom[name] = {"overlap": metrics, "layout": layout}
            if metrics["overlaps"] or metrics["clipped"] or layout["pageOverflow"] > 1 or layout["offenders"]:
                zoom_ok = False
        zoom["method"] = (
            "Chrome browser zoom at 200% on a 1280×900 window makes the layout viewport 640×450 CSS px "
            "and devicePixelRatio 2. Headless Chrome has no Ctrl+Plus dialog, so this context is that layout. "
            "No cable was involved."
        )
        record(138, zoom_ok, zoom)
        zoom_context.close()

        # 137 request log. Cable was not unplugged.
        page.set_viewport_size({"width": 1280, "height": 900})
        reloaded = []
        for path in ("/", "/rooms/1", "/rooms/1/sheet", "/calc", "/import", "/about"):
            page.goto(BASE + path, wait_until="networkidle")
            resources = page.evaluate(
                """() => performance.getEntriesByType('resource').map(entry => entry.name)"""
            )
            attrs = page.evaluate(
                """() => Array.from(document.querySelectorAll('[src],[href]')).map(el => el.src || el.getAttribute('href')).filter(Boolean)"""
            )
            style_loaded = page.evaluate("() => !!getComputedStyle(document.body).backgroundColor")
            script_present = page.evaluate("() => !!document.querySelector('script[src*=\"app.js\"]')")
            reloaded.append(
                {
                    "path": path,
                    "resources": resources,
                    "attrs": attrs,
                    "style_loaded": style_loaded,
                    "script_present": script_present,
                }
            )
        external_attrs = []
        for item in reloaded:
            for url in item["attrs"] + item["resources"]:
                if url.startswith("#") or url.startswith("/") or url.startswith("?") or url.startswith("mailto:"):
                    continue
                host = urlparse(url).hostname
                if host and host != "127.0.0.1":
                    external_attrs.append(url)
        request_hosts = hosts_of(requests)
        ok137 = request_hosts == ["127.0.0.1"] and not external_attrs and all(
            item["style_loaded"] and item["script_present"] for item in reloaded
        )
        record(
            137,
            ok137,
            {
                "cable_unplugged": False,
                "method": "Playwright request log plus performance resource entries and src/href attributes. No network cable was unplugged.",
                "request_hosts": request_hosts,
                "request_count": len(requests),
                "external_attrs": external_attrs,
                "pages": [
                    {"path": item["path"], "resource_count": len(item["resources"]), "style_loaded": item["style_loaded"], "script_present": item["script_present"]}
                    for item in reloaded
                ],
            },
        )
        context.close()

        # 134 JavaScript disabled
        off = browser.new_context(
            viewport={"width": 1280, "height": 900},
            java_script_enabled=False,
        )
        op = off.new_page()
        dialogs_off = []

        def on_off_dialog(dialog):
            dialogs_off.append(dialog.message)
            dialog.dismiss()

        op.on("dialog", on_off_dialog)
        op.goto(BASE + "/", wait_until="networkidle")
        op.fill("#name", "QA134 Room")
        op.click("form[action='/rooms'] button")
        op.wait_for_load_state("networkidle")
        added_room = {
            "url": op.url,
            "h1": op.inner_text("h1"),
            "flash": op.locator(".flash").inner_text() if op.locator(".flash").count() else "",
        }
        op.fill("#temp_c", "31")
        op.fill("#rh_percent", "50")
        # The app rejects a future minute. 2026-10-10 09:30 is before this clock.
        op.fill("#taken_at", "2026-10-10T09:30")
        op.fill("#note", "qa134")
        op.click("form[action$='/readings'] button")
        op.wait_for_load_state("networkidle")
        added_reading = {
            "url": op.url,
            "flash": op.locator(".flash").inner_text() if op.locator(".flash").count() else "",
            "errors": op.locator(".error").all_inner_texts(),
            "rows": op.locator("#readings tbody tr").count(),
            "table": op.locator("#readings").inner_text() if op.locator("#readings").count() else "",
        }
        op.locator("form[action^='/readings/'] button").click()
        op.wait_for_load_state("networkidle")
        deleted_reading = {
            "flash": op.locator(".flash").inner_text() if op.locator(".flash").count() else "",
            "rows": op.locator("#readings tbody tr").count(),
        }
        op.locator("form[action$='/delete'] button").click()
        op.wait_for_load_state("networkidle")
        deleted_room = {
            "url": op.url,
            "flash": op.locator(".flash").inner_text() if op.locator(".flash").count() else "",
            "cards": op.locator(".room-card").count(),
            "qa_room_visible": "QA134 Room" in op.inner_text("body"),
        }
        op.goto(BASE + "/calc", wait_until="networkidle")
        op.fill("#temp_c", "30")
        op.fill("#rh_percent", "85")
        op.click("form.calc-form button")
        op.wait_for_load_state("networkidle")
        calc = {
            "humidex": op.locator("[data-condition='a']").get_attribute("data-humidex") if op.locator("[data-condition='a']").count() else None,
            "text": op.locator("[data-condition='a']").inner_text() if op.locator("[data-condition='a']").count() else "",
        }
        op.goto(BASE + "/", wait_until="networkidle")
        with op.expect_download() as download_info:
            op.locator("a[href='/export.csv']").click()
        download = download_info.value
        csv_path = SHOTS / "134-export.csv"
        download.save_as(str(csv_path))
        csv_text = csv_path.read_text(encoding="utf-8")
        export = {
            "filename": download.suggested_filename,
            "has_study_room": "Demo Estate Study Room" in csv_text,
            "has_header": csv_text.lstrip("\ufeff").startswith("room,"),
        }
        import_csv = Path("/tmp/hrl-rc4/qa-import.csv")
        import_csv.write_text(
            "room,taken_at,temp_c,rh_percent,note\nQA Import Room,2026-10-10 09:00,28,40,qa\n",
            encoding="utf-8",
        )
        op.goto(BASE + "/import", wait_until="networkidle")
        op.set_input_files("#file", str(import_csv))
        op.click("form[action='/import'] button")
        op.wait_for_load_state("networkidle")
        imported = {"h1": op.inner_text("h1"), "summary": op.inner_text("#import-summary")}
        op.goto(BASE + "/", wait_until="networkidle")
        op.locator("form[action='/reset'] button").click()
        op.wait_for_load_state("networkidle")
        reset = {
            "flash": op.locator(".flash").inner_text() if op.locator(".flash").count() else "",
            "cards": op.locator(".room-card").count(),
            "names": op.locator(".room-card h2").all_inner_texts(),
            "import_room_visible": "QA Import Room" in op.inner_text("body"),
        }
        op.goto(BASE + "/rooms/1/sheet", wait_until="networkidle")
        op.click("#copy-letter")
        copy_label = op.inner_text("#copy-letter")
        op.click("#print-sheet")
        op.wait_for_timeout(300)
        print_still = op.inner_text("#print-sheet")
        still_sheet = "/sheet" in op.url
        op.screenshot(path=str(SHOTS / "134-after-reset.png"))
        ok134 = (
            not dialogs_off
            and "QA134 Room" in added_room["h1"]
            and added_room["flash"] == "Room added."
            and added_reading["flash"] == "Reading added."
            and added_reading["rows"] == 1
            and "qa134" in added_reading["table"]
            and deleted_reading["flash"] == "Reading deleted."
            and deleted_reading["rows"] == 0
            and deleted_room["flash"] == "Room deleted."
            and deleted_room["cards"] == 3
            and not deleted_room["qa_room_visible"]
            and calc["humidex"] == "44.4"
            and export["has_study_room"]
            and export["has_header"]
            and imported["h1"] == "Import results"
            and "Readings added: 1" in imported["summary"]
            and "New rooms: 1" in imported["summary"]
            and reset["flash"] == "Sample data restored."
            and reset["cards"] == 3
            and not reset["import_room_visible"]
            and copy_label == "Copy letter"
            and print_still == "Print / Save as PDF"
            and still_sheet
        )
        record(
            134,
            ok134,
            {
                "dialogs": dialogs_off,
                "add_room": added_room,
                "add_reading": added_reading,
                "delete_reading": deleted_reading,
                "delete_room": deleted_room,
                "calculator": calc,
                "export": export,
                "import": imported,
                "reset": reset,
                "copy_label": copy_label,
                "print_label": print_still,
                "still_on_sheet": still_sheet,
            },
        )
        off.close()
        browser.close()

    report["failures"] = failures
    report["pass"] = failures == []
    report["git_at_end"] = git_identity()
    report["request_hosts"] = hosts_of(requests)
    # Keep the full request list out of the summary file; store hosts and a count.
    # The 137 detail already has the host set.
    (OUT / "qa-129-138.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"pass": report["pass"], "failures": failures, "git": report["git_at_end"]}, indent=2))
    for number, item in report["qa"].items():
        print(number, "PASS" if item["pass"] else "FAIL")
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
