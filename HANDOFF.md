# Handoff

Read this first if you are picking up Tukang Copilot (human or AI).

## State on 2026-11-01 14:20 WIB (v1.25.1): submission-ready, waiting on Malik's steps
- **New since 1.25.0 (audit 7, `../work/IMPROVEMENT_BACKLOG.md` L1 to L3):** the first screen follows the phone's language (an English-speaking judge no longer lands on Bahasa; Indonesian or Javanese anywhere in the phone's language list keeps Bahasa / Basa Jawa; `?lang=id|jv|en` overrides; the saved choice wins) and the phone Back button returns to the first screen instead of leaving the site (Forward resumes the same repair; Start again / Erase step back). 9 new real-Chromium tests (`test_playwright_lang.py`, `test_playwright_back.py`). The demo-asset script pins id-ID so screenshots/video are unchanged (the UI otherwise looks the same, so no re-shoot). Details: CHANGELOG 1.25.1.
- **Checks (real runs, 2026-11-01 ~14:15 WIB):** `make_test_report.py` ALL PASSED: pytest **539 passed, 0 failed, 0 skipped** (527 s, Chromium at /tmp/bin/chromium + jsdom at /tmp/jd), ruff, check_keys --fake, smoke; `mypy api` strict no issues in 101 files; `smoke_e2e.py` ALL PASSED on `MOCK=1 PORT=8765 python app.py`; `run_eval.py` regenerated (app 1.25.1). Fast `-m "not slow"` = 510, slow = 29.
- **Sandbox restore (Debian trixie arm64, no root):** `apt-get -o Dir::State::Lists=/tmp/apt/lists -o Dir::Cache=/tmp/apt/cache -o Debug::NoLocking=1 update`, then the same options with `download` for the Chromium package list in the 1.24.0 state below, `dpkg-deb -x` into /tmp/chr, wrapper /tmp/bin/chromium; `npm install --prefix /tmp/jd jsdom`; `pip install weasyprint` for the one-pager / bundle PDFs (one-pager: `pandoc docs/launch/ONE_PAGER.md -f markdown -t html5 -s --embed-resources --css docs/launch/one-pager.css`, then weasyprint with base_url docs/launch).
- **Honest status:** unchanged: no live Meta answer verified yet (needs the key); demo assets and the recorded demo are demo mode; eval numbers are mock / fake-model.

## State on 2026-11-01 12:30 WIB (v1.25.0): submission-ready, waiting on Malik's steps
- **New since 1.24 (code lane C1 to C5):** laptop view (>= 1024 px: phone frame + side panel with QR code of the current URL, 1-tap demo, id/jv/en switch); static judge build `scripts/build_static.py` → `dist-static/` (gitignored, recorded demo, no server, relative paths, NOT deployed; instructions in `--help`); offline eval `scripts/run_eval.py` → `docs/EVAL.md` (mock + fake-model, labelled, live pending) which found 12 of 20 red-team texts and 7 of 10 dangerous plan steps slipping past the v1.24 safety gate, now fixed (100 % recall, 0 false stops on 17 safe cases, 7/7 injection cases); `scripts/first_live_run.py` (one command after set_keys.py, writes `docs/LIVE_RUN.md`, `--fake` rehearsal); video re-cut with a 3 s hook title card (hackathon dates), burned-in English captions and a Muse Image diagram scene (**2:57**, X clip 43.5 s, scene times in `docs/demo/TIMESTAMPS.txt`, new shots 28/29). Details: CHANGELOG 1.25.0.
- **Checks (real runs, 2026-11-01 ~13:00 WIB, final 1.25.0):** `make_test_report.py` one run: **ALL PASSED**, pytest **530 passed, 0 failed, 0 skipped** of 530 (550 s, real Chromium at /usr/bin/chromium + jsdom at /tmp/jd), ruff, check_keys --fake, smoke (docs/TEST_REPORT.md). The once-flaky `test_agent_log_lines_jump_to_what_they_describe` now waits on conditions (15 to 20 s), no sleeps. `run_eval.py` regenerated docs/EVAL.md (header app 1.25.0). `ruff check api scripts` clean; `mypy api` strict no issues in 99 files; no-em-dash tests pass; `smoke_e2e.py` ALL PASSED (66 checks) on `MOCK=1 PORT=8765 python app.py` with `NO_PROXY=127.0.0.1,localhost`. Pytest in chunks if needed: `-m "not slow"` = 501, `-m slow` = 29.
- **Docs reconciled (1.25.0 wrap-up):** YouTube chapters and JUDGING_MAP times follow `docs/demo/TIMESTAMPS.txt`; 29 screenshots; X clip 43.5 s; EVAL / laptop view / static build / first_live_run added to SUBMISSION, JUDGING_MAP, JUDGE_FAQ (Q11); test counts 539 everywhere; one-pager PDF re-made (1 page); thumbnail unchanged (its text did not change).
- **Deliverables:** `../docs-out/`: `tukang-copilot.zip` (git archive HEAD), `Tukang-Copilot-Guide-Bundle.pdf` (now 13 docs: + JUDGING_MAP, EVAL, JUDGE_FAQ), `one-pager.pdf`, `thumbnail.png`, both demo mp4s; `dist-static/` rebuilt (not hosted).
- **Honest status:** unchanged: no live Meta answer verified yet (needs the key); demo assets, the recording and the static build are demo mode; eval numbers are mock / fake-model; impact numbers are MOCK.

