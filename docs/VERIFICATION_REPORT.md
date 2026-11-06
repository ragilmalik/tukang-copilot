# Verification report

I checked the app against SPEC.md and the hackathon rules. The first version of this report is from 2026-10-30; the latest check is 2026-11-06 WIB (v1.32.0). Section 5d covers 1.24 and 1.25, section 5e covers 1.27.0, section 5f covers 1.28 to 1.29.4, section 5g covers 1.29.6 to 1.29.13, section 5h covers 1.30.0, section 5i covers 1.31.0 and 1.31.1, section 5j covers 1.32.0, and the earlier sections date from v1.22.0.

Legend: ✅ verified by a test or run · 🟡 built, verified only offline (needs a real-key or real-phone check) · ⬜ not done yet (in TODO.md) · ↔️ done differently (see DECISIONS.md).

Evidence names point to tests in `api/tests/` (TEST_REPORT.md has the run) or to scripts.

## 1. Hackathon rules

| Rule | Status | Evidence / note |
|---|---|---|
| Uses Meta models (Stage 1 pass/fail) | ✅ | 5 Meta models wired (`meta_client.py`). Live on the real API on 5 Nov 2026: `scripts/check_keys.py` passed all 5 required models, and every sample scenario ran live (docs/LIVE_RUN.md, docs/EVAL.md live column); the recorded 1-tap demo is a live run from 6 Nov 2026 |
| Fits a problem statement (Push the Frontier) | ✅ | README / SUBMISSION framing: understanding + repairing physical systems |
| New work only, Oct 26 to Nov 4 | ✅ | First commit 2026-10-30 (9c2401d), public commit history; CHANGELOG |
| Public repo, open license | ✅ | https://github.com/ragilmalik/tukang-copilot (public), MIT LICENSE |
| 3-minute demo video | ✅ (file) / ⬜ (YouTube) | docs/demo/tukang-copilot-demo.mp4, 2:25 (1080p30, re-made 6 Nov 2026): real Meta API answers recorded on a live run on 6 Nov 2026 and played back in the app, said on every phone frame; labelled AI-generated scenes for the people and homes; voice-over and music. A real-phone recording (DEMO_SCRIPT.md) and the YouTube upload are still mine to do |
| No unlicensed assets | ✅ | ATTRIBUTIONS.md: Barlow (OFL) and Lucide (ISC) with their licences; the sample photos are AI-generated and labelled as such; diagrams drawn by my own code |
| Avoid anti-projects (medical, basic RAG, simple image analyser, edu chatbot, politics) | ✅ | Medical blocked (`test_hard_stops[…luka berdarah…]`); multi-step agent with verification and re-plan, not one-shot analysis |

## 2. User flow (SPEC §5)

| Item | Status | Evidence |
|---|---|---|
| Start: camera + mic, language id/jv/en, category chips | ✅ | `test_web::test_every_id_used_in_js_exists_in_index`, `test_engine::test_languages`, `test_api::test_bad_requests` (category validation) |
| Capture 1-3 photos + ≤60 s voice, text fallback | ✅ | `test_api::test_upload_flow_and_files` (2 photos), `test_engine::test_audio_is_deleted_after_listen`, 60 s cap in app.js |
| Capture 5-10 s **video** → 3 frames | ✅ | Built in v1.2 (sharpest frame per third); media tests |
| Named progress stages | ✅ | `test_api::test_sse_events_stream`; smoke_e2e |
| Diagnosis card: object, top causes + confidence + why, SAM parts on own photo, tools, difficulty 1-5, time, cost estimate, safety level | ✅ | `test_engine::test_faucet_green_full_run`, `test_overlay::*`, `test_schemas::test_cost_estimate_sums_parts` |
| Guided mode: one step per screen, annotated image, instruction, voice, why, warnings | ✅ / 🟡 | Rendering logic checked statically (`test_web`); visual check on a real phone pending |
| Check my step → ✅ / ⚠️ correction | ✅ | `test_engine::test_step_check_pass_fail_and_escalate`, `test_live_path::test_live_motor_full_flow` |
| Stuck → re-plan to next cause | ✅ | `test_engine::test_replan_moves_to_next_cause_then_exhausts` |
| Finish: shareable report link | ✅ | `test_api::test_upload_flow_and_files` (guide page + report) |
| Report as **PDF**, "Save to my garage" history | ✅ | `test_report_pdf`, jsdom garage checks; stop report PDF for code-gate stops (`test_handoff::test_gate_stop_gets_a_stop_report_pdf`) |
| Workshop mode (stretch) | ✅ | Large-print workshop PDF (`test_report_pdf`) |

## 3. AI pipeline (SPEC §6)

