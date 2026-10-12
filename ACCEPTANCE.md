# Hot Room Log — acceptance contract (rc7)

Candidate under test: rc7, built on rc6 (`16fc9352494d8643e1d36e6fdd996bb0adfd7c70`, tag `rc6`, branch `rc3-work`). Product parent of that tag is `a4e1542232d65dbdadf8195d4a6a55d856b87459`.

Source of this rework: `/workspace/pipeline/stemergent/FIX-TASK-RC7.md` (copy at `FIX-TASK-RC7.md` in this worktree, left untracked). Contract text stays v2: top-level `idea.md`, `prd.md`, and `qa.md` under `/workspace/pipeline/stemergent`. This contract is the checkable form of the rc7 work. It is not a pass of an external review.

## Goal

On the rc6 tree, stop the on-screen chart point and trend ink from covering y-axis labels 30, 40, and 45, including at 200% zoom and at narrow widths. Re-run pytest, QA 124–127, QA 129–138, and the print measurements on the new product commit, with an SVG hit test that can see that overlap. Keep the narrated v4 demo unless a frame shows the covered "40". Record the owner's QA 151 decision and close that item. Rehearse a local public-branch history that still shows the competition work and does not leak internal paths. Tag local `rc7`. The running app still calls no external service.

## Target environment

- OS: Linux. Browser checks use Chrome. One QA 134 hover shot is headed Chrome.
- Start, from the project directory:

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

- App URL: `http://127.0.0.1:5050` (override with `PORT`). Binds to `127.0.0.1` unless `HOST` is set.
- No account and no login. Sample data loads once into `instance/hotroom.db`.
- Do not regenerate the voice-over unless a kept timeline is impossible. The packaged file stays named `hot-room-log-demo-v4.mp4`. The rc6 file sha256 is `d42d05ef21227ccacbebce2ce36f693b3fe2810841399ae63bc3c71eaf3d2c9b` and the ffprobe duration is 152.067 seconds.

## Core flows

1. First launch creates the database and three fictional sample rooms. The dashboard shows three banded cards.
2. Opening a room shows the latest humidex, the latest-reading sentence, a chart, and a table. Adding a valid reading updates the card, chart, and table. An invalid reading returns 400, keeps the typed values, and shows a field error.
3. The evidence sheet shows the summary, chart, table, method, and letter. Editing the letter, then Copy or Print, uses the edited text. Room 1 prints on at most 2 A4 pages. For the sample study room, page 1 has the chart and the table, and page 2 has the edited letter. Navigation, buttons, footer links, the textarea, the "Letter (edit before sending)" label, and the screen sentence "Hot Room Log does not send anything. Copy the letter into your own email, or print this sheet." are not printed.
4. The calculator shows worked steps and a comparison sentence.
5. CSV export and import merge readings, skip exact duplicates, and report bad rows. Reset restores the three sample rooms after confirmation. Read-only mode returns 403 on writes.
6. With JavaScript off, add, delete, calculate, export, import, and reset still work. Chart points keep their server-rendered titles. Wide tables scroll inside `.table-scroll`. At 320, 375, 640, 720, 768, and 1280 px, and at 200% zoom, the y-axis labels 30, 40, and 45 are clear of point ink and the trend line on the room page and on the sheet.

## Scope

In scope for rc7:

- Horizontal inset of the first and last chart points in `hotroom/chart.py` `x_at` (about 20 viewBox units). The label anchor in `hotroom/templates/_chart.html` stays at x=50. JavaScript does not move labels. A screen-path radius cap is allowed only if the inset alone fails the SVG hit test, and only by the same idea as `printInkCoversLabels` (prd §3 whitelist item 4).
- QA 138 detection copied forward under `review/rc7/evidence/` so overlap checks include SVG text against circles and the trend polyline. 200% zoom runs that test. A point covering "40" at 320 or 375 px is a failure.
- Evidence regenerated under `review/rc7/evidence/`: pytest, QA 124–127, QA 129–138 at the widths above, and print measurements with occlusion checks. Every result file names the product commit. Files are written once, with LF line endings.
- Demo: keep the rc6 narrated file if no frame shows a covered "40". Copy it byte-for-byte into `review/rc7/`. Record that some frames may still show the previous point positions while the labels stay readable.
- English `DECISIONS-NEEDED.txt` with item 5 updated to the owner QA 151 decision. About, README, and Devpost disclosure wording stay as they are.
- A local public-branch dry-run (no push) documented in `BUILD-RC7.txt`.
- `BUILD-RC7.txt`, `review/rc7/`, local commit on `rc3-work`, and tag `rc7`.

## Non-goals

