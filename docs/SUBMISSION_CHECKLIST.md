# Submission checklist

Published deadline: Wed Nov 4, 2026, 9:00 PM ET, which is Thu Nov 5, 2026, 09:00 WIB. Check the event page for any
change before relying on it.

The "Needs" column marks the steps that need my keys or accounts. Nothing goes public until I decide it does. The form
only takes text and links (no file uploads), and every field is written out in docs/SUBMISSION.md.

| # | Step | Needs | How to check it's done | Status |
|---|---|---|---|---|
| 1 | Meta key: credits claimed, spend limit set, `python scripts/set_keys.py` | my key | Ends with ALL GOOD | done 5 Nov |
| 2 | Live runs on all sample scenarios, results written up | my key | docs/LIVE_RUN.md and the live column in docs/EVAL.md | done 5 Nov |
| 3 | Recorded 1-tap demo, screenshots and video made from live answers | my key | `web/replay/demo.json` says live; video corner note says "Live Meta API answers" | done 5 Nov |
| 4 | Make the GitHub repo `ragilmalik/tukang-copilot` (MIT) public and push | my GitHub | Repo opens logged out; `git ls-files .env` prints nothing | done (public, MIT, checked 6 Nov) |
| 5 | Deploy on Render (render.yaml, free plan, docs/DEPLOY.md); set `PUBLIC_BASE_URL` to the https URL | my Render | `python scripts/deploy_check.py https://<app>.onrender.com --live` says READY | open |
| 6 | Phone test over 4G: camera, live camera guide, hands-free, check-my-step, hand-off (WhatsApp opens), PDF, install to home screen | my phone | Every row of the manual QA in docs/TESTING.md ticked | open |
| 7 | Upload docs/demo/tukang-copilot-demo.mp4 (2:54) to YouTube with docs/launch/YOUTUBE.md | my YouTube | Opens logged out, under 3:00 | open |
| 8 | Post on X with docs/demo/tukang-copilot-x-vertical.mp4 (43.5 s) and docs/launch/X_THREAD.md | my X | Post link copied | open |
| 9 | Fill in `[LIVE_URL]`, `[YOUTUBE_URL]`, `[X_POST_URL]` in README, docs/SUBMISSION.md and docs/launch | nothing | `grep -rn "_URL\]" README.md docs` prints only lines I chose to leave | open |
| 10 | Submit on Cerebral Valley (account ragilmalika): paste the SUBMISSION.md fields in order | my account | Confirmation shown or emailed | not submitted: on 6 Nov 2026 at 09:29 WIB, signed in as ragilmalika (Google), the submit page showed a disabled "Event Finished" button and "That's time! All submissions are due now." No form opened and nothing was sent. Only a late entry the organisers accept is left |
| 11 | Optional: one real Muse Spark Open run on Baseten before claiming the open-weights prize | Baseten key | Header badge on and a logged repair in docs/LIVE_RUN.md | open |
| 12 | Optional: real photos and user trials (docs/USER_TRIAL_KIT.md), then `scripts/impact_report.py` | me + testers | docs/IMPACT.md shows real repairs | open |

Before submitting, run `scripts/check_all.sh` and wait for ALL CHECKS PASSED. On a slow machine, run the test files in
smaller groups (docs/TESTING.md).
