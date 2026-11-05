# TODO

The entry deadline was Thu Nov 5, 2026, 09:00 WIB (Nov 4, 9 PM ET). Code is done; what is left is media, final numbers and the steps only I can do with my accounts.

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
- [ ] Watch test_playwright_motion: failed once in 4 runs on 6 Nov, passed 3 times since; find the flaky wait

## Now (1.30.0, 6 Nov)
- [x] Sample "plug cap" photo is checked on the step it shows (`sample_step`, api/sample_step.py), with a line saying which step; buttons say what each sample photo is
- [x] WhatsApp simulator label reads naturally in Bahasa and Basa Jawa ("menjalankan" / "nglakokake"), tests match
- [x] Full test run: non-browser 838/0, Playwright 127/0, ruff, mypy 162 files, offline smoke 69 checks, static build OK
- [x] Re-record the 1-tap demo from the live API (one yes/no question in every language, the sample photo passes on its step): 6 Nov 01:23 WIB, pipeline $0.18
- [x] Commit and push (main at 9179f81 on 6 Nov)

## Must (to submit)
Done by me (code, docs, media):
- [x] Meta key set, `check_keys.py` passes all 5 required models (5 Nov 2026)
- [x] Live runs on 7 scenarios and the live eval (docs/LIVE_RUN.md, docs/EVAL.md); fixes from them shipped in 1.30.0
- [x] Public repo https://github.com/ragilmalik/tukang-copilot, history cleaned of private data
- [x] Full doc set: TUTORIAL, HOW_TO_USE, HOW_IT_WORKS, ARCHITECTURE, METHODS, SUGGESTIONS, TEST_CHECKLIST, VERIFICATION_REPORT, REPORT, HANDOFF
- [ ] Final media from the live API: screenshots, hero.gif, thumbnail, og image, demo video under 3:00, vertical clip (in progress)
- [ ] Fill the measured numbers in README, SUBMISSION, WRITEUP, JUDGING_MAP, SUBMISSION_CHECKLIST
- [ ] Rebuild the one-pager PDF and the guide bundle, fresh-clone check, Drive upload

Only I can do these (my accounts):
- [ ] Check with the organisers whether a late entry is accepted (the form closed Thu Nov 5, 09:00 WIB)
- [ ] Upload the video to YouTube with docs/launch/YOUTUBE.md, then put the link in README and SUBMISSION
- [ ] Post the X thread (docs/launch/X_THREAD.md) with the vertical clip
- [ ] Paste the docs/SUBMISSION.md fields into Cerebral Valley and submit; answer the AI-tools question honestly (the sample photos are AI-generated and labelled)
- [ ] Deploy on Render (docs/DEPLOY.md) if I want a live link, then `deploy_check.py <url> --live`
- [ ] Rotate the Meta key after judging
- [ ] Share docs/launch/COMMUNITY_VOTE_KIT.md when voting opens Tue Nov 10, 00:00 WIB
- [ ] Real photos and 5 owner trials (docs/USER_TRIAL_KIT.md), then `scripts/impact_report.py`

## Should (scores better)
- [x] Water pump mock scenario and fixtures (spec §8 case 2)
- [x] Video capture (5 to 10 s, 3 sharpest frames)
- [x] PDF export of the report, plus local "My garage" history (localStorage)
- [ ] (keys) Open-weights run on Baseten (needs BASETEN_API_KEY); the badge is built and shows when active
- [ ] (keys) Post the X thread (docs/launch/X_THREAD.md, 43.5 s clip ready) before submitting; engagement counts until Nov 8 11:59 PM ET (Nov 9 11:59 WIB)
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
- [ ] Open the live link a few minutes before judging or recording so the free server is awake (a brand-new visitor can't get the recording until the page itself loads)

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
