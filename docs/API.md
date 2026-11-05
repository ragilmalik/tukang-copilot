# HTTP API

Base: `http://localhost:8000` (or your Render URL). All responses JSON unless noted. Interactive docs: `/docs` (FastAPI Swagger).

## `GET /health`
```bash
curl localhost:8000/health
```
```json
{"ok":true,"version":"1.0.0","mode":"offline","meta_api_key":false,"open_weights":false,
 "models":{"listen":"muse-voice-transcribe-1.0","listen_javanese":"muse-spark-1.2","look":"muse-spark-1.3","segment":"sam-3.1",
           "diagnose":"muse-spark-1.3","plan":"muse-spark-1.3","illustrate":"muse-image-1.0","verify":"muse-spark-1.3"}}
```

## `POST /api/sessions` (multipart)
| Field | Required | Notes |
|---|---|---|
| `photos` | yes (1-3), unless `video` is sent | jpg/png/webp, plus iPhone HEIC/HEIF (converted to JPEG on the server) ≤ 15 MB each |
| `video` | no | mp4/mov/webm/3gp/mkv/m4v ≤ 40 MB, ≤ 30 s. The server keeps the sharpest frame from each third of the clip (3 frames; photos first, max 3 in total). If there is no `audio` and no `text`, the clip's own sound is used as the voice description. |
| `audio` | text or audio | webm/ogg/wav/mp3/m4a/mp4/aac/opus ≤ 20 MB |
| `text` | text or audio | ≤ 2000 chars |
| `language` | no | `id` (default), `jv`, `en` |
| `category` | no | `motor`, `pump`, `appliance`, `plumbing`, `other` |
| `sample` | no | `motor` / `pump` / `faucet` / `rice`: uses a built-in photo + description |
```bash
curl -F photos=@bike.jpg -F text="Motor susah hidup" -F language=id -F category=motor localhost:8000/api/sessions
curl -F video=@pump.mp4 -F language=id -F category=pump localhost:8000/api/sessions   # video only: frames + its sound
# {"id":"d2b5d598d8c6","owner_token":"Qk2…"}
```
`owner_token` (since 1.27.0) is returned only here, once. Keep it on the owner's device: the outcome and erase calls
need it as the `X-Owner-Token` header. No GET returns it, and the shared guide link does not carry it.
Errors: 400 (missing photo/description, bad type, bad language/category, unreadable image), 413 (too large), 429 (too many new repairs from one visitor, live mode only, `Retry-After` set), 503 (rolling 24 h spend cap reached, live mode only).

## `GET /api/sessions/{id}`
The whole session (see ARCHITECTURE.md for fields) plus `files_base` (`/files/{id}/`). Statuses: `created`, `running`, `needs_answer`, `ready`, `stopped`, `exhausted`, `error`.

## `GET /api/sessions/{id}/events` (Server-Sent Events)
```bash
curl -N localhost:8000/api/sessions/d2b5d598d8c6/events
data: {"status": "running", "stages": {...}, "question": null}
data: {"status": "needs_answer", "stages": {...}, "question": "Apakah tercium bau bensin saat distarter?"}
```
Closes when the status leaves `created`/`running`. Since v1.23 each message is the trimmed `progress_view`: `status`, `stages`, `question`, `error`, `agent_log`, `models`, `files_base`, plus each stage's result as soon as it exists: `object_report` (object, model guess, component names), `parts_image` + `parts_found` (after SAM 3.1), `diagnosis` (summary, safety level, top 3 causes with confidence) and `plan_steps`. Built from the public session view, so it never carries the owner's own words or raw errors. Offline sample mode holds each finished stage on screen for `MOCK_PACE` seconds (default 0.6, first analysis only, never in live mode).

## `POST /api/sessions/{id}/answer` (form: `text`)
Answers the follow-up question and resumes. 409 if the session isn't waiting.

## `POST /api/sessions/{id}/steps/{n}/check` (multipart: `photo`)
```json
{"passed":false,"observation":"Foto terlalu gelap…","correction":"Nyalakan senter HP…","fails":1,"escalate":false}
```
After `MAX_CHECK_FAILS` fails: `"escalate":true` + `escalate_hint`. 409 for an unknown step or no plan.

## `DELETE /api/sessions/{id}`
Erases the repair (photos, voice leftovers, diagrams, PDFs, session JSON) from the server right now: `{"id":"…","deleted":true}`, `404` if it does not exist, `403` without the right `X-Owner-Token` header (owner only, since 1.27.0). A worker still running for that session cannot write it back. The "Delete my photos now" button calls it; "Clear history" in My garage calls it for every saved repair, best effort. The server also purges anything older than `RETENTION_HOURS` at startup and then every hour.

