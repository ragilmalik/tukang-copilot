# Changelog

All dates WIB (UTC+7). Everything below was built during the hackathon window (Oct 26 – Nov 4, 2026).

## 2026-10-30 22:00 · v1.4.0
- Shopping help: every tool and part in the result and guide gets "Compare prices" links to Tokopedia and Shopee search pages (links only, Tukang Copilot never buys), plus a "Send shopping list to WhatsApp" button (wa.me share of tools, parts and rough prices in the session language). New `api/shop.py`; the session JSON carries `shop_url`, `shop_alt_url` and `whatsapp_url`. Front end only accepts those three https hosts. 4 new tests, one Playwright assertion.

## 2026-10-30 21:30 · v1.3.1
- Upload hardening: files stream to disk in 1 MB chunks and stop at the size limit (no whole file in memory); a corrupt, disguised or decompression-bomb image now gives a friendly 400 and leaves no half-made session folder behind. 8 new tests (`test_hardening.py`).
- Test isolation: conftest waits for pipeline threads at teardown, so a late worker can no longer write into the next test's folder or the repo `data/` folder.

## 2026-10-30 night · v1.3.0
- Abuse guard for a public deployment (`api/guard.py`): per-visitor rate limit (`RATE_LIMIT_PER_HOUR`, default 30) and a rolling 24 h spend cap across all repairs (`DAILY_BUDGET_USD`, default 10). Live mode only, so demo mode and judges using a mock site are never blocked. Friendly id/jv/en message, `Retry-After` header, 429 or 503. 8 tests.

## 2026-10-30 evening · v1.2.0
- Video capture: record a 5–10 s clip instead of photos. One ffmpeg pass samples 12 frames, the sharpest (Laplacian variance) of each third is kept as a photo; with no voice note or text, the clip's own sound is transcribed. Max 30 s / 40 MB, clean 400s.
- Basa Jawa: every UI string translated (ngoko); a test fails if any string is missing in jv or en.
- Open-weights badge in the header when diagnosis + planning really run on Muse Spark Open (flag + Baseten key), in id/jv/en.
- Safety escalation card for red stops and "all safe causes tried": why, what to do now, nearby service-centre search, technician PDF, 112 emergency line.
- PWA: manifest, generated icons (scripts/make_icons.py), shell-only service worker (never caches API or photos).
- Tests: 10 clearly labelled stand-in photo fixtures run end to end; Playwright browser smoke (6 tests, skip without Chromium); mypy strict config (mypy.ini) + CI step; scripts/check_all.sh. 121 tests.
- Demo assets from the real app in demo mode: 2:37 1080p video with captions + edge-tts voice-over, .srt, 36 s vertical X clip, 14 phone screenshots, architecture diagram.
- `set_keys.py` one-step key swap: `--stdin` (non-interactive), `--check-only`, `--help`; never creates .env without a key.
- Docs: SPEC §17 (verified judging criteria → features), docs/WINNING_PLAN.md, docs/SUBMISSION_CHECKLIST.md, README screenshots/diagram, judge 60-second tour.

## 2026-10-30 evening · v1.1.0
- Water pump scenario (SPEC §8 case 2): Shimizu pump runs but gives no water. Amber safety (220V near water, unplug first). Plan 1 re-primes the pump; "still broken" re-plans to the clogged foot valve. New sample photo and "Try a sample" button.
- Printable PDF repair report: `GET /api/sessions/{id}/report.pdf` (A4, id/jv/en): safety badge, marked SAM photo, every step with its camera check, tools and parts with prices, attempts, disclaimer. Pure Pillow, no new dependency. "Download PDF report" button on the result and shared guide pages.
- "My garage": past repairs kept only on the phone (localStorage, max 20), shown on the start screen with safety level, steps verified and a link back to the guide.
- PWA: root routes for `/manifest.webmanifest` and `/sw.js`, manifest link + theme colour, service worker registration (worker, icons and manifest by the parallel run).
- mypy strict now passes on all of `api/` (typed `_chat_json` generic, FastAPI handlers, SSE generator).

## 2026-10-30 · v1.0.0 (first complete build)
- Spec (SPEC.md) and plan.
- Verified Meta Model API docs: model ids, Chat Completions structured output, audio input, Voice Transcribe file endpoint, SAM 3.1 Responses streaming + box grammar, Muse Image edits, Muse Spark Open on Baseten, pricing (docs/META_API_NOTES.md).
- Backend: `meta_client` (retries, cost meter), pydantic schemas, versioned prompts, pipeline engine (listen → gate → look → SAM → diagnose → follow-up → plan → plan safety gate → Muse Image diagrams with review → narration), step verification, re-plan, report, 24 h cleanup, per-session budget.
- Three-layer safety gate (text, model level, plan scan) in id/jv/en.
- Phone web app: camera + mic capture, category chips, live stage progress (SSE), diagnosis card with SAM overlay, guided steps with voice and hands-free mode, check-my-step, still-broken re-plan, shareable read-only guide, Bahasa/Javanese/English UI.
- Demo mode with three scenarios (motorbike, faucet, rice cooker) and drawn sample photos.
- Fake Meta API server; `scripts/check_keys.py`, `scripts/set_keys.py`, `scripts/smoke_e2e.py`.
- 78 automated tests, ruff, GitHub Actions CI, Dockerfile, docker-compose, Render blueprint.
- Docs: README, HANDOFF, TODO, setup tutorial, how-to-use (EN/ID), architecture, AI pipeline, API, safety, testing, test report, verification report, troubleshooting, demo script, submission text + X drafts, roadmap, attributions, decisions.
- Fix: "gas" alone (motorbike throttle) no longer trips the gas safety stop; only LPG/cooking-gas phrases do.
