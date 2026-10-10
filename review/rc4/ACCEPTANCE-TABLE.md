# Acceptance table — rc4 candidate

HEAD at evidence time: `e7a7d83eaf1c5d95934dfe98d729aec7e92fe539`
sha256 of `git diff HEAD`: `b88001a03024e6f3d0aec7826aecd34bc90d866360af5963e17795407ebe9d9f`
candidate commit: pending supervisor

| Item | Status | Evidence |
|---|---|---|
| A1 Print chart labels | PASS | `review/rc4/evidence/print/a1-a2-a3.json`, `review/rc4/evidence/print/pdfs/`, `review/rc4/evidence/print/bbox/` |
| A2 White page 2 | PASS | `review/rc4/evidence/print/a1-a2-a3.json`, `review/rc4/evidence/print/png/` |
| A3 Latest-reading sentence | PASS | `review/rc4/evidence/print/a1-a2-a3.json` (`facts`) |
| A4 Delivery video docs | PASS | `README.md`, `docs/devpost.md`, `BUILD-RC4.txt`, `docs/narration-check.md`, `review/rc4/evidence/docs-check.json` |
| A5 Disclosure | PASS | `hotroom/templates/about.html`, `README.md`, `docs/devpost.md`, `review/rc4/evidence/docs-check.json` |
| A6 Final-build evidence | PASS | `review/rc4/evidence/pytest.txt`, `review/rc4/evidence/http/qa-124-127.log`, `review/rc4/evidence/qa-129-138.json` |
| A7 Candidate package | FAIL | Package files in `review/rc4/` are present. No rc4 commit, no `rc4` tag, worktree dirty. Pending supervisor. |
| A8 Regression | PASS | `review/rc4/evidence/pytest.txt`, QA 129–133 in `review/rc4/evidence/qa-129-138.json` |
| A9 Decisions file | PASS | `DECISIONS-NEEDED.txt` |
| A10 Video identity | PASS | `review/rc4/hot-room-log-demo-v4.mp4`, `review/rc4/evidence/docs-check.json` |
