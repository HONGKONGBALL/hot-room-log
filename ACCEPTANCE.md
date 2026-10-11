# Hot Room Log — acceptance contract (rc6)

Candidate under test: rc6, built on rc5 (`14f04de30d4cf591efd57e1564a49e574e22000c`, tag `rc5`, branch `rc3-work`). Product parent of that tag is `85e5aaeccfa66f66883d2ff69561bc451e33d796`.

Source of this rework: `/workspace/pipeline/stemergent/FIX-TASK-RC6.md` (copy at `FIX-TASK-RC6.md` in this worktree, left untracked). Contract text stays v2: top-level `idea.md`, `prd.md`, and `qa.md` under `/workspace/pipeline/stemergent`. This contract is the checkable form of the rc6 work. It is not a pass of an external review.

## Goal

On the rc5 tree, stop printed chart points and the trend line from covering the y-axis labels 30, 40, and 45, and stop screen-only letter chrome from printing on page 1. Re-run the browser and print evidence on the new product commit, including the QA 134 v2 no-JS checks. Refresh only the About and print pictures in the demo, keeping the existing v4 audio and caption timeline. Record a local `rc6` tag and a public-export note. The running app still calls no external service.

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
- Do not regenerate the voice-over. The packaged file stays named `hot-room-log-demo-v4.mp4`. Audio and burned-in caption timing stay the v4 timeline (sha256 of the rc5 picture+audio file was `f6f41d0ad643388d27526485fbcf87aaaa6325eaf06813375ab1947efadb26a1`, duration 152.067 seconds). Replacing About and print pictures changes the file hash. Duration stays 152.067 seconds unless the mux itself changes it, in which case README, Devpost, and BUILD-RC6 all show the new ffprobe duration.

## Core flows

1. First launch creates the database and three fictional sample rooms. The dashboard shows three banded cards.
2. Opening a room shows the latest humidex, the latest-reading sentence, a chart, and a table. Adding a valid reading updates the card, chart, and table. An invalid reading returns 400, keeps the typed values, and shows a field error.
3. The evidence sheet shows the summary, chart, table, method, and letter. Editing the letter, then Copy or Print, uses the edited text. Room 1 prints on at most 2 A4 pages. For the sample study room, page 1 has the chart and the table, and page 2 has the edited letter. Navigation, buttons, footer links, the textarea, the "Letter (edit before sending)" label, and the screen sentence "Hot Room Log does not send anything. Copy the letter into your own email, or print this sheet." are not printed.
4. The calculator shows worked steps and a comparison sentence.
5. CSV export and import merge readings, skip exact duplicates, and report bad rows. Reset restores the three sample rooms after confirmation. Read-only mode returns 403 on writes.
6. With JavaScript off, add, delete, calculate, export, import, and reset still work. Chart points keep their server-rendered titles. Wide tables scroll inside `.table-scroll`.

## Scope

In scope for rc6:

- Print-only chart fitting in `hotroom/static/app.js`, and print CSS or markup needed to hide the letter label and the screen instruction. Screen layout at viewport width ≥640 px stays as it is on rc5.
- Evidence regenerated under `review/rc6/evidence/`: pytest, QA 124–127, QA 129–138 including QA 134 v2, and print measurements with occlusion checks.
- Demo picture refresh for the About segment and the print stills only. Mux onto the existing v4 audio.
- `docs/narration-check.md` path cleanup, README and Devpost video identity lines, `BUILD-RC6.txt`, `review/rc6/`, `KNOWN-ISSUES` for this candidate.
- Local commit on `rc3-work` and tag `rc6`.

## Non-goals

- Do not edit contract v2 (`idea.md`, `prd.md`, `qa.md`, `brief.md`, `contract-v1/`). Do not run `run.sh` on stemergent.
- Do not change the About AI disclosure, QA 119 text, or `tests/test_o_pages.py` disclosure assertions.
- Do not invent a QA 151 billing or terms result. Do not switch the video to the silent cut. Do not call a TTS API unless the existing timeline cannot be kept, and do not call one without recording why the timeline broke.
- Do not do the optional UX items listed in FIX-TASK-RC6 (error scroll, calculator scroll, room-name input type, copy-failure honesty, API 400 for deep JSON, tighter pytest asserts, tag style).
- QA 139–146 stay submission-window work. They are not required to tag rc6.
- Do not push, deploy, or submit to Devpost.
- Do not delete `FIX-TASK-RC6.md`. Leave it untracked.
- Do not change rc4 or rc5 evidence files.

## Acceptance criteria

A1. Printed y-axis labels. For the sample study room's evidence sheet, at 1280 px and at 1920 px, for the Print button path and the native `beforeprint` path, with background graphics on and off: the labels 30, 40, and 45 are not covered by a point or by the trend line. Under print media, each label `getBBox` does not intersect any point box expanded by its stroke, and does not intersect the trend stroke box. Magnified screenshots of that label region are saved. `pdftotext -bbox` height of every chart axis and time label is at least 7 pt and is not smaller than the same label in the noscript PDF from the same run. Six points stay visibly separate. Room 1 is at most 2 A4 pages. The edited letter is in the PDF. Header navigation, buttons, footer links, and the textarea are absent. Each point still has the server-rendered `<title>`.