| Stage | Status | Evidence |
|---|---|---|
| 1 Listen: Voice Transcribe (id/en), Spark 1.2 audio (jv) | 🟡 | Indonesian ASR request shape + recording deletion: `test_live_path::test_live_voice_note_is_transcribed` (fake server). Javanese route only in offline sample mode |
| 2 Look: Spark vision → ObjectReport | 🟡 | live-path tests; schema tests |
| 3 SAM 3.1 masks + server overlay | 🟡 / ✅ | Overlay pixel-checked (`test_overlay`); SAM SSE parsed with Meta's parser on fake stream |
| 4 Diagnose (+ open-weights toggle) | 🟡 | `test_live_path::test_live_open_weights_path` |
| 5 Plan + re-plan | 🟡 | engine + live-path tests |
| 6 Illustrate with Muse Image (+ review/redraw) | 🟡 | diagram created via `/v1/images/edits` on fake server |
| 7 Narrate (Meta has no TTS → edge-tts, browser fallback) | ↔️ 🟡 | D4; edge-tts disabled in tests (network) |
| 8 Verify step + escalate | ✅ / 🟡 | engine tests; real-photo judgement pending |
| 9 Safety gate | ✅ | `test_safety` (16 cases), `test_engine::test_rice_cooker_red_stop`, `test_gate_stops_before_any_model_call`, `test_replan_report_goes_through_gate` |
| Validate every response, retry once with error | ✅ | `_chat_json` in engine; schemas tests |
| Endpoints verified against live docs, written down | ✅ | META_API_NOTES.md |

## 4. Architecture & quality (SPEC §7, §9)

