# Devpost draft — Hot Room Log

Paste this only after the STEMergent Hacks 2026 submission form is open. The manage page read on 2026-10-08 said submissions run from Oct 30, 11:00 pm CDT (Oct 31, 12:00 noon Hong Kong time) through Nov 15, 2026. Re-check the live page on the day. Do not submit before it opens.

Leave **Challenges** and **What I learned** blank here. Those two answers should be written by Zhenhua after the build, from real experience.

## Fields

| Field | Content |
|---|---|
| Project title | Hot Room Log |
| Tagline, if the form asks | Turn "it's too hot to study" into evidence: log a room's temperature and humidity, see how hot it really feels, and print a one-page sheet asking for a fix. |
| Pathway | Hackathon |
| Team | Solo: Zhenhua Liu (Devpost: Zhenhua; GitHub: HONGKONGBALL). No teammates. |
| Code link | `https://github.com/HONGKONGBALL/hot-room-log` — create the public repo before submitting, and confirm the README quick start works on a fresh clone. |
| Prototype link | Leave blank unless a read-only demo (`HOTROOM_READONLY=1`) is deployed and has been opened in a private browser window. Do not post a dead link. |
| Built with | python, flask, sqlite, jinja, html, css, javascript, svg, pytest |

## Description

**Problem.** Students study in shared rooms like classrooms, estate study rooms, library corners or a desk at home, and in a humid city like Hong Kong these can get hot and sticky. "It's too hot" is easy to dismiss, and air temperature alone undersells humid heat. By the humidex formula, 30 °C at 85 % humidity scores 44.4, higher than 35 °C at 40 % (41.9). A student who wants a room fixed needs a simple, free and private way to turn a few readings into a clear record and a polite request.

**Solution.** Hot Room Log is a small web app. You type in a room's temperature and relative humidity from any thermometer or humidity display. For each reading it calculates the humidex, the dew point and how much the humidity adds, and shows a comfort band in colour and text. Each room gets a chart with comfort-band strips, key stats and a table. One click builds an evidence sheet with the summary, chart, table, method and an editable letter to copy or print. A calculator shows every step of the maths and compares two conditions. CSV export and import let classmates merge their logs. There is no account, no hardware and no internet connection needed, and the data stays on the computer running the app.

**How it works.** Python and Flask render every page on the server, and readings live in SQLite. Humidex = T + 0.5555 × (e − 10), where the vapour pressure is e = RH/100 × 6.105 × exp(17.27·T / (237.7 + T)) hPa. The dew point uses the inverse of the same formula. Bands are below 30, 30–39.9, 40–45 and above 45. The chart is an inline SVG drawn on the server, with no chart library or CDN. Editing the letter updates the printed page, including the browser's own print command. CSV import checks every row, reports problems by row number, creates missing rooms and skips exact duplicates, so importing the same file twice changes nothing. An optional read-only mode makes a public demo safe. Automated tests (pytest) cover the formulas, every route and the CSV round trip.

**What's next (ideas, not built).** A Traditional Chinese interface. Optional automatic readings through the existing JSON API. Comparing rooms side by side.

**Honesty notes.** The rooms and readings in the demo and screenshots are fictional sample data. Hot Room Log is not deployed at, endorsed by or used by any school, estate or organisation. Humidex bands are a comfort guide, not medical advice. This is a solo project by Zhenhua Liu, built new for STEMergent Hacks 2026.

**AI tools and third-party resources.** AI tools: Claude (Anthropic) helped draft the idea, requirements and test plan. Grok (xAI) helped write the application code. Zhenhua reviews this list before submission. Third-party: Flask and its dependencies (Werkzeug, Jinja2, MarkupSafe, ItsDangerous, Click, Blinker) and pytest. Formulas: the Canadian humidex (Masterton & Richardson, 1979, Environment Canada) and a Magnus-type vapour-pressure approximation. No third-party images, fonts or icons. The pages use the system font stack.

## Screenshots and video

The screenshots in `screenshots/` show the fictional sample banner. No personal data is shown.

The demo video for this candidate is `hot-room-log-demo-v2.mp4`: 1920×1080, 2 minutes 32 seconds, H.264 with silent AAC audio, English title cards and burned-in English subtitles. Playwright recorded the running app (no terminal and no address bar). It uses the fictional sample rooms, then adds one library reading and imports one new room. Upload it only if the open Devpost form asks for a video. It is not stored in this repository.

- `screenshots/dashboard.png` — three sample rooms
- `screenshots/room.png` — Demo Estate Study Room, chart and readings
- `screenshots/sheet.png` — heat evidence sheet and letter
- `screenshots/calculator.png` — dry 35 °C at 40 % compared with humid 30 °C at 85 %, working open
- `screenshots/import-results.png` — CSV import results
