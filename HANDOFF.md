# Handoff

Read this first if you are picking up Tukang Copilot (human or AI).

## State on 2026-10-31 01:30 WIB (v1.8.1)
- **New:** wider text safety gate: electric shock (kesetrum, tersengat), fire/smoke/swollen battery (fire service 113), short circuit variants (konslet, korslet), refrigerant (freon, AC compressor). New `shock` and `fire` stop messages in id/jv/en. 14 new tests (gate + engine stop before any model call). Everyday phrases ("api kompor kecil", "knalpot putih") still pass.
- **Checks (real runs, 01:25 WIB):** ruff clean, `mypy api` strict no issues in 47 files, pytest **183 passed, 7 skipped** (Playwright/jsdom, no Chromium installable here as non-root arm64), `node --check web/app.js` ok, `smoke_e2e.py` ALL PASSED, `make_test_report.py` ALL PASSED (183/190).
- **Next up (Malik):** re-take demo screenshots/video with the Under the hood panel when a Chromium exists; Render preview smoke once deployed; prompt tuning on real photos / first live key run. Malik-side steps unchanged.

## State on 2026-10-31 00:55 WIB (v1.8.0)
- **New:** `api/coerce.py` model-drift tolerance (tolerant JSON extraction, enum/number/list repair, caps on causes/steps/components) wired into `engine._chat_json` and `meta_client._extract_json`; a no-JSON reply retries once. Never invents content. 11 tests in `test_coerce.py`.
- **Checks (real runs, 00:50 WIB):** ruff clean, `mypy api` strict no issues in 47 files, pytest **169 passed, 7 skipped** (Playwright and jsdom, none installable as root/arm64 here), `node --check web/app.js` ok, `smoke_e2e.py` ALL PASSED, `make_test_report.py` ALL PASSED (169/176).
- **Next up (Malik):** re-take demo screenshots/video with the Under the hood panel when a Chromium exists; Render preview smoke once deployed; prompt tuning on real photos / first live key run. Malik-side steps unchanged.

## State on 2026-10-31 00:20 WIB (v1.7.1)
- **New:** headless UI check without a browser. `api/tests/dom/dom_flow.mjs` runs the real `web/app.js` in jsdom against a live mock server (`api/tests/test_dom_jsdom.py`, CI installs jsdom): 41 checks across id/jv/en and all four scenarios (result page, hood panel rows and names, no raw i18n keys, follow-up question for the motorbike, red stop box for the rice cooker, next-step button, no uncaught JS errors). This verifies the Under the hood panel and Try again wiring in a DOM for the first time. Skips cleanly if node/jsdom are missing (local install: `cd /tmp/jd && npm install jsdom`).
- **Checks (real runs, 00:15 WIB):** ruff clean, `mypy api` strict no issues in 45 files, pytest **159 passed, 6 skipped** (Playwright, no Chromium downloadable on this arm64 sandbox), `node --check web/app.js` ok, `smoke_e2e.py` ALL PASSED, `make_test_report.py` ALL PASSED (159/165).
- **Next up (Malik):** re-take demo screenshots/video with the Under the hood panel (needs a Chromium; do it when one exists); Render preview smoke once deployed; prompt tuning when real photos arrive. Malik-side steps unchanged.

## State on 2026-10-30 23:50 WIB (v1.7.0)
- **New:** "Under the hood" panel (`api/trace.py`, `trace` in session JSON, collapsible list on result + guide pages in id/jv/en, section in the PDF report). Shows which Meta model ran each stage and where code gates / edge-tts are used. Report PDF page inspected visually.
- **Checks (real runs, 23:45 WIB):** ruff clean, `mypy api` strict no issues in 44 files, pytest **158 passed, 6 skipped** (Playwright, no Chromium here; new hood assertions unverified in a browser), `node --check web/app.js` ok, `smoke_e2e.py` ALL PASSED.
- **Next up (Malik):** re-take demo screenshots/video to include the Under the hood panel; Playwright assertions when a browser exists; Render preview smoke once deployed; prompt tuning when real photos arrive. Malik-side steps unchanged.