## State on 2026-11-01 WIB (v1.24.0): submission-ready, waiting on Malik's steps
- **New since 1.23:** recorded 1-tap demo (backlog J5): when the free Render server is asleep (no `/api/health` answer within 4 s), offline, or with `?replay=1`, the demo plays a recorded demo-mode run from `web/replay/` (made by `scripts/record_replay.py`; `--check` and `test_replay.py` catch drift), labelled "▶ Recorded demo" on screen; own photos are refused, never faked; the service worker pre-caches it and shows the cached shell after 3.5 s. Skeptical-judge audit 5 (screens in id/jv/en at 390x844, a 1280x800 laptop, keyboard-only, slow 3G; 14 scored findings in `../work/IMPROVEMENT_BACKLOG.md`): red stop now on screen under a "Stopped for your safety" heading, result opens at the top, "🔁 Plan 2 of 3" banner after a re-plan, focus to the quick answers, PDF says "Cause worked on", language-neutral landing picture, demo check names what it confirmed, laptop note, one PDF button on the stop card, `/api/health` shows the full version. Demo kit re-made: 27 screenshots (new `27_recorded_demo.png`), **2:57** video, 45 s X clip, GIF. Details: CHANGELOG 1.24.0.
- **Checks (real runs, 2026-11-01):** see docs/TEST_REPORT.md (`make_test_report.py`, one run: pytest **496 passed, 0 failed, 0 skipped** in 241 s with Chromium + jsdom, ruff, check_keys --fake, smoke ALL PASSED); `ruff check api scripts` clean; `mypy api` strict no issues in 84 files; `smoke_e2e.py` ALL PASSED (66 checks, new: recorded demo served) on `MOCK=1 PORT=8765 python app.py` with `NO_PROXY=127.0.0.1,localhost`. Pytest in chunks under the 120 s tool limit: `-m "not slow"` (475, ~105 s, split by file if needed), then `test_playwright_smoke.py` (12, ~70 s) and the other 4 browser files (9, ~100 s) with Chromium on PATH.
- **Sandbox restore (fresh box):** `pip install -r requirements-dev.txt`; Chromium: `apt-get download chromium chromium-common libopenh264-8 libatk1.0-0t64 libatk-bridge2.0-0t64 libdouble-conversion3 libharfbuzz-subset0 libxnvctrl0 libxcomposite1 libxdamage1 libatspi2.0-0t64 libminizip1t64` in a temp dir, `dpkg-deb -x` each into `/tmp/chr`, wrapper `/tmp/bin/chromium` that sets `LD_LIBRARY_PATH=/tmp/chr/usr/lib/chromium:/tmp/chr/usr/lib/aarch64-linux-gnu` and execs `/tmp/chr/usr/lib/chromium/chromium`; jsdom: `npm install --prefix /tmp/jd jsdom`.
- **Deliverables:** `../docs-out/tukang-copilot.zip` (git archive of the 1.24.0 wrap-up commit) and `../docs-out/Tukang-Copilot-Guide-Bundle.pdf` (same 10 docs) rebuilt 2026-11-01.
- **Honest status:** unchanged: no live Meta answer verified yet (needs the key); demo assets and the recorded demo are demo mode; impact numbers are MOCK. A brand-new visitor to a sleeping Render URL still waits for the page itself (the recording helps once the page has loaded or is cached).

