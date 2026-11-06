# Project report: Tukang Copilot 1.33.1

Written 6 November 2026 by me, Malik, and brought up to 1.33.1 on 7 November. Tukang Copilot is my own open-source project. This is the one document that says what I built, how well it works, what I measured, and what is still open. Every number here comes from a real run that is linked; nothing is projected.

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

Built by me alone in Semarang, from 30 October 2026 (first commit) to now. I first built it for the Meta AI developer hackathon (Oct to Nov 2026); the submission page had closed when I tried on 6 November, so nothing was submitted, and I carry it on as a personal project. The live runs were on 5 and 6 November 2026 against `api.meta.ai`.

## How (the build)

Python 3.11 and FastAPI on the server, plain JavaScript in the browser, no database. Five Meta models: Muse Spark 1.3 (look, diagnose, plan, check), SAM 3.1 (masks), Muse Image (diagrams), Muse Voice Transcribe and Muse Spark 1.2 (voice, including Javanese). Details: [ARCHITECTURE.md](ARCHITECTURE.md), [METHODS.md](METHODS.md), [AI_PIPELINE.md](AI_PIPELINE.md).

## Results on the real Meta API

From [LIVE_RUN.md](LIVE_RUN.md) and [EVAL.md](EVAL.md), 5 November 2026. These ran on the earlier set of AI-generated sample photos; the photos changed in 1.33.0 and the eval has not been run again on the new ones:

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

- 1126 automated tests passed, 0 failed, 0 skipped ([TEST_REPORT.md](TEST_REPORT.md), run of 7 Nov 2026, 01:21 WIB on the 1.33.1 code before its commit): 973 without a browser, 153 in real Chromium.
- mypy strict: `mypy api --strict` no issues in 175 files, `mypy --strict .` (the whole repo) none in 197. ruff: clean. `scripts/check_voice.py`: 0 hits.
- HTTP smoke on a running offline server: ALL PASSED, 77 checks.
- Recorded demo: re-recorded live on 6 November 2026, 14:01 WIB, on the new photorealistic sample photos. The plug cap is visibly off in the new motorbike photo, so the model was 85 to 88% sure of the cause in each language and asked no follow-up question (it asks only under 60%); the sample photo passes on the step it shows.
- Static build: builds and passes its own check.

## What changed in 1.33.1 (a recheck and bug hunt)