## State on 2026-10-30 23:15 WIB (v1.6.0)
- **New:** Workshop mode. `GET /api/sessions/{id}/workshop.pdf` (+ "Workshop sheets (large print)" button on result and guide pages, id/jv/en): A4 cover with safety banner, marked photo and tick list, then one big-type page per step (warnings in a red box, what the camera should see, diagram or marked photo, tick box), final "Done when" page. `api/render/workshop_pdf.py`, 5 tests; pages inspected visually.
- **Checks (real runs, 23:10 WIB):** ruff clean, `mypy api` strict no issues in 42 files, pytest **153 passed, 6 skipped** (Playwright, no Chromium here), `node --check web/app.js` ok, `smoke_e2e.py` ALL PASSED (incl. workshop PDF for every sample), `make_test_report.py` ALL PASSED (153/159). The new button is not browser-tested.
- **Next up (Malik):** Playwright assertions for Try again + workshop button when a browser exists; re-take demo screenshots/video if wanted; Render preview smoke once deployed; prompt tuning when real photos arrive. Malik-side steps unchanged.

## State on 2026-10-30 22:45 WIB (v1.5.0)
- **New:** live-mode resilience. `api/errors.py` maps failures to friendly id/jv/en sentences; `POST /api/sessions/{id}/retry` + a "Try again" button resume a failed session; check/replan outages give 503 + Retry-After; failed re-plan rolls back the cause index. Fake Meta server has `FAULTS` injection; `api/tests/test_resilience.py` (10 tests).
- **Checks (real runs, 22:40 WIB):** ruff clean, `mypy api` strict no issues in 41 files, pytest **148 passed, 6 skipped** (Playwright, no Chromium downloadable here), `node --check web/app.js` ok, `smoke_e2e.py` ALL PASSED on a local mock server, `make_test_report.py` ALL PASSED (148/154). The new Try again button is not browser-tested (no Chromium here).
- **Next up (Malik):** Workshop mode; Playwright assertion for the Try again button when a browser exists; re-take demo screenshots/video if wanted; prompt tuning when real photos arrive. Malik-side steps unchanged.

## State on 2026-10-30 22:05 WIB (v1.4.0)
- **New:** shopping links per tool/part (Tokopedia + Shopee search, links only) and a WhatsApp share button for the parts list (`api/shop.py`, fields `shop_url`, `shop_alt_url`, `whatsapp_url` in the session JSON; UI in result + guide pages, id/jv/en strings).
- **Checks (real runs, 22:00 WIB):** ruff clean, `mypy api` strict no issues in 39 files, pytest **138 passed, 6 skipped** (Playwright, no Chromium here; its new assertions for the links are unverified in a browser), `node --check web/app.js` ok, `smoke_e2e.py` ALL PASSED on a local mock server, `make_test_report.py` ALL PASSED (138/144).
- **Next up (Malik):** Workshop mode (illustrated guide from a session); re-take demo screenshots/video if the result page change matters; Render preview smoke once deployed; prompt tuning when real photos arrive.

## State on 2026-10-30 21:35 WIB (v1.3.1)
- **New:** upload hardening (chunked size-limited writes, corrupt/disguised/huge images give 400 and no leftover session folder), conftest joins pipeline threads between tests. 8 tests in `api/tests/test_hardening.py`.
- **Checks (real runs, 21:35 WIB):** ruff clean, `mypy api` strict no issues in 37 files, pytest **134 passed, 6 skipped** (Playwright, no Chromium), `node --check web/app.js` ok, `smoke_e2e.py` ALL PASSED on a local mock server, `make_test_report.py` ALL PASSED (134/140).
- **Next up (Malik):** Workshop mode (illustrated guide from a session); Render preview smoke once deployed; prompt tuning when real photos arrive; double-check demo video still matches UI after later changes.