| Item | Status | Note |
|---|---|---|
| Next.js front end on Vercel | ↔️ | Plain HTML/JS served by FastAPI (D1) |
| FastAPI endpoints (sessions, analyze, events SSE, step check, replan, report) | ✅ | API.md; `test_api` (analysis starts on create, so no separate `/analyze`) |
| SQLite storage | ↔️ | JSON per session (D2) |
| Uploads auto-deleted after 24 h | ✅ | `test_engine::test_cleanup_removes_old_sessions` |
| Docker / compose / cloud deploy | 🟡 | Container emulated (Dockerfile CMD + render.yaml env, PORT 10000): smoke ALL PASSED, `deploy_check.py` READY, RSS ~150 MB. ⬜ first real Render deploy still to do |
| Config via .env; cost cap; image downscale 1536 px; DEMO_MODE | ✅ | `test_overlay::test_normalize_caps_size_and_applies_exif`, `test_engine::test_budget_guard` |
| `/health` | ✅ | `test_api::test_health` |
| Lint (ruff) | ✅ | TEST_REPORT |
| mypy strict / Playwright / jsdom | ✅ | `mypy api` strict: no issues in 67 files; real-Chromium tests (smoke + live camera with test camera feed); jsdom UI flow (214 checks) |
| CI on push | ✅ | `.github/workflows/ci.yml` on GitHub Actions: ruff, mypy, the full pytest suite with real Chromium, jsdom and (from 1.31.1) axe-core; green on 09fa5f1 (https://github.com/ragilmalik/tukang-copilot/actions/runs/42134244102); for 1.32.0 green on 05dc01d (https://github.com/ragilmalik/tukang-copilot/actions/runs/42159090902) and 60047bc (https://github.com/ragilmalik/tukang-copilot/actions/runs/42159375750) |
| Path traversal / upload validation | ✅ | `test_api::test_not_found_and_path_traversal`, `test_bad_requests` |
| Performance (< 25 s diagnosis on 4G, < 8 s check) | ⬜ | Measure on a real phone with real models |

## 5. Documentation (SPEC §11)

| Doc | Status |
|---|---|
| README | ✅ (live URL, video, GIF placeholders until recorded) |
| SETUP (how I run it) | ✅ |
| HOW_TO_USE | ✅ |
| ARCHITECTURE | ✅ |
| AI_PIPELINE | ✅ |
| META_API_NOTES | ✅ |
| API | ✅ |
| SAFETY | ✅ |
| TESTING + TEST_REPORT | ✅ (TEST_REPORT regenerated by script) |
| VERIFICATION_REPORT | ✅ (this file) |
| TROUBLESHOOTING | ✅ |
| DEMO_SCRIPT | ✅ |
| SUBMISSION + X drafts | ✅ |
| ROADMAP | ✅ |
| ATTRIBUTIONS | ✅ |
| CHANGELOG | ✅ |
| TODO, DECISIONS | ✅ |
| Docstrings on public functions | ✅ (modules + public functions documented) |

## 5b. v1.21.0 features

| Feature | Status | Evidence |
|---|---|---|
| Live camera guide (SAM 3.1 on live frames, overlay, throttle, cap, frames not stored) | ✅ / 🟡 | `test_live_track` (12 tests incl. cost in live mode, 429 throttle, frame cap); `test_playwright_live` (real Chromium, test camera feed: highlight drawn, Check now works). Real SAM quality/latency on 4G unverified |
| Hands-free voice commands + push-to-talk | ✅ / 🟡 | `test_voice` (JS ↔ Python word lists and parser identical, endpoint text/audio, live ASR path on fake server); jsdom checks. Real SpeechRecognition (jv-ID on Android) unverified |
| Bengkel hand-off (WhatsApp, Maps, mechanic brief PDF) | ✅ / 🟡 | `test_handoff` (13 tests); screenshot 18/22. WhatsApp deep link on a real phone unverified |
| Demo fallback + deploy_check flag | ✅ | `test_demo_fallback` (7 tests); `deploy_check.py --live` against a local LIVE server with a wrong key on the Meta API test double → FAIL "LIVE repair silently used demo answers for: object_report, diagnosis"; with the right key → READY, "no smoke session needed the demo fallback" (2026-10-31) |
| Impact trial kit | ✅ (mock data) | `test_impact` (9 tests); docs/IMPACT.md and docs/img/impact.png are MOCK-stamped |
| Render config lists every setting | ✅ | render.yaml parses; keys incl. MAX_TRACK_FRAMES, TRACK_MIN_INTERVAL_S, DEMO_FALLBACK, IMPACT_TOKEN, PUBLIC_BASE_URL (sync:false) |

**Run numbers (2026-10-31, v1.21.0):** pytest 410 passed, 0 failed (4 chunks: 141 + 88 + 173 fast, 8 slow); `ruff check api scripts` clean; `mypy api` strict no issues in 67 files; `smoke_e2e.py` ALL PASSED (52 PASS lines) on a local mock server; `deploy_check.py` READY on the same server.

## 5c. v1.22.0 features

| Feature | Status | Evidence |
|---|---|---|
| Agent log "What the AI did" (screen) | ✅ | `test_agent_log` (7 tests: full loop logged with tools, red stop / exhausted hand-offs, code gate before any model call, owner words never in the log, cap); jsdom checks per language (no `ag_`/`{` leftovers, the 60 % question explained); Playwright 1-tap test reads the log (muse-spark-1.3, sam-3.1, "Only 55% sure", re-plan line, ≥ 7 loop phases lit) |
| Agent log in the PDF report | ✅ | `test_report_pdf`: strings identical to web/app.js in id/jv/en, every placeholder filled on a full faucet repair with a check and a re-plan, special kinds and bad entries handled; page inspected visually (2026-10-31 11:30 WIB) |
| 1-tap guided demo | ✅ | Playwright `test_one_tap_demo_runs_the_whole_agent_loop` (real Chromium, 390×844): button above the fold, quick answer, dark photo rejected, right photo passes, re-plan; smoke step "1-tap demo sample check photo" |
| Compact tip bar (folds after the first step check) | ✅ / 🟡 | Playwright `test_tip_bar_is_compact_and_collapses_after_first_check`: ≤ 370 px wide, ≤ 60 px chip after the first check, aria-expanded/labels, the button under it still clickable, reopen + close. Real small phones with the keyboard open unverified |
| Prompt-injection hardening | ✅ | `test_injection` (8 tests: invisible/bidi characters stripped, fence can't be closed from inside, id/jv/en signals, re-plan report in the user turn not the system prompt, flagged + logged + not echoed, cannot lift a hard stop, photo-text rule) |
| Cost guards | ✅ | `test_cost_guards` (step checks capped across a re-plan, step-check spend in the session cost, follow-up rate limit in live mode, none in offline sample mode, oversized answer/report refused) |
| WCAG AA contrast, model chips, elapsed timer | ✅ / 🟡 | Chips and timer covered by jsdom/Playwright checks. Contrast was fixed by hand against AA ratios; no automated contrast test |

**Run numbers (2026-10-31 11:40 WIB, v1.22.0):** pytest **453 passed, 0 failed** (`make_test_report.py` one run, 152 s; also in chunks 218 + 225 fast and 10 slow with real Chromium); `ruff check .` clean; `mypy api` strict no issues in 73 files; `smoke_e2e.py` ALL PASSED (60 PASS lines) on a local demo-mode server.

**Run numbers (2026-10-31 14:08 WIB, v1.23.0):** pytest **470 passed, 0 failed** (`make_test_report.py` one run, 202 s); `ruff check .` clean; `mypy api` strict no issues in 76 files; `smoke_e2e.py` ALL PASSED (65 checks, incl. share card PNG and link-preview tags) on a local demo-mode server. New in v1.23 and covered by tests: streaming progress (`progress_view`, no owner words), tappable agent-log lines, share card `card.png` (404 after erase), Open Graph tags, gzip (SSE uncompressed), favicon.

## 5d. v1.24.0 and v1.25.0 features

| Feature | Status | Evidence |
|---|---|---|
| Recorded 1-tap demo when the server sleeps or the phone is offline (v1.24) | ✅ | `test_replay.py`, `test_playwright_replay.py`, `record_replay.py --check`; `27_recorded_demo.png` |
| Laptop view: phone frame + side panel with QR code, 1-tap demo, language switch (v1.25) | ✅ / 🟡 | `test_desk.py`, `test_playwright_desk.py` (1280x800, 1440x900); `29_laptop.png`. Real laptop browsers other than Chromium unverified |
| Static judge build `scripts/build_static.py` → `dist-static/` (v1.25) | ✅ / ⬜ | `test_build_static.py`, `test_playwright_static.py` (served under a sub-path, fails on any `/api/` request). Not hosted yet |
| Red-team eval `scripts/run_eval.py` → docs/EVAL.md (v1.25) | ✅ (mock / test-double) | `test_run_eval.py`. Safety-stop recall 100% on 33 cases (30 before v1.26.0 added 3 motorbike brake-failure texts), 0 false stops on 17 safe cases, 7/7 injection cases. Found 12 text-gate and 7 plan-guard misses in the v1.24 rules, fixed in `api/pipeline/safety.py`. Live run pending |
| First live run `scripts/first_live_run.py` → docs/LIVE_RUN.md (v1.25) | ✅ (fake) / ⬜ (live) | `test_first_live_run.py` against the Meta API test double (wrong key, no key, report has no key). Real run needs the key |
| Video re-cut: 3 s hook title card, burned-in captions, Muse Image diagram scene (v1.25) | ✅ | 2:57 (177.8 s, ffprobe), X clip 43.5 s, `docs/demo/TIMESTAMPS.txt`, `28_diagram_step.png` (diagram is a demo-mode sample drawing) |

**Run numbers (2026-11-01, v1.25.0 final):** `make_test_report.py` ALL PASSED: pytest **530 passed, 0 failed, 0 skipped** (550 s, real Chromium + jsdom), ruff, check_keys --fake, smoke; `ruff check api scripts` clean; `mypy api` strict no issues in 99 files; `smoke_e2e.py` ALL PASSED (66 checks) on a local demo-mode server.

**Run numbers (2026-11-01, v1.25.3):** `make_test_report.py` ALL PASSED: pytest **550 passed, 0 failed, 0 skipped** (445 s, real Chromium + jsdom), ruff, check_keys --fake, smoke; `mypy api` strict no issues in 103 files; `smoke_e2e.py` ALL PASSED on a local demo-mode server. New and covered: first-screen language by phone / `?lang=`, Back / Forward button handling, thumb-sized small links (1.25.2), refusals of a wrong file in the owner's language and an at-once refusal of a non-photo (1.25.3).

**Run numbers (2026-11-01, v1.25.7):** `make_test_report.py` ALL PASSED: pytest **620 passed, 0 failed, 0 skipped** (about 584 s on a 2-CPU test machine), ruff, check_keys --fake, smoke; `mypy api` strict no issues in 105 files. New and covered: street Indonesian / Javanese wording in the text gate and 8 more plan-guard rules (49 tests in `test_safety.py`); screen-reader names in id/jv/en (7 Chromium tests).

## 5e. v1.27.0 features

| Feature | Status | Evidence |
|---|---|---|
| WhatsApp channel: Cloud API webhook (Graph API v26.0) on the same engine and safety gate; photos + text or voice in; SAM-marked photo, diagnosis, step buttons, camera checks, re-plan, red stop and PDF out, in id/jv/en | ✅ (Graph API test double) / ⬜ (real number) | `test_whatsapp.py` (34 tests, incl. `X-Hub-Signature-256` check) against `api/tests/doubles/fake_graph.py`. A real WhatsApp number needs the Meta app setup in docs/WHATSAPP.md |
| WhatsApp simulator `/wa` (labelled), linked from the first screen in id/jv/en only when the server says it is on; absent from the static build | ✅ | `test_owner_token.py`, `test_playwright_owner.py` (link in 3 languages opens /wa), `test_playwright_wa.py`, `test_playwright_replay.py` (`?replay=1` sends no `/api/` request, incl. the simulator check); `30_whatsapp_*.png` |
| Owner token: only the phone that started a repair can set the outcome or erase it; a guide-link holder gets 403 even via the API; no GET returns the token; pre-1.27 repairs still work | ✅ | `test_owner_token.py` (15 tests), `test_outcome.py`, `test_erase.py`, `test_playwright_owner.py` (second Chromium phone gets 403, owner's button works) |
| render.yaml lists the four optional WhatsApp secrets (`sync: false`, empty keeps the channel off) | ✅ | `test_owner_token.py` (render.yaml parsed) |
| Demo video with a 12 s WhatsApp scene in Basa Jawa at 2:16 | ✅ | 2:55 (175.7 s, ffprobe), X clip 43.5 s, `docs/demo/TIMESTAMPS.txt`, `test_demo_video.py` |

**Run numbers (2026-11-02, v1.27.0):** `make_test_report.py` ALL PASSED: pytest **768 passed, 0 failed, 0 skipped** (687 s, real Chromium + jsdom), ruff, check_keys --fake, smoke; `ruff check api scripts` clean; `mypy api --strict` no issues in 132 files; `record_replay.py --check` up to date; `build_static.py --check` OK; `smoke_e2e.py` ALL PASSED (70 checks) on a `OFFLINE=1` server; `run_eval.py` (app 1.27.0): diagnosis 9/9, stop recall and precision 100%, injection 7/7 (offline and test-double).

**Re-run for v1.27.1 (2026-11-02; docs, video captions and test file names changed, no app code):** `make_test_report.py` ALL PASSED: pytest **768 passed, 0 failed, 0 skipped** (1102 s on a busy 2-CPU box); `ruff check api scripts` clean; `mypy api --strict` no issues in 132 files; `smoke_e2e.py` ALL PASSED (70 checks); `record_replay.py --check` up to date; `build_static.py --check` OK; `run_eval.py` (app 1.27.1) gives the same results. Demo video still 2:55 (175.7 s by ffprobe), X clip 43.5 s.

## 5f. v1.28 and v1.29 features

| Feature | Status | Evidence |
|---|---|---|
| New look (bengkel-sign design): Barlow served from `web/fonts` (no font CDN), Lucide icons instead of emoji on screen, safety colours with one meaning each, light and dark theme from the phone | ✅ | `test_web.py` (every emoji the screen can show has an icon, fonts and both licences ship, nothing from a font CDN); screenshots re-made |
| AI-generated sample photos for all five scenarios, labelled on the picture and in EXIF, with hand-drawn part masks | ✅ | `test_fixtures.py` (16 labelled fixtures), `scripts/make_fixtures.py`, `api/pipeline/sample_masks.json`; docs/EVAL_REPORT.md 10/10 photos and 5/5 step checks (mock) |
| Demo video re-shot on the new UI | ✅ | 2:53 (173.5 s by ffprobe), 1920x1080 at 60 fps, WhatsApp scene at 2:13; X clip 43.5 s, 1080x1920 at 60 fps; `docs/demo/TIMESTAMPS.txt`, `test_demo_video.py` |
| PDF report, workshop sheet and share cards in the app's look; link preview `web/og.png` about 170 KB so WhatsApp shows it | ✅ | `api/render/brand.py`, `test_report_pdf*.py`, `test_share_card.py` |
| Friendly page for an expired or erased guide link (id/jv/en, still 404); readable server errors; `HEAD /` for uptime monitors; laptop side panel links the WhatsApp simulator | ✅ | `test_gone_page.py`, `test_playwright_desk.py` |
| A shared guide link to a red stop shows the STOP card and its "do this now" list | ✅ | `test_playwright_guide.py::test_red_stop_guide_link_shows_the_stop_card` |
| Strict Content-Security-Policy on every HTML page (no inline script, no eval), HSTS only behind https; WhatsApp simulator script moved to `web/wa.js` | ✅ | `test_csp.py`, `test_headers.py` |
| Accessibility: axe-core finds nothing serious or critical on the home, progress, question, result, stop, shared guide, WhatsApp simulator and laptop screens; one h1 per screen; native file inputs in the tab order | ✅ (Chromium) / 🟡 (real TalkBack) | `test_playwright_a11y.py` (needs axe-core from npm, skips without it), `test_a11y_buttons.py` |
| No gzip for files that are already packed (fonts, photos, PNG, audio, PDF); offline cache `tukang-shell-v17` | ✅ | `test_gzip.py`, `web/sw.js` |

**Run numbers (2026-11-03, v1.29.4):** `make_test_report.py` ALL PASSED: pytest **823 passed, 0 failed, 0 skipped** (818 s, real Chromium in 18 Playwright test files + jsdom), ruff, check_keys --fake, smoke; `mypy api --strict` no issues in 141 files; `smoke_e2e.py` ALL PASSED (69 checks; 70 in 1.27 with the same script, since some checks only run when a scenario has a follow-up question, a parts image or a diagram step) on a demo-mode server; `run_eval.py` (app 1.29.4): diagnosis 9/9, step and edge-case checks 6/6, stop recall and precision 100%, injection 7/7 (offline and test-double).

## 5g. v1.29.6 to v1.29.13 features

These came from playing every flow again on a 390x844 phone and a laptop in all three languages, mostly in Basa Jawa.

| Feature | Status | Evidence |
|---|---|---|
| After "Still broken" the PDF report and the mechanic brief list the attempt in the owner's language; the cause being tried is "being tried now", not "already tried"; the link preview says "Plan 2 of 3, being tried now" | ✅ | `test_replan_report.py`, `test_brief_now.py` |
| Causes already tried are greyed out and struck through with a red "tried" label in the PDF, like on the phone; the PDF never ends with a page holding only the last line of the disclaimer | ✅ | `test_report_tried_and_jv_words.py`, `test_report_tail.py` |
| The red stop's "Do this now" list fits the hazard: gas, house wiring and brakes keep their own lists, a rice cooker, another appliance or a water pump gets "unplug it and let it cool, don't open the casing (220V inside), take it to a service centre" | ✅ | `test_playwright_kind_safety.py`, `11_rice_stop.png`, video 2:04 |
| The two "Safety first" lines on the guide fit the kind of repair (motorbike, tap, pump, appliance; anything else keeps the general pair) | ✅ | `test_playwright_kind_safety.py`, `15_preflight.png` |
| A shared guide link opened after a re-plan shows the "Plan 2 of 3" banner; after "Still broken" focus moves to that banner | ✅ | `test_playwright_guide.py`, `test_playwright_replan_stop.py` |
| The red stop has one nearest-service button; "See the message it sends" and every other fold-out has an open/close chevron; My garage says "0/4 camera-checked" and "plan 2" | ✅ | `test_playwright_replan_stop.py`, `22_stop_handoff.png`, `14_garage_jv.png` |
| Tools and parts each link to Tokopedia and Shopee by name on one row ("Compare prices on ..." for screen readers) | ✅ | `test_playwright_share_shop_tour.py`, `04_diagnosis.png` |
| Share on a laptop (no share sheet) writes "Link copied:" and the link in a line under the button, or just the link when the clipboard is blocked; no alert() or prompt() | ✅ (Chromium) | `test_playwright_share_shop_tour.py` |
| /static files send Cache-Control: fonts and ?v= URLs a year (immutable), pictures and the QR library a day, app code revalidated on every load | ✅ | `test_static_cache.py`, DECISIONS D12 |
| Basa Jawa in one register (ngoko) across the app, the PDF and the workshop sheets; "keslametan" for safety everywhere | ✅ (word lists) / 🟡 (a native speaker has not read every screen) | `test_jv_register.py`, `test_report_tried_and_jv_words.py` |
| Screenshots, hero GIF, thumbnail, demo video and X clip re-made on these screens; offline cache `tukang-shell-v21` | ✅ | `docs/demo/`, `web/sw.js` |

**Run numbers (2026-11-04, v1.29.13, commit 6ad8f0a):** `make_test_report.py` ALL PASSED: pytest **894 passed, 0 failed, 0 skipped** (961 s, real Chromium in 21 Playwright test files + jsdom), ruff, check_keys --fake, smoke; `mypy api --strict` no issues in 150 files; `smoke_e2e.py` ALL PASSED (69 checks) on a demo-mode server; `run_eval.py` (app 1.29.13): diagnosis 9/9, stop recall and precision 100%, injection 7/7 (offline and test-double), the same results as 1.29.4. Demo video 2:53 (173.5 s by ffprobe, 1920x1080 at 60 fps, scene times unchanged), X clip 43.5 s.

## 5h. v1.30.0: sample step check and the live recording

| Feature | Status | Evidence |
|---|---|---|
| "Sample photo: plug cap on" is checked on the step the photo shows (`sample_step` from api/sample_step.py, stored per plan in the recording), the step card moves there and a line says "Checking step N with this sample photo"; "Sample photo: too dark" is checked on the open step | ✅ | `test_sample_step.py`, `test_replay.py`, `test_playwright_replay.py`, `test_playwright_static.py` |
| (Recording of 6 Nov 2026, 01:23 WIB, replaced in 1.33.0) In that live recording the plug cap photo passes on its step in every language and plan: id steps 6 and 5, jv steps 6 and 5, en steps 5 and 4; the dark photo fails on every step | ✅ | `web/replay/demo.json`, `test_replay.py` |
| (Same replaced recording) The follow-up question asks one yes/no thing (live): id "Apakah suara starter terdengar lemah atau lambat dibanding biasanya?", jv "Sawise distarter bola-bali, knalpot mambu bensin mentah ora?", en "Is there petrol in the tank above empty?" | ✅ | `web/replay/demo.json` |
| WhatsApp simulator label in Bahasa and Basa Jawa matches the English line ("menjalankan" / "nglakokake mesin ...") | ✅ | `test_playwright_wa.py` |

**Run numbers (2026-11-06, v1.30.0):** pytest without a browser **838 passed, 0 failed** (97 files, one by one), Playwright **127 passed, 0 failed** (22 files, real Chromium), ruff clean, `mypy api --strict` no issues in 162 files, `smoke_e2e.py` ALL PASSED (69 checks) on an `OFFLINE=1` server, `build_static.py` and `--check` OK, `record_replay.py --check` up to date. The live recording cost $0.70 by the app's own meter (pipelines, re-plans and 66 step checks in three languages).

## 5i. v1.31.0 UI pass and v1.31.1 media

| Feature | Status | Evidence |
|---|---|---|
| 1.31.0 UI pass (view transitions, step slide, placeholders, busy buttons, layout fixes at 360 px) | ✅ (Chromium) / 🟡 (real phones) | `test_playwright_layout.py`, `test_playwright_motion.py`, `test_ui_motion.py`; CHANGELOG 1.31.0 |
| Recorded demo hand-off links point at the site you are on (were `http://testserver/...`); offline cache `tukang-shell-v25` | ✅ | `test_playwright_replay.py::test_recorded_hand_off_links_point_at_this_site` |
| 28 phone screenshots re-shot on the 1.31.0 screens from recorded live answers (1-tap demo recording and live sessions recorded on 6 Nov 2026), the live camera guide shot live; every shot looked at | ✅ | `docs/demo/screenshots/`, `scripts/make_demo_assets.py` (recorded mode) |
| Demo video and X clip re-made from the same recordings; every frame looked at (one every 2 s); loudness and silence measured | ✅ | Main video 2:54 (174.1 s by ffprobe), 1920x1080 at 60 fps, 34.2 MB; loudness -16.0 LUFS integrated, true peak -3.9 dBFS (ffmpeg ebur128); the only silence of 1 s or more below -40 dB is the last 1.6 s on the close card (ffmpeg silencedetect). A speech-to-text pass (faster-whisper tiny.en) on the voice-over found 402 of the 424 script words (94.8%); the misses are proper nouns (Tukang, bengkel, Muse Spark). X clip 43.5 s, 1080x1920, 12.1 MB, every frame of its contact sheets looked at. Live spend for making the media: about $0.34 by the app's own meter |

**Run numbers (2026-11-06, v1.31.1):** pytest without a browser **858 passed, 0 failed, 0 skipped** (99 files, one by one), Playwright **147 passed, 0 failed, 0 skipped** (24 files, real Chromium, one by one), 1005 in total, the same count `make_test_report.py` got on the whole suite in one run (docs/TEST_REPORT.md); the jsdom flow and the axe-core check ran (not skipped); ruff clean; `mypy api --strict` no issues in 166 files; `smoke_e2e.py` ALL PASSED (69 checks) on an `OFFLINE=1` server; `build_static.py` and `--check` OK; `record_replay.py --check` up to date. No live API calls in this pass. GitHub Actions CI is green again from 09fa5f1 on (the failures before it were the demo video test running on commits without the MP4s).

## 5j. v1.32.0 weakness hunt

| Finding (ranked by user impact) | Status | Evidence |
|---|---|---|
| Two writers on one repair overwrote each other: a second "Still broken" while one was planning was accepted and then lost (confirmed on 5d9dd75) | ✅ | `test_races.py::test_a_second_replan_while_one_is_planning_is_busy` |
| A step check finishing after "Still broken" ticked the same step of the new plan | ✅ | `test_races.py::test_a_check_that_finishes_after_a_replan_is_not_put_on_the_new_plan` |
| Parallel photo checks got past `MAX_STEP_CHECKS`; two checks on one step overwrote each other's photo; a failed check now gives its count back | ✅ | `test_parallel_checks_cannot_get_past_the_photo_check_cap`, `test_two_checks_on_one_step_keep_both_photos`, `test_a_failed_check_gives_its_count_back` |
| Step checks and the live guide accepted on a red stop (confirmed on 5d9dd75); re-plan from any status | ✅ | `test_steps_and_live_guide_are_refused_off_the_steps`, `test_replan_only_from_a_plan_on_screen` |
| A second start or two quick Try again taps ran the repair twice | ✅ | `test_a_second_start_does_not_run_a_finished_repair_again`, `test_two_quick_retries_make_one` |
| Live-guide frame and "It works now" during a re-plan | ✅ | `test_live_guide_frame_during_a_replan_waits_its_turn`, `test_it_works_now_during_a_replan_is_busy` |
| A server restart left a repair at "running" forever | ✅ (offline) / 🟡 (Render restart) | `test_a_repair_left_running_by_a_restart_becomes_retryable`, `test_server_start_runs_the_recovery`, Chromium `test_a_repair_a_restart_interrupted_comes_back_with_try_again` |
| The live photo check ran on the event loop and stalled the server | ✅ | `test_step_check_runs_off_the_event_loop` |
| Lock, erase-mark, throttle and folder leaks on a long-running server; erase during an open progress stream | ✅ | `test_erase_and_janitor_drop_the_lock_and_erase_marks`, `test_janitor_drops_locks_of_expired_sessions`, `test_janitor_removes_half_made_folders_and_stale_tmp_files`, `test_progress_stream_ends_cleanly_when_the_repair_is_erased` |
| Shared guide link could re-plan, check, track, answer and spend through the API (confirmed on 5d9dd75: re-plan without a token was 200) | ✅ | `test_owner_routes.py::test_every_route_that_changes_a_repair_needs_the_owner_token` (6 routes), `test_the_app_sends_the_owner_token_on_each_of_those_routes`, smoke checks "refused without the owner token" |
| Rate limit skipped with a made-up X-Forwarded-For (confirmed on 5d9dd75) | ✅ (code) / ⬜ (Render header not checked live) | `test_rate_limit_key_is_the_address_our_proxy_wrote`, `test_a_spoofed_header_no_longer_skips_the_limit`, `test_a_header_the_edge_proxy_overwrites_wins` |
| Erasing a repair took its spend out of the daily cap (confirmed on 5d9dd75) | ✅ | `test_erasing_a_repair_keeps_its_spend_in_the_daily_cap` |
| No cache rule on the owner's photos and JSON; Unicode session ids; a bomb on the step check answered "AI busy" | ✅ | `test_private_repair_data_is_never_cached`, `test_session_ids_are_ascii_letters_and_digits`, `test_a_bomb_on_the_step_check_is_400_not_503` |
| Console errors on any main screen; progress on a throttled connection; English in the id/jv tables | ✅ (Chromium) | `test_playwright_screens_clean.py`, `test_i18n.py::test_no_english_string_shows_in_bahasa_or_basa_jawa` |
| test_doc_counts.py had stopped checking (3-digit pattern, 4-digit count) | ✅ | `test_doc_counts.py::test_the_pattern_reads_four_digit_counts` |
| Disk full during a run leaves the repair at "running" until the next restart | ⬜ (not fixed) | Nothing can be written while the disk is full; `recover_interrupted` marks it retryable at the next start |

**Run numbers (2026-11-06 10:29 WIB, v1.32.0, commit 29823cd):** `make_test_report.py` ALL PASSED on the whole suite in one run: pytest **1096 passed, 0 failed, 0 skipped** (945 without a browser in 103 files, 151 in real Chromium in 25 Playwright files; the jsdom flow and the axe-core check ran, not skipped), ruff clean, `check_keys.py --fake` and the run's own demo-server smoke passed (docs/TEST_REPORT.md). Separately: `mypy api --strict` no issues in 171 files; `smoke_e2e.py` ALL PASSED (77 checks) on an `OFFLINE=1` server on port 8765; `scripts/check_voice.py` 0 hits. No live API calls in this pass.

## 6. What is not verified yet

1. Live Meta answers: the sample scenarios ran on the real API on 5 November 2026 (docs/LIVE_RUN.md) and the recorded 1-tap demo was recorded live on 6 November 2026. Real-photo quality is still item 2.
2. Real-photo quality: SAM hit rate on real bikes/pumps, diagnosis accuracy, step-check judgement, live-tracking quality. → real photos + 5 user trials (docs/USER_TRIAL_KIT.md).
3. Real phones: rear camera over https (iOS needs playsinline + https), SpeechRecognition with jv-ID, WhatsApp deep link, HEIC upload, TalkBack, airplane mode. So far I've only used headless Chromium and jsdom.
4. The Render deployment has not run. The container was only emulated (no Docker on the test machine). GitHub Actions CI does run on every push (section 5i).
5. The impact numbers are mock until the real trials run.
6. The demo video plays real Meta API answers recorded on a live run (6 Nov 2026), not answers made while filming, on AI-generated sample photos and Chromium's test camera feed. All of it is labelled on screen.
7. The WhatsApp channel has only run against a Graph API test double and in the `/wa` simulator; no real WhatsApp number has sent or received a message (needs the Meta app setup in docs/WHATSAPP.md).

## 1.33.0 media remake: live re-recording on the new sample photos (6 Nov 2026)

| Check | Status | Evidence |
|---|---|---|
| 1-tap demo re-recorded live (14:01 WIB), one take per language: top cause "plug cap off the spark plug" at 85% (id), 88% (jv), 88% (en), amber safety, no follow-up question; re-plan goes to the second cause (fouled or worn plug) | ✅ | `web/replay/demo.json`, `test_replay.py` |
| The plug cap photo passes on its step in every language and plan (id steps 4 and 6, jv 5 and 6, en 4 and 6); the dark photo fails on every step | ✅ | `web/replay/demo.json`, `test_replay.py` |
| Live sessions for the screenshots: pump (id) "pump lost its prime" 75%; rice cooker (id) red stop by the model (220 V, opening the body), top cause "plug not in the socket" 75%; faucet (en) "worn washer or cartridge seal" 85% with a Muse Image diagram on step 5; tyre (jv) "slow leak from a nail" 88% | ✅ | recorded session folders (outside the repo), `docs/demo/screenshots/` |
| Spend of the remake by the ledger that wraps the app's cost meter: $0.9405 of the $1.00 cap (first failed take $0.163, recording $0.604, four sessions $0.173) | ✅ | stage notes |
| `record_replay.py --check` up to date; test_replay, test_playwright_replay, test_playwright_static, test_build_static, test_fixtures, test_sample_masks, test_sample_step, test_whatsapp pass; `build_static.py --check` OK | ✅ | this run |

