# Submission checklist

Deadline: Wed Nov 4, 2026, 9:00 PM ET, which is Thu Nov 5, 2026, 09:00 WIB. I'm aiming to submit by Wed Nov 4 evening WIB.

The "Needs" column marks the steps that need my keys or accounts. Nothing goes public until I decide it does. The form only takes text and links (no file uploads), and every field is already written out in docs/SUBMISSION.md.

| # | Step | Needs | How to check it's done |
|---|---|---|---|
| 1 | Claim the Meta credits, set a spend limit, create a key (dev.meta.ai), run `python scripts/set_keys.py` | my keys | Ends with ALL GOOD (every model PASS) |
| 2 | Optional open weights: Baseten key, then `set_keys.py` again | my keys | Header shows the "🔓 Muse Spark Open (open weights)" badge |
| 3 | First live run on the 5 samples; tune prompts if needed; update the "Honest status" lines in WRITEUP/SUBMISSION | live key | `smoke_e2e.py http://localhost:8000` all PASS in LIVE mode, no `FALLBACK` lines |
| 4 | Real photos and 5 user trials (docs/USER_TRIAL_KIT.md), then `scripts/impact_report.py` | me + testers | docs/IMPACT.md no longer MOCK-stamped |
| 5 | Make the GitHub repo `ragilmalik/tukang-copilot` (MIT) public and push | my GitHub | Repo page shows the README with screenshots; `git ls-files .env` prints nothing |
| 6 | Deploy on Render (render.yaml, free plan, docs/DEPLOY.md); set `PUBLIC_BASE_URL` to the https URL | my Render | `python scripts/deploy_check.py https://<app>.onrender.com --live` says READY, with no "silently used demo answers" FAIL |
| 7 | Phone test over 4G: camera, live camera guide, hands-free, check-my-step, hand-off (WhatsApp opens), PDF, install to home screen | my phone | Every row of the manual QA in docs/TESTING.md ticked |
| 8 | Video: record the real one (docs/DEMO_SCRIPT.md) or use the backup docs/demo/tukang-copilot-demo.mp4 (2:53, demo mode, labelled) | my YouTube | Uploaded to YouTube (Unlisted is fine), opens logged out, under 3:00 |
| 9 | Post on X with docs/demo/tukang-copilot-x-vertical.mp4 (43.5 s); the draft post is in SUBMISSION.md | my X | Post link copied |
| 10 | Fill in the links in README and docs/SUBMISSION.md (live, video, X) | nothing | No `[…]` / `_add …_` placeholders left |
| 11 | Submit on Cerebral Valley (account ragilmalika): paste the SUBMISSION.md fields in order | my account | Confirmation shown or emailed before 09:00 WIB Nov 5 |

Before submitting, run `scripts/check_all.sh` and wait for ALL CHECKS PASSED. On a slow machine, run the fast and slow pytest chunks separately.