## State on 2026-10-31 14:30 WIB (v1.23.0): submission-ready, waiting on Malik's steps
- **New since 1.22:** streaming progress (each stage's result appears as it finishes: what Muse Spark saw, the SAM 3.1 outlines, the top cause with confidence + safety level, step count; SSE carries a trimmed `progress_view`, no owner words); tappable agent log (each line jumps to the stage, photo, causes, safety list, hand-off or exact camera-checked step; checks from an earlier plan aren't linked); share card `GET /api/sessions/{id}/card.png` + Open Graph/twitter tags on guide pages and `web/og.png` on the front page; gzip for static files (app.js 90 KB → ~29 KB); favicon; follow-up question scrolled on screen. Demo kit re-made: 26 screenshots, **2:57** voice-over video, 45 s vertical X clip, README GIF. Details: CHANGELOG 1.23.0.
- **Checks (real runs, 2026-10-31 14:08 WIB):** pytest **470 passed, 0 failed** (`make_test_report.py`, 202 s); `ruff check .` clean; `mypy api` strict no issues in 76 files; `smoke_e2e.py` ALL PASSED (65 checks, incl. share card PNG + link-preview tags; demo server `MOCK=1 PORT=8765 python app.py`, `NO_PROXY=127.0.0.1,localhost`).
- **Deliverables:** `../docs-out/tukang-copilot.zip` (git archive of the v1.23.0 wrap-up commit) and `../docs-out/Tukang-Copilot-Guide-Bundle.pdf` (same 10 docs as before) rebuilt 2026-10-31.
- **Honest status:** unchanged: no live Meta answer verified yet (needs the key); demo assets are demo mode; impact numbers are MOCK.

## State on 2026-10-31 11:45 WIB (v1.22.0): feature-complete for submission
- **New since 1.21:** agent log "What the AI did" (screen + PDF), 1-tap guided demo with a compact tip bar that folds after the first step check, prompt-injection hardening (`api/untrusted.py`), cost guards (`FOLLOWUP_RATE_PER_HOUR`, `MAX_STEP_CHECKS`), Javanese demo answers, model chips + timer on progress, WCAG AA contrast, faster overlay, README rewrite, regenerated screenshots/2:53 video/GIF. Details: CHANGELOG 1.22.0. Ranked backlog: `../work/IMPROVEMENT_BACKLOG.md`.
- **Checks (real runs, 2026-10-31 11:40 WIB):** pytest **453 passed, 0 failed** (`make_test_report.py`, 152 s in one run; in chunks: `-m "not slow"` over 2 file groups = 218 + 225, `-m slow` = 10 with Chromium at /tmp/bin/chromium on PATH); `ruff check .` clean; `mypy api` strict no issues in 73 files; `smoke_e2e.py` ALL PASSED (60 PASS lines; port 8000 in this sandbox belongs to another app, so start a demo server with `MOCK=1 PORT=8765 python app.py` and pass `http://127.0.0.1:8765`, with `NO_PROXY=127.0.0.1,localhost`).
- **Deliverables:** `../docs-out/tukang-copilot.zip` (git archive of the v1.22.0 wrap-up commit: no .env, .git, caches or data) and `../docs-out/Tukang-Copilot-Guide-Bundle.pdf` (README, SETUP_FOR_MALIK, HOW_TO_USE, DEPLOY, SUBMISSION, WRITEUP, USER_TRIAL_KIT, VERIFICATION_REPORT, HANDOFF, TODO; pandoc → weasyprint, emoji shown as plain symbols) rebuilt 2026-10-31.
- **Honest status:** unchanged: no live Meta answer verified yet (needs the key); demo assets are demo mode; impact numbers are MOCK.

