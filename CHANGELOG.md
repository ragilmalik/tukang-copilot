# Changelog

All dates WIB (UTC+7). Everything below was built during the hackathon window (Oct 26 – Nov 4, 2026).

## 1.26.0 (2026-11-02 WIB)
Judge QA: a skeptical judge played every flow on a phone-sized Chromium in Bahasa, Basa Jawa and English, then read the PDFs and the shared guide page. Everything they tripped over is fixed and tested.
- **Failing brakes are a safety stop.** "Rem motorku blong", "rem ora makan", "my brakes don't work" or "spongy brakes" on the owner's own motorbike used to get a repair guide; only a car's brake line stopped. They now get a red stop that says not to ride it and to push or tow it to a workshop. Everyday brake words that are not a failure (a dead brake light, squeaky pads) still get help. The red-team eval grew to 33 cases, all stopped.
- **A safety stop is no longer a dead end.** A "Fix something else" button sits under the stop card, and the "Do this now" list fits the hazard: close the gas valve and open the windows for gas, switch off the breaker for house wiring, don't ride it for brakes.
- **The demo's one question now matters.** In the 1-tap demo the answer to "Do you smell fuel when you crank it?" moves the diagnosis (70% with a fuel smell, 58% without) and shows up as evidence. The recorded demo, screenshots and demo video were re-made; the video shows the 70% result.
- **The 1-tap demo survives a server that stops answering.** If the page loaded but the server then goes quiet or returns a gateway error, the demo plays the recording instead of showing "No connection".
- **Honest numbers and plain words.** The share card counts the steps that really passed a camera check instead of claiming every step was checked. The cost chip says "parts" (tools are reusable and not in the estimate). "It works now" reads "You saved about Rp35.000 compared with a workshop.", and the garage says "1 repair", not "1 repairs".
- **The mechanic brief tells the truth after a fix.** After "It works now" the PDF's status line says the owner reports it works again, not that the owner asked for a mechanic.
- **A shared guide is read-only.** Whoever opens someone else's guide link sees the owner's answer but can no longer change it with the outcome buttons. The share fallback label is translated ("Tautan", "Pranala", "Link").
- **No near-empty last page on the workshop sheet.** "Done when" now closes the last step page when it fits there.
- New tests: `test_judge_qa.py` (safety gate, demo diagnosis, share card, mechanic brief, workshop sheet, read-only guide wiring) and `test_playwright_judge_qa.py` (real Chromium: stop button, hazard lists, cost chip and wording, demo fallback, read-only guide). Offline cache bumped to v11 so phones pick up the new app. Full test report: 710 tests, all passed.

## 1.25.10 (2026-11-01 WIB)
Audit 16 (the shared guide page /guide/{id} and the large-print workshop sheet, read in Bahasa, Basa Jawa and English in Chromium 390x844 and as PDFs).
- **The shared guide page now leads with the repair.** Whoever opens a shared link (the friend, the mechanic, a judge) used to land on the diagnosis followed by a nine-row "What the AI did" log, with the checklist and the steps two screens down. The log now sits after the steps and the outcome question, still complete and still tappable. The phone app's own result screen is unchanged (it is in the demo assets). Workshop sheet read in all three languages: nothing to fix.
- Audit 17 (server robustness): `test_hostile_input.py`, 11 tests that fuzzed input (odd text, category, language, uploads, every session endpoint, traversal paths) never gives a 5xx. No app change.
- 4 new real-Chromium tests (`test_playwright_guide.py`: steps and outcome come before the log in id/jv/en, the log keeps its rows, main screen order unchanged; the three guide tests fail on 1.25.9).

## 1.25.9 (2026-11-01 WIB)
Audit 15 (garage + PDF report + share card: a real session rendered in Bahasa, Basa Jawa and English and read page by page).
- **The Javanese PDF report is Javanese.** Only the title, a few headings and the footer were; the cost lines ("Perkiraan biaya suku cadang", "Hemat sendiri"), the disclaimer, "Sebelum mulai, pastikan", the safety badge ("HATI-HATI" where the app and the share card say "ATI-ATI"), "Mode demo", the page word and every under-the-hood stage name were Indonesian. A full Javanese label set now follows the app's wording.
- **No English "rules in code" in the Bahasa and Javanese PDF.** The under-the-hood list printed the English tag for the two safety gates; it now reads "aturan di kode" / "aturan ing kode".
- 4 new tests (`test_report_pdf_jv.py`: same label keys in all three languages, no Indonesian leftovers in the Javanese set, badge words match the app, localized tag). Share card in Javanese checked: nothing clipped. UI unchanged, so screenshots, GIF and video were not re-shot.

