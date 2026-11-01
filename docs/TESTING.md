# Testing

## Automated (free, offline, ~60 s)
```bash
pip install -r requirements-dev.txt
python -m playwright install chromium  # optional: browser tests skip cleanly without a Chromium
scripts/check_all.sh                   # ruff + mypy strict (mypy.ini) + all 530 tests (fast and slow chunks: 501 fast, 29 slow incl. browser)
```
CI (`.github/workflows/ci.yml`) runs the same on every push. Browser tests also find a system Chromium (`/usr/bin/chromium`) or `PLAYWRIGHT_CHROMIUM=/path`.

| File | What it proves |
|---|---|
| `test_schemas.py` | All fixtures validate in 3 languages; sorting/renumbering; bad values rejected; schemas have no `$ref` |
| `test_safety.py` | Hard stops (gas, mains, HV, brakes, medical) in id/en; everyday repairs pass; plan gate blocks 220 V internals and brake bleeding |
| `test_overlay.py` | Box-local SAM masks land in the right pixels; out-of-bounds clipped; only masked area tinted; EXIF rotation + size cap |
| `test_engine.py` | Full pipeline per scenario: green faucet, amber motor with follow-up/resume, red rice cooker, gate stop, 3 languages, step check pass/fail/escalate, re-plan → exhaust, audio deleted, path-safe ids, 24 h cleanup, budget guard |
| `test_api.py` | HTTP: health, pages, multi-photo upload, files, guide, report, answer, check, replan, SSE stream, 7 bad-request cases, 404s and path traversal |
| `test_live_path.py` | The **real `meta_client`** (HTTP, multipart ASR, structured output, SAM SSE + mask parsing, image edits, Baseten) against `api/testing/fake_meta.py`; wrong key → clean 401 |
| `test_fixtures.py` | All 14 stand-in fixtures are labelled (red banner + EXIF) and each runs end to end with the expected safety level; step-check photos accepted |
| `test_video.py` | Video → 3 frames from different moments; sharper frame wins; >30 s and garbage rejected with 400; video-only session uses the clip's sound; photos + video capped at 3 |
| `test_playwright_smoke.py` | Real Chromium, phone viewport: faucet flow + check-my-step, motor follow-up question, rice STOP card (3 actions, maps link, PDF works, 112), PWA manifest, open-weights badge (+ language switch), video capture; fails on any JS error |
| `test_pwa.py` | Manifest valid with 192/512/maskable icons served; service worker never caches the API; health reports open weights only when really active |
| `test_i18n.py` | Every Indonesian UI string exists in Basa Jawa and English |
| `test_set_keys.py` | One-step key swap writes MODEL_API_KEY/MOCK=0 (+ Baseten) and runs the checks; no key → .env untouched |
| `test_report_pdf.py` | PDF repair report |
| `test_web.py` | `app.js` parses; every element id the JS uses exists; every UI string has id + en text; shared page is read-only; no secrets in web files |

## Recorded demo (v1.24)
- `python scripts/record_replay.py` re-records `web/replay/` after a change to the mock answers, the session shape or the demo flow; `--check` exits 1 when the recording no longer matches (also a test in `test_replay.py`).
- `test_playwright_replay.py`: with every `/api` call hanging (sleeping server) the 1-tap demo still runs end to end from the recording, labelled; a visitor's own photo is refused, never faked; `?replay=1` sends nothing to the server.

## Fake Meta server
`python -m api.testing.fake_meta` serves `http://127.0.0.1:8765/v1` with key `test-key`, built from the documented request/response shapes. Run the app against it:
```bash
META_API_BASE=http://127.0.0.1:8765/v1 MODEL_API_KEY=test-key NO_PROXY=127.0.0.1,localhost python app.py
```

## Scripts
- `python scripts/check_keys.py`: real key: PASS/FAIL per Meta model (< $0.02). `--no-cost` = key + model list only. `--fake` = dry run.
- `python scripts/smoke_e2e.py <url>`: drives a running server like a phone: 5 scenarios, follow-up, check, re-plan, report, PDF, guide, images, PWA files. Use on localhost and on the Render URL.

## Manual QA checklist (phone, real photos, live mode)

| # | Scenario | Do | Expect |
|---|---|---|---|
| 1 | Motorbike won't start | Photo of plug area + "Motor susah hidup, starter bunyi" | Parts numbered (plug cap, cable); amber; maybe a fuel-smell question; 3–6 steps; step 1 makes it safe |
| 2 | Check a step | On "push the cap in", take a dark photo, then a good one | ⚠️ "more light/closer", then ✅ and auto-advance |
| 3 | Still broken | Type "cap tight, still dead" → Still broken | New plan for the next cause (fouled plug) |
| 4 | Water pump no water | Pump photo + "pompa bunyi tapi air tidak keluar" | Prime / foot-valve causes, green/amber |
| 5 | Leaking tap/hose | Photo + description | Washer or clamp, green, one diagram for the inside step |
| 6 | Rice cooker not heating | Photo + description | 🔴 STOP, service-centre message, no steps |
| 7 | Gas | Type "bau gas di dapur" | Stopped at the first safety check, no model call |
| 8 | Javanese voice | Language Basa Jawa, speak | Transcript in Javanese, answers in Javanese |
| 9 | English | Switch to English | Whole UI + guide in English |
| 10 | Hands-free | Tick hands-free, move steps | Each step read aloud |
| 11 | Share | Share report → open link on another phone | Read-only guide, no check buttons |
| 13 | Video | Tap "rekam video", film the pump 5–10 s while describing it | 3 frames used as photos, transcript from the clip, normal diagnosis |
| 14 | Install | Chrome menu → Add to Home screen | Orange wrench icon; opens full-screen |
| 15 | PDF | Finish a repair → Download PDF | A4 report with marked photo, steps, checks |
| 12 | 4G speed | On mobile data | Diagnosis card < 25 s, step check < 8 s (record actual times in TEST_REPORT) |
