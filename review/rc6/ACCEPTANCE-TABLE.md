# Acceptance table — rc6 candidate

Parent: `14f04de30d4cf591efd57e1564a49e574e22000c` (tag rc5)
Product and evidence commit: `a4e1542232d65dbdadf8195d4a6a55d856b87459`. See `BUILD-RC6.txt` and `review/rc6/SOURCE.txt`.
Tag `rc6` points at the commit that records this candidate. Its parent is the product and evidence commit. This table does not embed that tag commit's own hash.

Implementation and self-check are done. No FINAL PASS is claimed. Nothing was pushed. Nothing was submitted.

| Item | Status | Evidence |
|---|---|---|
| A1 Printed y-axis labels | self-check pass | `review/rc6/evidence/print/a1-a2-occlusion.json` (`pass` true, `failures` empty). Magnified crops in `review/rc6/evidence/print/magnified/`. Eight JavaScript PDFs: no label intersection with a point box expanded by its stroke, or with the trend stroke box. Six points. Label bbox height at least 7 pt and at least the noscript PDF from the same run. |
| A2 Screen at 1280 px | self-check pass | Same JSON, `screen_after`: first point `cx` `56.00`, live `r` `3.89`, which is `(7 * 640) / 1152`. Screenshot `review/rc6/evidence/print/room-1280-screen.png`. |
| A3 Print chrome | self-check pass | Same JSON. Page 1 has neither the letter label nor "does not send anything". Page 2 contains "Dear Room manager". Buttons are not on page 2. Two A4 pages. |
| A4 Pytest | self-check pass | `review/rc6/evidence/pytest.txt`. 114 passed, exit 0. Mtime is after the last product-file edit. |
| A5 QA 124–127 | self-check pass | `review/rc6/evidence/qa-124-127.sh`, `review/rc6/evidence/http/qa-124-127.log` (`fail=0`). Servers stopped. Nothing left on 5050 or 5051. |
| A6 QA 129–138 and QA 134 v2 | self-check pass | `review/rc6/evidence/qa-129-138.json` (`pass` true). Headed hover `review/rc6/evidence/qa-shots/134-noscript-hover-headed.png`. No-JS 320 and 375 shots `134-noscript-room-320.png` and `134-noscript-room-375.png`. `#taken_at` focus `136-room-taken-at-focus.png` (ring visible, outline 3px solid). |
| A7 Print measurements | self-check pass | `review/rc6/evidence/print/` (PDFs, bbox, magnified crops, `a1-a2-occlusion.json`). The JSON names the method and the product commit. |
| A8 Demo video | self-check pass | `review/rc6/hot-room-log-demo-v4.mp4`. `review/rc6/evidence/video-identity.txt`. Frames in `review/rc6/evidence/video-frames/`. Duration 152.067 s, 1920×1080. Audio copied from the rc5 v4 file. No TTS call. |
| A9 Public export | self-check pass | `docs/narration-check.md` names `hot-room-log-demo-v4.mp4` only. `review/rc6/evidence/public-export-grep.txt`. README and `docs/devpost.md` say Public video URL: TBD. |
| A10 Decisions and known issues | pending QA 151 | `DECISIONS-NEEDED.txt` unchanged. `review/rc6/KNOWN-ISSUES.md`. No billing result. No FINAL PASS. |
| A11 Contract and scope held | self-check pass | Contract v2 hashes in `BUILD-RC6.txt` match `BUILD-RC5.txt`. About disclosure and `tests/test_o_pages.py` were not edited. |
| A12 Candidate package | self-check pass | Branch `rc3-work`. Product commit, then the hash-record commit, local tag `rc6` on that commit. Nothing pushed. Nothing submitted. |
| A13 Evidence timing | self-check pass | Pytest, QA, and print evidence name product commit `a4e1542232d65dbdadf8195d4a6a55d856b87459`. Mtimes are after `hotroom/static/app.js` (last product edit, 2026-10-12 04:01:10 +0800). This hash-record commit does not change product files. |
| A14 Video and disclosure identity | self-check pass | sha256 `d42d05ef21227ccacbebce2ce36f693b3fe2810841399ae63bc3c71eaf3d2c9b`, duration 152.067 s, in `BUILD-RC6.txt`, `video-identity.txt`, `docs/narration-check.md`, README, and Devpost. The unified AI paragraph is still the rc5 paragraph. |