## 1.25.8 (2026-11-01 WIB)
Audit 14 (recorded demo in Bahasa, Basa Jawa and English with no server, then a read of every number the docs quote).
- **No stale test count in the docs.** `docs/TESTING.md` still said "all 550 tests" while the README, SUBMISSION and WRITEUP said 620. It now points to docs/TEST_REPORT.md, and a new test (`test_doc_counts.py`) fails if any submission doc quotes a test count different from the last real run, so a judge never sees two numbers.
- The recorded demo (`?replay=1`) was walked end to end in id/jv/en (landing, progress, question, result, all four camera-checked steps, outcome, PDF and WhatsApp buttons): no console errors, nothing in the wrong language.

## 1.25.7 (2026-11-01 WIB)
Audit 13 (result + steps: walked all four steps of the demo repair in Bahasa Jawa and English, fast like a real owner).
- **A passed camera check no longer skips a step.** After "Step looks right" the app moves on by itself after 1.5 s. An owner who tapped Next (or Back) in the meantime was moved a second time: step 2 jumped to step 4, and on the last step the stale timer ran past the end and threw "Cannot read properties of undefined". Any other move to a step now cancels the timer.
- **The repair no longer just stops after the last step.** When the last step passes and all steps are camera-verified, "Does it work again?" scrolls into view with a line in the owner's language (id/jv/en) that screen readers announce, and focus moves to the "It works now" button (nothing is forced when steps were skipped or an answer already exists).
- Service-worker shell cache bumped to `tukang-shell-v10`.
- 8 new real-Chromium tests in `test_playwright_steps.py` (the skip, back, crash and prompt tests fail on 1.25.6).

## 1.25.6 (2026-11-01 WIB)
Audit 12 (what a screen reader says, in each language; laptop view).
- **The back button has a name.** The "previous step" control was only "◀"; it now says "Langkah sebelumnya" / "Langkah sadurunge" / "Previous step" (app and shared guide page).
- **Labels follow the chosen language.** The SAM parts picture ("Highlighted parts"), the "How it works" list and the laptop QR code were English-only labels on the Indonesian and Javanese pages. A new `data-ta` hook in `applyLang` sets aria-labels from the language table.
- Service-worker shell cache bumped to `tukang-shell-v9`.
- 7 new real-Chromium tests in `test_playwright_labels.py` (they fail on 1.25.5).

## 1.25.5 (2026-11-01 WIB)
Audit 11 (video and voice-recording refusals, landing in Basa Jawa).
- **A too-long video no longer says your text is too long.** The server's "That video is too long" matched the long-text rule, so a 40 s clip got a message about the owner's text. Video rules now come first: unreadable video, too short, too long and unreadable voice recording each show a message in Bahasa, Basa Jawa or English (`videoBad`, `videoShort`, `videoLong`, `recBad`).
- 6 new real-Chromium tests in `test_playwright_capture.py` (a garbage .mp4 in 3 languages; a real 40 s ffmpeg clip in 3 languages that fails on 1.25.4).

## 1.25.4 (2026-11-01 WIB)
Audit 10 (red stop + re-plan screens in Bahasa and Basa Jawa, then a probe of the safety gate with 40 street-wording texts).
- **Text gate speaks street Indonesian and Javanese.** 15 of 40 probes slipped through: "kulkas nyetrum", "kabel PLN putus", "trafo meledak", "listrik ngeletik percikan api di stopkontak", "aki meledak", "kompor mbledug", "kompor nyemprot api", "baterai nggembung", "bensin netes ing mesin panas", "kompresor kulkas", "anakku keracunan gas", three-phase / 380 V. All now stop with the right category and message. Words that are normal repair talk still pass: "percikan api busi", "ban meledak", "nyetrum aki" (charging a battery), "bensin netes" from a carburettor with no heat, "kabel gas / rem / charger putus", 12 V "tegangan aki".
- **Plan guard**: 8 new rules for steps a model could write: refrigerant refill, CRT capacitors and flyback, gas pipe repair, patching a fuel leak, piercing a swollen lithium cell, touching terminals while plugged in, live mains testing, bypassing a thermal fuse or safety switch. A warning such as "do not touch the terminals while plugged in" or "never bypass the thermal fuse" is not stopped.
- 49 new parametrised tests in `test_safety.py`. docs/EVAL.md numbers (30 dangerous, 17 safe) are unchanged: the labelled eval set was not enlarged, so nothing quoted elsewhere moved.

