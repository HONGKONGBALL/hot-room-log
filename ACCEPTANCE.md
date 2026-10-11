# Hot Room Log — acceptance contract (rc5)

Candidate under test: rc5, built on rc4 (`f79ad403afb1a24730ef3a31c5b0d670979b7104`, tag `rc4`, branch `rc3-work`).

Source of this rework: `/workspace/pipeline/stemergent/FIX-TASK-RC5.md` and `/workspace/pipeline/stemergent/contract-v2-ruling.md`. Contract text follows the ruling section 「contract_version: v2 完整变更清单」. This contract is the checkable form of that work. It is not a pass of an external review.

## Goal

Apply contract v2. The five open conflicts are decided in the documents and in the disclosure text. Product logic, CSS layout, `app.js` behaviour, Python, requirements, screenshots, and the demo video stay as they are in rc4. Room 1 still prints on at most 2 A4 pages. The running app still calls no external service.

## Target environment

- OS: Linux. Browser checks for rc5 are the reused rc4 runs, unless a product file outside `about.html` text changes and those runs must be repeated.
- Start, from `/workspace/hot-room-log-rc3`:

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

- App URL: `http://127.0.0.1:5050` (override with `PORT`). Binds to `127.0.0.1` unless `HOST` is set.
- No account and no login. Sample data loads once into `instance/hotroom.db`.
- Do not re-narrate or regenerate the demo. The delivery file remains `hot-room-log-demo-v4.mp4` (sha256 `f6f41d0ad643388d27526485fbcf87aaaa6325eaf06813375ab1947efadb26a1`, duration 152.067 seconds).

## Core flows

These flows are unchanged from rc4. rc5 does not re-test them in the browser when `git diff rc4 --stat -- hotroom app.py requirements.txt` lists only `hotroom/templates/about.html` and that diff is text inside `<p>` or `<li>`.

1. First launch creates the database and three fictional sample rooms. The dashboard shows three banded cards.
2. Opening a room shows the latest humidex, the latest-reading sentence, a chart, and a table. Adding a valid reading updates the card, chart, and table. An invalid reading returns 400, keeps the typed values, and shows a field error.
3. The evidence sheet shows the summary, chart, table, method, and letter. Editing the letter, then Copy or Print, uses the edited text. Room 1 prints on at most 2 A4 pages. Navigation, buttons, and the textarea are not printed.
4. The calculator shows worked steps and a comparison sentence.
5. CSV export and import merge readings, skip exact duplicates, and report bad rows. Reset restores the three sample rooms after confirmation. Read-only mode returns 403 on writes.

## Scope

In scope for rc5:

- Top-level `/workspace/pipeline/stemergent/idea.md`, `prd.md`, and `qa.md`, edited to contract v2. `brief.md` is not edited. `contract-v1/` is the frozen v1 copy and is not edited. Do not run `run.sh` on stemergent.
- `README.md`, `docs/devpost.md`, `hotroom/templates/about.html` (wording only), `tests/test_o_pages.py`, `DECISIONS-NEEDED.txt`, `BUILD-RC5.txt`.
- Full pytest, including QA 147–150, and the ruling's grep checks.
- Local commit on `rc3-work` and tag `rc5`. Package `review/rc5/`.

## Non-goals

- Do not modify `hotroom/static/app.js`, `hotroom/static/style.css`, templates other than the two text spots in `about.html`, any Python app module, `requirements.txt`, `requirements-dev.txt`, `screenshots/*.png`, or `hot-room-log-demo-v4.mp4`.
- Do not do the optional print CSS letter-block cleanup.
- Do not change `run.sh`.
- Do not push, deploy, or submit to Devpost.
- QA 151 is Zhenhua's billing and terms check. Record it as pending. Do not invent a billing result. Do not switch the video to the silent cut.
- Do not add product judgments beyond the five rulings.

## Acceptance criteria

A1. Contract v1 is unchanged on disk. Before any edit, the top-level v1 files match the recorded prefixes: brief `a7847236`, idea `3e8c68b4`, prd `599f65d6`, qa `6653f1b6`. `contract-v1/` holds those same bytes. `brief.md` is not modified. `v1/` is not used as the contract.

A2. Contract v2 text. Top-level `idea.md`, `prd.md`, and `qa.md` contain every required edit in the ruling list: I1, P1, P2, P3, P4, P5a, P5b, P6, P7, P8a, P8b, P9a, P9b, P9c, P9d, Q0, Q119, Q132, Q134, Q142, Q143, Q144, Q147, Q148, Q149, Q150, Q151. Existing QA numbers 1–146 stay. New rows are 147–151 only. `BUILD-RC5.txt` records the new SHA-256 of brief, idea, prd, and qa (full hash and 8-character prefix).

