# Hot Room Log — acceptance contract (rc4)

Candidate under test: rc4, built on rc3 (`e7a7d83eaf1c5d95934dfe98d729aec7e92fe539`, tag `rc3`, branch `rc3-work`).

Source of this rework: external FINAL review of rc3, decision CHANGES_REQUIRED. Required items are the numbered fixes in `/workspace/pipeline/review/hot-room-log-rc3-fix-task.md`. This contract is the checkable form of those items plus the flows that must still work. It is not a pass of the external review.

## Goal

A student can log temperature and humidity for a room on one local machine, see humidex, dew point, and how much humidity adds, and produce a polite evidence sheet they can copy or print. rc4 keeps that behavior and repairs the rc3 print regression, the printed page background, the latest-reading sentence, delivery docs, and the disclosure.

## Target environment

- OS: Linux. Browser: Chrome (headless or headed) for the checks below.
- Start, from `/workspace/hot-room-log-rc3`:

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

- App URL: `http://127.0.0.1:5050` (override with `PORT`). Binds to `127.0.0.1` unless `HOST` is set.
- No account and no login. Sample data loads once into `instance/hotroom.db`.
- The running app must not call a network API. The delivery video is the existing file `/workspace/demo/hot-room-log-demo-v4.mp4`. Do not re-narrate it.

## Core flows

1. First launch creates the database and three fictional sample rooms. The dashboard shows three banded cards.
2. Opening a room shows the latest humidex, the latest-reading sentence, a chart, and a table. Adding a valid reading updates the card, chart, and table. An invalid reading returns 400, keeps the typed values, and shows a field error.
3. The evidence sheet shows the summary, chart, table, method, and letter. Editing the letter, then Copy or Print, uses the edited text. Room 1 prints on at most 2 A4 pages. Navigation, buttons, and the textarea are not printed.
4. The calculator shows worked steps and a comparison sentence.
5. CSV export and import merge readings, skip exact duplicates, and report bad rows. Reset restores the three sample rooms after confirmation. Read-only mode returns 403 on writes.

## Scope

In scope for rc4: print chart labels, printed page background, latest-reading DOM text, docs and disclosure for demo v4, QA evidence on the rc4 tree, `BUILD-RC4.txt`, local commit and tag `rc4`.

## Non-goals

Do not invent a product decision for these conflicts. List them in `DECISIONS-NEEDED.txt` and leave the behavior as it is:

- README Chinese paragraph versus the brief (Chinese only in `idea.md`).
- Sample banner on the calculator and import pages versus the screenshot rule.
- JavaScript beyond copy, print, and confirm, versus the requirements.
- The words "one-page" versus a 2-page Room 1 sheet.

- Whether the brief's "no paid API" rule covers the DashScope/Bailian narration used only to produce the demo. Disclose that tool (A5). Do not rule on compliance, and do not remove or regenerate the narration.

Also out of scope: optional UI polish (autofocus on the first error, 320 px point-versus-label overlap, `type="text"` on the room name, hiding screen-only print hints, letter textarea growth, scrolling to the calculator result, copy-failure UI, import error heading, sheet "back to room" link, deep-JSON 500 / CSV message fixes), backend behavior changes, push, deploy, and Devpost submission. Do not regenerate the demo with edge-tts or a new TTS call.

## Acceptance criteria

A1. Print chart labels. The Print button, the browser print path (print preview / Ctrl+P's print pipeline), and Save as PDF, at both 1280 and 1920 CSS px viewports, produce an A4 PDF of Room 1 where every axis label and time label has a `pdftotext -bbox` box height of at least 7 pt, and not smaller than the same labels on a JavaScript-disabled print of the same page. Datapoints are visible as separate points. After leaving print, the on-screen chart matches the pre-fix screen metrics (label font size and point radius at 1280). Room 1 is still at most 2 pages.

A2. Printed page background. Page 2 below the footer is white when background graphics are printed and when they are not. The sheet is still 2 pages. Band colours on the page may still print.

A3. Latest-reading sentence. On the sample study room, the DOM text of the latest-facts line is exactly `Air 34 °C · Humidity 65 % · Dew point 26.5 °C · Humidity adds +13.6`. The middle dots are real text nodes. Narrow layouts may wrap or hide separators with CSS; they must not invent the dots only with CSS.

A4. Delivery video docs. `README.md`, `docs/devpost.md`, and `BUILD-RC4.txt` name `/workspace/demo/hot-room-log-demo-v4.mp4`, its sha256, its duration, and that the narration is DashScope/Bailian TTS (`qwen3-tts-flash`, voice Cherry) with burned-in English captions. They must not present silent v2 or edge-tts v3 as the delivery video. `docs/` contains a narration check that aligns the v4 speech with the scene script and does not claim a human listened unless a person did.

A5. Disclosure. About, README, and Devpost say the same facts: Grok wrote the app, docs, scripts, screenshots, and recording scripts; Claude drafted the planning docs; DashScope/Bailian TTS narrated the demo; Playwright/Chrome, ffmpeg, and DejaVu Sans were used to produce the demo. The phrase about no third-party images, fonts, or icons is limited to the running app, not the demo pipeline. The running app still does not call an external API.

A6. Final-build evidence. On the rc4 tree, after the last product edit: `pytest` exits 0; HTTP checks QA 124–127 pass, and the "after stop, nothing listens on 5050 or 5051" check actually runs (a failing `ss` probe must not skip it); browser checks QA 129–138 pass, including QA 134 with JavaScript off for add room, add reading, delete, calculator, export, import, and reset; 320 and 375 px widths; 200% zoom; keyboard traversal of dashboard, room, sheet, and calculator. Each evidence JSON records `git rev-parse HEAD` at generation time and the sha256 of `git diff HEAD`. Evidence file mtimes are later than the last product-code edit. `BUILD-RC3.txt` no longer claims a focus tooltip on datapoints unless a focus listener exists, and no longer claims a label-gap measurement that ignored point occlusion.

A7. Candidate package. Branch `rc3-work` has a local commit for this work, tag `rc4` points at the candidate, and `BUILD-RC4.txt` records the start command, port, environment, per-item pass/fail, evidence paths, and the v4 sha256. `review/rc4/` holds the requirements pointer, source hash, diff from rc3, start command, acceptance table, run evidence, known issues, and the demo (same bytes as the v4 file). No push and no Devpost activity. `git status` is clean aside from ignored files.

A8. Regression. Pytest sections A–O still pass. Browser flows for the dashboard cards, chart tooltip, edited-letter copy, confirm-cancel, and the evidence sheet still match QA 129–133.

A9. Decisions file. `DECISIONS-NEEDED.txt` lists all five conflicts in Non-goals, including whether "no paid API" covers the demo narration, with no chosen resolution. The A5 disclosure stays. The file must not add a sentence that rules any of the five.

A10. Video identity. The packaged demo's sha256 equals `f6f41d0ad643388d27526485fbcf87aaaa6325eaf06813375ab1947efadb26a1` and the duration is 152.067 seconds. Those values must be recomputed from the file, not copied on trust.
