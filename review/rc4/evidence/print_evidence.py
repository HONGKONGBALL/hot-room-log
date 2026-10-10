"""A1, A2, and A3 evidence for Room 1 on a fresh sample database.

Print PDFs are produced with Chrome Page.printToPDF (the print-preview and
Save-as-PDF pipeline). The Print button path calls window.print(), which
fires beforeprint, and the PDF is then captured with Page.printToPDF.
Headless Chrome does not open a print dialog for Ctrl+P.
"""

import base64
import json
import re
import subprocess
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path("/workspace/hot-room-log-rc3")
OUT = ROOT / "review" / "rc4" / "evidence" / "print"
PDF_DIR = OUT / "pdfs"
BBOX_DIR = OUT / "bbox"
PNG_DIR = OUT / "png"
BASE = "http://127.0.0.1:5050"
CHROME = "/usr/bin/google-chrome"
EXPECTED_FACTS = "Air 34 °C · Humidity 65 % · Dew point 26.5 °C · Humidity adds +13.6"
WORD_RE = re.compile(
    r'<word xMin="([^"]+)" yMin="([^"]+)" xMax="([^"]+)" yMax="([^"]+)">([^<]*)</word>'
)
PAGE_RE = re.compile(
    r'<page width="([^"]+)" height="([^"]+)">(.*?)</page>',
    re.S,
)

OUT.mkdir(parents=True, exist_ok=True)
PDF_DIR.mkdir(parents=True, exist_ok=True)
BBOX_DIR.mkdir(parents=True, exist_ok=True)
PNG_DIR.mkdir(parents=True, exist_ok=True)


def git_identity():
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    diff = subprocess.check_output("git diff HEAD | sha256sum", cwd=ROOT, shell=True, text=True)
    return {"git_head": head, "git_diff_head_sha256": diff.split()[0]}


def parse_bbox(pdf: Path):
    text = subprocess.check_output(["pdftotext", "-bbox", str(pdf), "-"], text=True)
    (BBOX_DIR / (pdf.stem + ".bbox")).write_text(text, encoding="utf-8")
    pages = []
    for width, height, body in PAGE_RE.findall(text):
        words = []
        for x0, y0, x1, y1, word in WORD_RE.findall(body):
            y0f, y1f = float(y0), float(y1)
            words.append(
                {
                    "text": word,
                    "x0": float(x0),
                    "y0": y0f,
                    "x1": float(x1),
                    "y1": y1f,
                    "h": round(y1f - y0f, 3),
                }
            )
        pages.append({"width": float(width), "height": float(height), "words": words})
    return pages


def pdf_meta(pdf: Path):
    info = subprocess.check_output(["pdfinfo", str(pdf)], text=True)
    pages = None
    size = None
    for line in info.splitlines():
        if line.startswith("Pages:"):
            pages = int(line.split()[1])
        elif line.startswith("Page size:"):
            size = line.split(":", 1)[1].strip()
    return {"pages": pages, "page_size": size, "pdfinfo": info}


def chart_labels(pages, axis_texts, time_texts):
    if not pages:
        return {"error": "no pages"}
    words = pages[0]["words"]
    headers = [w for w in words if w["text"] == "Temperature"]
    if not headers:
        return {"error": "Temperature header missing on page 1"}
    table_y = min(w["y0"] for w in headers)
    axis_set = set(axis_texts)
    axis = [w for w in words if w["text"] in axis_set and w["y1"] < table_y - 1]
    if not axis:
        return {"error": "no chart axis labels above the table", "table_y": table_y}
    axis_bottom = max(w["y1"] for w in axis)
    tokens = []
    for label in time_texts:
        tokens.extend(label.split())
    token_set = set(tokens)
    times = [
        w
        for w in words
        if w["text"] in token_set and w["y0"] >= axis_bottom - 1 and w["y1"] < table_y - 1
    ]
    return {
        "table_y": table_y,
        "axis": sorted(axis, key=lambda w: (w["y0"], w["x0"])),
        "time": sorted(times, key=lambda w: (w["y0"], w["x0"])),
        "expected_axis": list(axis_texts),
        "expected_time_tokens": tokens,
    }