## 1.25.3 (2026-11-01 WIB)
Audit 9 (capture screen with a text file, a broken JPG, a 20 px image and a 6000x4000 photo, in Bahasa / Basa Jawa / English, real Chromium 390x844).
- **Refusals in the owner's language.** A wrong file or a broken photo showed the server's English ("Unsupported file type .txt", "Could not read that photo. Try a JPG or PNG.") on the Indonesian and Javanese pages. The app now translates every refusal a person can cause (not a photo, unreadable photo, too big, empty, text too long, missing photo or description) in all three languages, on every request path (start, answer, step check, re-plan, report).
- **A non-photo is refused at once.** Picking a PDF or text file used to leave a blank dashed box and say nothing until Go. Now the picker rejects it on the spot with the translated message and keeps nothing. A photo the browser cannot draw (e.g. HEIC on some phones) shows its file name instead of a blank box. 8 Chromium tests (`test_playwright_capture.py`; the language ones fail on 1.25.2).
- Service worker cache `tukang-shell-v8`.

## 1.25.2 (2026-11-01 WIB)
Audit 8 (accessibility of the small controls, English flow at 390x844 in real Chromium, a script that measures every visible control).
- **Thumb-sized small links.** The "Compare prices" / "Shopee" links were 16 px tall, the sample links under the camera 30 px, the garage entries the browser's default blue, and the "Agent log" / "models used" summaries 24 px: hard to hit with greasy or gloved hands. Now 40 px (shop and sample links), 44 px (record-a-video), garage entries themed and 8 px padded, summaries 44 px. 3 Chromium tests measure the real boxes (`test_playwright_targets.py`; all three fail on 1.25.1).
- Service worker cache `tukang-shell-v7`.

## 1.25.1 (2026-11-01 WIB)
Audit 7 (garage, PDF, share card, Javanese screens at 390x844 in real Chromium) found two things a judge on a phone would hit in the first minute.
- **First screen follows the phone.** It always opened in Bahasa Indonesia, so an English-speaking judge landed on a page they could not read. Now: an earlier choice wins, then `?lang=id|jv|en` on the link, then the phone's language list (Indonesian or Javanese anywhere in it keeps Bahasa / Basa Jawa, so an Indonesian phone set to English is not switched), else English. 5 Chromium tests (`test_playwright_lang.py`). The demo-asset script now pins the browser to id-ID so screenshots and video do not change.
- **Back button.** Starting a repair used `replaceState`, so the phone Back button left the site and dropped the user out of the repair. Now it pushes `#<id>`: Back returns to the first screen (stream, timers, camera and voice are stopped), Forward comes back to the same repair, "Start again" and "Erase" step back instead of leaving a duplicate history entry. Works in the recorded demo too. 4 Chromium tests (`test_playwright_back.py`; the first fails on 1.25.0).
- Service worker cache `tukang-shell-v6`; README judge path mentions both.