## State on 2026-10-31 09:30 WIB (v1.21.0)
- **New since 1.20 (win plan lanes A/B/C):** live camera guide (SAM 3.1 on camera frames, `POST /steps/{n}/track`), hands-free voice commands (`POST /command` push-to-talk fallback), bengkel hand-off (`GET /handoff`: WhatsApp + Maps + mechanic brief PDF), `DEMO_FALLBACK`, impact trial kit, Render free-plan deploy readiness, `scripts/deploy_check.py` (in LIVE mode it FAILs any session that silently used demo answers), regenerated demo kit (22 screenshots, 2:50 video, 45 s vertical clip, captions + voice-over), docs/WRITEUP.md, a field-by-field docs/SUBMISSION.md for the Cerebral Valley form. Details: CHANGELOG 1.21.0.
- **Checks (real runs, 2026-10-31):** pytest **410 passed, 0 failed** (run in chunks under 110 s: `-m "not slow"` split over 3 file groups = 141 + 88 + 173, then `-m slow` = 8); `ruff check api scripts` clean; `mypy api` strict no issues in 67 files; `smoke_e2e.py` ALL PASSED on a local mock server (set `NO_PROXY=127.0.0.1,localhost`); `deploy_check.py` READY (mock), and in LIVE mode against the fake Meta server: wrong key → FAIL fallback flagged, right key → READY.
- **Sandbox tips:** the full suite takes ~4 min, so split it (see above or `../work/run_tests.sh`). Demo assets: `python scripts/make_demo_assets.py shots|diagram|voice|video` (video takes ~3 min, so run it with nohup; segments are cached in `$TMPDIR/tukang-video`, delete that after changing screenshots). edge-tts needs the env proxy removed (the script does that unless `EDGE_TTS_PROXY` is set).
- **Honest status:** no live Meta answer has been verified yet. Demo assets are demo mode (labelled stand-in photos, recorded answers, Chromium fake camera). Impact numbers are MOCK.

## State on 2026-10-31 08:20 WIB (v1.20.0)
- **New:** "Before you start" safety gate. `Diagnosis.before_you_start` (max 4), tick list on result and shared guide pages, step card dimmed and `inert` until all ticked (ticks kept in localStorage per repair), no hands-free voice while locked, PDF prints the list, prompt asks for it, red stops carry none. Also made the jsdom timer check less timing-sensitive (it flaked once under load: the 500 ms tick can still show 10:00 at 700 ms).
- **Checks (real runs, 08:15 WIB):** ruff clean, `mypy api` strict no issues in 57 files, pytest **289 passed, 6 skipped** (Playwright only; jsdom runs after `npm install --prefix /tmp/jd jsdom`), `node --check web/app.js` ok, `smoke_e2e.py` ALL PASSED, `make_test_report.py` ALL PASSED (289/295). Lock/unlock only jsdom-verified (no Chromium here, so no real-browser check of `inert`); the Playwright smoke does not click inside the step card, so it should be unaffected.
- **Next up (Malik):** after first live key run: eval_fixtures live, tune prompts (check `before_you_start` is short and not generic); re-take screenshots/video when a Chromium exists (preflight card, timer, saving chip, outcome buttons not in current assets); Render preview smoke once deployed.