A2. Screen at ≥640 px. At a 1280 px viewport the on-screen chart still uses the rc5 fit: point `cx` values stay the server coordinates (first point 56.00), and the on-screen radius still follows `(7 * 640) / layoutWidth` rather than the print radius. A 1280 px room screenshot from after the change is saved. No screen-only layout, copy, or color change on the dashboard, room, sheet, or calculator at ≥640 px.

A3. Print chrome. On the same PDFs, page 1 does not contain "Letter (edit before sending)" and does not contain "Hot Room Log does not send anything". Page 2 contains the edited letter, including "Dear Room manager" when that is what was typed. Buttons are not on page 2. The sheet is still at most 2 A4 pages. If hiding the chrome would pull the letter onto page 1, a print page-break keeps the letter on page 2.

A4. Pytest. On the final product tree, `.venv/bin/pytest -q` exits 0. The log is `review/rc6/evidence/pytest.txt` and includes the commit hash. Its mtime is after the last edit to a product file (`app.py`, `hotroom/**`, `tests/**`, `requirements*.txt`).

A5. QA 124–127. Re-run on a clean database copy. The log and HTTP captures are under `review/rc6/evidence/`. The server is stopped afterwards. Nothing is left listening on 5050 or 5051. The log names the product commit hash.

A6. QA 129–138, including QA 134 v2. Re-run and save `review/rc6/evidence/qa-129-138.json` plus screenshots. The JSON names the product commit hash. QA 134 includes both missing no-JS actions: (1) JavaScript off, hover all 6 points: no JS tooltip element in the DOM, each point `title` matches the QA 130 text, and one headed-Chrome hover screenshot is saved; (2) JavaScript off, viewports 375 and 320: `.table-scroll` `scrollWidth` > `clientWidth`, and the page itself has no horizontal overflow, with screenshots. The room-page focus pass records whether `#taken_at` (datetime-local) shows a visible focus ring, with a screenshot taken while that control is focused.

A7. Print measurements. A1/A2 sizes plus the A1 occlusion checks are in `review/rc6/evidence/print/`. PDFs, bbox dumps, magnified label crops, and a JSON summary are there. The JSON names the product commit hash and the method. Evidence mtimes are after the last product-file edit.

A8. Demo video. `review/rc6/hot-room-log-demo-v4.mp4` is 1920×1080, under 180 seconds, with the existing v4 English narration and captions. About frames show the current About page: "printable evidence sheet", no "one-page" or "one page", and the AI disclosure that names an AI-generated voice, Model Studio, and qwen3-tts-flash. Print frames show the fixed chart (the 40 label readable) and do not show "Letter (edit before sending)" on the printed page; page 2 still shows the edited greeting. Spot-check frames and timestamps are under `review/rc6/evidence/video-frames/`. `review/rc6/evidence/video-identity.txt` records sha256, ffprobe duration, and those timestamps. README and `docs/devpost.md` state the same duration and do not claim the file is absent or name a local absolute path. No new TTS call was made.

A9. Public export. `docs/narration-check.md` has no `/workspace`, `/etc`, or other machine-local absolute path, and its sha256 and duration match the packaged video. `BUILD-RC6.txt` documents the export filter. A clean export excludes `review/`, local task files, and build notes that contain machine paths or account details (`builder-account.txt` and the same class of file). `git grep "/workspace"` on that export is empty. The command and its empty result are saved at `review/rc6/evidence/public-export-grep.txt`. README and Devpost name the public video URL as an explicit TBD placeholder and do not contain a local absolute path.

A10. Decisions and known issues. `DECISIONS-NEEDED.txt` is unchanged: QA 151 stays pending for Zhenhua, with no billing result. `review/rc6/KNOWN-ISSUES.md` does not repeat the rc4 "A7 is not met" line and does not reopen the five contract-v2 decisions. It lists QA 151 as pending, QA 139–146 as not run, and any limit the new evidence still shows (including the 320/375 on-screen point over the "40" label if that is still true). It does not claim a FINAL PASS.

A11. Contract and scope held. SHA-256 of `/workspace/pipeline/stemergent/brief.md`, `idea.md`, `prd.md`, and `qa.md` match the hashes in `BUILD-RC5.txt`. About disclosure text and QA 119 tests are unchanged. `git diff rc5` does not touch contract files. Optional UX items stay undone.

A12. Candidate package. Branch `rc3-work`. One product commit contains the code, the evidence, the demo, and `review/rc6/`. A later hash-record commit updates `BUILD-RC6.txt` and `review/rc6/SOURCE.txt` (and the acceptance table if needed) so they name the product commit. Tag `rc6` points at that hash-record commit. The tagged commit does not contain its own hash. `review/rc6/` holds the requirements pointer, source hashes, diff from rc5, start command, acceptance table, evidence, known issues, and the demo. Nothing was pushed. Nothing was submitted. `git status` is clean except untracked `FIX-TASK-RC6.md` and ignored files.

A13. Evidence timing. Every JSON and log under `review/rc6/evidence/` that records a result names the product commit. File mtimes for pytest, QA, and print evidence are later than the last product-file edit. The hash-record commit does not change product files.

A14. Video and disclosure identity. The packaged demo's sha256 and duration in `BUILD-RC6.txt`, `video-identity.txt`, `docs/narration-check.md`, README, and Devpost agree. The unified AI paragraph on About, in README, and in Devpost is still the rc5 paragraph.
