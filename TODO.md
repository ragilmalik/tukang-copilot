# TODO

Deadline: Thu Nov 5, 2026, 09:00 WIB (Nov 4, 9 PM ET). My own target: feature-complete Nov 3, 23:59 WIB.
Items marked (keys) need my keys or accounts.

## Now (1.30.0, 6 Nov)
- [x] Sample "plug cap" photo is checked on the step it shows (`sample_step`, api/sample_step.py), with a line saying which step; buttons say what each sample photo is
- [x] WhatsApp simulator label reads naturally in Bahasa and Basa Jawa ("menjalankan" / "nglakokake"), tests match
- [x] Full test run: non-browser 838/0, Playwright 127/0, ruff, mypy 162 files, offline smoke 69 checks, static build OK
- [x] Re-record the 1-tap demo from the live API (one yes/no question in every language, the sample photo passes on its step): 6 Nov 01:23 WIB, pipeline $0.18
- [ ] Commit and push

## Must (to submit)
Order: live run first, Baseten optional, real clip and trials, then repo/deploy, YouTube and X, submit.
- [ ] (keys) Meta key → `python scripts/set_keys.py` → ALL GOOD (claim the credits and set a spend limit on dev.meta.ai first), then `python scripts/first_live_run.py` → DONE (writes docs/LIVE_RUN.md)
- [ ] First live run on the 5 samples (no FALLBACK lines); fix whatever differs in the real API; update the META_API_NOTES ⚠️ items and the "Honest status" lines in WRITEUP/SUBMISSION
- [ ] (keys) Real photos and 5 user trials (docs/USER_TRIAL_KIT.md), then `scripts/impact_report.py`, replace the MOCK impact numbers, tune prompts
- [ ] (keys) Push to GitHub (`ragilmalik/tukang-copilot`) and deploy on Render (docs/DEPLOY.md, free plan); set `PUBLIC_BASE_URL`
- [ ] (keys) Host the static judge build (`python scripts/build_static.py`, then GitHub Pages or a Netlify drop; see `--help`) so judges get no cold start
- [ ] (keys) Optional, with the deploy: WhatsApp channel (docs/WHATSAPP.md: Meta app and test number, fill `WA_TOKEN`, `WA_PHONE_NUMBER_ID`, `WA_VERIFY_TOKEN`, `WA_APP_SECRET` in Render, paste the webhook URL); then one real chat test and update the "Honest status" lines
- [ ] `deploy_check.py <url> --live` → READY
- [ ] Phone test over 4G: camera, live guide, hands-free (Android Chrome jv-ID), WhatsApp hand-off, PDF
- [ ] (keys) Upload the video to YouTube (real recording per DEMO_SCRIPT.md, or the 2:53 backup cut) and post the X clip
- [ ] Fill in the links in README and SUBMISSION
- [ ] (keys) Paste the docs/SUBMISSION.md fields into Cerebral Valley (account ragilmalika) and submit before Nov 5 09:00 WIB
- [ ] (keys) Share docs/launch/COMMUNITY_VOTE_KIT.md when voting opens Tue Nov 10, 00:00 WIB

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
- [ ] After the live run: `python scripts/run_eval.py` stays green; add the live numbers to the docs
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
