# Submission checklist

Deadline: **Wed Nov 4, 2026, 9:00 PM ET = Thu Nov 5, 2026, 09:00 WIB.** Aim to submit by Wed Nov 4 evening WIB.
**M** = Malik does it (needs his accounts or approval). **H** = Malik does it. Nothing public happens without Malik's yes.
The form takes only text and links (no file uploads): every field is pre-written in **docs/SUBMISSION.md**.

| # | Step | Who | How to check it's done |
|---|---|---|---|
| 1 | Claim Meta credits, set a spend limit, create a key (dev.meta.ai) and run `python scripts/set_keys.py` | M | Ends with **ALL GOOD** (every model PASS) |
| 2 | Optional open weights: Baseten key → `set_keys.py` again | M | Header shows the "🔓 Muse Spark Open (open weights)" badge |
| 3 | First live run on the 5 samples; tune prompts if needed; update the "Honest status" lines in WRITEUP/SUBMISSION | H | `smoke_e2e.py http://localhost:8000` all PASS in LIVE mode, no `FALLBACK` lines |
| 4 | Real photos + 5 user trials (docs/USER_TRIAL_KIT.md), then `scripts/impact_report.py` | M+H | docs/IMPACT.md no longer MOCK-stamped |
| 5 | Say yes to the public GitHub repo `ragilmalik/tukang-copilot` (MIT) | M | Malik pushes; repo page shows README with screenshots; `git ls-files .env` prints nothing |
| 6 | Deploy on Render (render.yaml, free plan, docs/DEPLOY.md); set `PUBLIC_BASE_URL` to the https URL | M+H | `python scripts/deploy_check.py https://<app>.onrender.com --live` → **READY**, no "silently used demo answers" FAIL |
| 7 | Phone test over 4G: camera, live camera guide, hands-free, check-my-step, hand-off (WhatsApp opens), PDF, install to home screen | M | Every row in docs/TESTING.md manual QA ticked |
| 8 | Video: record the real one (docs/DEMO_SCRIPT.md) or use the backup docs/demo/tukang-copilot-demo.mp4 (2:57, demo mode, labelled) | M | Uploaded to YouTube (Unlisted is fine), opens logged-out, under 3:00 |
| 9 | Post on X with docs/demo/tukang-copilot-x-vertical.mp4 (43.5 s); draft post in SUBMISSION.md | M | Post link copied |
| 10 | Fill links in README + docs/SUBMISSION.md (live, video, X) | H | No `[…]` / `_add …_` placeholders left |
| 11 | Submit on Cerebral Valley (account ragilmalika): paste the SUBMISSION.md fields in order | M | Confirmation shown/emailed before 09:00 WIB Nov 5 |

Before submitting, run `scripts/check_all.sh` → **ALL CHECKS PASSED** (on a slow machine run the fast and slow pytest chunks separately).