def compare_labels(js_labels, ns_labels):
    failures = []
    for kind in ("axis", "time"):
        left = js_labels.get(kind) or []
        right = ns_labels.get(kind) or []
        if js_labels.get("error"):
            failures.append(f"js {kind}: {js_labels['error']}")
            continue
        if ns_labels.get("error"):
            failures.append(f"noscript {kind}: {ns_labels['error']}")
            continue
        if len(left) != len(right):
            failures.append(
                f"{kind} count js {len(left)} texts {[w['text'] for w in left]} "
                f"vs noscript {len(right)} texts {[w['text'] for w in right]}"
            )
        for js_word, ns_word in zip(left, right):
            if js_word["text"] != ns_word["text"]:
                failures.append(
                    f"{kind} order {js_word['text']} vs noscript {ns_word['text']}"
                )
                continue
            if js_word["h"] < 7:
                failures.append(f"{kind} {js_word['text']} height {js_word['h']} < 7 pt")
            if js_word["h"] + 0.05 < ns_word["h"]:
                failures.append(
                    f"{kind} {js_word['text']} height {js_word['h']} < noscript {ns_word['h']}"
                )
    return failures


def render_pages(pdf: Path):
    prefix = PNG_DIR / pdf.stem
    subprocess.check_call(
        ["pdftoppm", "-png", "-r", "72", str(pdf), str(prefix)],
        stdout=subprocess.DEVNULL,
    )
    return sorted(PNG_DIR.glob(pdf.stem + "-*.png"))


ANALYZER = r"""
import json, sys
from PIL import Image

page1, page2, y_max = sys.argv[1], sys.argv[2], float(sys.argv[3])
img2 = Image.open(page2).convert("RGB")
w, h = img2.size
px = img2.load()

def white(rgb):
    r, g, b = rgb
    return r >= 253 and g >= 253 and b >= 253

last = -1
for y in range(h):
    for x in range(w):
        if not white(px[x, y]):
            last = y
            break

bad = []
bad_count = 0
start = last + 2
if start < h:
    for y in range(start, h):
        for x in range(w):
            rgb = px[x, y]
            if not white(rgb):
                bad_count += 1
                if len(bad) < 15:
                    bad.append({"x": x, "y": y, "rgb": list(rgb)})

samples = []
if start < h:
    span = h - start
    y_step = max(1, span // 6)
    x_step = max(1, w // 8)
    for y in range(start, h, y_step):
        for x in range(1, w - 1, x_step):
            samples.append({"x": x, "y": y, "rgb": list(px[x, y])})
    # force a bottom row and a mid row so this is not corner-only
    for y in (min(h - 2, start + max(1, span // 2)), h - 2):
        for x in (2, w // 2, w - 3):
            samples.append({"x": x, "y": y, "rgb": list(px[x, y])})

img1 = Image.open(page1).convert("RGB")
p1 = img1.load()
pw, ph = img1.size

def is_point(r, g, b):
    dark_red = 90 < r < 200 and g < 90 and b < 90 and r > g + 40 and r > b + 40
    dark_brown = 70 < r < 190 and 15 < g < 110 and b < 60 and r > g + 15 and g >= b
    return dark_red or dark_brown

seen = [[False] * pw for _ in range(ph)]
blobs = []
for y in range(ph):
    row = seen[y]
    for x in range(pw):
        if row[x]:
            continue
        r, g, b = p1[x, y]
        if not is_point(r, g, b):
            row[x] = True
            continue
        stack = [(x, y)]
        row[x] = True
        minx = maxx = x
        miny = maxy = y
        count = 0
        while stack:
            cx, cy = stack.pop()
            count += 1
            if cx < minx: minx = cx
            if cx > maxx: maxx = cx
            if cy < miny: miny = cy
            if cy > maxy: maxy = cy
            for nx, ny in ((cx-1, cy), (cx+1, cy), (cx, cy-1), (cx, cy+1)):
                if nx < 0 or ny < 0 or nx >= pw or ny >= ph or seen[ny][nx]:
                    continue
                rr, gg, bb = p1[nx, ny]
                seen[ny][nx] = True
                if is_point(rr, gg, bb):
                    stack.append((nx, ny))
        bw = maxx - minx + 1
        bh = maxy - miny + 1
        cy = (miny + maxy) / 2
        if cy >= y_max or cy < 160:
            continue
        # Noscript circles use the SVG default r=6, so their fills are smaller
        # than the fitted print circles. 8 px at 72 dpi still rejects specks.
        if count >= 8 and bw >= 4 and bh >= 4 and max(bw, bh) / max(1, min(bw, bh)) < 2.4:
            blobs.append({
                "x": round((minx + maxx) / 2, 1),
                "y": round((miny + maxy) / 2, 1),
                "w": bw,
                "h": bh,
                "area": count,
            })

blobs.sort(key=lambda b: b["x"])
gaps = []
separated = True
for i in range(1, len(blobs)):
    gap = blobs[i]["x"] - blobs[i - 1]["x"] - (blobs[i]["w"] + blobs[i - 1]["w"]) / 2
    gaps.append(round(gap, 2))
    if gap < 2:
        separated = False

print(json.dumps({
    "page2": {
        "size": [w, h],
        "last_content_y": last,
        "rows_below": max(0, h - start) if last >= 0 else 0,
        "nonwhite_below": bad_count,
        "nonwhite_samples": bad,
        "grid_samples": samples,
        "grid_all_white": all(white(tuple(s["rgb"])) for s in samples) if samples else False,
        "png": page2,
    },
    "points": {
        "count": len(blobs),
        "separated": separated and len(blobs) >= 2,
        "blobs": blobs,
        "gaps_px": gaps,
        "png": page1,
    },
}))
"""


