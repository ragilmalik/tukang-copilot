# TODO

Tukang Copilot is my own project. I built it first for the Meta AI developer hackathon (Oct to Nov 2026); the submission page had closed when I tried on 6 Nov 2026, so nothing was submitted, and the items that only made sense for the event are marked "dropped" below. What is left: listening to the new film, the steps only I can do with my accounts, and real-world trials.

## 1.33.1 recheck and bug hunt (7 Nov)
- [x] Fresh clone of main bdefe47: same files as my working copy; ruff clean, `mypy api --strict` clean, offline smoke ALL PASSED
- [x] A repair whose worker died on a full disk no longer spins until a restart: shown and saved as "stalled" with Try again (test_stalled_repair.py)
- [x] Report and workshop PDFs written in one step; an erase during drawing leaves no folder (test_pdf_write.py)
- [x] Live guide frames respect DAILY_BUDGET_USD
- [x] Muse Image download status checked; SAM 3.1 waits between network retries
- [x] Service worker: cached app on a 5xx, no home page HTML for a missing script (test_sw_fetch.py), cache v28
- [x] `mypy --strict .` on the whole repo clean (was 21 errors on 194 files, 0 on 197 now); CI and `scripts/check_all.sh` run it too
- [x] WhatsApp: a repair whose last save failed gets the error and Try again instead of silence
- [x] Progress screen layout shift 0.007 to 0 (stage note on its own line from the start; tip bar keeps its height in Basa Jawa)
- [x] Checked, no bug: header language pill at 360, 390 and 430 px; Basa Jawa demo button text
- [x] Full run on 7 Nov, 01:21 WIB: 1126 passed, 0 failed, 0 skipped (973 without a browser in 107 files, 153 in real Chromium in 25 files); the 01:01 run had 4 layout failures from an earlier draft of the progress-row fix, fixed before the second run
- [x] `mypy api --strict` 175 files, `mypy --strict .` 197 files, ruff clean, check_voice 0 hits, `record_replay.py --check` up to date, `build_static.py --check` OK, offline smoke ALL PASSED (77 checks, port 8765)
- [x] Version 1.33.1, CHANGELOG, README, HANDOFF, REPORT, WRITEUP, TESTING, ONE_PAGER, VERIFICATION_REPORT, TEST_REPORT
- [ ] One-pager and guide bundle rebuilt, commit, push, CI
- [ ] Tag v1.33.1, package, GitHub Release, Drive copy (1.33.0 files moved to old-1.33.0)

