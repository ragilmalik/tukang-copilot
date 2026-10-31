# Changelog

All dates WIB (UTC+7). Everything below was built during the hackathon window (Oct 26 – Nov 4, 2026).

## v1.23.5
- Test keeping the app version and CHANGELOG in sync.

## v1.23.4
- Test locking the security headers on pages and errors.

## v1.23.3
- Landing: result preview thumbnail under the demo button (backlog J6).

## v1.23.1
- Share button now attaches the result card image via Web Share files when the phone supports it, link fallback otherwise.

## 1.23.0 (2026-10-31 WIB)
Judges can now watch the agent think, tap through its decisions, and share a result that previews well.
- **Streaming progress**: as each stage finishes, its result appears on the progress screen: what Muse Spark saw (object + parts), the photo with SAM 3.1's outlines, the top cause with confidence and safety level, then the step count. Server-Sent Events carry a trimmed `progress_view` (built from `public()`, so no owner words or raw errors); the polling fallback renders the same. In demo mode `MOCK_PACE` (default 0.6 s) holds each finished stage on screen during the first analysis only; it is never applied to live Meta calls or re-plans and never counted in a stage's timing.
- **Agent log lines link to what they describe**: tap a line to scroll to and highlight the stage or streamed result (progress), or the photo, causes, safety list, hand-off or the exact camera-checked step (result and guide pages; the step card jumps back to that step). Checks from an earlier plan are not linked (`check` events now carry `cause`). Lines are real buttons; focus follows for keyboard users.
- **Share card / link previews**: `GET /api/sessions/{id}/card.png` (1200×630: marked photo, object, top cause, safety badge, plan line, honest DEMO label; never the owner's words; 404 after erase). Guide pages carry Open Graph + `twitter:card` tags, the front page uses `web/og.png` (`scripts/make_og.py`, labelled stand-in photo). The Share button sends the object and cause with the link.
- **Judge-audit fixes** (390×844, id/jv/en): the follow-up question is scrolled on screen when it appears (streaming had pushed it below the fold); gzip for static files (app.js 90 KB → ~29 KB; SSE not compressed); favicon (removes a console 404). Tip-bar-moves-up-while-typing (ffc24d8) verified in real Chromium with a new test.
- Demo kit re-made: 26 screenshots (new: streaming progress, log jump, PDF agent-log page, share card), 2:57 voice-over video, 45 s vertical X clip (now with streaming progress and the share card), README GIF. Smoke test checks the share card and link-preview tags (65 checks). Service-worker cache `tukang-shell-v3`.

## 1.22.0 (2026-10-31 11:45 WIB)
Judge-facing polish: the agent now shows its work, a 1-tap demo runs the whole loop, and the public deploy is harder to abuse.
- **Agent log "🤖 What the AI did"**: every decision (look, mark parts, diagnose, ask under 60 %, plan, code safety gate, verify, re-plan, hand off) with the Meta model or code rule that made it and how long it took; loop strip on progress, result and the shared guide page. Never holds the owner's own words, so it is safe on a shared link. **The PDF report now prints the same log** (same wording as the app in id/jv/en; a test keeps the two in sync).
- **1-tap guided demo**: hero button runs the motor repair with tips, quick answers and labelled stand-in check photos (`GET /api/demo/check-photo/{dark|ok}`): a too-dark photo is rejected, the right one passes, *Still broken* re-plans. **The tip bar is a compact corner pill** that folds to a 💡 chip by itself after the first step check, with reopen/close buttons (aria labelled), so it never covers the main action.
- **Prompt-injection hardening**: `api/untrusted.py` fences owner text as data, the re-plan report moved out of the system prompt, a photo-text rule, and an input guard that logs instruction-like phrases (they can never lift a code safety stop).
- **Cost guards**: `FOLLOWUP_RATE_PER_HOUR` (240 model calls inside repairs per visitor), `MAX_STEP_CHECKS` (40 per repair), step-check spend counted in the session cost and the daily budget, length caps on answers and reports. Listed in render.yaml, .env.example and docs/DEPLOY.md.
- Javanese demo answers (`mock_jv.py`), model chip + elapsed timer per stage on the progress screen, WCAG AA contrast, overlay drawing 8× faster (fast suite 118 s → ~70 s), stage notes translated.
- README rewrite (60-second start, what judges should look at, Meta model → code table), service-worker cache `tukang-shell-v2`, two new smoke steps (agent log, demo check photo). Regenerated 23 screenshots, 2:53 video, 45 s vertical clip, README hero GIF.
- Tests: **453 passed, 0 failed** (443 fast + 10 slow, real Chromium); ruff clean; mypy strict clean (73 files); smoke 60 checks pass.

## 1.21.0 (2026-10-31 09:30 WIB)
Four features from the win plan (built 08:00–08:40 WIB), plus deploy readiness and a new demo kit.
- **Live camera guide**: `POST /api/sessions/{id}/steps/{n}/track` runs SAM 3.1 on a live camera frame (≤3 MB JPEG, ~640 px) and returns the target part's boxes and polygon. The guide draws an orange outline over the video, and *Check now* verifies the step from the current frame. Throttled (`TRACK_MIN_INTERVAL_S` 0.6 s → 429 + Retry-After) and capped (`MAX_TRACK_FRAMES` 120 per repair, about $0.30). Frames are never stored. Real-Chromium test with a fake camera.
- **Hands-free voice loop**: continuous SpeechRecognition (id-ID / jv-ID / en-US) for next / back / repeat / check / broken / stop, with a listening indicator. `POST /api/sessions/{id}/command` gives push-to-talk through Voice Transcribe on phones without it. Python `parse_command` mirrors the JS (same word lists, enforced by tests).
- **Bengkel hand-off**: `GET /api/sessions/{id}/handoff` returns a WhatsApp summary, a Maps workshop search, and guide + PDF links (`PUBLIC_BASE_URL` if set). The card shows on a red stop, when the causes run out, on "Call a mechanic" and on "Took it to a mechanic". The PDF gets a mechanic brief page, and code-gate stops now get a stop report PDF (was 409).
- **Demo fallback** (`DEMO_FALLBACK=1`, default on): a live chat call that still fails after retries uses the labelled demo answer for that stage. This shows in the UI badge, the PDF, `session.fallback` and `/health`. Fallback step checks never count as verified.
- **Impact trial kit**: append-only outcome log, trial mode (`?trial=T1`, minutes), token-gated download (`IMPACT_TOKEN`), `scripts/impact_report.py` → docs/IMPACT.md + slide (MOCK-stamped until real trials), docs/USER_TRIAL_KIT.md.
- **Deploy**: Render free plan in Singapore, non-root Docker with proxy headers and HEALTHCHECK, `/tmp` data dir. New `scripts/deploy_check.py` (PASS/WARN/FAIL with fixes; in LIVE mode it flags any session whose `fallback` list is non-empty, so a bad key can't hide behind demo answers). `smoke_e2e.py` prints a FALLBACK line per affected session. `check_keys.py` covers every model incl. the live track and open weights. render.yaml / .env.example / docs/DEPLOY.md list `MAX_TRACK_FRAMES`, `TRACK_MIN_INTERVAL_S`, `DEMO_FALLBACK`, `IMPACT_TOKEN`, `PUBLIC_BASE_URL`.
- **Demo kit**: 22 screenshots (new: safety list, live guide, hands-free, hand-off, stop PDF, Javanese result, open-weights badge, stop hand-off). New 2:50 video with voice-over and captions covering live camera, hands-free and hand-off. 45 s vertical X clip. docs/WRITEUP.md and the field-by-field docs/SUBMISSION.md for the Cerebral Valley form.
- Fixes: jv rice-cooker sample went to the motor scenario; an unreadable check photo is now 400 (was 503); the hand-off message wraps long URLs; edge-tts voice generation works behind the sandbox proxy; the vertical clip's architecture caption was white on white.
- Tests: `slow` marker for jsdom/Chromium tests, run as separate chunks. **410 passed, 0 failed.**

## 1.20.0 (2026-10-31 08:20 WIB)
- "Before you start" safety gate. Diagnosis has a new `before_you_start` list (up to 4 short statements: "the pump is unplugged", "the engine is off and cooled"). The result and shared guide pages show it as a tick list; the step card stays dimmed and `inert` (no taps, no keyboard focus, no hands-free voice) until every box is ticked, and the ticks are remembered per repair on the phone. Red stops carry none (`coerce.py` drops them). `prompts/diagnose.md` asks for it, all four non-red mock scenarios have it in id/jv/en, the PDF report prints it as a tick list before the steps. 19 tests (`test_preflight.py`) plus 7 jsdom checks per language and scenario (shown, translated, locked, still locked with one box open, unlocks).

## 1.19.0 (2026-10-31 07:50 WIB)
- Closes the loop. New `POST /api/sessions/{id}/outcome` (`fixed` or `pro`), "It works now" / "Took it to a mechanic" buttons on the result and shared guide pages (id/jv/en), a Result line in the PDF report, and a running "Total saved" line in My garage (sum of `diy_saving_idr` over repairs marked fixed, localStorage only). A re-plan clears the outcome. 12 tests (`test_outcome.py`), jsdom checks, smoke step.

## 1.18.0 (2026-10-31 07:15 WIB)
- Waiting-time steps. A plan step can now carry `wait_minutes` (0 to 120; "let the engine cool 10 minutes", glue or sealant drying). The guide shows a countdown with Start/Stop, then vibrates and reads "waiting time is over" aloud (id/jv/en); the workshop sheet prints a tick-box line ("Wait 10 minutes"). `coerce.py` `_wait` repairs "about 15 min" style values and drops silly ones; `prompts/plan.md` asks for it; the motor mock plan's first step waits 10 minutes. Tests: `test_wait_timer.py` (9), a coerce test, and 7 jsdom checks (timer shown, 10:00, counts down, stops, absent on other scenarios). Timer ticks use wall-clock time so it stays right if the phone throttles the tab; if the screen locks the vibrate/voice alert may not fire (not testable without a real phone).

## 1.17.1 (2026-10-31 06:40 WIB)
- Price sanity for live mode (`api/coerce.py` `_price`): shop and part prices now accept "75k", "75rb", "1,5 juta", "Rp 75.000"; negative values and anything above Rp15 million (a unit misread) become unknown (0) instead of a wild saving chip; a red-stop diagnosis never keeps a shop price. 13 new tests in `test_shop_cost.py`.

## 1.17.0 (2026-10-31 06:10 WIB)
- "Bengkel vs DIY" price line. Diagnosis has a new `shop_cost_estimate_idr` (typical bengkel/servis price, parts plus labour; 0 when unknown or red stop) and a computed `diy_saving_idr` (shop price minus parts, never negative; tools left out because they are reusable). Prompt `diagnose.md` asks for it, `coerce.py` repairs "Rp 75.000" style values, all four non-red mock scenarios carry one. Phone UI shows a chip ("bengkel Rp150.000 · hemat Rp110.000", id/jv/en), the PDF report prints both lines. Also fixed the PDF total, which was labelled "tools + parts" but showed parts only; it is now labelled "parts". Tests: `test_shop_cost.py` (9) and a jsdom check per language and scenario.

## 1.16.0 (2026-10-31 05:30 WIB)
- Real-phone photo formats. New `api/pipeline/photos.py`: iPhone HEIC/HEIF uploads (repair photos and the step check photo) are converted to JPEG on the server with the optional `pillow-heif` package (added to requirements.txt); without it HEIC gets a clear 400 message ("set the camera to JPG") instead of a crash. `.jfif` and upper-case extensions accepted. 7 new tests in `test_photo_formats.py` (HEIC round trip incl. check photo, EXIF-rotated JPEG, corrupt file gives 400, unsupported types, decoder-missing message).

## 1.15.0 (2026-10-31 05:05 WIB)
- Weak-signal handling in the phone UI. Network failures (start, answer, step photo check, re-plan, Try again) now show a friendly id/jv/en sentence instead of "Failed to fetch" or a stuck "Checking photo..."; an offline banner appears on the home and guide pages while the phone has no connection and disappears when it returns. Step photo check and answer no longer end in an unhandled promise rejection. 18 new jsdom checks (3 languages: banner shows and hides, fetch rejection gives friendly text, Start button usable again). Not verified in a real browser with airplane mode (no Chromium here).

## 1.14.0 (2026-10-31 04:35 WIB)
- Accessibility pass on the phone UI. Page language is now tagged `jv` for Basa Jawa (was `id`, so screen readers mispronounced it); photo, video and step-check pickers are reachable by keyboard (tab + Enter/Space); category chips and the mic button expose `aria-pressed`; progress has a short screen-reader status line instead of re-reading the whole list; check results, errors and recording state are live regions; focus moves to the new section heading on each screen change; visible focus ring, 44 px touch targets, reduced-motion support. 8 new jsdom checks per language run plus a static test. Not verified with a real screen reader or in Chromium (none available here).

## 1.13.0 (2026-10-31 04:10 WIB)
- Hostile input and hostile model output hardening. (1) Prompt-injection rule appended to the look, diagnose, plan and replan prompts (owner text and text in photos are data, never orders; `api/prompts.py`). (2) jsdom XSS check: every free-text field of a real session is poisoned with `<img onerror>` and `<script>` payloads and the guide page must run none of it (verified to fail when an `esc()` is removed). (3) `api/tests/test_security.py` (16 tests): guide page title escaping, odd session ids, path traversal on `/files`, private `session.json`, a prompt-injection sentence cannot lift the code safety gate. (4) Small fixes: parts list label now escaped, duplicate `sTire` key removed. Documented in docs/SAFETY.md.

## 1.12.0 (2026-10-31 03:30 WIB)
- Phone photos are shrunk on the phone before upload (`shrinkImage` in web/app.js: longest side 1600 px, JPEG 85 percent, only for jpeg/png/webp over 400 KB, original kept if the result is not smaller or anything fails, e.g. an undecodable HEIC). A 6 MB photo becomes roughly 300 KB, so three photos and the step check photos go over 4G in seconds. The Start button is disabled while shrinking so a double tap cannot create two repairs. jsdom test with a stubbed canvas covers resize, fallbacks and untouched small and non-image files.

## 1.11.0 (2026-10-31 03:00 WIB)
- Privacy controls. `DELETE /api/sessions/{id}` and a "Delete my photos now" button (id/jv/en) erase a repair from the server immediately; "Clear history" in My garage now erases the saved repairs on the server too. A background janitor purges sessions older than `RETENTION_HOURS` every hour (before, only at startup, so a deploy running for days would have kept photos past the 24 h promise). A worker still running cannot resurrect an erased folder. `api/tests/test_erase.py` (6 tests), jsdom check for the button, smoke_e2e step.

## 1.10.0 (2026-10-31 02:30 WIB)
- `scripts/eval_fixtures.py`: scores every photo fixture against its manifest expectation (safety level, red stop vs plan, object category, share of parts found by SAM, step count, seconds, cost) plus the camera step checks, against any running server, mock or live, and can point at a folder of real photos with the same `manifest.json` shape (`--dir`). Writes `docs/EVAL_REPORT.md`. For the first live run this gives honest accuracy numbers. `api/tests/test_eval_script.py` (2 tests, incl. a deliberate mismatch that must FAIL).

## 1.9.1 (2026-10-31 02:00 WIB)
- Four more labelled stand-in fixtures for the tyre scenario (flat tyre with nail in id and en, valve check photo, pressure sticker close-up), now 14 in total; `api/tests/test_tire_fixture.py` runs them end to end (diagnosis, optional follow-up answer, camera check, PDF report).

## 1.9.0 (2026-10-31 01:40 WIB)
- Fifth demo scenario: flat scooter tyre with a nail (tubeless plug repair, amber). Cause 1 nail in tread, cause 2 leaking valve stem (re-plan tightens the valve core), SAM phrases `tyre tread` / `valve stem` / `wheel rim`, id/jv/en text, new sample photo `samples/tire.jpg`, "flat tyre" sample button in the 3 languages, routing for kempes/gembos/tambal ban/tubeless/puncture/tyre. Tests: 2 engine tests, 4 routing cases, jsdom flow (Javanese), smoke_e2e.

## 1.8.1 (2026-10-31 01:30 WIB)
- Safety text gate widened: electric shock (kesetrum, tersengat listrik, got shocked), fire/smoke/swollen battery (points to fire service 113), konslet/korslet/short circuit, freon/refrigerant/AC compressor. New `shock` and `fire` stop messages in id/jv/en; docs/SAFETY.md updated; 14 tests.

## 1.8.0 (2026-10-31 00:50 WIB)
- Model-drift tolerance for live mode (`api/coerce.py`): JSON is pulled out of think tags, code fences and surrounding prose; harmless quirks are repaired before validation (capitalised or synonym enums such as "Amber"/"danger", confidence as 0.85 or "85%", "Rp 25.000" prices, a string where a list belongs, a sixth cause or twelfth step, percent boxes). A reply with no JSON at all now gets one retry instead of failing. 11 tests (`test_coerce.py`).

## 1.7.1
- jsdom headless UI test (41 checks, id/jv/en, 4 scenarios) for the real web/app.js; CI installs jsdom.

## 2026-10-30 23:50 · v1.7.0
- "Under the hood" panel: every session JSON now has `trace` (one row per pipeline stage: tool, kind meta/open/tts/code, status, ms) from the new `api/trace.py`. The result and guide pages show it as a collapsible list (id/jv/en) and the PDF report prints it, so judges can see exactly which Meta model did what and where plain-code safety gates and edge-tts take over. Replaces the old one-line model list. 5 new tests (`test_trace.py`) plus a Playwright assertion (skipped here, no Chromium).

## 2026-10-30 23:10 · v1.6.0
- Workshop mode: "Workshop sheets (large print)" button on the result and guide pages and `GET /api/sessions/{id}/workshop.pdf`, an A4 one-step-per-page PDF to pin up next to the bike or pump (id/jv/en). New `api/render/workshop_pdf.py`; 5 new tests; smoke script checks it.

## 2026-10-30 22:40 · v1.5.0
- Resilience for live mode: pipeline failures now show one calm sentence in the person's language (busy, dropped signal, wrong key, cost limit, unusable AI answer) instead of raw HTTP text; technical detail stays on the server (`error_detail`, keys scrubbed). New `api/errors.py`.
- "Try again" button and `POST /api/sessions/{id}/retry`: a failed session resumes from the failed stage and keeps what was already done and spent.
- Step check and re-plan outages answer 503 with a friendly message and `Retry-After`; a failed re-plan no longer skips a cause (cause index and history are rolled back).
- Fake Meta server got fault injection (`FAULTS`); 10 new tests in `test_resilience.py` (outage then recovery, flaky 429s absorbed, SAM and image-edit outages degrade gracefully, bad key in Javanese).

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

## v1.23.2
- Share card Cache-Control cut from 300 s to 60 s so erased repairs leave crawler caches sooner (backlog J8).