## State on 2026-10-31 07:55 WIB (v1.19.0)
- **New:** outcome buttons ("It works now" / "Took it to a mechanic"), `POST /api/sessions/{id}/outcome`, PDF Result line, My garage "Total saved" line (localStorage, sums `diy_saving_idr` of repairs marked fixed). SUBMISSION, README, HOW_TO_USE, API docs updated with the 1.11 to 1.19 features that were missing from the write-up.
- **Checks (real runs, 07:50 WIB):** ruff clean, `mypy api` strict no issues in 56 files, pytest **270 passed, 6 skipped** (Playwright only; jsdom runs after `npm install --prefix /tmp/jd jsdom`), `node --check web/app.js` ok, `smoke_e2e.py` ALL PASSED (new outcome step), `make_test_report.py` ALL PASSED (270/276). Outcome UI only jsdom-verified (no Chromium here).
- **Next up (Malik):** after first live key run: eval_fixtures live, tune prompts; re-take screenshots/video when a Chromium exists (timer, saving chip, outcome buttons not in current assets); Render preview smoke once deployed.

## State on 2026-10-31 07:15 WIB (v1.18.0)
- **New:** waiting-time steps (`wait_minutes` on Step; guide countdown timer with vibrate and spoken alert; workshop sheet tick line; coerce `_wait`; prompt line). See CHANGELOG 1.18.0.
- **Checks (real runs, 07:12 WIB):** ruff clean, `mypy api` strict no issues in 55 files, pytest **258 passed, 7 skipped** (Playwright only; jsdom runs with /tmp/jd, incl. 7 new timer checks), `node --check web/app.js` ok, `smoke_e2e.py` ALL PASSED, `make_test_report.py` ALL PASSED. Timer alert on a locked phone screen not testable here.
- **Next up (Malik):** after first live key run: eval_fixtures live, tune prompts (check the model uses wait_minutes sensibly, not on every step); re-take screenshots/video when a Chromium exists (timer and saving chip not in current assets); Render preview smoke once deployed.

## State on 2026-10-31 06:40 WIB (v1.17.1)
- **New:** price sanity in `coerce.py` (k/rb/juta units, implausible values become unknown, no shop price on red stops). See CHANGELOG 1.17.1.
- **Checks (real runs, 06:35 WIB):** ruff clean, `mypy api` strict no issues in 54 files, pytest **247 passed, 7 skipped** (Playwright only; no Chromium downloadable on this arm64 sandbox), `node --check web/app.js` ok, `smoke_e2e.py` ALL PASSED, `make_test_report.py` run.
- **Next up (Malik):** after first live key run: eval_fixtures live, tune prompts; re-take screenshots/video when a Chromium exists; Render preview smoke once deployed.

## State on 2026-10-31 06:10 WIB (v1.17.0)
- **New:** bengkel price vs DIY saving chip and PDF lines (`shop_cost_estimate_idr`, `diy_saving_idr`), PDF total label fixed (parts only). See CHANGELOG 1.17.0. The shop prices in mock mode are illustrative; in live mode they are the model's estimate, so judge them on real runs.
- **Checks (real runs, 06:08 WIB):** ruff clean, `mypy api` strict no issues in 54 files, pytest **236 passed, 6 skipped** (Playwright only), `node --check web/app.js` ok, `smoke_e2e.py` ALL PASSED, `make_test_report.py` ALL PASSED (236/242). PDF page inspected visually.
- **Next up (Malik):** after first live key run: eval_fixtures live, tune prompts (check shop price sanity); re-take screenshots/video when a Chromium exists (new chip not in current assets); Render preview smoke once deployed.

## State on 2026-10-31 05:30 WIB (v1.16.0)
- **New:** HEIC/HEIF (iPhone) upload support via optional `pillow-heif` (`api/pipeline/photos.py`), friendly refusal when the decoder is missing, `.jfif` accepted, 7 tests (`test_photo_formats.py`). See CHANGELOG 1.16.0.
- **Checks (real runs, 05:28 WIB):** ruff clean, `mypy api` strict no issues in 53 files, pytest **226 passed, 7 skipped**, `node --check web/app.js` ok, `smoke_e2e.py` ALL PASSED, `make_test_report.py` ALL PASSED (226/233). pillow-heif must be in the Render build (it is in requirements.txt; wheels exist for linux x86_64/arm64).
- **Next up (Malik):** after first live key run: eval_fixtures live, tune prompts; re-take screenshots/video when a Chromium exists; Render preview smoke once deployed; real phone tests (airplane mode, TalkBack, HEIC) by Malik.