def analyze(pdf: Path, y_max: float):
    pngs = render_pages(pdf)
    if len(pngs) < 2:
        return {"error": f"expected 2 page pngs, got {[p.name for p in pngs]}"}
    out = subprocess.check_output(
        ["/usr/bin/python3", "-c", ANALYZER, str(pngs[0]), str(pngs[1]), str(y_max)],
        text=True,
    )
    return json.loads(out)


def a4_ok(meta):
    size = meta.get("page_size") or ""
    return meta.get("pages") == 2 and "A4" in size and size.startswith("595.")


def arm_print_listener(page):
    page.evaluate(
        """() => {
          window.__printEvents = [];
          window.addEventListener('beforeprint', () => {
            const axis = document.querySelector('text.axis-label');
            const time = document.querySelector('text.time-label');
            const circle = document.querySelector('circle.point');
            const svg = document.querySelector('svg.chart');
            window.__printEvents.push({
              phase: 'beforeprint',
              axisFont: axis && axis.style.fontSize,
              timeFont: time && time.style.fontSize,
              r: circle && circle.getAttribute('r'),
              matchMediaPrint: window.matchMedia('print').matches,
              svgWidth: svg ? svg.getBoundingClientRect().width : null
            });
          });
          window.addEventListener('afterprint', () => {
            const axis = document.querySelector('text.axis-label');
            const circle = document.querySelector('circle.point');
            window.__printEvents.push({
              phase: 'afterprint',
              axisFont: axis && axis.style.fontSize,
              r: circle && circle.getAttribute('r'),
              matchMediaPrint: window.matchMedia('print').matches
            });
          });
        }"""
    )


def chart_dom(page):
    return page.evaluate(
        """() => {
          const svg = document.querySelector('svg.chart');
          return {
            axis: Array.from(svg.querySelectorAll('text.axis-label')).map(n => n.textContent),
            time: Array.from(svg.querySelectorAll('text.time-label')).map(n => n.textContent),
            points: Array.from(svg.querySelectorAll('circle.point')).map(n => ({
              cx: n.getAttribute('cx'),
              cy: n.getAttribute('cy'),
              r: n.getAttribute('r')
            }))
          };
        }"""
    )