## `POST /api/sessions/{id}/retry`
Re-runs a session whose `status` is `error` (busy AI service, dropped signal). Finished stages and the cost so far are kept. `{"ok":true}`; `409` if the session did not fail. Failed sessions carry a friendly `error` in the session language and an `error_kind` (`busy`, `network`, `auth`, `budget`, `invalid`, `generic`); the technical detail is never sent to the browser. Step-check and replan outages answer `503` with the same friendly text and `Retry-After`.

## `POST /api/sessions/{id}/replan` (form: `report`)
Moves to the next likely cause and returns the updated session (`status` `ready`), or `exhausted` with `stop_reason`, or `stopped` if the report trips the safety gate.

## `POST /api/sessions/{id}/outcome` (form: `result`)
Records how the repair ended. `result` is `fixed` (it works now) or `pro` (a mechanic took over). Stores `outcome: {result, at, saved_idr}` on the session (`saved_idr` is the diagnosis `diy_saving_idr` for `fixed`, else 0) and returns the session. `422` for any other value, `409` when there is no plan (red stop), `404` unknown session, `403` without the right `X-Owner-Token` header (owner only, since 1.27.0: someone holding the shared guide link cannot answer for the owner; repairs saved before 1.27.0 have no token and stay open). A re-plan removes the outcome. The PDF report gets a Result line.

## Session JSON: `trace`
Every session object carries `trace`: nine rows in pipeline order, each `{stage, tool, kind, status, ms}`. `kind` is `meta` (a Meta model), `open` (Muse Spark Open on Baseten), `tts` (edge-tts) or `code` (rule-based safety gates). Used by the "Under the hood" panel and the PDF report.

## `GET /api/sessions/{id}/report.pdf`
Printable A4 repair report in the session's language: safety level, the photo with the SAM-marked parts, each step with its camera check ([OK] or [  ]), tools and parts with estimated prices, attempts, disclaimer. `409` while the diagnosis is not ready, `404` for an unknown session.
```bash
curl -o report.pdf http://localhost:8000/api/sessions/$ID/report.pdf
```

## `GET /api/sessions/{id}/workshop.pdf`
Large-print workshop sheets (A4) to pin up next to the job: a cover with the safety banner, the marked photo and a tick list of tools and parts, then one page per step (giant step number, instruction, warnings in a red box, what the camera should see, the step diagram or marked photo, a tick box) and a final "Done when" page. Session language. `409` while there is no plan (including a red safety stop), `404` for an unknown session.

## `GET /api/sessions/{id}/card.png`, `GET /og.png`
Link-preview cards (1200×630 PNG, Open Graph size). The session card shows the SAM-marked photo, the object, the most likely cause with confidence (after a re-plan, the cause being tried with "Plan 2 of 3" above it), the safety badge and a plan line (steps, minutes, DIY saving), plus "DEMO MODE" in offline sample mode; it never shows the owner's own words. `409` before the photo has been looked at, `404` for an unknown or erased session. `/guide/{id}` carries `og:*` and `twitter:card` tags pointing at it (absolute URL from `PUBLIC_BASE_URL`, else the request host); the front page points at `/og.png` (`web/og.png`, made by `scripts/make_og.py` from a labelled AI-generated sample photo).

## `GET /manifest.webmanifest`, `GET /sw.js`
PWA manifest and the app-shell service worker, served from the root so the app can be installed to the home screen. `404` if the file is missing.

## `GET /api/sessions/{id}/report`
```json
{"object":"Honda Beat, area busi","problem":"…","fix":"Busi kotor / berkerak","steps_total":4,"steps_verified":1,
 "tools":[…],"parts":[…],"cost_estimate_idr":25000,"shop_cost_estimate_idr":60000,"diy_saving_idr":35000,"minutes_estimate":20,"safety_level":"amber","attempts":["Dicoba: Cop busi longgar. Hasilnya: …"],"status":"ready"}
```
`attempts` is one line per "Still broken" press, in the session's language (Bahasa, Basa Jawa or English). Repairs saved before 1.29.6 show the older English line.

## `GET /files/{id}/{name}`
Only generated media: `photo1-3.jpg`, `parts.jpg`, `part_<id>.jpg`, `diagram_<n>.png`, `voice_<c>_<n>.mp3`, `check_*.jpg`. Everything else (incl. `session.json`) is 404.

## Pages
`/` the app · `/guide/{id}` read-only shared guide · `/static/*` assets.
