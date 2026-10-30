# HTTP API

Base: `http://localhost:8000` (or your Render URL). All responses JSON unless noted. Interactive docs: `/docs` (FastAPI Swagger).

## `GET /health`
```bash
curl localhost:8000/health
```
```json
{"ok":true,"version":"1.0.0","mode":"mock","meta_api_key":false,"open_weights":false,
 "models":{"listen":"muse-voice-transcribe-1.0","listen_javanese":"muse-spark-1.2","look":"muse-spark-1.3","segment":"sam-3.1",
           "diagnose":"muse-spark-1.3","plan":"muse-spark-1.3","illustrate":"muse-image-1.0","verify":"muse-spark-1.3"}}
```

## `POST /api/sessions` (multipart)
| Field | Required | Notes |
|---|---|---|
| `photos` | yes (1–3), unless `video` is sent | jpg/png/webp ≤ 15 MB each |
| `video` | no | mp4/mov/webm/3gp/mkv/m4v ≤ 40 MB, ≤ 30 s. The server keeps the sharpest frame from each third of the clip (3 frames; photos first, max 3 in total). If there is no `audio` and no `text`, the clip's own sound is used as the voice description. |
| `audio` | text or audio | webm/ogg/wav/mp3/m4a/mp4/aac/opus ≤ 20 MB |
| `text` | text or audio | ≤ 2000 chars |
| `language` | no | `id` (default), `jv`, `en` |
| `category` | no | `motor`, `pump`, `appliance`, `plumbing`, `other` |
| `sample` | no | `motor` / `pump` / `faucet` / `rice`: uses a built-in photo + description |
```bash
curl -F photos=@bike.jpg -F text="Motor susah hidup" -F language=id -F category=motor localhost:8000/api/sessions
curl -F video=@pump.mp4 -F language=id -F category=pump localhost:8000/api/sessions   # video only: frames + its sound
# {"id":"d2b5d598d8c6"}
```
Errors: 400 (missing photo/description, bad type, bad language/category, unreadable image), 413 (too large).

## `GET /api/sessions/{id}`
The whole session (see ARCHITECTURE.md for fields) plus `files_base` (`/files/{id}/`). Statuses: `created`, `running`, `needs_answer`, `ready`, `stopped`, `exhausted`, `error`.

## `GET /api/sessions/{id}/events` (Server-Sent Events)
```bash
curl -N localhost:8000/api/sessions/d2b5d598d8c6/events
data: {"status": "running", "stages": {...}, "question": null}
data: {"status": "needs_answer", "stages": {...}, "question": "Apakah tercium bau bensin saat distarter?"}
```
Closes when the status leaves `created`/`running`.

## `POST /api/sessions/{id}/answer` (form: `text`)
Answers the follow-up question and resumes. 409 if the session isn't waiting.

## `POST /api/sessions/{id}/steps/{n}/check` (multipart: `photo`)
```json
{"passed":false,"observation":"Foto terlalu gelap…","correction":"Nyalakan senter HP…","fails":1,"escalate":false}
```
After `MAX_CHECK_FAILS` fails: `"escalate":true` + `escalate_hint`. 409 for an unknown step or no plan.

## `POST /api/sessions/{id}/replan` (form: `report`)
Moves to the next likely cause and returns the updated session (`status` `ready`), or `exhausted` with `stop_reason`, or `stopped` if the report trips the safety gate.

## `GET /api/sessions/{id}/report.pdf`
Printable A4 repair report in the session's language: safety level, the photo with the SAM-marked parts, each step with its camera check ([OK] or [  ]), tools and parts with estimated prices, attempts, disclaimer. `409` while the diagnosis is not ready, `404` for an unknown session.
```bash
curl -o report.pdf http://localhost:8000/api/sessions/$ID/report.pdf
```

## `GET /manifest.webmanifest`, `GET /sw.js`
PWA manifest and the app-shell service worker, served from the root so the app can be installed to the home screen. `404` if the file is missing.

## `GET /api/sessions/{id}/report`
```json
{"object":"Honda Beat, area busi","problem":"…","fix":"Busi kotor / berkerak","steps_total":4,"steps_verified":1,
 "tools":[…],"parts":[…],"cost_estimate_idr":25000,"minutes_estimate":20,"safety_level":"amber","attempts":["Tried 'Cop busi longgar', result: …"],"status":"ready"}
```

## `GET /files/{id}/{name}`
Only generated media: `photo1-3.jpg`, `parts.jpg`, `part_<id>.jpg`, `diagram_<n>.png`, `voice_<c>_<n>.mp3`, `check_*.jpg`. Everything else (incl. `session.json`) is 404.

## Pages
`/` the app · `/guide/{id}` read-only shared guide · `/static/*` assets.