## State on 2026-10-31 05:05 WIB (v1.15.0)
- **New:** weak-signal handling. Friendly id/jv/en network error text on every fetch path (start, answer, check, re-plan, retry), offline banner on home and guide pages, no more stuck "Checking photo..." when the signal drops. jsdom checks added (offline bar show/hide, rejected fetch gives friendly message). See CHANGELOG 1.15.0.
- **Checks (real runs, 05:00 WIB):** ruff clean, `mypy api` strict no issues in 51 files, pytest **220 passed, 6 skipped** (Playwright only; jsdom test now has 108 checks), `node --check web/app.js` ok, `smoke_e2e.py` ALL PASSED, `make_test_report.py` run. Offline behaviour only jsdom-verified (no Chromium here).
- **Next up (Malik):** after first live key run: eval_fixtures live, tune prompts; re-take screenshots/video when a Chromium exists; Render preview smoke once deployed; real phone test of airplane-mode behaviour and TalkBack (Malik).

## State on 2026-10-31 04:40 WIB (v1.14.0)
- **New:** accessibility pass (html lang `jv`, keyboard-reachable pickers, aria-pressed on chips and mic, screen-reader progress status, live regions, focus to new section heading, focus ring, 44 px targets, reduced motion). See CHANGELOG 1.14.0.
- **Checks (real runs, 04:38 WIB):** ruff clean, `mypy api` strict no issues in 51 files, pytest **220 passed, 6 skipped** (Playwright only), `node --check web/app.js` ok, `smoke_e2e.py` ALL PASSED, `make_test_report.py` ALL PASSED (220/226). No Chromium downloadable here, so screenshots and video are unchanged and the a11y changes are only jsdom-verified.
- **Next up (Malik):** after first live key run: eval_fixtures live, tune prompts; re-take screenshots/video with hood panel, tyre, erase button when a Chromium exists; Render preview smoke once deployed; try a real screen reader pass on a phone (Malik: TalkBack on, one repair).

## State on 2026-10-31 04:10 WIB (v1.13.0)
- **New:** hostile input hardening: untrusted-input rule in the four owner-text prompts, jsdom XSS test (poisons all free text of a real session; confirmed it fails when `esc()` is removed), `api/tests/test_security.py` (16 tests: escaping, odd ids, traversal, injection vs code gate). docs/SAFETY.md section added.
- **Checks (real runs, 04:05 WIB):** ruff clean, `mypy api` strict no issues in 51 files, pytest **219 passed, 6 skipped** (Playwright only; jsdom runs after `npm install --prefix /tmp/jd jsdom`), `node --check web/app.js` ok, `smoke_e2e.py` ALL PASSED, `make_test_report.py` ALL PASSED (219/225). No Chromium downloadable here, so screenshots and video are unchanged.
- **Next up (Malik):** after first live key run: eval_fixtures live, check the untrusted-input rule did not change live outputs, tune prompts; re-take screenshots/video with hood panel, tyre, erase button when a Chromium exists; Render preview smoke once deployed.

## State on 2026-10-31 03:35 WIB (v1.12.0)
- **New:** client-side photo shrinking before upload (`shrinkImage` in web/app.js; 1600 px, JPEG 85 percent, falls back to the original on any problem) for the repair photos and the step check photo; Start button disabled during shrinking. Real canvas behaviour is only tested with a stub in jsdom (no Chromium here), so check one real phone upload on 4G.
- **Checks (real runs, 03:33 WIB):** ruff clean, `mypy api` strict no issues in 50 files, pytest **203 passed, 6 skipped** (Playwright only), `node --check web/app.js` ok, `smoke_e2e.py` ALL PASSED, `make_test_report.py` ALL PASSED (203/209).
- **Next up (Malik):** after first live key run: eval_fixtures live, tune prompts; re-take screenshots/video with hood panel, tyre, erase button when a Chromium exists; Render preview smoke once deployed.