## State on 2026-10-30 21:00 WIB (v1.3.0)
- **New in v1.3.0:** `api/guard.py` abuse guard for a public deploy (live mode only): `RATE_LIMIT_PER_HOUR` (default 30 new repairs per visitor, uses X-Forwarded-For) and `DAILY_BUDGET_USD` (default 10, rolling 24 h sum of session costs on disk) answer 429 or 503 with a friendly id/jv/en message and Retry-After; security headers (nosniff, SAMEORIGIN, no-referrer, camera/mic self) on every response; render.yaml and .env.example carry the new vars.
- **Checks (real runs, 21:00 WIB):** ruff clean, `mypy api` strict no issues in 36 files, pytest **126 passed, 6 skipped** (Playwright, no Chromium here), `node --check web/app.js` ok, `smoke_e2e.py` ALL PASSED on a local mock server, security headers verified by curl, `make_test_report.py` regenerated.
- **Next up (Malik):** nothing blocking; ideas: Workshop mode (illustrated guide from a session), Render preview smoke once deployed, prompt tuning when real photos arrive. Malik-side steps unchanged (repo yes, key, photos, deploy, video, submit).

## State on 2026-10-30 19:25 WIB (v1.2.0)
- **New in v1.2.0:** video capture (5–10 s clip → sharpest frame from each third, clip sound used as the voice note), full Basa Jawa UI strings, open-weights badge (only when Muse Spark Open is really active), safety escalation card (why / do this now / nearby service centre / PDF / 112), PWA manifest + service worker + icons, 10 labelled stand-in photo fixtures, Playwright browser smoke tests, demo assets (2:37 captioned voice-over video, 36 s vertical X clip, 14 screenshots, architecture diagram), `set_keys.py --stdin/--check-only/--help`, docs/WINNING_PLAN.md + docs/SUBMISSION_CHECKLIST.md, SPEC §17.
- **Checks (real runs, 19:22 WIB):** `scripts/check_all.sh` → ruff clean, `mypy api` (strict, mypy.ini) no issues in 33 files (a typing slip in test_set_keys.py was caught and fixed in a follow-up commit), pytest **121/121 passed** incl. 6 Playwright browser tests (system Chromium; `python -m playwright install chromium` failed to download in the sandbox, tests skip cleanly when no browser), `make_test_report.py` ALL PASSED, `smoke_e2e.py` ALL PASSED on a local mock server (4 scenarios + PDFs + PWA), `check_keys.py --fake` 5/5 PASS.
- **Next up:** (1) Malik: repo yes → push → CI green; (2) real Meta key via `set_keys.py` → live run of the 4 samples; (3) real Semarang photos → swap fixtures + prompt tuning; (4) deploy on Render + phone/4G test; (5) record the real video (backup in docs/demo/); (6) submit (docs/SUBMISSION_CHECKLIST.md).

## State on 2026-10-30 19:20 WIB (v1.1.0)
- **Complete, working app in demo mode, four scenarios:** motorbike (amber), water pump (amber, new), faucet (green), rice cooker (red stop). All stages, the phone UI, safety, verification and re-plan are built.
- **New in v1.1.0:** water pump flow with re-plan to the foot valve; PDF repair report (`/api/sessions/{id}/report.pdf`, button on result + guide pages); "My garage" history on the phone (localStorage); PWA routes; mypy strict clean on `api/`.
- **Checks (real runs, 19:15 WIB):** pytest 103/103 pass (`make_test_report.py`), ruff clean, `python -m mypy api` "no issues in 28 files", `node --check web/app.js` ok, `smoke_e2e.py` ALL PASSED on a local mock server, pump sample in jv + PDF endpoint 200 application/pdf checked by curl, PDF pages inspected visually.
- **Not yet live:** no Meta API key has been used. The real HTTP client is tested against a fake server that follows Meta's documented shapes. First real-key run is the next step.
- **Not yet published:** no GitHub repo, no deploy, no video. Malik must approve the repo and any public post or submission.