I cloned 1.33.0 fresh, checked it, and then looked for bugs where faults are likely. I found and fixed 9, each with a test that failed on the old code first. The one that mattered most: when the disk filled up in the middle of a repair, every save failed, the last one too, so the repair said "running" with no worker left, and the phone spun for 7.5 minutes until a server restart. It now shows "the server could not save it" with Try again after a minute, in the web app and in WhatsApp. The others: PDFs written in one step (a parallel download could get half a file, and an erase during drawing left the owner's report on disk), the live camera guide now respects the daily spend cap, a failed Muse Image download is an error instead of a broken diagram, SAM 3.1 waits between network retries, the service worker shows the cached app when the server answers 5xx and never serves HTML in place of a script, the progress screen no longer shifts as notes arrive (layout shift 0.007 to 0), and `mypy --strict .` over the whole repo went from 21 errors to 0. Two older open items (the header language pill at 390 px and the Basa Jawa demo button text) turned out fine. No prompt, safety rule or recording changed, and I made no Meta call. Full list: [CHANGELOG.md](../CHANGELOG.md) 1.33.1.

## What changed in 1.33.0 (new photos and media)

I wanted more realistic sample photos, images and video, a more natural voice and better music. 1.33.0 has new photorealistic sample photos (still AI-generated and labelled on the image), and I recorded the 1-tap demo again on them from the live API on 6 November 2026 at 14:01 WIB. On the new motorbike photo the model was 85 to 88% sure the plug cap was off, so it asked no question, and the recorder had to learn to record what the model did instead of insisting on a question. Four more live sessions (pump, rice cooker red stop, tyre in Basa Jawa, tap with a diagram) feed the screenshots. All 118 screenshots are listed in docs/demo/screenshots/INDEX.md, 7 of them still from the previous photo set and marked. The marketing images, the 2:25 film, the 31.4 s vertical clip and the 2.92 MB GIF are new, with a per-sentence voice-over and licensed music (CC BY 3.0). A fix in the screenshot script came out of it: recorded sessions were opened without the owner's token, so some screens showed 403 errors. Full list: [CHANGELOG.md](../CHANGELOG.md) 1.33.0.

## What changed in 1.32.0 (a weakness hunt)

CI found a real race in 1.31.1 (a quick answer to the follow-up question was overwritten by the worker's last save), so I went looking for the same kind of bug everywhere and found it in most writers: two "Still broken" at once, a step check finishing after a re-plan, parallel photo checks getting past their cap, two Try again taps, a live-guide frame or "It works now" during a re-plan. Each repair now has one lock that every writer takes, and each of those cases has a deterministic test (a held lock, a blocked model call or a barrier, never a sleep). Three of them I confirmed by running the same steps on the 1.31.1 code first.

The same pass found a server-wide stall (the live photo check ran on the event loop), repairs stuck at "running" forever after a restart (now they come back with Try again), and four security gaps: anyone with a shared guide link could re-plan or spend on the owner's repair through the API, the rate limit could be skipped with a made-up X-Forwarded-For header, erasing a repair took its spend out of the daily cap, and the owner's photos had no cache rule. All fixed with tests. The full list, ranked by impact, is in [CHANGELOG.md](../CHANGELOG.md) 1.32.0.

## What changed in 1.31.0 and 1.31.1

1.31.0 is a UI pass: smoother screen changes, instant feedback on every tap, placeholders that stop the progress screen from jumping, and the layout bugs I found at 360 px (CHANGELOG). 1.31.1 re-made the screenshots, the demo video, the X clip, the GIF and the thumbnail on those screens from recorded live answers, fixed the recorded demo's hand-off links (they pointed at the machine it was recorded on), and gave the test suite's waits for a repair a 60 s budget, because CI runners are slower than my machine and three waits of 10 to 15 s timed out there.

## What changed in 1.30.0 (from the live runs)

Fourteen fixes found by running the real API and reviewing every screen, each with a test. The main ones: structured calls always stream (the API returned 504 on long answers), every schema field is required (the API dropped optional ones), SAM masks are clipped to the part's box (one mask tinted a whole wall), the follow-up is one yes/no question, the sample photo is checked on the step it shows, the red-stop PDF no longer lists parts to buy, and Basa Jawa wording fixes. Full list: [CHANGELOG.md](../CHANGELOG.md).

## What is real, what is sample, what is not measured

- Real: all live answers, the recorded demo, the eval's live column, the screenshots, the film and the GIF (real Meta API answers recorded on the live run of 6 November 2026 and played back in the app). The film opens on AI-generated scenes of people and homes, labelled on screen. The older `16_live_guide` screenshot called SAM 3.1 live.
- Sample: the photos are AI-generated and labelled on the image itself. Offline sample mode uses pre-written answers and says so on screen. Prices are labelled estimates.
- Not measured: real owner trials and real-world photos. I make no claim about money saved by real people.

## Known limits

- One close-up sample photo fits only the steps it shows; per-step real photos would be better ([SUGGESTIONS.md](SUGGESTIONS.md) item 3).
- Repairs take about 80 seconds on the live API, mostly model time.
- The free host forgets repairs on restart. A repair whose files survive a restart comes back with Try again.
- The per-repair lock lives in the server process, so the app runs as one process.
- WhatsApp is not connected to a real number yet.

## Next

Ten suggestions, most useful first, are in [SUGGESTIONS.md](SUGGESTIONS.md). The dated plan is in [ROADMAP.md](ROADMAP.md).
