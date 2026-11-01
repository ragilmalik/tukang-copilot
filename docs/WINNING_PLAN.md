# Winning plan: official judging criteria → features

Sources (fetched 2026-10-30): official page https://dev.meta.ai/events/global-hackathon ; Official Rules summary at
https://madrobot.blog/2026/10/03/meta-global-ai-developer-hackathon-1-million-prizes-muse-model-api/ (the Cerebral
Valley rules/waiver page needs sign-in). Spec section: SPEC.md §17.

| Criterion (weight) | What judges look for | Our evidence | Status |
|---|---|---|---|
| Impact (30%) | Real-world potential, who benefits, could it become a product | 4 Indonesian scenarios (motorbike, water pump, faucet, rice cooker); Bahasa / Basa Jawa / English; PDF report for a mechanic; My garage; money-saved shown as an estimate | ✅ built · real Semarang photos still needed from Malik |
| Creative use of Meta AI tools (25%) | Several Meta models doing real work | Voice Transcribe → Spark vision → SAM 3.1 masks on the user's photo → Spark diagnose/plan → Muse Image edit of the user's photo → Spark verifies each step; Muse Spark Open (open weights) switch with visible badge | ✅ built · first live run with a real key pending |
| Demo incl. video (25%) | Clear, working, compelling | 2:37 demo-mode video with captions + voice-over, 36 s vertical X clip, 14 screenshots, architecture diagram (docs/demo/); script for the real-phone video (DEMO_SCRIPT.md) | ✅ backup video · real-phone video = Malik |
| Technical depth & execution (20%) | Ambition, quality, does it work | Typed pipeline, JSON-schema outputs with retry, cost cap, 3-layer safety gate in code, mypy strict, ruff, 120+ tests incl. Playwright browser smoke, CI, video→sharpest-frames, PWA, one-step key swap with checks | ✅ |
| Indie lens: "creativity, technical ambition, and whether it works" | | Plan → act → verify → re-plan → escalate loop that checks the physical world with the camera | ✅ |

Prizes: Indie $150K/$100K/$75K/$50K/$25K. Bonus prizes up to $50K total (examples given: public vote, most viral), announced ~Nov 10.
✅ Verified 2026-11-01 from the Participant Guide (cerebralvalley.ai/e/meta-ai-developer-hackathon/details) and the kickoff slide: Most Viral $20K, Best Build on Meta Open Weights $10K, Community Vote $10K, Best Agentic Use-Case $5K, Best Creative Build (Muse Image or Muse Wonder) $5K. Exact judging rules per prize: docs/JUDGING_MAP.md.

## Backlog status (v2)
| Item | Status | Where |
|---|---|---|
| Water pump flow | ✅ | api/pipeline/mock.py, samples/pump.jpg |
| Video capture (5–10 s → 3 frames) | ✅ sharpest frame per third + clip sound as voice | api/pipeline/media.py `extract_frames`, api/main.py |
| PDF repair report | ✅ | api/render/report_pdf.py, `GET /api/sessions/{id}/report.pdf` |
| Garage / history | ✅ phone-only (localStorage) | web/app.js |
| Open-weights badge | ✅ only when really active (flag + Baseten key) | web/app.js `badges()`, `/api/health.open_weights` |
| Indonesian / Javanese strings | ✅ every UI string in jv (ngoko); test enforces coverage | web/app.js, api/tests/test_i18n.py |
| PWA | ✅ manifest, icons, shell-only service worker | web/manifest.webmanifest, web/sw.js |
| Safety escalation polish | ✅ STOP card: why, do-this-now, service-centre search, PDF, 112 | web/app.js `renderStop` |
| ~10 labelled stand-in photo fixtures | ✅ 14 (10 + 4 tyre), red "STAND-IN" banner + EXIF note | api/tests/fixtures, scripts/make_fixtures.py |
| Playwright smoke | ✅ 6 browser tests; skip cleanly without Chromium | api/tests/test_playwright_smoke.py |
| Demo video, screenshots, diagram | ✅ demo-mode backup | docs/demo/, docs/img/architecture.png |
| Real-key run, real photos, deploy, real video, submit | ⏳ needs Malik | docs/SUBMISSION_CHECKLIST.md |