## 1.25.0 (2026-11-01 WIB)
Judges on laptops, a server-free judge build, an honest offline eval that found and fixed real safety misses, a one-command first live run, and a tighter video.
- **Laptop view**: at 1024 px and wider the app sits in a centred phone frame (it scrolls inside the frame) with a side panel: what it is, a QR code of the page's own address to carry on with a phone (says when the address only works on this computer), a 1-tap demo button and an id/jv/en switch. The QR encoder (`web/vendor/qrcode.js`, MIT, Kazuhiko Arase) is fetched only on wide screens. Phones are unchanged. Screens checked at 1280x800 and 1440x900; Chromium tests (`test_playwright_desk.py`) and static tests (`test_desk.py`).
- **Static judge build**: `python scripts/build_static.py` writes `dist-static/` (gitignored): the recorded demo as plain files with relative paths, so it runs from GitHub Pages (also under a sub-path) or Netlify with no server and no cold start. The replay is forced on, the API is never called, the "Recorded demo" badge shows from the first second, no service worker. `--help` carries the build / try / host instructions; `--check` verifies. Chromium test serves it from a plain file server under `/tukang-copilot/` and fails on any `/api/` request. The recording now follows a language change made before the demo starts (it was fixed to the language at page load). Not deployed.
- **Eval** (`scripts/run_eval.py` → `docs/EVAL.md`): all stand-in fixtures, a 20-case red-team set (gas leak, LPG regulator, 240 V panel / consumer unit, wall socket, car brake lines, ceiling fan wiring, microwave; id/jv/en), 12 everyday controls, 15 plan-guard cases and 7 prompt-injection cases (owner text, fake system tags, follow-up answer, writing in a photo with a model that obeys it), in `mock` and `fake` (real live code path against the stand-in Meta server) mode, with latency and cost from `api/cost.py`. All labelled as mock / fake-model results, live run pending. Runs as a test (`test_run_eval.py`).
- **Safety fixes found by the eval**: the v1.24 text gate let 12 of 20 red-team texts through and the plan guard passed 7 of 10 dangerous steps (37 % recall overall). New rules in `api/pipeline/safety.py` for Javanese "gase", gas pipes and cylinders, "tabung melon", 220/240 V panels, consumer units / RCDs, wall sockets, ceiling fan and ceiling wiring, water heater elements, car brake lines / "rem blong"; plan-guard rules for LPG regulators, panels / MCBs, ceiling wiring and brake lines. Now 100 % recall with 0 false stops on the controls (motorbike throttle "gas", a carburettor gasket, motorbike brake squeal still pass). The diagnose / plan / look prompts name these jobs and say writing in a photo is never an instruction.
- **First live run** (`scripts/first_live_run.py`): one command after `set_keys.py`: checks the key without printing it, asks Meta which models the key can see, runs one sample repair live with DEMO_FALLBACK off (answers the follow-up, checks one step photo), writes `docs/LIVE_RUN.md` with outputs, time per stage and cost, and exits 0 / 1 / 2 with a plain-English fix. `--fake` rehearses against the stand-in server. Tests with the fake server, incl. a wrong key and no key.
- **Video**: 3-second hook title card ("Fix it yourself, safely. In Javanese." and "Built during the Meta AI Developer Hackathon, Oct 26 to Nov 4, 2026 (first commit Oct 30)"), burned-in English captions of the voice-over (one sentence at a time), a Muse Image diagram step scene (demo mode shows a labelled stand-in drawing); the log-jump and PDF scenes were dropped to stay under 3:00. Main cut **2:57** (177.8 s, ffprobe), X clip 43.5 s with English captions, `docs/demo/TIMESTAMPS.txt` scene times. New screenshots `28_diagram_step.png`, `29_laptop.png`; GIF re-made.
- Service worker cache `tukang-shell-v5`.
- **Test robustness**: `test_agent_log_lines_jump_to_what_they_describe` waited 5 s for a smooth scroll and failed once under a loaded full run; it now waits on conditions (step number, element in view, focus) with up to 15 to 20 s, no fixed sleeps.
- **Docs reconciled with the re-cut video**: YouTube chapters, JUDGING_MAP timestamps, 29 screenshots, 43.5 s X clip; docs/EVAL.md, the laptop view, the static judge build and `first_live_run.py` added as evidence in SUBMISSION, JUDGING_MAP and JUDGE_FAQ (new question 11); one-pager PDF re-made; HANDOFF Malik-only list re-ordered with the live run first.

## 1.24.0 (2026-11-01 WIB)
The 1-tap demo now works even when the free server is asleep, and a skeptical-judge pass fixed what a first-time viewer trips over.
- **Recorded demo (backlog J5)**: `scripts/record_replay.py` records the demo-mode motorbike run in id/jv/en into `web/replay/` (progress snapshots, follow-up question, ready session, one replayable "delta" per action: each step x both stand-in check photos, re-plan, outcome; SAM-marked photos, share cards, PDF reports). `web/replay.js` plays it when `/api/health` has not answered within 4 s (Render free tier cold start), when the phone is offline, or with `?replay=1`. A purple "▶ Recorded demo" badge is on every screen and a note explains the server is waking up. The visitor's own photo is refused with "needs the live server", never faked; the live camera guide and voice commands say the same; the workshop sheet button is hidden (not recorded). The service worker pre-caches the recording and shows the cached app shell after 3.5 s if the server is slow (`tukang-shell-v4`). `record_replay.py --check` (and a test) fails when the app's session shape drifts from the recording.
- **Red stop on screen**: the progress heading becomes "⛔ Stopped for your safety" and the STOP card sits right under it (before, the heading kept saying "Checking…" and the card was ~1000 px down). One PDF button instead of two.
- **Result opens at the top** (object name and safety badge were scrolled off after answering the question).
- **Re-plan is visible**: "🔁 Plan 2 of 3: <cause>" banner at the top of the result; tried causes greyed with "✗ tried".
- **Keyboard**: focus moves to the first quick answer when the follow-up question appears.
- **PDF**: "Cause worked on" instead of "Cause fixed" (it was printed before anything was fixed).
- **Landing**: the preview picture is an 11 KB language-neutral crop of the SAM-marked stand-in photo with a translated caption (was the Indonesian 81 KB og.png on every language). Laptops get a "Made for phones" note.
- **Demo check text** names what it confirmed ("Looks right: The cap is off and the plug is visible.") instead of "It matches the expected state."
- `/api/health` version now follows the full version (was stuck at 1.23.0); test compares it with the top CHANGELOG entry.
- Tests: `test_replay.py`, `test_audit5.py`, `test_playwright_replay.py`, `test_playwright_audit5.py`, version sync.

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