## State on 2026-10-31 03:00 WIB (v1.11.0)
- **New:** privacy controls. `DELETE /api/sessions/{id}` + "Delete my photos now" button (id/jv/en); My garage "Clear history" also erases on the server; hourly janitor purges sessions past `RETENTION_HOURS` (before, only at startup, so a long-running Render deploy would have broken the 24 h promise); erased sessions cannot be resurrected by a running worker.
- **Checks (real runs, 02:58 WIB):** ruff clean, `mypy api` strict no issues in 50 files, pytest **203 passed, 6 skipped** (Playwright only; jsdom runs after `npm install --prefix /tmp/jd jsdom`), `node --check web/app.js` ok, `smoke_e2e.py` ALL PASSED (incl. erase step), `make_test_report.py` ALL PASSED (203/209). The erase button's confirm/alert flow is not browser-tested (no Chromium here); jsdom checks that it exists and is translated.
- **Next up (Malik):** after first live key run: run eval_fixtures live, tune prompts; re-take screenshots/video with hood panel, tyre and erase button when a Chromium exists; Render preview smoke once deployed.

## State on 2026-10-31 02:30 WIB (v1.10.0)
- **New:** `scripts/eval_fixtures.py` + `docs/EVAL_REPORT.md` (mock run: 10/10 photos and 3/3 camera checks meet expectations). Live use: `python scripts/eval_fixtures.py https://<app> --out docs/EVAL_REPORT.md`; for real photos put them with a `manifest.json` (same shape as api/tests/fixtures) in a folder and pass `--dir`. Edge case note: in mock mode the unknown-object photo "passes" because the motorbike mock asks a follow-up; the live run is the real test of that.
- **Checks (real runs, 02:25 WIB):** ruff clean, `mypy api` strict no issues in 49 files, pytest **196 passed, 7 skipped** (Playwright/jsdom, no Chromium downloadable here), `node --check web/app.js` ok, `smoke_e2e.py` ALL PASSED, `make_test_report.py` ALL PASSED (196/203).
- **Next up (Malik):** after first live key run: run eval_fixtures live, tune prompts, record numbers in SUBMISSION; re-take screenshots/video with hood panel + tyre when a Chromium exists; Render preview smoke once deployed.

## State on 2026-10-31 02:05 WIB (v1.9.1)
- **New:** four more labelled stand-in fixtures for the tyre scenario (14 total) and `api/tests/test_tire_fixture.py` (flow, follow-up answer, camera check, PDF).
- **Checks (real runs, 02:00 WIB):** ruff clean, `mypy api` strict no issues in 48 files, pytest **195 passed, 6 skipped** (Playwright only; jsdom UI test runs after `npm install --prefix /tmp/jd jsdom`), `node --check web/app.js` ok, `smoke_e2e.py` ALL PASSED, `make_test_report.py` ALL PASSED (195/201).
- **Next up (Malik):** re-take demo screenshots/video with the Under the hood panel and tyre sample when a Chromium exists; Render preview smoke once deployed; prompt tuning on real photos / first live key run. Malik-side steps unchanged.

