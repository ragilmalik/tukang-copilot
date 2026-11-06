# Handoff

My notes for whoever picks this up next: a contributor, a friend helping me test, or me in a month. Read this first, then [TODO.md](TODO.md).

## What this is

Tukang Copilot 1.33.1 is my own open-source project (MIT). It is a phone web app that looks at a photo of a broken motorbike, pump, tap, tyre or rice cooker, marks the parts with SAM 3.1, diagnoses and plans with Muse Spark 1.3, checks each step from a photo, re-plans, and stops dangerous jobs. It speaks Bahasa Indonesia, Basa Jawa and English. I build it alone in Semarang. Repo: https://github.com/ragilmalik/tukang-copilot

Release 1.33.0 (tag v1.33.0 on 1156e90): https://github.com/ragilmalik/tukang-copilot/releases/tag/v1.33.0, with the repo zip (154.2 MB), the film and the vertical clip as downloads.

History in one line: I built it first for the Meta AI developer hackathon (Oct to Nov 2026); the submission page had closed when I tried on 6 Nov 2026, so nothing was submitted. The papers from that event are in [docs/archive/hackathon/](docs/archive/hackathon/README.md) and no longer drive any decision.

## Run it

| You have | Do this | You get |
|---|---|---|
| Nothing | `./start.sh` (Mac/Linux) or `start.bat` (Windows), open http://localhost:8000 | Offline sample mode: pre-written answers, labelled on screen, free |
| A Meta Model API key | `python scripts/set_keys.py`, paste the key, restart | Live mode: every answer from the real Meta models, about $0.04 per repair |
| No server at all | `python scripts/build_static.py`, then serve `dist-static/` with any static file server | The recorded live demo, labelled as a recording |

Step by step: [docs/TUTORIAL.md](docs/TUTORIAL.md). Every setting: [docs/SETUP.md](docs/SETUP.md). Deploy: [docs/DEPLOY.md](docs/DEPLOY.md).

## Real vs sample

- **Real:** live mode answers, the recorded 1-tap demo (a live run from 6 Nov 2026, 14:01 WIB), the live column of [docs/EVAL.md](docs/EVAL.md), [docs/LIVE_RUN.md](docs/LIVE_RUN.md), and the screenshots, film and GIF (real answers recorded on the live run of 6 Nov 2026 and played back; only the older `16_live_guide` screenshot called SAM 3.1 live). The film opens on AI-generated scenes, labelled on screen; how it is built and measured is in [docs/demo/README.md](docs/demo/README.md).
- **Earlier photo set:** the EVAL and LIVE_RUN numbers (median 83 s and $0.044 per repair, 33 of 33 dangerous cases stopped) come from 5 Nov 2026, on the sample photos used before 1.33.0. I have not run the eval again on the new photos.
- **Sample:** the photos in `samples/` are AI-generated and say so on the image. Offline mode answers are pre-written. Prices are estimates.
- **Not measured:** real owner trials and photos of real broken things.

## Test results (1.33.1)

1126 automated tests passed, 0 failed, 0 skipped (973 without a browser, 153 in real Chromium), run of 7 Nov 2026, 01:21 WIB on the 1.33.1 code before its commit (the tree over bdefe47); `mypy api --strict` clean on 175 files and `mypy --strict .` (whole repo) on 197; ruff clean; offline HTTP smoke ALL PASSED (77 checks, port 8765); `scripts/check_voice.py` 0 hits; every relative Markdown link resolves (test_doc_links.py). Details: [docs/TEST_REPORT.md](docs/TEST_REPORT.md), [docs/VERIFICATION_REPORT.md](docs/VERIFICATION_REPORT.md). Re-run: [docs/TEST_CHECKLIST.md](docs/TEST_CHECKLIST.md).

## Where things are

- Code: `api/` (engine in `api/pipeline/engine.py`, every Meta call in `api/meta_client.py`), browser app in `web/`, prompts in `prompts/`, tests in `api/tests/`, scripts in `scripts/`.
- Understanding it: [docs/HOW_IT_WORKS.md](docs/HOW_IT_WORKS.md) (plain words), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/METHODS.md](docs/METHODS.md), [docs/AI_PIPELINE.md](docs/AI_PIPELINE.md).
- Results: [docs/REPORT.md](docs/REPORT.md). Write-up: [docs/WRITEUP.md](docs/WRITEUP.md).
- Demo media: [docs/demo/](docs/demo/README.md) (118 screenshots listed in [INDEX.md](docs/demo/screenshots/INDEX.md)). Launch kit: [docs/launch/](docs/launch/) (YouTube text, one-pager, marketing images and their claims table).
- Copy of the deliverables (repo zip with a LINKS.txt, film, vertical clip, captions, one-pager, guide PDF, screenshots): my Google Drive folder "Meta Hackathon - Tukang Copilot" (private to my account; the name is from before the project went personal): https://drive.google.com/drive/folders/1mxVXV1tgjCuxfKoSAHWJpc6V7Yz9vslt. The 1.33.0 files (136, from commit 1156e90) sit at the top with screenshots in a subfolder; the 1.32.0 copies sit in its "old-1.32.0" subfolder.

## Before you change anything

Keys stay out of git: `scripts/set_keys.py` writes `.env`, and `.gitignore` covers it. Only `api/meta_client.py` talks
to Meta, and I'd keep it that way, because the per-repair cost cap and the log scrubber only see calls that go through
it.

After a change I run ruff, `mypy api --strict`, `mypy --strict .`, the tests, `python scripts/check_voice.py` (it keeps filler words and
dashes out of the docs and comments) and then `python scripts/make_test_report.py`, which rewrites docs/TEST_REPORT.md
from the real run. Then I update CHANGELOG, TODO and whichever docs the change touches. A change to the prompts or to
the session shape means re-recording the demo with `python scripts/record_replay.py` (needs the key, about $0.60) and
checking it with `--check`. A moved or renamed doc needs its links fixed; test_doc_links.py finds the broken ones.

## Open items

Listed in [TODO.md](TODO.md) under "Only I can do these": listening to the film by ear, re-checking the music licence, YouTube and X posts if I want them, an optional Render deploy, real photos and owner trials, and rotating the Meta key.
