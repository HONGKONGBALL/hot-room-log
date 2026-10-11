# Acceptance table — rc5 candidate

Parent: `f79ad403afb1a24730ef3a31c5b0d670979b7104` (tag rc4)
Product and evidence commit: recorded by the following hash-record commit. See `BUILD-RC5.txt` and `review/rc5/SOURCE.txt`.
Tag `rc5` points at that hash-record commit. Its parent is the product commit.

No FINAL PASS is claimed. Reused rows are rc4 evidence. There is no rc4 FINAL review on record.

| Item | Status | Evidence |
|---|---|---|
| A1 Contract v1 unchanged | checked | `BUILD-RC5.txt` (v1 hashes). `contract-v1/` was not edited. `brief.md` prefix `a7847236`. |
| A2 Contract v2 text | checked | Top-level `idea.md`, `prd.md`, `qa.md`. Hashes in `BUILD-RC5.txt`. |
| A3 README | checked | `README.md` |
| A4 Devpost draft | checked | `docs/devpost.md` |
| A5 About page | checked | `hotroom/templates/about.html` (text inside one `p` and one `li`) |
| A6 Tests | checked | `tests/test_o_pages.py`, `review/rc5/evidence/pytest.txt` (114 passed, exit 0) |
| A7 Grep checks | checked | `review/rc5/evidence/grep.txt`. Secret-pattern scan matches `ACCEPTANCE.md` line 69, which names the patterns. |
| A8 Decisions | checked | `DECISIONS-NEEDED.txt` |
| A9 Evidence reuse | REUSED | `review/rc4/evidence/qa-124-127.sh`, `review/rc4/evidence/http/`, `review/rc4/evidence/qa-129-138.json`, `review/rc4/evidence/qa-shots/`, `review/rc4/evidence/print/a1-a2-a3.json`, `review/rc4/evidence/print/pdfs/`, `review/rc4/evidence/print/bbox/`. Diff stat in `BUILD-RC5.txt`. |
| A10 QA 151 | pending | `BUILD-RC5.txt`. Human confirmation by Zhenhua. No billing result. |
| A11 Out of scope held | checked | `git diff rc4 --stat -- hotroom app.py requirements.txt` is only `hotroom/templates/about.html`. |
| A12 Candidate package | checked | This commit on `rc3-work`. Tag `rc5` is the following hash-record commit. Nothing pushed. Nothing submitted. |
| A13 Video identity | checked | `review/rc5/hot-room-log-demo-v4.mp4`, `review/rc5/evidence/video-identity.txt` |
| A14 Disclosure match | checked | `hotroom/templates/about.html`, `README.md`, `docs/devpost.md`, `review/rc5/evidence/pytest.txt` (`test_119_about_copy`) |
