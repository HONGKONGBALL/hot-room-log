# Known issues — rc6 candidate

Implementation and self-check are done. This candidate is awaiting acceptance. No FINAL PASS is claimed.

## QA 151

Pending human confirmation by Zhenhua. This package does not say the demo voice-over call was free, billed, allowed, or forbidden. No billing result is recorded. The existing v4 narration was kept. No TTS API was called for rc6.

## QA 139–146

Not run. Those remain submission checks for the open Devpost form. Nothing was submitted.

## Limits the new evidence still shows

On-screen chart at 320 px and 375 px. The screen fit was not changed. QA 135 still records the first point over the y-axis label "40": at 320 px the point radius is 15.14, and at 375 px it is 12.76. That is a narrow-viewport limit, separate from the print fit. Print measurements show the labels 30, 40, and 45 clear of the points and the trend line.

Headless Chrome does not fire `beforeprint` for Ctrl+P and does not open a print dialog for that shortcut. The print button path and the native `beforeprint` path used by print preview were measured with `window.print` and `Page.printToPDF`. See `review/rc6/evidence/print/a1-a2-occlusion.json`.

QA 134 with JavaScript off found no `.chart-tip` element, and the six point titles matched the QA 130 strings. One headed-Chrome hover screenshot is saved.

QA 137 is the request log from the browser run. The checks used 127.0.0.1. The network cable was not unplugged.

Noscript print PDFs in this run report six separate points. The print occlusion check is the label `getBBox` test, and it passed for the eight JavaScript PDFs.

## Not reopened

The five contract-v2 decisions stay as recorded in `DECISIONS-NEEDED.txt`. They were not reopened.
