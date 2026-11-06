# Testing

## Automated (free, offline; the full run took about 16 minutes on a 2-CPU box)
```bash
pip install -r requirements-dev.txt
python -m playwright install chromium  # optional: browser tests skip cleanly without a Chromium
scripts/check_all.sh                   # ruff + mypy strict (mypy.ini) + all tests (fast and slow chunks; the count is in docs/TEST_REPORT.md)
```
CI (`.github/workflows/ci.yml`) runs the same thing on every push. The browser tests also pick up a system Chromium (`/usr/bin/chromium`) or whatever `PLAYWRIGHT_CHROMIUM=/path` points at.

| File | What it proves |
|---|---|
| `test_schemas.py` | All fixtures validate in 3 languages; sorting/renumbering; bad values rejected; schemas have no `$ref` |
| `test_safety.py` | Hard stops (gas, mains, HV, brakes, medical) in id/en; everyday repairs pass; plan gate blocks 220 V internals and brake bleeding |
| `test_overlay.py` | Box-local SAM masks land in the right pixels; out-of-bounds clipped; only masked area tinted; EXIF rotation + size cap |
| `test_engine.py` | Full pipeline per scenario: green faucet, amber motor with follow-up/resume, red rice cooker, gate stop, 3 languages, step check pass/fail/escalate, re-plan → exhaust, audio deleted, path-safe ids, 24 h cleanup, budget guard |
| `test_api.py` | HTTP: health, pages, multi-photo upload, files, guide, report, answer, check, replan, SSE stream, 7 bad-request cases, 404s and path traversal |
| `test_live_path.py` | The real `meta_client` (HTTP, multipart ASR, structured output, SAM SSE + mask parsing, image edits, Baseten) against `api/tests/doubles/fake_meta.py`; wrong key → clean 401 |
| `test_fixtures.py` | All 16 sample fixtures (AI-generated photos) carry the "Sample photo (AI-generated), offline sample mode" corner tag and EXIF label, and each runs end to end with the expected safety level; step-check photos accepted |
| `test_video.py` | Video → 3 frames from different moments; sharper frame wins; >30 s and garbage rejected with 400; video-only session uses the clip's sound; photos + video capped at 3 |
| `test_playwright_smoke.py` | Real Chromium, phone viewport: faucet flow + check-my-step, motor follow-up question, rice STOP card (3 actions, maps link, PDF works, 112), PWA manifest, open-weights badge (+ language switch), video capture; fails on any JS error |
| `test_pwa.py` | Manifest valid with 192/512/maskable icons served; service worker never caches the API; health reports open weights only when really active |
| `test_i18n.py` | Every Indonesian UI string exists in Basa Jawa and English |
| `test_set_keys.py` | One-step key swap writes MODEL_API_KEY/OFFLINE=0 (+ Baseten) and runs the checks; no key → .env untouched |
| `test_report_pdf.py` | PDF repair report |
| `test_races.py` | 28 deterministic race tests (a held lock, a model call blocked on an Event, a Barrier): double re-plan, a check landing on the next plan, the photo-check cap under parallel checks, double retry and start, restart recovery, janitor bookkeeping, the erased-spend ledger |
| `test_owner_routes.py` | Owner token on every route that changes a repair, the rate-limit key (CLIENT_IP_HEADER, FORWARDED_HOPS), ASCII session ids, a decompression bomb on the step check |
| `test_missing_files.py` | A repair whose pictures went missing on the server still opens everywhere (session, PDFs, share card, hand-off, guide); a corrupt session file is a 404 and the "guide is gone" page |
| `test_check_voice.py` | `scripts/check_voice.py` finds 0 hits in the repo's docs, comments and docstrings and has no stale allowlist entry; each rule catches its own example, real uses (number ranges, the steps that unlock, the app's agent loop) pass, prompts keep their imperative voice, code strings are left alone |
| `test_playwright_screens_clean.py` | Chromium: every main screen with no console or page error, a repair a restart interrupted coming back with Try again, the progress screen on a throttled connection |
| `test_web.py` | `app.js` parses; every element id the JS uses exists; every UI string has id + en text; shared page is read-only; no secrets in web files; every emoji the screen can show has a Lucide icon; the Barlow fonts and both licences ship; nothing loads from a font CDN |
| `test_csp.py` | Every HTML page sends a strict Content-Security-Policy (no inline script, no eval), JSON answers don't; HSTS only when the proxy says https; no inline script or event handler in the pages; `web/wa.js` served as a file; status notes and disclaimer inside landmarks |
| `test_playwright_a11y.py` | Real Chromium (axe-core found in JSDOM_DIR, the repo's node_modules or /tmp/jd; CI installs it): axe-core finds nothing serious or critical on the home, progress, question, result, stop, shared guide, WhatsApp simulator and laptop screens; one h1 per screen; file pickers are native inputs in the tab order. Needs axe-core from npm (`npm install --prefix /tmp/jd axe-core`) and skips without it |
| `test_gone_page.py` | An expired or erased guide link gets a short page in the owner's language (still 404), with the link id escaped |
| `test_gzip.py` | Text is gzipped; fonts, photos, PNGs, audio and PDFs are sent as they are |
| `test_replan_report.py`, `test_brief_now.py` | After "Still broken" the PDF report and the mechanic brief list the attempt in the owner's language; the cause being tried now is "being tried now", not "already tried"; the link preview follows the current plan |
| `test_report_tail.py`, `test_report_tried_and_jv_words.py` | The PDF never ends with a page holding only the last line of the disclaimer; causes already tried are struck through with a "tried" label; Basa Jawa says "keslametan" |
| `test_playwright_kind_safety.py` | Real Chromium: the red stop's "Do this now" list and the two "Safety first" lines depend on what is being fixed (appliance or pump: unplug; tap: stop valve; motorbike: engine off); the gas list wins over the kind |
| `test_playwright_replan_stop.py`, `test_playwright_guide.py` | Focus moves to the "Plan 2 of 3" banner after a re-plan; the red stop has one nearest-service button and a message preview you can open; My garage says "camera-checked" and the plan number; a shared guide link opened after a re-plan shows the banner |
| `test_playwright_share_shop_tour.py` | Price links are named by shop (Tokopedia, Shopee) and sit on one row; Share on a laptop writes "Link copied:" in a line, never an alert(); the 1-tap demo keeps the newest finding above the tip bar |
| `test_static_cache.py` | /static sends Cache-Control: fonts and ?v= URLs a year (immutable), pictures a day, app code revalidated |
| `test_jv_register.py` | Basa Jawa stays in ngoko: no "sampeyan", "antosna" or other krama words in the app, PDF or workshop sheets |
| `test_launch_assets.py` | The one-pager build refuses anything but exactly one page and an unknown asset name; ONE_PAGER.md has no placeholder left and its PDF is committed |

## Recorded demo (v1.24)
- `python scripts/record_replay.py` re-records `web/replay/` from the live API (about $0.60) after a change to the prompts, the session shape or the demo flow; `--check` exits 1 when the recording no longer matches (also a test in `test_replay.py`).
- `test_playwright_replay.py`: with every `/api` call hanging (a sleeping server), the 1-tap demo still runs end to end from the recording and says so on screen. A visitor's own photo is refused instead of faked, and `?replay=1` sends nothing to the server.

## Meta API test double
`python -m api.tests.doubles.fake_meta` serves `http://127.0.0.1:8765/v1` with key `test-key`. I built it from the documented request/response shapes. To run the app against it:
```bash
META_API_BASE=http://127.0.0.1:8765/v1 MODEL_API_KEY=test-key NO_PROXY=127.0.0.1,localhost python app.py
```

## Scripts
- `python scripts/check_keys.py`: with a real key, PASS/FAIL per Meta model (under $0.02). `--no-cost` checks only the key and the model list; `--fake` is a dry run.
- `python scripts/smoke_e2e.py <url>`: drives a running server the way a phone would (5 scenarios, follow-up, check, re-plan, report, PDF, guide, images, PWA files). I use it on localhost and on the Render URL.

## Manual QA checklist (phone, real photos, live mode)

| # | Scenario | Do | Expect |
|---|---|---|---|
| 1 | Motorbike won't start | Photo of plug area + "Motor susah hidup, starter bunyi" | Parts numbered (plug cap, cable); amber; maybe a fuel-smell question; 3-6 steps; step 1 makes it safe |
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
| 13 | Video | Tap "rekam video", film the pump 5-10 s while describing it | 3 frames used as photos, transcript from the clip, normal diagnosis |
| 14 | Install | Chrome menu → Add to Home screen | Orange wrench icon; opens full-screen |
| 15 | PDF | Finish a repair → Download PDF | A4 report with marked photo, steps, checks |
| 12 | 4G speed | On mobile data | Diagnosis card < 25 s, step check < 8 s (record actual times in TEST_REPORT) |
