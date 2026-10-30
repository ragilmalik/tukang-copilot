# Submission checklist

Deadline: **Wed Nov 4, 2026, 9:00 PM ET = Thu Nov 5, 2026, 09:00 WIB.** Aim to submit by Wed Nov 4 evening WIB.
**M** = Malik does it (needs his accounts or approval). **H** = Malik does it. Nothing public happens without Malik's yes.

| # | Step | Who | How to check it's done |
|---|---|---|---|
| 1 | Say yes to a public GitHub repo `tukang-copilot` (MIT) | M | Malik pushes; repo page shows README with screenshots |
| 2 | CI green on GitHub (ruff, mypy strict, tests, browser smoke) | H | Green tick on the latest commit |
| 3 | Claim $150 Meta credits, add card, set a spend limit (dev.meta.ai) | M | Billing page shows credits + limit |
| 4 | Create a Meta API key and run `python scripts/set_keys.py` (paste key, Enter) | M | Ends with **ALL GOOD** (5 × PASS) |
| 5 | First live run on the 4 samples; fix any differences | H | `smoke_e2e.py http://localhost:8000` all PASS in LIVE mode |
| 6 | Optional open weights: Baseten key → `set_keys.py` again | M | Header shows "🔓 Muse Spark Open (open weights)" badge |
| 7 | Send 8–10 real photos (bike plug area, pump, tap/hose, rice cooker) | M | Malik replaces `api/tests/fixtures/standin_*` names with real ones |
| 8 | Deploy on Render (render.yaml), put keys in Environment | M+H | `python scripts/smoke_e2e.py https://<app>.onrender.com` passes |
| 9 | Phone test over 4G: camera, mic, video, check-my-step, PDF, install to home screen | M | Every row in docs/TESTING.md manual QA ticked |
| 10 | Record the real 3-min video (docs/DEMO_SCRIPT.md); backup = docs/demo/tukang-copilot-demo.mp4 | M | Uploaded to YouTube as Public or Unlisted, opens logged-out |
| 11 | Fill links in README + docs/SUBMISSION.md (repo, live, video, X) | H | No `_add …_` placeholders left |
| 12 | Post on X with the vertical clip (docs/demo/tukang-copilot-x-vertical.mp4); drafts in SUBMISSION.md | M | Post link copied |
| 13 | Submit on Cerebral Valley (account ragilmalika), paste fields from docs/SUBMISSION.md | M | Confirmation shown/emailed before 09:00 WIB Nov 5 |

Before submitting, run `scripts/check_all.sh` → **ALL CHECKS PASSED**, and make sure `.env` is not in the repo (`git ls-files .env` prints nothing).