- Do not edit contract v2 (`idea.md`, `prd.md`, `qa.md`, `brief.md`, `contract-v1/`). Do not run `run.sh` on stemergent.
- Do not change the About AI disclosure, QA 119 text, README disclosure, Devpost disclosure, or `tests/test_o_pages.py` disclosure assertions.
- Do not call a TTS API unless the existing v4 timeline cannot be kept. Do not switch to the silent cut.
- Do not do the optional UX items listed in FIX-TASK-RC7 (room-name input type, autofocus on 400, calculator scroll, letter textarea min-height, print chart width, README screenshots, copy-failure honesty, API 400 for deep JSON or huge ints, CSV formula injection, tighter weak asserts, real Ctrl+P, Firefox, Safari, or a cable-unplugged QA 137).
- QA 139–145 and the live Devpost half of QA 146 stay submission-window work. The QA 146 item in this contract is the local dry-run only.
- Do not push, deploy, or submit to Devpost.
- Do not delete `FIX-TASK-RC6.md` or `FIX-TASK-RC7.md`. Leave both untracked. Do not add them to a commit.
- Do not change files under `review/rc4/`, `review/rc5/`, or `review/rc6/`. Copy scripts into `review/rc7/` and edit the copies.
- Do not rewrite rc3-work history. The public-branch rehearsal happens in a temporary clone.

## Acceptance criteria

A1. On-screen labels. For the sample study room, on `/rooms/1` and `/rooms/1/sheet`, at viewport widths 320, 375, 640, 720, 768, and 1280: each y-axis label 30, 40, and 45 has a `getBBox` that does not intersect any point box expanded by its full stroke, and does not intersect the trend polyline expanded by its full stroke. The same test is run for the 200% zoom cases (room, sheet, dashboard, calculator). Dashboard and calculator have no chart overlap failure. Label font size is not reduced as the fix. Each point still has the server-rendered `<title>`. Screenshots of the room and the sheet at each of those widths, and the 200% zoom shots, are under `review/rc7/evidence/qa-shots/`. The SVG hit results are in `review/rc7/evidence/qa-129-138.json` and show no hits.

A2. Geometry. `x_at` insets the first and last points by about 20 viewBox units from `PLOT_LEFT` (56) and `PLOT_RIGHT` (624). A single reading stays centered. The axis-label `x` stays 50 and `text-anchor` stays `end`. JavaScript does not set label positions. The rc6 screen radius formula `(7 * 640) / layoutWidth` still applies when the inset alone keeps the labels clear. If a required width still fails A1 after that inset, either increase the inset just enough to pass or cap screen radius and stroke the way `printInkCoversLabels` does, and record which one shipped. QA 55 still passes: six points, strictly increasing `cx`, the six humidex values, four strips, one trend polyline, `role="img"`, and a chart `<title>`.

A3. Print does not regress. For the sample study room's evidence sheet, at 1280 px and at 1920 px, for the Print button path and the native `beforeprint` path, with background graphics on and off: labels 30, 40, and 45 are not covered by a point or by the trend line, using the same full-stroke `getBBox` test as rc6. `pdftotext -bbox` height of every chart axis and time label is at least 7 pt and is not smaller than the same label in the noscript PDF from the same run. Six points stay visibly separate. Room 1 is at most 2 A4 pages. The edited letter is in the PDF. Page 1 does not contain "Letter (edit before sending)" or "Hot Room Log does not send anything". Page 2 contains the edited letter, including "Dear Room manager" when that is what was typed. Buttons are not on page 2. Each point still has the server-rendered `<title>`. Magnified label crops are saved.

A4. Pytest. On the final product tree, `.venv/bin/pytest -q` exits 0. The log is `review/rc7/evidence/pytest.txt` and includes the product commit hash. Its mtime is after the last edit to a product file (`app.py`, `hotroom/**`, `tests/**`, `requirements*.txt`). The hash-record commit does not change that log.

A5. QA 124–127. Re-run on a clean database copy. The log and HTTP captures are under `review/rc7/evidence/`. The server is stopped afterwards. Nothing is left listening on 5050 or 5051. The log names the product commit hash. Result lines are not rewritten later, and CRLF is not normalized in a follow-up commit.

A6. QA 129–138. Re-run and save `review/rc7/evidence/qa-129-138.json` plus screenshots. The JSON names the product commit hash. The SVG intersection check in A1 is part of QA 135 and QA 138, and a hit fails the case. QA 134 still includes both no-JS actions: (1) JavaScript off, hover all 6 points: no JS tooltip element in the DOM, each point `title` matches the QA 130 text, and one headed-Chrome hover screenshot is saved; (2) JavaScript off, viewports 375 and 320: `.table-scroll` `scrollWidth` > `clientWidth`, and the page itself has no horizontal overflow, with screenshots. The room-page focus pass records whether `#taken_at` shows a visible focus ring, with a screenshot taken while that control is focused.

