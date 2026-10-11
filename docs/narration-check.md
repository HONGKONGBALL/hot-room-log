# Narration check — hot-room-log-demo-v4

No person listened to this file for this check. No automatic speech recognizer was run. `whisper`, `faster-whisper`, `speech_recognition`, and `vosk` are not installed. Torch and Whisper were not installed, and no network transcription API was called.

## What the file is

Packaged file, named by filename only: `hot-room-log-demo-v4.mp4`

- sha256: `d42d05ef21227ccacbebce2ce36f693b3fe2810841399ae63bc3c71eaf3d2c9b`
- ffprobe duration: 152.067 s
- Video: H.264, 1920×1080
- Audio: AAC LC, stereo, 48000 Hz

The picture in rc6 replaces the About segment and the print stills. The audio stream is the existing v4 narration, unchanged. No TTS call was made for this check.

Engine and voice, from the v4 narration note (not from a listen):

- engine: dashscope
- model: qwen3-tts-flash
- voice: Cherry
- that note says edge-tts was not used

The narration script still has the header line `Voice: en-US-JennyNeural`. That header is the older script label. The 23 spoken lines under it match the `hot` cues in the timing file (same start time and the same text). This check treats those 23 cues as the scene script. It does not treat JennyNeural as the voice in v4.

## What was measured

Command, run on the packaged file:

```
ffmpeg -i hot-room-log-demo-v4.mp4 -af silencedetect=noise=-30dB:d=0.25 -f null -
```

`silencedetect` marks audio below −30 dB for at least 0.25 s as silence. Speech bursts are the gaps between those silences. A cue counts as aligned when a burst starts inside the cue window `[start, deadline]`, within 0.3 s after `start`, and some of that burst falls inside the window. The detector splits a sentence on short pauses, so the energy inside a window is shorter than the cue's `spoken` field. That field is the timing file's planned length, not a measurement from this file.

This shows where speech energy sits. It does not show that the words are the cue text.

The rc6 picture change does not change the audio. The same command on the packaged file still shows the bursts below: leading silence from 0 to 0.438 s, and the last burst ending at 149.350 s.

## Result

23 cues. 23 windows contain speech. Each first burst starts about 0.09 s after the cue `start` (range 0.088 s to 0.106 s). Each of those bursts ends before the cue `deadline`. Leading silence runs from 0 to 0.438 s. After the last burst (ends 149.350 s) the file is silent through 152.067 s, which is after cue 22's deadline 151.75 s.

| # | Cue start (s) | First speech (s) | Lag (s) | Speech inside window (s) | Cue `spoken` (s) |
|---|---:|---:|---:|---:|---:|
| 0 | 0.35 | 0.438 | 0.088 | 5.24 | 7.18 |
| 1 | 8.15 | 8.238 | 0.088 | 5.82 | 7.61 |
| 2 | 16.25 | 16.339 | 0.089 | 4.04 | 5.83 |
| 3 | 23.85 | 23.956 | 0.106 | 5.88 | 7.08 |
| 4 | 31.25 | 31.343 | 0.093 | 3.35 | 4.32 |
| 5 | 36.70 | 36.797 | 0.097 | 3.80 | 4.68 |
| 6 | 42.15 | 42.238 | 0.088 | 3.72 | 4.82 |
| 7 | 47.65 | 47.742 | 0.092 | 4.28 | 6.10 |
| 8 | 54.85 | 54.943 | 0.093 | 2.86 | 4.82 |
| 9 | 61.25 | 61.341 | 0.091 | 4.77 | 5.90 |
| 10 | 68.20 | 68.299 | 0.099 | 4.58 | 4.92 |
| 11 | 74.70 | 74.796 | 0.096 | 3.68 | 4.42 |
| 12 | 81.05 | 81.138 | 0.088 | 2.69 | 3.13 |
| 13 | 84.55 | 84.640 | 0.090 | 1.31 | 2.26 |
| 14 | 87.75 | 87.855 | 0.105 | 2.18 | 2.93 |
| 15 | 92.20 | 92.288 | 0.088 | 4.43 | 5.52 |
| 16 | 100.15 | 100.239 | 0.089 | 3.61 | 5.28 |
| 17 | 108.15 | 108.252 | 0.102 | 5.99 | 7.78 |
| 18 | 116.70 | 116.794 | 0.094 | 4.97 | 6.88 |
| 19 | 124.10 | 124.200 | 0.100 | 3.85 | 5.53 |
| 20 | 130.15 | 130.251 | 0.101 | 4.37 | 6.19 |
| 21 | 137.15 | 137.242 | 0.092 | 4.60 | 5.59 |
| 22 | 144.35 | 144.438 | 0.088 | 4.25 | 5.83 |

Cue text, same in the timing file and the script file:

0. Hot Room Log, for STEMergent Hacks. A too-hot study room, turned into evidence.
1. Three fictional rooms. The study room is already Dangerous: humidex 47.6.
2. Every card is labelled sample data. These are not measurements of a real room.
3. The study room reads 34 degrees, 65 percent humidity, humidex 47.6.
4. Each point shows the time, the humidex, and the band.
5. All six readings in this room are Great discomfort, or above.
6. Add 31 degrees, 79 percent, air-con off.
7. Saved. Latest humidex 45.1, in the Dangerous band.
8. The library card turns red. Seven readings.
9. Dry heat: 35 degrees at 40 percent is humidex 41.9.
10. 30 degrees at 85 percent feels 2.5 points hotter.
11. The evidence sheet drafts a letter you can edit before you send it.
12. The greeting now says Dear Room manager.
13. Copied to the clipboard.
14. Print uses that same edited letter.
15. Page one keeps the chart, the 47.6 reading, and the table.
16. Page two keeps Dear Room manager. The buttons are not printed.
17. A CSV with the same columns can add readings, or create a room. The file stays on this computer.
18. One reading added. One new room. No duplicates, and no invalid rows.
19. A comfort guide, not medical advice. Nothing is sent anywhere.
20. The sample rooms are fictional. Not deployed at any school or organisation.
21. The imported Demo Reading Club stays on this computer, next to the sample rooms.
22. Solo project by Zhenhua Liu, for STEMergent Hacks twenty twenty-six.
