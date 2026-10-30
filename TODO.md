# TODO

Deadline: **Thu Nov 5, 2026, 09:00 WIB** (Nov 4, 9 PM ET). Internal target: feature-complete Nov 3, 23:59 WIB.
Owner: **M** = Malik, **H** = Malik.

## Must (to submit)
- [ ] **M** Say yes to creating the public GitHub repo `tukang-copilot` → **H** pushes, CI goes green
- [ ] **M** Claim $150 Meta credits, add card, set spend limit on dev.meta.ai
- [ ] **M** Create Meta API key → run `python scripts/set_keys.py` → ALL GOOD
- [ ] **H** First live run on the samples; fix any real-API differences; update META_API_NOTES ⚠️ items
- [ ] **M** Send 8–10 real photos (bike plug area, water pump, tap/hose, rice cooker)
- [ ] **H** Tune prompts on real photos; record results in TEST_REPORT manual QA table
- [ ] **H/M** Deploy on Render (render.yaml), redeem a Render credit, `smoke_e2e.py <url>` passes
- [ ] **M** Phone test over 4G (camera + mic need https)
- [ ] **M** Record the 3-min video (DEMO_SCRIPT.md), upload to YouTube (backup cut ready: docs/demo/tukang-copilot-demo.mp4)
- [ ] **H** Fill links in README + SUBMISSION, regenerate TEST_REPORT
- [ ] **M** Submit on Cerebral Valley (account ragilmalika) before Nov 5 09:00 WIB

## Should (scores better)
- [x] **H** Water pump mock scenario + fixtures (spec §8 case 2)
- [x] **H** Video capture (5–10 s → 3 sharpest frames)
- [x] **H** PDF export of the report + local "My garage" history (localStorage)
- [ ] **H** Open-weights run on Baseten (needs BASETEN_API_KEY); badge is built and shows when active
- [ ] **M** Post the X clip (drafts in SUBMISSION.md); engagement counts until Nov 8
- [x] **H** Screenshots + demo video + vertical clip (docs/demo/)

## Could
- [x] Abuse guard (rate limit + daily spend cap) and security headers for the public deploy
- [x] PWA manifest (install to home screen)
- [x] Javanese strings for every UI label
- [x] mypy strict on all of api/, Playwright smoke in CI (6 browser tests)
- [x] Shopping links (Tokopedia/Shopee) + WhatsApp share of the parts list (v1.4.0)
- [x] Friendly errors + Try again + fault-injection tests (v1.5.0)
- [x] Workshop mode: large-print one-step-per-page PDF (v1.6.0)
- [x] "Under the hood" stage-to-model panel + PDF section (v1.7.0)