A7. Print measurements. A3 sizes plus the occlusion checks are in `review/rc7/evidence/print/`. PDFs, bbox dumps, magnified label crops, and a JSON summary are there. The JSON names the product commit hash and the method. Evidence mtimes are after the last product-file edit. The hash-record commit does not change these files.

A8. Demo video. `review/rc7/hot-room-log-demo-v4.mp4` is 1920×1080, under 180 seconds, English narration and burned-in English captions. If no existing frame shows the "40" label covered, the file is a byte copy of `review/rc6/hot-room-log-demo-v4.mp4` (same sha256 and duration). `BUILD-RC7.txt` says that chart geometry in some frames may be from the prior build while the labels remain readable. Spot-check frames are under `review/rc7/evidence/video-frames/`, including the print still where 30, 40, and 45 are readable. `review/rc7/evidence/video-identity.txt` records sha256, ffprobe duration, and those timestamps. README and `docs/devpost.md` keep the same duration and the same disclosure sentences. No new TTS call was made. Re-capture pictures only if a frame shows the covered "40", and keep the existing audio unless the timeline breaks.

A9. QA 151 and the decisions file. `BUILD-RC7.txt`, `review/rc7/ACCEPTANCE-TABLE.md`, and `review/rc7/KNOWN-ISSUES.md` close QA 151. They cite `/workspace/pipeline/stemergent/QA151-DECISION.txt` and `/workspace/pipeline/stemergent/DECISIONS-NEEDED.txt`, timestamp 2026-10-12 03:39:15 CST (UTC+8), and the decision: qwen3-tts-flash calls used free quota and were not billed; Model Studio terms allow publishing the generated audio in a public video; submit the narrated v4 demo; keep the QA 119 / About TTS disclosure. They do not say "QA 151 pending". Repo-root `DECISIONS-NEEDED.txt` is English. It keeps the five contract-v2 decisions closed. Item 5 records that same owner decision. It has no character in the QA 147 ranges. About, README, and Devpost text are unchanged from rc6.

A10. Public-branch dry-run. `BUILD-RC7.txt` documents a local procedure that keeps meaningful commit history and, in a temporary clone only, drops `review/`, `BUILD*`, `ACCEPTANCE*`, `FIX-TASK*`, and `DECISIONS*` plus machine-local paths. Nothing is pushed. Saved evidence shows: `git log --all -p` on that clone has no match for `/workspace`, `builder-account`, or `grok-build`; `git log --oneline` still shows the work from rc1 through this candidate (more than one commit); a fresh clone of that filtered history follows the README quick start and `.venv/bin/pytest -q` exits 0. rc3-work's own history is not rewritten. The rc6 single-commit rsync plan is not the public history.

A11. Contract and scope held. SHA-256 of `/workspace/pipeline/stemergent/brief.md`, `idea.md`, `prd.md`, and `qa.md` match `BUILD-RC6.txt`:

- brief.md `a784723622afead05a8e029cc77dc65743911e418973f21a168d1b836f142688`
- idea.md `5cb30bfecfb9877c431f6bdc1a8305743373e5bbb5ec3159fd26fc4450859a83`
- prd.md `bd0a2a29219fbeab8a6c0732943379224bedcfe8c75c1ade2da7d5d2f75c769e`
- qa.md `1961075a80ebb305dfc084394e7136ae0a868c72661883945b31e5fade4049c6`

About disclosure text and QA 119 tests are unchanged. Optional UX items stay undone. No FINAL PASS is claimed.

A12. Candidate package. Branch `rc3-work`. The product commit contains the chart fix and the English decisions file and does not contain its own hash. Evidence is generated after that commit and already contains that hash when it is first committed. A later hash-record commit updates `BUILD-RC7.txt` and `review/rc7/SOURCE.txt` (and the acceptance table if needed) so they name the product commit. That hash-record commit does not change product files and does not change evidence result files. Tag `rc7` points at the hash-record commit. The tagged commit does not contain its own hash. `review/rc7/` holds the requirements pointer, source hashes, diff from rc6, start command, acceptance table, evidence, known issues, and the demo. Nothing was pushed. Nothing was submitted. `git status` is clean except untracked `FIX-TASK-RC6.md`, untracked `FIX-TASK-RC7.md`, and ignored files.

A13. Evidence timing. Every JSON and log under `review/rc7/evidence/` that records a result names the product commit. File mtimes for pytest, QA, and print evidence are later than the last product-file edit. No later commit rewrites those result lines.

A14. Known issues and status. `review/rc7/KNOWN-ISSUES.md` does not list QA 151 as pending and does not reopen the five contract-v2 decisions. It lists QA 139–145 as not run. It lists the local QA 146 dry-run as a rehearsal, not a live submission. It keeps any limit the new evidence still shows (headless Chrome does not fire `beforeprint` for Ctrl+P; QA 137 did not unplug a cable). It does not claim a FINAL PASS. Status of the candidate is: implementation and self-check done, awaiting acceptance.