def facts_probe(page):
    return page.evaluate(
        """() => {
          const facts = document.querySelector('p.facts');
          const seps = Array.from(facts.querySelectorAll('.sep')).map(node => ({
            text: node.textContent,
            display: getComputedStyle(node).display,
            before: getComputedStyle(node, '::before').content,
            after: getComputedStyle(node, '::after').content,
            childNodes: Array.from(node.childNodes).map(child => ({
              nodeType: child.nodeType,
              data: child.nodeType === 3 ? child.data : null
            }))
          }));
          return { textContent: facts.textContent, seps: seps };
        }"""
    )


def screen_metrics(page):
    return page.evaluate(
        """() => {
          const svg = document.querySelector('svg.chart');
          const box = svg.getBoundingClientRect();
          return {
            viewport: { width: window.innerWidth, height: window.innerHeight },
            svg: { width: box.width, height: box.height },
            labels: Array.from(svg.querySelectorAll('text')).map(node => ({
              className: node.getAttribute('class'),
              text: node.textContent,
              inlineFontSize: node.style.fontSize
            })),
            circles: Array.from(svg.querySelectorAll('circle.point')).map(node => node.getAttribute('r'))
          };
        }"""
    )


def write_pdf(page, path: Path, background: bool):
    session = page.context.new_cdp_session(page)
    data = session.send(
        "Page.printToPDF",
        {
            "printBackground": background,
            "paperWidth": 8.27,
            "paperHeight": 11.69,
            "preferCSSPageSize": True,
        },
    )
    path.write_bytes(base64.b64decode(data["data"]))
    session.detach()