A3. README. The Chinese paragraph is gone, and so is the blank line it would leave. The pitch says "printable evidence sheet". The video section does not say the file is absent from the repository, does not contain a `/workspace/` path, and says the voice-over is an AI-generated voice (Alibaba Cloud Model Studio text-to-speech, qwen3-tts-flash, voice Cherry) with burned-in English captions. The AI disclosure bullet is the unified paragraph from the ruling.

A4. Devpost draft. The tagline is the P8a slogan. The AI section starts with the same unified paragraph, then keeps the third-party and formula sentences. The banner sentence is the ruling's dashboard/room/sheet sentence (calculator and import-results have no banner). The video sentence does not say the file is absent from the repository, does not contain a `/workspace/` path, and uses the same AI-generated voice sentence.

A5. About page. The pitch says "builds a printable evidence sheet". The AI list item is the same unified paragraph. No other template markup or layout change.

A6. Tests. `tests/test_o_pages.py` checks the QA 119 phrases Grok, Claude, qwen3-tts-flash, AI-generated voice, and does not call. It adds QA 147 (no CJK in `README.md` and `docs/*.md` for the ranges in the ruling), QA 148 (no "one-page" or "one page" in `/about`, `README.md`, and `docs/devpost.md`), QA 149 (app.js ban list and exactly one `/static/app.js` script on each case-117 page), and QA 150 (one Flask requirement; no banned imports in `app.py` and `hotroom/**/*.py`). `pytest` exits 0. The log is saved under `review/rc5/evidence/`.

A7. Grep checks from the ruling, saved under `review/rc5/evidence/`: no CJK in `README.md`, `docs/`, or `hotroom/templates/`; no "one-page" or "one page" or "一页" in `README.md`, `docs/`, `hotroom/templates/`, `idea.md`, or `prd.md`; the app.js ban list is empty; the ruling's endpoint and API-key scan of the git tree has no output; banner mentions in `README.md` and `docs/devpost.md` are only the rewritten sentence.

A8. Decisions. `DECISIONS-NEEDED.txt` marks all five items 已决（contract v2）, with one conclusion line each: English-only README; banner rule kept and screenshot rule rewritten; existing JavaScript accepted as progressive enhancement; wording is printable and Room 1 stays at most 2 pages; "No paid API" applies to the running product and the voice-over is disclosed, with QA 151 still open.

A9. Evidence reuse. After the edits, `git diff rc4 --stat -- hotroom app.py requirements.txt` shows only `hotroom/templates/about.html`. That diff is text inside `<p>` or `<li>` only. rc5 reuses rc4 QA 124–127, QA 129–138, and A1–A3 print evidence and names the rc4 paths in `BUILD-RC5.txt`. It does not claim an rc4 FINAL review accepted those files. There is no rc4 FINAL PASS on record. If the diff is wider, those checks are re-run on the new tree and the new logs replace the reuse claim.

A10. QA 151. `BUILD-RC5.txt` says the billing and terms check is pending human confirmation by Zhenhua. It does not state that the call was free, billed, allowed, or forbidden.

A11. Out of scope held. `git diff rc4` does not change `app.js`, `style.css`, Python app modules, `app.py`, `requirements.txt`, `requirements-dev.txt`, `screenshots/`, or the demo mp4 bytes. Print CSS is unchanged.

A12. Candidate package. Branch `rc3-work` has the rc5 commit. Tag `rc5` points at the commit that records the candidate hash in `BUILD-RC5.txt`, same pattern as rc4. `review/rc5/` holds the requirements pointer, source hash, diff from rc4, start command, acceptance table, pytest and grep logs, known issues (QA 151 pending; optional print cleanup not done), and `hot-room-log-demo-v4.mp4` with the same sha256 as rc4. No push and no Devpost activity. `git status` is clean aside from ignored files. Unrelated uncommitted work is kept.

A13. Video identity. The packaged demo's sha256 equals `f6f41d0ad643388d27526485fbcf87aaaa6325eaf06813375ab1947efadb26a1` and the duration is 152.067 seconds, recomputed from the file.

A14. Disclosure match. The unified AI paragraph is the same text on the rendered About page, in `README.md`, and in `docs/devpost.md`. It names Grok, Claude, Alibaba Cloud Model Studio, DashScope/Bailian, qwen3-tts-flash, voice Cherry, and that the running app does not call an external service.
