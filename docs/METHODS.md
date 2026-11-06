# Methods and implementation

This is the "how did you build it and why that way" document. It sits between [HOW_IT_WORKS.md](HOW_IT_WORKS.md) (plain words) and the code. Each section says what the method is, where it lives, why I chose it, and how I test it.

## 1. One engine, many front doors

- **What:** the phone web app, the shared read-only guide, the WhatsApp channel and the `/wa` simulator all call the same `engine.create` / `engine.run` in `api/pipeline/engine.py`.
- **Why:** one safety gate, one cost meter, one set of tests. A second code path for WhatsApp would drift and miss a safety rule sooner or later.
- **How tested:** `test_engine.py`, `test_whatsapp_*.py`, and the Playwright flows run the same repair through each door.

## 2. All Meta calls in one file

- **What:** `api/meta_client.py` is the only module that talks to `api.meta.ai`. It sets the auth header, streams structured calls, retries 429/5xx with backoff (honouring `Retry-After`, capped at 30 s), never retries 400 or auth errors, and charges every call to the cost meter.
- **Why:** when the live API misbehaved on 5 Nov 2026 (504 after about 20 s on long structured answers), I fixed it in one place: structured calls now always stream.
- **How tested:** a test double of the HTTP API (`api/tests/doubles/`) replays success, 429, 503, timeout and bad JSON cases.

## 3. Typed answers with strict JSON schemas

- **What:** every model stage returns JSON that must match a pydantic schema in `api/schemas.py`. The schema sent to the API marks every field required, because the live API dropped optional fields (no parts meant no SAM masks and no follow-up question).
- **Why:** the UI can trust the data. A missing field is caught on the server, not as a blank screen on a phone.
- **Repair before retry:** `api/coerce.py` fixes harmless drift first (a list sent as a string, a percentage as "65%", a name starting lower case, an empty tools list). Only a real mismatch costs a retry call, and the retry carries the validation error.

## 4. Box prompts for SAM, then clipping

- **What:** Muse Spark returns rough boxes for the parts. All boxes go into one SAM 3.1 call using Meta's box grammar. If that fails, the app falls back to one noun-phrase call per part. `engine.clip_to_box` then keeps each mask near the box Spark located, because live SAM sometimes tinted a whole wall for a thin part like a plug cable.
- **Why:** pixel outlines on the owner's own photo are the main thing a chatbot can't do. Clipping keeps a stray mask from pointing at the wrong thing.
- **Overlay:** `api/render/overlay.py` draws the masks and number badges and moves a badge to a free spot when two would overlap.

## 5. Ask before guessing

- **What:** when the top cause is under 60%, the diagnosis returns exactly one yes/no follow-up question and the run pauses (`needs_answer`). The answer goes back into the context and the run continues.
- **Why:** one cheap question beats a wrong plan. One question, not three, because the buttons are Yes / No / Not sure.

## 6. Two safety gates

- **What:** `api/pipeline/safety.py` checks the owner's words before any paid call, then checks the plan after it is written. Both are rules in code (street Bahasa and Javanese wording included), plus the model's own safety level.
- **Why:** a safety rule that depends only on the model can be talked around. The code gate can't. It also costs nothing: a red stop on "rem blong" returns in 0.2 s with zero model calls.
- **How tested:** the eval in [EVAL.md](EVAL.md): 23/23 dangerous owner texts stopped, 10/10 dangerous steps stopped, 0 false stops on 17 everyday jobs, on the live API.

## 7. Prompt-injection hygiene

- **What:** text from the owner and text read off the photo are wrapped as untrusted data (`api/untrusted.py`) and the prompts say to treat it as data. Instructions inside a photo ("ignore your rules") do not change the safety level.
- **How tested:** injection cases in the eval: 4 of 4 that ran were resisted.

## 8. State in files, progress over SSE

- **What:** each repair is a folder `data/sessions/<id>/` with `session.json`, photos, masks, diagrams and audio. Every stage writes its status there, and the phone follows along over server-sent events.
- **Why:** no database or queue to run or pay for on a free host. A janitor deletes folders after `RETENTION_HOURS` (24).

## 9. Ownership without accounts

- **What:** creating a repair returns an `owner_token` once. The owner's browser keeps it and sends it on every call that changes the repair or spends on it: answer, Try again, Still broken, the step check, the live guide, the voice command, the outcome and erase (the first five since 1.32.0). A shared guide link never carries it.
- **Why:** sharing a guide with a mechanic must not let them delete or change it, or spend on it.

## 9b. One change to a repair at a time

- **What:** `engine.locked(sid)` is a per-repair lock. The first analysis and a re-plan hold it for their whole run; answer, retry, outcome and the bookkeeping of a step check, a live-guide frame and a voice command hold it for a few lines. A step check reserves its count and photo name under the lock, runs the model with no lock held, and records the result under the lock only if the repair is still on the same plan.
- **Why:** every writer loads the whole session, changes a part and saves the whole session. Without a lock the later save silently drops the other's change (CI found it with a quick answer to the follow-up question; the 1.32.0 audit found the same bug in a double re-plan, a check landing on the next plan, parallel checks past their cap and more).
- **How it is tested:** `api/tests/test_races.py` holds the lock, blocks the mock model call on an Event or meets two threads at a Barrier, so every race happens on every run, without sleeps.

## 10. Cost guard and abuse guard

- **What:** `api/cost.py` meters every call and stops before a call that would pass `MAX_COST_PER_SESSION_USD` (0.50). A live site also has `RATE_LIMIT_PER_HOUR` per visitor and `DAILY_BUDGET_USD` for the whole site.
- **Measured:** median 83 s and $0.044 per repair on the live API (5 Nov 2026).

## 11. Recorded demo for sleeping servers

- **What:** `scripts/record_replay.py` records one full live repair in all three languages into `web/replay/`. When the free server is asleep or unreachable, `web/replay.js` plays that recording, labelled on screen, and never fakes an answer for the visitor's own photo.
- **Why:** a judge opening a cold free-tier link should still see the real product within seconds.

## 12. Logging and security

- **Logs:** `api/logs.py` scrubs secrets, including inside tracebacks. One access line per request with an `X-Request-ID`, no query string and no owner text. `LOG_FORMAT=json` for hosts that parse logs.
- **HTTP:** strict CSP, HSTS, no `Server` header, CORS off unless `CORS_ORIGINS` names a site, `Cache-Control` per route.

## 13. Testing approach

Unit tests for each module, test doubles for the Meta API and WhatsApp Graph API, jsdom and Playwright for the browser, an end-to-end smoke script against a running server, and an eval script that runs the same cases offline and live. See [TESTING.md](TESTING.md) and [TEST_CHECKLIST.md](TEST_CHECKLIST.md).