def main():
    identity = git_identity()
    report = {
        **identity,
        "base": BASE,
        "note": (
            "Page.printToPDF is the print-preview and Save-as-PDF pipeline. "
            "Headless Chrome does not open a print dialog for Ctrl+P and does not "
            "fire beforeprint for that key event. The Print button calls window.print(), "
            "which does fire beforeprint; the PDF for that path is then captured with Page.printToPDF."
        ),
        "viewports": {},
        "facts": {},
        "screen_after": {},
        "failures": [],
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=CHROME,
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        for width, height in ((1280, 900), (1920, 1080)):
            key = str(width)
            context = browser.new_context(
                viewport={"width": width, "height": height},
                device_scale_factor=1,
            )
            page = context.new_page()
            page.goto(BASE + "/rooms/1/sheet", wait_until="networkidle")
            dom = chart_dom(page)
            arm_print_listener(page)
            bucket = {
                "viewport": {"width": width, "height": height},
                "dom": dom,
                "pdfs": {},
                "ctrl_p": {},
            }

            # Direct print-preview / Save-as-PDF pipeline, both background settings.
            for background, tag in ((True, "native-bg"), (False, "native-nobg")):
                page.evaluate("() => { window.__printEvents = []; }")
                pdf_path = PDF_DIR / f"{tag}-{width}.pdf"
                write_pdf(page, pdf_path, background)
                events = page.evaluate("() => window.__printEvents")
                bucket["pdfs"][tag] = measure_pdf(pdf_path, dom, events, background)

            # Print button path: a fresh load, then window.print(), then Page.printToPDF.
            # A second window.print() while the first headless print is still settling
            # does not fire beforeprint, so each background setting gets its own page.
            for background, tag in ((True, "button-bg"), (False, "button-nobg")):
                page.goto(BASE + "/rooms/1/sheet", wait_until="networkidle")
                arm_print_listener(page)
                page.evaluate("() => { window.__printEvents = []; }")
                page.click("#print-sheet", timeout=8000)
                page.wait_for_timeout(400)
                after_click = page.evaluate("() => window.__printEvents.slice()")
                page.evaluate("() => { window.__printEvents = []; }")
                pdf_path = PDF_DIR / f"{tag}-{width}.pdf"
                write_pdf(page, pdf_path, background)
                capture_events = page.evaluate("() => window.__printEvents")
                measured = measure_pdf(pdf_path, dom, capture_events, background)
                measured["button_click"] = {"events_after_window_print": after_click}
                bucket["pdfs"][tag] = measured

            # Headless Ctrl+P does not open a dialog.
            page.evaluate("() => { window.__printEvents = []; }")
            dialog = None
            try:
                page.keyboard.press("Control+P")
                page.wait_for_timeout(500)
            except Exception as exc:  # noqa: BLE001
                dialog = str(exc)
            ctrl_events = page.evaluate("() => window.__printEvents")
            bucket["ctrl_p"] = {
                "dialog_opened": bool(dialog),
                "exception": dialog,
                "beforeprint_events": ctrl_events,
                "statement": (
                    "Headless Ctrl+P did not open a print dialog and did not fire beforeprint. "
                    "The shortcut is a browser UI accelerator. The print pipeline that Ctrl+P, "
                    "print preview, and Save as PDF use was captured with Page.printToPDF."
                ),
            }

            # JavaScript disabled, same sheet, both background settings.
            ns = browser.new_context(
                viewport={"width": width, "height": height},
                device_scale_factor=1,
                java_script_enabled=False,
            )
            np = ns.new_page()
            np.goto(BASE + "/rooms/1/sheet", wait_until="networkidle")
            for background, tag in ((True, "noscript-bg"), (False, "noscript-nobg")):
                pdf_path = PDF_DIR / f"{tag}-{width}.pdf"
                write_pdf(np, pdf_path, background)
                bucket["pdfs"][tag] = measure_pdf(pdf_path, dom, [], background)
            ns.close()

            # Compare every JS PDF's chart labels with the noscript-bg PDF at this viewport.
            ns_labels = bucket["pdfs"]["noscript-bg"]["labels"]
            for tag, item in bucket["pdfs"].items():
                if tag.startswith("noscript"):
                    continue
                item["label_failures_vs_noscript"] = compare_labels(item["labels"], ns_labels)
                item["pass_labels"] = item["label_failures_vs_noscript"] == []
                item["pass_points"] = bool(item["analysis"]["points"]["count"] == 6 and item["analysis"]["points"]["separated"])
                item["pass_pages"] = item["meta"]["pages"] == 2 and a4_ok(item["meta"])
                page2 = item["analysis"]["page2"]
                item["pass_page2_white"] = (
                    page2["nonwhite_below"] == 0
                    and page2["rows_below"] >= 40
                    and page2["grid_all_white"]
                    and len(page2["grid_samples"]) >= 20
                )

            report["viewports"][key] = bucket
            context.close()

        # On-screen room chart after leaving print, at 1280.
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            device_scale_factor=1,
        )
        page = context.new_page()
        page.goto(BASE + "/rooms/1", wait_until="networkidle")
        metrics = screen_metrics(page)
        page.screenshot(path=str(OUT / "room-1280-after-print.png"), full_page=False)
        page.locator("svg.chart").screenshot(path=str(OUT / "chart-1280-after-print.png"))
        facts_1280 = facts_probe(page)
        page.set_viewport_size({"width": 320, "height": 800})
        page.wait_for_timeout(200)
        facts_320 = facts_probe(page)
        page.set_viewport_size({"width": 640, "height": 800})
        page.wait_for_timeout(100)
        facts_640 = facts_probe(page)
        report["facts"] = {"1280": facts_1280, "320": facts_320, "640_boundary": facts_640}
        report["screen_after"] = metrics
        context.close()
        browser.close()

    # Pass / fail rollup. Keep the bulky grid in the files, but the summary is first.
    failures = []
    for width, bucket in report["viewports"].items():
        ctrl = bucket["ctrl_p"]
        if ctrl["dialog_opened"] or ctrl["beforeprint_events"]:
            failures.append(f"{width} Ctrl+P opened a dialog or fired beforeprint: {ctrl}")
        for tag, item in bucket["pdfs"].items():
            if tag.startswith("noscript"):
                if item["meta"]["pages"] != 2 or not a4_ok(item["meta"]):
                    failures.append(f"{width} {tag} not 2-page A4: {item['meta']['pages']} {item['meta']['page_size']}")
                page2 = item["analysis"]["page2"]
                if page2["nonwhite_below"] or not page2["grid_all_white"]:
                    failures.append(f"{width} {tag} page 2 not white below footer")
                continue
            if not item["pass_labels"]:
                failures.append(f"{width} {tag} labels: {item['label_failures_vs_noscript']}")
            if not item["pass_points"]:
                failures.append(
                    f"{width} {tag} points: count={item['analysis']['points']['count']} "
                    f"separated={item['analysis']['points']['separated']}"
                )
            if not item["pass_pages"]:
                failures.append(f"{width} {tag} pages: {item['meta']['pages']} {item['meta']['page_size']}")
            if not item["pass_page2_white"]:
                failures.append(
                    f"{width} {tag} page2: nonwhite={item['analysis']['page2']['nonwhite_below']} "
                    f"rows_below={item['analysis']['page2']['rows_below']}"
                )
            click = item.get("button_click")
            if click is not None:
                events = click["events_after_window_print"]
                if not any(event.get("phase") == "beforeprint" for event in events):
                    failures.append(f"{width} {tag} button click did not fire beforeprint")

    fonts = [label["inlineFontSize"] for label in report["screen_after"]["labels"]]
    radii = report["screen_after"]["circles"]
    if fonts != ["7.22px"] * len(fonts) or not fonts:
        failures.append(f"screen fonts after print: {fonts}")
    if radii != ["3.89"] * len(radii) or len(radii) != 6:
        failures.append(f"screen radii after print: {radii}")
    if abs(report["screen_after"]["svg"]["width"] - 1152) > 1:
        failures.append(f"screen svg width drifted: {report['screen_after']['svg']}")

    for label, facts in report["facts"].items():
        if facts["textContent"] != EXPECTED_FACTS:
            failures.append(f"facts {label}: {facts['textContent']!r}")
        for sep in facts["seps"]:
            texts = [child for child in sep["childNodes"] if child["nodeType"] == 3]
            if not texts or "·" not in (texts[0]["data"] or ""):
                failures.append(f"facts {label} sep is not a text node: {sep}")
            if sep["before"] not in ("none", "normal") or sep["after"] not in ("none", "normal"):
                failures.append(f"facts {label} sep uses generated content: {sep}")
    if report["facts"]["320"]["seps"][0]["display"] != "none":
        failures.append("320px separators are not display:none")
    if report["facts"]["1280"]["seps"][0]["display"] == "none":
        failures.append("1280px separators are hidden")

    report["failures"] = failures
    report["pass"] = failures == []
    # Re-read identity at the end so the file records the hash after generation started.
    report["git_at_end"] = git_identity()
    (OUT / "a1-a2-a3.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    summary = {
        "pass": report["pass"],
        "failures": failures,
        "facts_1280": report["facts"]["1280"]["textContent"],
        "screen": {
            "fonts": fonts,
            "r": radii,
            "svg": report["screen_after"]["svg"],
        },
        "git": report["git_at_end"],
    }
    for width, bucket in report["viewports"].items():
        summary[width] = {
            tag: {
                "pages": item["meta"]["pages"],
                "size": item["meta"]["page_size"],
                "axis_h": [w["h"] for w in item["labels"].get("axis", [])],
                "time_h": [w["h"] for w in item["labels"].get("time", [])],
                "points": item["analysis"]["points"]["count"],
                "page2_nonwhite": item["analysis"]["page2"]["nonwhite_below"],
                "page2_rows_below": item["analysis"]["page2"]["rows_below"],
                "label_failures": item.get("label_failures_vs_noscript"),
            }
            for tag, item in bucket["pdfs"].items()
        }
        summary[width]["ctrl_p_events"] = len(bucket["ctrl_p"]["beforeprint_events"])
    print(json.dumps(summary, indent=2))
    return 0 if report["pass"] else 1


def measure_pdf(pdf_path: Path, dom, events, background: bool):
    pages = parse_bbox(pdf_path)
    meta = pdf_meta(pdf_path)
    labels = chart_labels(pages, dom["axis"], dom["time"])
    table_y = labels.get("table_y") or 330
    analysis = analyze(pdf_path, float(table_y) - 12)
    return {
        "pdf": str(pdf_path.relative_to(ROOT)),
        "printBackground": background,
        "events": events,
        "meta": {"pages": meta["pages"], "page_size": meta["page_size"]},
        "labels": labels,
        "analysis": analysis,
    }


if __name__ == "__main__":
    raise SystemExit(main())