## 1.33.0 release (6 Nov)
- [x] CI fix: the app said 1.32.0 while CHANGELOG headed 1.33.0 (test_version_sync); the version lives only in api/__init__.py and is now 1.33.0. The offline cache name is not tied to the version (v27 since this release's new recording)
- [x] `mypy api --strict` failed on two test files (test_demo_video.py, test_replay.py) and the demo scripts had 8 more errors; all fixed, clean on 172 files
- [x] Docs rewritten for a personal project (README, HANDOFF, REPORT, WRITEUP, VERIFICATION_REPORT, ONE_PAGER, YOUTUBE, demo README, ROADMAP, SETUP, TUTORIAL, DEPLOY, DECISIONS, METHODS, WHATSAPP, TROUBLESHOOTING, ARCHITECTURE, AI_PIPELINE, CHANGELOG header); user-facing wording in check_keys.py, deploy_check.py, record_replay.py, first_live_run.py and render.yaml
- [x] Hackathon papers moved to docs/archive/hackathon/ with a README (SUBMISSION, SUBMISSION_CHECKLIST, JUDGING_MAP, JUDGE_FAQ, COMMUNITY_VOTE_KIT, X_THREAD, DEMO_SCRIPT, SPEC); test_doc_links.py checks every relative link; test_doc_counts, test_no_em_dash_docs and test_no_emdash follow the move
- [x] Full run: 1104 passed, 0 failed, 0 skipped (6 Nov 2026, 15:53 WIB, commit 1f84cae; 953 without a browser in 104 files, 151 in real Chromium in 25 files). The first run on ee04108 had 2 failures: two browser tests still waited for the recorded demo's follow-up question, fixed in 1f84cae; offline smoke ALL PASSED (77 checks, port 8765)
- [x] One-pager rebuilt (1 A4 page, 1104 tests and 77-check smoke on it, looked at) and guide bundle rebuilt (54 pages, 14 docs, v1.33.0, page 1 looked at)
- [x] Commit 1156e90 pushed, CI green on it (https://github.com/ragilmalik/tukang-copilot/actions/runs/42193387965); package built from 1156e90 (repo zip 154.2 MB, 527 repo files plus LINKS.txt, film, vertical clip, captions, one-pager, guide PDF, marketing images, GIF, 4 docs, 118 screenshots: 136 files)
- [x] Drive: all 136 files in the folder (screenshots and screenshots/gallery as subfolders, the 1.32.0 copies in old-1.32.0); every file matches by size and MD5, the folder, both subfolders and the files checked are owner-only
- [x] GitHub Release v1.33.0 on 1156e90: https://github.com/ragilmalik/tukang-copilot/releases/tag/v1.33.0 with the zip, the film and the vertical clip as assets (zip over GitHub's 100 MB file limit, so it is a release asset and not a repo file); asset sizes and SHA-256 match the local files

## 1.33.0 media remake (6 Nov)
What I want from it: more realistic images and video, a more natural voice, better music, new realistic sample photos with a live re-recording, every screen shot again, all docs updated.
- [x] a. Voice A/B of free engines (Kokoro-82M, edge-tts, Piper): narrator edge-tts AndrewMultilingual at -8%; music "Lucky Acoustic" (Jesse Keller, CC BY 3.0); five labelled b-roll stills in docs/launch/broll/
- [x] a. Marketing images (thumbnail, cover, square, vertical) with real app screens composited on the phones: docs/launch/make_marketing_images.py, claims table in docs/launch/ASSETS.md
- [x] b. New photorealistic sample photos for every scenario, labelled "Sample photo (AI-generated)", hand outlines redrawn; old photos kept in the trash folder
- [x] c. Live re-recording on the new photos (cap $1.00 from the app's spend log): 1-tap demo in id/jv/en with no follow-up question (the model was 85-88% sure), plus live pump (id), rice cooker red stop (id), faucet with a Muse Image diagram (en) and tyre (jv) sessions for the screenshots; `record_replay.py --check` up to date, recorded-demo and sample tests pass, `build_static.py --check` OK
- [ ] WhatsApp simulator shots not re-taken: they need about $0.15 of live answers and the $1.00 cap had $0.06 left
- [x] d. Every screen shot again (id, jv, en; light and dark; laptop view) with docs/demo/screenshots/INDEX.md: 118 files (26 numbered re-shot + 85 gallery on the new photos, 7 older shots kept and marked: 03_question, 16_live_guide, 30_whatsapp_*)
- [ ] 16_live_guide on the new photos: the take on the pump photo (20 SAM 3.1 frames, $0.05) did not lock within 30 s; needs budget and maybe a tighter part outline
- [x] e. New video (2:25, 1080p30, -16.0 LUFS, voice + music, burned-in captions + .srt), vertical clip (31.4 s, 1080x1920, voice + music) and hero GIF (640x1200, 2.9 MB), all from screens recorded on the 6 Nov live run (no model calls, $0.00); hook on labelled AI-generated scenes, proof card from docs/EVAL.md and docs/TEST_REPORT.md, music credit on the end card and in ATTRIBUTIONS, YOUTUBE (new description and chapters), README, CHANGELOG, one-pager rebuilt (1 page, looked at); test_demo_video.py rewritten; speech-to-text 91.5% of narration words (faster-whisper base.en)
- [ ] Listen to the film and the vertical clip by ear before upload (voice, music level, the Bahasa and Basa Jawa owner lines, "Javanese" in the tyre scene, which the speech-to-text heard as "Japanese")
- [ ] Re-check the music licence on https://www.jamendo.com/track/1540859 (read from Openverse as CC BY 3.0)

## 1.32.0 weakness hunt (6 Nov)
Findings ranked by user impact, each with its test; the full audit is in CHANGELOG 1.32.0.
- [x] Session lock on every writer: double re-plan, a step check landing on the next plan, photo-check cap under parallel checks, two checks on one step, double retry, double start, live-guide / voice / outcome writes during a re-plan (test_races.py)
- [x] Status rules: step checks and live guide only on the steps, re-plan only from a plan on screen, outcome not while running
- [x] Restart mid-repair: marked as an error with Try again at startup (engine.recover_interrupted)
- [x] Photo check off the event loop (a live check froze the whole server)
- [x] Owner token on answer, retry, still broken, step check, live guide and voice command; app sends it (test_owner_routes.py)
- [x] Rate-limit key no longer spoofable (CLIENT_IP_HEADER, FORWARDED_HOPS)
- [x] Erasing a repair no longer resets the daily spend cap (data/spend-erased.jsonl)
- [x] Cache-Control no-store on /api and /files, ASCII session ids, decompression bomb is a 400 on check and track
- [x] Janitor clears locks, erase marks, half-made folders and stale tmp files; erase ends an open progress stream cleanly
- [x] Every main screen with no console error, restart recovery and slow network in Chromium (test_playwright_screens_clean.py); no English in the id/jv string tables
- [x] CI on 17cf49a and daaf282 went red: the shared-guide re-plan test had no owner token (fixed in a454620) and the erased-spend ledger rounded the erase time up by up to 0.05 s, so a daily sum asked right after an erase missed it (fixed in 7d7969c, test_an_erase_counts_in_the_cap_at_once). CI on 7d7969c then failed the slow-connection test: the progress clock waited for the first server state; it now counts from the tap (test_the_clock_starts_before_the_first_answer_arrives)
- [x] Writing check: `scripts/check_voice.py` + test_check_voice.py, every hit rewritten (0 hits), HANDOFF rewritten as maintainer notes
- [x] Full run on 29823cd (6 Nov, 10:29 WIB): `make_test_report.py` ALL PASSED, 1096 passed, 0 failed, 0 skipped (945 without a browser in 103 files, 151 in real Chromium in 25 files); ruff clean; mypy strict 171 files; offline smoke ALL PASSED (77 checks, port 8765); check_voice 0 hits; `build_static.py --check` OK; `record_replay.py --check` up to date
- [x] Docs filled with the measured numbers (README, HANDOFF, REPORT, JUDGING_MAP, SUBMISSION, WRITEUP, VERIFICATION_REPORT, ONE_PAGER, COMMUNITY_VOTE_KIT)
- [x] One-pager rebuilt (1 A4 page, 1096 tests and 77-check smoke on it, looked at) and guide bundle rebuilt (54 pages, v1.32.0)
- [x] Gate on 60047bc: ruff clean, mypy strict 171 files, check_voice 0 hits, offline smoke ALL PASSED (77 checks, port 8765), leak scan clean (history hits are only test fixtures, redaction patterns and Authorization header code); pushed. CI green on 05dc01d (https://github.com/ragilmalik/tukang-copilot/actions/runs/42159090902) and 60047bc (https://github.com/ragilmalik/tukang-copilot/actions/runs/42159375750)
- [x] Package built from c234a06 (repo zip 78.6 MB, demo video, X clip, captions, one-pager, guide bundle, thumbnail, 4 docs, 33 screenshots: 44 files) and copied to the Drive folder (screenshots in a subfolder); all 44 match by size and MD5, the folder and files are owner-only. The Drive token only sees files it made, so copies uploaded in earlier sessions were not visible and were not moved to an "old" subfolder; same-name older copies may still sit in that folder
- [ ] After the first Render deploy: check that `cf-connecting-ip` reaches the app (the rate limit keys on it)

## 1.31.1 media and docs (6 Nov)
- [x] A. Flaky test_playwright_motion fixed (deterministic waits, 6 clean runs)
- [x] B. Screenshots re-shot on the 1.31.0 UI from recorded live answers (1-tap demo recording + recorded live sessions); only the live camera guide calls SAM 3.1 live. Recorded hand-off links point at the site you are on (were http://testserver), offline cache v25 (pushed 5dbfa8b)
- [x] C1. Intro voice-over says where the answers come from: "recorded on a live run" when the video plays recorded answers, "live" when it films live calls; the video refuses a voice clip made for the other mode (pushed dee1364)
- [x] C. Main video re-captured and rendered: 2:54 (174.1 s), 1080p60, captions burned in, -16.0 LUFS, true peak -3.9 dBFS, no silence of 1 s or more except the last 1.6 s on the close card; voice-over speech-to-text 402/424 script words (pushed 9901da7)
- [x] D. Vertical X clip (43.5 s, 1080x1920, 12.1 MB), hero GIF (640x1200, 2.2 MB), YouTube thumbnail re-made (pushed 9901da7); the og image is a composed share card that does not show the 1.31.0 screens, looked at and kept
- [x] E. Docs: every placeholder filled with measured numbers (only `[LIVE_URL]`, `[YOUTUBE_URL]` and `[VOTE_URL]` stay for me to fill), stale wording fixed (CI status, TEST_REPORT live-run line), one-pager rebuilt by `make_launch_assets.py onepager` (1 A4 page, looked at), guide bundle rebuilt
- [x] F. Final full run on 6 Nov: ruff clean, mypy strict 166 files, 858 non-browser + 147 Chromium tests passed one file at a time (0 failed, 0 skipped), `make_test_report.py` 1005/1005 ALL PASSED, jsdom and axe ran, offline smoke ALL PASSED (69 checks), static build and --check OK, replay fixture up to date; CI green on 09fa5f1 and 7dffd03 (axe-core now runs there too); pushed
- [x] G. CI went red twice after F: a screen-timing test (fixed in 0ea30ea) and a real race where a quick answer to the follow-up question was lost (fixed with the session lock, new test). CI green again on 5d9dd75: https://github.com/ragilmalik/tukang-copilot/actions/runs/42145261120

## 1.31.0 UI pass (6 Nov)
- [x] Screen changes through a View Transition (fallback: instant), skipped by the first tap or key, the tap still lands, off under reduced motion
- [x] Step changes slide in (Web Animations), stay synchronous, are announced to screen readers and bring the card up under the header
- [x] Placeholders for findings on the progress screen (sized like the result, only the running stage shimmers, 400 ms minimum), layout shift 0.23 to 0.007
- [x] Progress line names the running stage and model, the running row counts its own seconds, live-only "usually 1 to 2 minutes"
- [x] Busy state on every button that starts something; one repair per double tap on the demo
- [x] Haptics on a step pass or fail and on a red stop (where the phone supports it)
- [x] Reload, Back or Forward mid-repair returns to the same step
- [x] Hands-free "Lanjut" no longer sticks out of the step card (360, 390, laptop frame); square icon buttons for Back and Listen in hands-free
- [x] Language picker no longer covers the app name under 400 px or in the laptop frame (short pill, real select on top)
- [x] Scroll targets land under the sticky header (scroll-padding), fixed 4:3 step picture box, result opens with its photo decoded
- [x] touch-action manipulation, 16 px picker text, safe-area insets on footer and gutters, no pull-to-refresh mid-repair
- [x] First paint: deferred scripts, Barlow 600 preloaded, high fetch priority on the landing picture, offline cache v24
- [x] Overflow audit at 360x740, 390x844, 430x932 and 1280x800, id/jv/en, light/dark: 0 issues
- [x] New tests: test_playwright_layout.py, test_playwright_motion.py, test_ui_motion.py
- [x] Full checks: ruff clean, mypy strict 165 files, 853 non-browser + 145 Chromium tests passed (0 failed), jsdom and axe pass, offline smoke ALL PASSED (70 checks), static build and --check OK, replay fixture up to date
- [x] Before/after screenshots reviewed (phone light/dark, 360, 430 Basa Jawa dark, laptop)
- [x] Watch test_playwright_motion: failed once in 4 runs on 6 Nov. The tap-during-a-transition test waited a fixed 40 ms and then expected the 200 ms screen transition to still be running, which a busy machine can miss (shown with a forced 400 ms delay); the transition is now stretched to a minute for that test and only the tap ends it. The step-slide test read document.getAnimations(), which only passed because unrelated bar animations linger; it now keeps the slide animations themselves and checks their direction and length. 6 clean runs in a row (6 Nov)

## Now (1.30.0, 6 Nov)
- [x] Sample "plug cap" photo is checked on the step it shows (`sample_step`, api/sample_step.py), with a line saying which step; buttons say what each sample photo is
- [x] WhatsApp simulator label reads naturally in Bahasa and Basa Jawa ("menjalankan" / "nglakokake"), tests match
- [x] Full test run: non-browser 838/0, Playwright 127/0, ruff, mypy 162 files, offline smoke 69 checks, static build OK
- [x] Re-record the 1-tap demo from the live API (one yes/no question in every language, the sample photo passes on its step): 6 Nov 01:23 WIB, pipeline $0.18
- [x] Commit and push (main at 9179f81 on 6 Nov)

## Must (from the hackathon days)
Done by me (code, docs, media):
- [x] Meta key set, `check_keys.py` passes all 5 required models (5 Nov 2026)
- [x] Live runs on 7 scenarios and the live eval (docs/LIVE_RUN.md, docs/EVAL.md); fixes from them shipped in 1.30.0
- [x] Public repo https://github.com/ragilmalik/tukang-copilot, history cleaned of private data
- [x] Full doc set: TUTORIAL, HOW_TO_USE, HOW_IT_WORKS, ARCHITECTURE, METHODS, SUGGESTIONS, TEST_CHECKLIST, VERIFICATION_REPORT, REPORT, HANDOFF
- [x] Final media from the live API: screenshots, hero.gif, thumbnail, og image, demo video under 3:00, vertical clip (1.33.0)
- [x] Fill the measured numbers in README, WRITEUP and REPORT (1.33.0; the submission papers are archived with the numbers of their day)
- [ ] Rebuild the one-pager PDF and the guide bundle, Drive upload (1.33.0 release, above)

Only I can do these (my accounts):
- [x] Dropped: asking the organisers about a late entry (personal project now)
- [ ] If I want it public: upload the video to YouTube with docs/launch/YOUTUBE.md, then put the link in the README
- [ ] If I want it: post about it on X with the vertical clip (the old thread draft is in docs/archive/hackathon/X_THREAD.md)
- [x] Dropped: the Cerebral Valley submission. Tried on 6 Nov 2026, 09:29 WIB, signed in as ragilmalika (Google): the submit page showed a disabled "Event Finished" button and "That's time! All submissions are due now." No form opened, nothing was submitted (the field text is archived in docs/archive/hackathon/SUBMISSION.md)
- [ ] Deploy on Render (docs/DEPLOY.md) if I want a live link, then `deploy_check.py <url> --live`
- [ ] Rotate the Meta key now that the live runs are done
- [x] Dropped: the community vote kit (archived in docs/archive/hackathon/COMMUNITY_VOTE_KIT.md)
- [ ] Real photos and 5 owner trials (docs/USER_TRIAL_KIT.md), then `scripts/impact_report.py`

## Should (scores better)
- [x] Water pump mock scenario and fixtures (spec §8 case 2)
- [x] Video capture (5 to 10 s, 3 sharpest frames)
- [x] PDF export of the report, plus local "My garage" history (localStorage)
- [ ] (keys) Open-weights run on Baseten (needs BASETEN_API_KEY); the badge is built and shows when active
- [x] Dropped: the X thread for the event's engagement prize
- [x] Screenshots, demo video and vertical clip (docs/demo/), regenerated for v1.23 (26 shots, 2:57 video, GIF)
- [x] Re-shot screenshots and video for the compact tip bar and the PDF agent-log page (v1.23)
- [x] Streamed partial results on the progress screen (object, SAM overlay, top cause as each stage finishes) (v1.23)
- [x] Recorded 1-tap demo that plays when the free server sleeps or the phone is offline, labelled "Recorded demo" (v1.24)
- [x] Fixes from a first-time-viewer pass: red stop on screen, result opens at the top, re-plan banner, keyboard focus, PDF wording, neutral landing picture (v1.24)
- [x] Demo kit re-shot for v1.24 (27 shots incl. the recorded demo, 2:57 video, 45 s X clip, GIF)
- [x] Laptop view: phone frame plus side panel with QR code, 1-tap demo, language switch (v1.25)
- [x] Static judge build `scripts/build_static.py` (recorded demo, no server; not deployed) (v1.25)
- [x] Offline eval `scripts/run_eval.py` → docs/EVAL.md (fixtures, 20 red-team, 7 injection; mock/fake labelled); safety gate fixed for 12 text and 7 plan misses (v1.25)
- [x] `scripts/first_live_run.py`, a one-command first live repair → docs/LIVE_RUN.md (v1.25)
- [x] Video: 3 s hook title card with the hackathon dates, burned-in English captions, Muse Image diagram scene, TIMESTAMPS.txt; 2:57 cut, 43.5 s X clip (v1.25)
- [x] Docs brought in line with the 1.25 re-cut (chapters, timestamps, 29 shots, 43.5 s clip) and the new evidence (EVAL, laptop view, static build, first_live_run) in SUBMISSION / JUDGING_MAP / JUDGE_FAQ; one-pager re-made (v1.25)
- [x] Flaky agent-log scroll test now waits on conditions (v1.25)
- [x] WhatsApp channel (Cloud API webhook, Graph API test double tests, `/wa` simulator) and an owner token for outcome and erase (v1.27)
- [x] New look: bengkel-sign design, Barlow, Lucide icons, light and dark theme (v1.28)
- [x] AI-generated sample photos, labelled, in place of the flat drawings; demo video re-shot at 1080p60, 2:53, X clip 43.5 s (v1.29.0)
- [x] PDF report, workshop sheet and share cards in the new look; friendly page for expired guide links; strict CSP and HSTS; STOP card on shared red-stop links; axe-core clean on every main screen (v1.29.1 to v1.29.4)
- [x] After the live run: eval re-run live, numbers in docs/EVAL.md (5 Nov 2026)
- [ ] Once deployed: open the live link a few minutes before a demo so the free server is awake (a brand-new visitor can't get the recording until the page itself loads)

## Could
- [x] Abuse guard (rate limit and daily spend cap) and security headers for the public deploy
- [x] PWA manifest (install to home screen)
- [x] Javanese strings for every UI label
- [x] mypy strict on all of api/, Playwright smoke in CI (6 browser tests)
- [x] Shopping links (Tokopedia/Shopee) and WhatsApp share of the parts list (v1.4.0)
- [x] Friendly errors, Try again, fault-injection tests (v1.5.0)
- [x] Workshop mode: large-print one-step-per-page PDF (v1.6.0)
- [x] jsdom headless UI test of web/app.js (v1.7.1)
- [x] "Under the hood" stage-to-model panel and PDF section (v1.7.0)
- [x] Fixture evaluation script with a markdown report, usable on real photos (v1.10.0)
- [x] Privacy: erase-now button and endpoint, hourly retention janitor (v1.11.0)
- [x] Fifth demo scenario: flat scooter tyre (v1.9.0)
- [x] Bengkel price vs DIY saving chip and PDF lines (v1.17.0)
- [x] Waiting-time steps with a countdown timer (v1.18.0)
- [x] Outcome buttons ("it works now"), PDF result line, garage total saved (v1.19.0)
- [x] "Before you start" tick list that locks the steps until confirmed (v1.20.0)
- [x] Live camera guide: SAM 3.1 on live frames with a canvas overlay (v1.21.0)
- [x] Hands-free voice commands with a push-to-talk fallback (v1.21.0)
- [x] Bengkel hand-off: WhatsApp summary, Maps search, mechanic brief PDF (v1.21.0)
- [x] Demo fallback on live API failure, flagged by deploy_check (v1.21.0)
- [x] Impact trial kit (outcome log → impact report) (v1.21.0)
- [x] Render free-plan deploy readiness and deploy_check.py (v1.21.0)
- [x] Agent log "What the AI did" on screen and in the PDF report (v1.22.0)
- [x] 1-tap guided demo and a compact, auto-folding tip bar (v1.22.0)
- [x] Prompt-injection hardening, follow-up rate limit, photo-check cap (v1.22.0)
- [x] Javanese demo answers, WCAG AA contrast, model chips and timer on progress (v1.22.0)
- [x] Streaming progress, tappable agent log, share card and Open Graph tags, gzip, favicon (v1.23.0)
