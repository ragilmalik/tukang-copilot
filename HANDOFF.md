# Handoff

The short version for whoever picks this up next: a judge, a contributor, or me in a month. Read this first, then [TODO.md](TODO.md).

## What this is

Tukang Copilot 1.31.1: a phone web app that looks at a photo of a broken motorbike, pump, tap, tyre or rice cooker, marks the parts with SAM 3.1, diagnoses and plans with Muse Spark 1.3, checks each step from a photo, re-plans, and stops dangerous jobs. Bahasa Indonesia, Basa Jawa and English. Repo: https://github.com/ragilmalik/tukang-copilot

## Run it

| You have | Do this | You get |
|---|---|---|
| Nothing | `./start.sh` (Mac/Linux) or `start.bat` (Windows), open http://localhost:8000 | Offline sample mode: pre-written answers, labelled on screen, free |
| A Meta Model API key | `python scripts/set_keys.py`, paste the key, restart | Live mode: every answer from the real Meta models, about $0.04 per repair |
| No server at all | Open `dist-static/` after `python scripts/build_static.py` | The recorded live demo, labelled as a recording |

Step by step: [docs/TUTORIAL.md](docs/TUTORIAL.md). Every setting: [docs/SETUP.md](docs/SETUP.md). Deploy: [docs/DEPLOY.md](docs/DEPLOY.md).

## Real vs sample

- **Real:** live mode answers, the recorded 1-tap demo (a live run from 6 Nov 2026), the live column of [docs/EVAL.md](docs/EVAL.md), [docs/LIVE_RUN.md](docs/LIVE_RUN.md), and the screenshots and video (real answers recorded on live runs and played back; the live camera guide ran live while filming).
- **Sample:** the photos in `samples/` are AI-generated and say so on the image. Offline mode answers are pre-written. Prices are estimates.
- **Not measured:** real owner trials.

## Test results (1.31.1)

1005 automated tests passed, 0 failed, 0 skipped; mypy strict clean on 166 files; ruff clean; offline HTTP smoke ALL PASSED (69 checks); static build and recorded-demo checks pass. Details: [docs/TEST_REPORT.md](docs/TEST_REPORT.md), [docs/VERIFICATION_REPORT.md](docs/VERIFICATION_REPORT.md). Re-run: [docs/TEST_CHECKLIST.md](docs/TEST_CHECKLIST.md).

## Where things are

- Code: `api/` (engine in `api/pipeline/engine.py`, every Meta call in `api/meta_client.py`), browser app in `web/`, prompts in `prompts/`, tests in `api/tests/`, scripts in `scripts/`.
- Understanding it: [docs/HOW_IT_WORKS.md](docs/HOW_IT_WORKS.md) (plain words), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/METHODS.md](docs/METHODS.md), [docs/AI_PIPELINE.md](docs/AI_PIPELINE.md).
- Results: [docs/REPORT.md](docs/REPORT.md).
- Submission text, field by field: [docs/SUBMISSION.md](docs/SUBMISSION.md); steps: [docs/SUBMISSION_CHECKLIST.md](docs/SUBMISSION_CHECKLIST.md).
- Demo media: [docs/demo/](docs/demo/README.md). Launch kit: [docs/launch/](docs/launch/).
- Copy of the deliverables (video, one-pager, guide PDF, repo zip): Google Drive folder "Meta Hackathon - Tukang Copilot" (private to my account): https://drive.google.com/drive/folders/1mxVXV1tgjCuxfKoSAHWJpc6V7Yz9vslt

## Before you change anything

Keys stay out of git: `scripts/set_keys.py` writes `.env`, and `.gitignore` covers it. Only `api/meta_client.py` talks
to Meta, and I'd keep it that way, because the per-repair cost cap and the log scrubber only see calls that go through
it.

After a change I run ruff, `mypy api --strict`, the tests, `python scripts/check_voice.py` (it keeps filler words and
dashes out of the docs and comments) and then `python scripts/make_test_report.py`, which rewrites docs/TEST_REPORT.md
from the real run. Then I update CHANGELOG, TODO and whichever docs the change touches. A change to the prompts or to
the session shape means re-recording the demo with `python scripts/record_replay.py` (needs the key, about $0.60) and
checking it with `--check`.

## Open items

Listed in [TODO.md](TODO.md) under "Only I can do these": the late-entry question for the organisers (the Cerebral Valley submit page showed "Event Finished" on 6 Nov at 09:29 WIB, so nothing was submitted), YouTube and X posts, an optional Render deploy, and rotating the Meta key after judging.
