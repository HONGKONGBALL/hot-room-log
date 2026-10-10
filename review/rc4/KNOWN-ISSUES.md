# Known issues — rc4 candidate

No resolution is chosen for the five conflicts. Zhenhua decides.

## Undecided conflicts

These match `DECISIONS-NEEDED.txt`. This file does not add a ruling.

1. README Chinese paragraph. The brief says English product docs, with Chinese only in `idea.md`. The pipeline run script asks for a short Chinese paragraph. `README.md` still has that paragraph.
2. Sample banner on the calculator and import pages. The banner is on the dashboard, on a sample room, and on a sample room's evidence sheet. It was not added to the calculator or import pages.
3. JavaScript beyond copy, print, and confirm. The script also fits chart text, updates table-scroll shadows, and shows a custom tooltip. Add room, add reading, delete, calculator, export, import, and reset still work with JavaScript off (QA 134).
4. The words "one-page" remain in About, the README pitch, and the Devpost tagline. Room 1 prints on 2 A4 pages. QA 132 allows at most 2.
5. Whether the brief's "no paid API" rule covers the DashScope/Bailian narration used only to produce the demo. The running app calls no external API. The A5 disclosure names that narration. This file does not say the usage complies and does not say it violates the brief.

## Optional polish not done

Autofocus on the first error, `type="text"` on the room name, hiding screen-only print hints, letter textarea growth, scrolling to the calculator result, copy-failure UI, import error heading, sheet "back to room" link, deep-JSON 500, and CSV message fixes. Backend behavior was not changed. The demo was not regenerated.

## QA 139–146

Not run. Those are submission checks for the open Devpost form. Nothing was submitted.

## Measurements and limits

- At 320 px and at 375 px, the first chart point's box covers the "40" axis label. QA 135 still passes for page scroll and in-box table scroll. Recorded in `review/rc4/evidence/qa-129-138.json` as `known_limit_point_covers_40`. The on-screen fit formula was not changed.
- Datapoints have no tabindex and no focus listener. No focus tooltip is claimed.
- Headless Chrome does not open a print dialog for Ctrl+P and does not fire `beforeprint` for that key. The print pipeline was captured with `window.print` / `beforeprint` and with `Page.printToPDF`.
- QA 137 is a request log. The network cable was not unplugged. Every recorded request host was `127.0.0.1`.
- The 72 dpi colour counter on the JavaScript-disabled chart found 1 dark blob. The rendered page `review/rc4/evidence/print/png/noscript-bg-1280-1.png` shows six separate points. The JavaScript print PDFs counted 6 separated points. Label heights on the noscript PDF are 7.758 pt and were the comparison baseline.
- `review/rc4/evidence/screen-before/metrics.json` is the kept pre-change baseline. It has no generation-time git stamp. The final-run JSON files do.
- A7 is not met: there is no rc4 commit and no `rc4` tag, and `git status` is dirty, because the builder was told not to commit or tag.

## Failed commands during the build

The first QA 124–127 attempt exited 127 because `rsync` is not installed. The EXIT trap still recorded that nothing listened on 5050 or 5051. The script was changed to use `tar` and the rerun exited 0. That failure is of the evidence script, not of the app.