## State on 2026-10-31 01:45 WIB (v1.9.0)
- **New:** fifth demo scenario, flat scooter tyre with a nail (amber): tubeless plug repair plan, re-plan to a leaking valve stem, SAM masks on tread/valve/rim, id/jv/en text, `samples/tire.jpg`, sample button "ban kempes" / "flat tyre". Marked-parts image inspected visually.
- **Checks (real runs, 01:40 WIB):** ruff clean, `mypy api` strict no issues in 47 files, pytest **190 passed, 6 skipped** (Playwright only; the jsdom UI test now RUNS here after `npm install --prefix /tmp/jd jsdom`, tip: plain `npm install` in /tmp/jd fails with EACCES on `/node_modules`), `node --check web/app.js` ok, `smoke_e2e.py` ALL PASSED (5 scenarios), `make_test_report.py` ALL PASSED (190/196).
- **Next up (Malik):** re-take demo screenshots/video with Under the hood panel and the tyre sample when a Chromium exists; Render preview smoke once deployed; prompt tuning on real photos / first live key run; more stand-in fixtures for the tyre case (`scripts/make_fixtures.py`). Malik-side steps unchanged.

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
| `api/tests/fixtures/` | 14 labelled STAND-IN photos (4 tyre ones added in v1.9.1) (scripts/make_fixtures.py) |
| `docs/demo/` | Demo video, X clip, screenshots (scripts/make_demo_assets.py) |
| `api/render/overlay.py` | SAM masks → numbered overlay |
| `api/pipeline/media.py` | ffmpeg WAV conversion, edge-tts |
| `api/settings.py`, `api/cost.py`, `api/prompts.py` | Config, cost meter, prompt loader |
| `prompts/*.md` | One versioned prompt per stage |
| `api/testing/fake_meta.py` | Fake Meta API for tests and dry runs |
| `api/tests/` | All tests |
| `scripts/` | set_keys, check_keys, first_live_run, smoke_e2e, run_eval (docs/EVAL.md), build_static (dist-static/), make_test_report |
| `web/vendor/qrcode.js` | MIT QR encoder for the laptop side panel (loaded only at >= 1024 px) |
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

## Next up (Malik, once Malik's steps unblock it)
1. After the key: `set_keys.py` ALL GOOD → `first_live_run.py` (docs/LIVE_RUN.md) → `smoke_e2e.py` in LIVE mode with no FALLBACK lines → `eval_fixtures.py` live → tune prompts → update META_API_NOTES ⚠️ items and the "Honest status" lines in WRITEUP/SUBMISSION/VERIFICATION_REPORT.
2. After real photos/trials: replace stand-in fixtures, `scripts/impact_report.py` (real rows), re-shoot screenshots with real photos.
3. After deploy: `deploy_check.py <url> --live`, fill the live/video/X links in README + SUBMISSION, rebuild docs-out/.
4. Resume the paused "Keep building Tukang Copilot" scheduled task only if Malik wants more polish.

## Malik-only (nothing else blocks the submission), in this order
1. **Meta key, then the first live run (top priority).** Stage 1 of judging is pass/fail on real Meta model use. Claim credits + set a spend limit on dev.meta.ai, create a key, run `python scripts/set_keys.py` (paste, Enter) → ALL GOOD, then `python scripts/first_live_run.py` → DONE (one sample repair, a few US cents; writes docs/LIVE_RUN.md).
2. **Optional: Baseten key + one logged open-weights run** (run `set_keys.py` again, set `USE_OPEN_WEIGHTS=1`), or drop the open-weights claim from SUBMISSION and JUDGING_MAP.
3. **Record 20 to 40 s of a real faucet or pump**, and run 3 to 5 real trials (docs/USER_TRIAL_KIT.md).
4. **Approve** the GitHub push (`ragilmalik/tukang-copilot`), the Render deploy (docs/DEPLOY.md, free plan; open the live link a few minutes before judging or recording, the free server sleeps) and hosting the static judge build `dist-static/` (made by `python scripts/build_static.py`; recorded demo, no server, no cold start; GitHub Pages or a Netlify drop, steps in `--help`).
5. **Upload the YouTube video** (kit and chapters: docs/launch/YOUTUBE.md; the real recording or the 2:57 docs/demo/tukang-copilot-demo.mp4; Unlisted is fine) and **post the X thread** (docs/launch/X_THREAD.md, 43.5 s clip docs/demo/tukang-copilot-x-vertical.mp4) **before submitting**, so both links go in the form.
6. **Paste docs/SUBMISSION.md into the Cerebral Valley form** (account ragilmalika) and submit before **Thu Nov 5, 09:00 WIB**. Then share docs/launch/COMMUNITY_VOTE_KIT.md when voting opens **Tue Nov 10, 00:00 WIB**.
