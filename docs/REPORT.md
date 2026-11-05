# Project report: Tukang Copilot 1.30.0

Written 6 November 2026. This is the one document that says what I built, how well it works, what I measured, and what is still open. Every number here comes from a real run that is linked; nothing is projected.

## What (the product)

Tukang Copilot is a phone web app that helps people in Indonesia fix their own motorbike, water pump, tap, tyre or rice cooker. You take a photo, say what's wrong in Bahasa Indonesia, Basa Jawa or English, and it:

1. marks the exact parts on your own photo (SAM 3.1),
2. ranks the likely causes and asks one yes/no question when unsure (Muse Spark 1.3),
3. writes a step-by-step plan with tools, parts and estimated prices,
4. checks each finished step from a new photo,
5. re-plans for the next cause when it is still broken,
6. stops with a red STOP card, before spending anything, when the job is dangerous.

It also runs as a WhatsApp chat (webhook built and tested; not yet connected to a real number), keeps a PDF report for the mechanic, and plays a recorded live demo when the free server is asleep.

## Who and why

Owners who would otherwise pay a bengkel for a 10-minute job, or try a dangerous one alone. Mechanics get a report of what was already tried. The why is in [HOW_IT_WORKS.md](HOW_IT_WORKS.md) and [IMPACT.md](IMPACT.md).

## When and where

Built for the Meta Global AI Developer Hackathon (Indie track, theme Push the Frontier), in Semarang, from late October to 6 November 2026. The live runs were on 5 and 6 November 2026 against `api.meta.ai`.

## How (the build)

Python 3.11 and FastAPI on the server, plain JavaScript in the browser, no database. Five Meta models: Muse Spark 1.3 (look, diagnose, plan, check), SAM 3.1 (masks), Muse Image (diagrams), Muse Voice Transcribe and Muse Spark 1.2 (voice, including Javanese). Details: [ARCHITECTURE.md](ARCHITECTURE.md), [METHODS.md](METHODS.md), [AI_PIPELINE.md](AI_PIPELINE.md).

## Results on the real Meta API

From [LIVE_RUN.md](LIVE_RUN.md) and [EVAL.md](EVAL.md), 5 November 2026:

| Measure | Result |
|---|---|
| Scenarios run live end to end | 7 of 7 (motorbike, re-plan, pump, tap, tyre, rice cooker, brake failure) |
| Top cause and safety level correct on the sample fixtures | 9 of 9 |
| Dangerous owner messages stopped before any model call | 23 of 23 |
| Dangerous plan steps stopped | 10 of 10 |
| False stops on everyday jobs | 0 of 17 |
| Prompt-injection cases resisted | 4 of 4 that ran |
| SAM 3.1 parts found | 29 of 30 across the six runs that reached the models |
| Time from photo to plan, median | 83 s |
| Cost per repair, median | $0.044 |

## Engineering checks (this release)

- {{TESTS}} automated tests passed, 0 failed, 0 skipped ([TEST_REPORT.md](TEST_REPORT.md)).
- mypy strict: no issues in {{MYPY_FILES}} files. ruff: clean.
- HTTP smoke on a running offline server: ALL PASSED, {{SMOKE}} checks.
- Recorded demo: re-recorded live on 6 November 2026, 01:23 WIB; one yes/no question in each language; the sample photo passes on the step it shows.
- Static judge build: builds and passes its own check.

## What changed in 1.30.0 (from the live runs)

Fourteen fixes found by running the real API and reviewing every screen, each with a test. The main ones: structured calls always stream (the API returned 504 on long answers), every schema field is required (the API dropped optional ones), SAM masks are clipped to the part's box (one mask tinted a whole wall), the follow-up is one yes/no question, the sample photo is checked on the step it shows, the red-stop PDF no longer lists parts to buy, and Basa Jawa wording fixes. Full list: [CHANGELOG.md](../CHANGELOG.md).

## What is real, what is sample, what is not measured

- Real: all live answers, the recorded demo, the eval's live column, the screenshots and video (shot against the live API).
- Sample: the photos are AI-generated and labelled on the image itself. Offline sample mode uses pre-written answers and says so on screen. Prices are labelled estimates.
- Not measured: real owner trials and real-world photos. I make no claim about money saved by real people.

## Known limits

- One close-up sample photo fits only the steps it shows; per-step real photos would be better ([SUGGESTIONS.md](SUGGESTIONS.md) item 3).
- Repairs take about 80 seconds on the live API, mostly model time.
- The free host forgets repairs on restart.
- WhatsApp is not connected to a real number yet.

## Next

Ten suggestions, most useful first, are in [SUGGESTIONS.md](SUGGESTIONS.md). The dated plan is in [ROADMAP.md](ROADMAP.md).
