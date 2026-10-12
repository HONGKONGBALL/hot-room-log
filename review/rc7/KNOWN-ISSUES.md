# Known issues — rc7 candidate

Implementation and self-check are done. This candidate is awaiting acceptance. No FINAL PASS is claimed.

## QA 151

Closed. Owner decision, 2026-10-12 03:39:15 CST (UTC+8), written in `/workspace/pipeline/stemergent/QA151-DECISION.txt` and `/workspace/pipeline/stemergent/DECISIONS-NEEDED.txt`.

qwen3-tts-flash calls used free quota (not billed). Model Studio terms allow publishing the generated audio in a public video. Submit the narrated v4 demo, not the silent cut. Keep the QA 119 / About TTS disclosure.

This package does not claim a billing result beyond those two files. No TTS API was called for rc7. The existing narrated v4 file was copied byte for byte.

## QA 139–145

Not run. Those remain submission checks for the open Devpost form. Nothing was submitted.

## QA 146

The local public-branch dry-run is a rehearsal, not a live submission. Nothing was pushed. The rc6 rsync-to-one-tree plan is not the public history. See `BUILD-RC7.txt` and `review/rc7/evidence/public-branch/`.

## Limits the new evidence still shows

Headless Chrome does not fire `beforeprint` for Ctrl+P and does not open a print dialog for that shortcut. The print button path and the native `beforeprint` path were measured with `window.print` and `Page.printToPDF`. See `review/rc7/evidence/print/a1-a2-occlusion.json`.

QA 137 is the request log from the browser run. The checks used 127.0.0.1. The network cable was not unplugged.

Some frames in `review/rc7/hot-room-log-demo-v4.mp4` can still show the prior build's chart point positions. The checked frames keep labels 30, 40, and 45 readable. The file was not re-encoded.

## Not reopened

The five contract-v2 decisions stay closed. They are recorded in English in `DECISIONS-NEEDED.txt`. They were not reopened.
