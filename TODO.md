# TODO

Deadline: **Thu Nov 5, 2026, 09:00 WIB** (Nov 4, 9 PM ET). Internal target: feature-complete Nov 3, 23:59 WIB.
Owner: **M** = Malik, **H** = Malik.

## Must (to submit): see HANDOFF.md "Malik-only" list
- [ ] **M** Meta key → `python scripts/set_keys.py` → ALL GOOD (claim credits + set a spend limit on dev.meta.ai first), then `python scripts/first_live_run.py` → DONE (writes docs/LIVE_RUN.md)
- [ ] **H** First live run on the 5 samples (no FALLBACK lines); fix real-API differences; update META_API_NOTES ⚠️ items and the "Honest status" lines in WRITEUP/SUBMISSION
- [ ] **M** Real photos + 5 user trials (docs/USER_TRIAL_KIT.md) → **H** `scripts/impact_report.py`, replace MOCK impact numbers, tune prompts
- [ ] **M** Approve GitHub push (`ragilmalik/tukang-copilot`) + Render deploy (docs/DEPLOY.md, free plan); set `PUBLIC_BASE_URL`
- [ ] **M** Approve hosting the static judge build (`python scripts/build_static.py`, then GitHub Pages or Netlify drop; see `--help`): no cold start for judges
- [ ] **H** `deploy_check.py <url> --live` → READY
- [ ] **M** Phone test over 4G: camera, live guide, hands-free (Android Chrome jv-ID), WhatsApp hand-off, PDF
- [ ] **M** Upload the video to YouTube (real recording per DEMO_SCRIPT.md, or the 2:57 backup cut), post the X clip
- [ ] **H** Fill links in README + SUBMISSION
- [ ] **M** Paste docs/SUBMISSION.md fields into Cerebral Valley (account ragilmalika) and submit before Nov 5 09:00 WIB

## Should (scores better)
- [x] **H** Water pump mock scenario + fixtures (spec §8 case 2)
- [x] **H** Video capture (5–10 s → 3 sharpest frames)
- [x] **H** PDF export of the report + local "My garage" history (localStorage)
- [ ] **H** Open-weights run on Baseten (needs BASETEN_API_KEY); badge is built and shows when active
- [ ] **M** Post the X clip (draft in SUBMISSION.md, 45 s clip ready); engagement counts until Nov 8
- [x] **H** Screenshots + demo video + vertical clip (docs/demo/), regenerated for v1.23 (26 shots, 2:57 video, GIF)
- [x] **H** Re-shoot shots/video for the compact tip bar + PDF agent-log page (v1.23)
- [x] **H** Streamed partial results on the progress screen (object, SAM overlay, top cause as each stage finishes) (v1.23)
- [x] **H** Recorded 1-tap demo that plays when the free server sleeps or the phone is offline, labelled "Recorded demo" (v1.24, backlog J5)
- [x] **H** Skeptical-judge audit 5 fixes: red stop on screen, result opens at top, re-plan banner, keyboard focus, PDF wording, neutral landing picture (v1.24)
- [x] **H** Demo kit re-shot for v1.24 (27 shots incl. recorded demo, 2:57 video, 45 s X clip, GIF)
- [x] **H** Laptop view: phone frame + side panel with QR code, 1-tap demo, language switch (v1.25)
- [x] **H** Static judge build `scripts/build_static.py` (recorded demo, no server; not deployed) (v1.25)
- [x] **H** Offline eval `scripts/run_eval.py` → docs/EVAL.md (fixtures, 20 red-team, 7 injection; mock/fake labelled); safety gate fixed for 12 text + 7 plan misses (v1.25)
- [x] **H** `scripts/first_live_run.py` one-command first live repair → docs/LIVE_RUN.md (v1.25)
- [x] **H** Video: 3 s hook title card with hackathon dates, burned-in English captions, Muse Image diagram scene, TIMESTAMPS.txt; 2:57 cut, 43.5 s X clip (v1.25)
- [ ] **H** After the live run: `python scripts/run_eval.py` stays green; add live numbers to docs (docs lane)
- [ ] **M** Open the live link once a few minutes before judging/recording so the free server is awake (a brand-new visitor can't get the recording until the page itself loads)

## Could
- [x] Abuse guard (rate limit + daily spend cap) and security headers for the public deploy
- [x] PWA manifest (install to home screen)
- [x] Javanese strings for every UI label
- [x] mypy strict on all of api/, Playwright smoke in CI (6 browser tests)
- [x] Shopping links (Tokopedia/Shopee) + WhatsApp share of the parts list (v1.4.0)
- [x] Friendly errors + Try again + fault-injection tests (v1.5.0)
- [x] Workshop mode: large-print one-step-per-page PDF (v1.6.0)
- [x] jsdom headless UI test of web/app.js (v1.7.1)
- [x] "Under the hood" stage-to-model panel + PDF section (v1.7.0)
- [x] Fixture evaluation script with markdown report, usable on real photos (v1.10.0)
- [x] Privacy: erase-now button + endpoint, hourly retention janitor (v1.11.0)
- [x] Fifth demo scenario: flat scooter tyre (v1.9.0)
- [x] Bengkel price vs DIY saving chip + PDF lines (v1.17.0)
- [x] Waiting-time steps with countdown timer (v1.18.0)
- [x] Outcome buttons ("it works now"), PDF result line, garage total saved (v1.19.0)
- [x] "Before you start" tick list that locks the steps until confirmed (v1.20.0)
- [x] Live camera guide: SAM 3.1 on live frames with canvas overlay (v1.21.0)
- [x] Hands-free voice commands + push-to-talk fallback (v1.21.0)
- [x] Bengkel hand-off: WhatsApp summary, Maps search, mechanic brief PDF (v1.21.0)
- [x] Demo fallback on live API failure + deploy_check flags it (v1.21.0)
- [x] Impact trial kit (outcome log → impact report) (v1.21.0)
- [x] Render free-plan deploy readiness + deploy_check.py (v1.21.0)
- [x] Agent log "What the AI did" on screen and in the PDF report (v1.22.0)
- [x] 1-tap guided demo + compact, auto-folding tip bar (v1.22.0)
- [x] Prompt-injection hardening, follow-up rate limit, photo-check cap (v1.22.0)
- [x] Javanese demo answers, WCAG AA contrast, model chips + timer on progress (v1.22.0)
- [x] Streaming progress, tappable agent log, share card + Open Graph tags, gzip, favicon (v1.23.0)