## Run it
```bash
./start.sh          # or start.bat on Windows → http://localhost:8000 (demo mode)
python scripts/set_keys.py      # go live
scripts/check_all.sh            # ruff + mypy strict + all tests (same as CI)
python scripts/make_demo_assets.py all   # screenshots, diagram, voice-over, demo video
python scripts/make_test_report.py   # regenerate docs/TEST_REPORT.md from real runs
```

## Where things are
| Path | What |
|---|---|
| `app.py` | Starts the server |
| `api/main.py` | HTTP endpoints + serves `web/` |
| `api/pipeline/engine.py` | The whole pipeline, session state, check, re-plan, report, cleanup |
| `api/meta_client.py` | The only code that calls Meta (and Baseten) |
| `api/schemas.py` | ObjectReport, Diagnosis, RepairPlan, StepCheck, DiagramReview |
| `api/pipeline/safety.py` | Text gate, plan gate, messages in id/jv/en |
| `api/pipeline/mock.py` | Demo answers + sample photos (motor, pump, faucet, rice) |
| `api/pipeline/media.py` | ffmpeg WAV, video → sharpest frames, edge-tts |
| `api/tests/fixtures/` | 10 labelled STAND-IN photos (scripts/make_fixtures.py) |
| `docs/demo/` | Demo video, X clip, screenshots (scripts/make_demo_assets.py) |
| `api/render/overlay.py` | SAM masks → numbered overlay |
| `api/pipeline/media.py` | ffmpeg WAV conversion, edge-tts |
| `api/settings.py`, `api/cost.py`, `api/prompts.py` | Config, cost meter, prompt loader |
| `prompts/*.md` | One versioned prompt per stage |
| `api/testing/fake_meta.py` | Fake Meta API for tests and dry runs |
| `api/tests/` | All tests |
| `scripts/` | set_keys, check_keys, smoke_e2e, make_test_report |
| `web/` | index.html, guide.html, app.js, style.css |
| `docs/` | Everything else (see README map) |
| `docs/SPEC.md` | The original spec |

## Key decisions
See docs/DECISIONS.md. Most important: single FastAPI process + plain JS (no Next.js); JSON per session; edge-tts because Meta has no TTS; Javanese via Spark 1.2 audio; safety in code (3 layers); Standard-mode model ids only.

## Rules for whoever continues
- Ask Malik before creating the repo, creating accounts, spending money, posting publicly, or submitting.
- Never put keys in code or chat. `.env` locally, Render env vars in the cloud.
- Keep Malik's instructions short, numbered, plain English (Bahasa if he prefers). He is not a developer.
- After any change: `python -m pytest api/tests -q`, then `python scripts/make_test_report.py`, then update CHANGELOG.md and TODO.md.
- Check his shift schedule before asking him to do anything (he works nights).

## Next up (Malik, no Malik needed)
1. Video capture (5 to 10 s clip, 3 frames) in web/app.js + engine (owner of engine/web).
2. Open-weights badge chip in the UI and the PDF when `USE_OPEN_WEIGHTS=true`; per-stage model chips.
3. Safety escalation polish: red stop screen with service-centre advice and a PDF; Javanese strings for every remaining UI label.
4. Parallel run (see ../work/COORDINATION.md) owns: Playwright smoke, fixtures, demo video assets, submission checklist, WINNING_PLAN.

## Next 3 actions (need Malik)
1. Get the repo approval → push → CI green.
2. Real key → `check_keys.py` → live run of the three samples → fix differences.
3. Real photos → prompt tuning → deploy → phone test → video.

## Known gaps
Video capture, PDF report, garage history, water-pump fixture, Playwright/mypy, real performance numbers. All in TODO.md.

## 2026-10-30 19:50 WIB check
check_all: ruff clean, mypy 33 files OK, 115 passed, 6 skipped (Playwright, no Chromium in this sandbox, skip cleanly). No code changes; Malik-side steps unchanged.
