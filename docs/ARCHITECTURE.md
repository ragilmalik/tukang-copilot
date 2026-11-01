# Architecture

## Components

```mermaid
flowchart TB
  subgraph Phone["Phone browser (web/)"]
    UI["index.html + app.js<br/>camera input, MediaRecorder, SSE, i18n id/jv/en"]
    Guide["guide.html<br/>read-only shared report"]
    Sim["wa.html (/wa)<br/>WhatsApp simulator, demo mode"]
  end
  WAUser["Owner's WhatsApp"] --> WACloud["WhatsApp Cloud API<br/>Graph v26.0"]
  subgraph Server["One Python process (FastAPI, api/main.py)"]
    HTTP["HTTP API<br/>/api/sessions…"]
    WAH["channels/whatsapp.py<br/>signed webhook, chat state, buttons"]
    Engine["engine.py<br/>stages + session state"]
    Safety["safety.py<br/>text gate + plan gate"]
    Overlay["render/overlay.py<br/>masks → numbered overlay"]
    Media["media.py<br/>ffmpeg WAV, edge-tts"]
    Mock["mock.py<br/>demo answers"]
    MC["meta_client.py<br/>auth, retries, cost meter"]
    Prompts["prompts/*.md<br/>versioned prompts"]
  end
  Store[("data/sessions/&lt;id&gt;/<br/>session.json, photos, masks, diagrams, mp3")]
  Meta["Meta Model API<br/>api.meta.ai/v1"]
  Baseten["Baseten<br/>Muse Spark Open"]
  UI --> HTTP --> Engine
  Guide --> HTTP
  WACloud -->|"POST /webhooks/whatsapp (X-Hub-Signature-256)"| WAH
  WAH -->|"send / media upload + download"| WACloud
  Sim -->|"/api/wa-sim/* (same handler)"| WAH
  WAH --> Engine
  Engine --> Safety & Overlay & Media & Prompts
  Engine -->|MOCK / no key| Mock
  Engine -->|live| MC --> Meta
  MC -.USE_OPEN_WEIGHTS.-> Baseten
  Engine --> Store
```

Design rules:
- **Two front doors, one engine.** The phone app and the WhatsApp channel (`api/channels/whatsapp.py`) both call `engine.create` / `engine.run` and go through the same safety gate; WhatsApp only changes how messages come in and go out (docs/WHATSAPP.md). The `/wa` simulator feeds the same handler with Cloud-API-shaped messages in demo mode; tests use a fake Graph API (`api/testing/fake_graph.py`).
- **Owner token.** `POST /api/sessions` returns an `owner_token` once; the owner's browser keeps it in localStorage and sends it as `X-Owner-Token` to set the outcome or erase the repair. A shared guide link (`/guide/{id}`) does not carry it, so a viewer gets 403. It is never returned by any GET.
- **One file talks to Meta** (`api/meta_client.py`): auth header, retries with backoff on 429/5xx, timeouts, cost charging. Nothing else imports `httpx` for Meta.
- **Every model output is validated** by a pydantic schema (`api/schemas.py`) and retried once with the validation error.
- **Every stage writes its status** into `session.json`, so the UI and SSE never need a database or queue.
- **Demo mode is the same code path** with `mock.py` returning the model answers, so tests exercise the real engine.

## Sequence of one repair

```mermaid
sequenceDiagram
  participant P as Phone
  participant A as API
  participant E as Engine
  participant M as Meta models
  P->>A: POST /api/sessions (photos, voice, text, lang, category)
  A->>E: create + start (background thread)
  A-->>P: {id, owner_token}
  P->>A: GET /events (SSE)
  E->>M: Voice Transcribe (or Spark 1.2 audio for Javanese)
  E->>E: safety text gate
  E->>M: Spark 1.3 vision → ObjectReport
  E->>M: SAM 3.1 box prompt (all parts) → masks
  E->>E: overlay.png per part
  E->>M: Spark → Diagnosis
  alt top cause < 60%
    E-->>P: needs_answer + question
    P->>A: POST /answer
    A->>E: resume
    E->>M: Spark → Diagnosis (with answer)
  end
  alt red
    E-->>P: stopped + reason
  else
    E->>M: Spark → RepairPlan
    E->>E: plan safety gate
    E->>M: Muse Image edits → diagrams (Spark reviews, redraw once)
    E->>E: edge-tts voice per step
    E-->>P: ready
  end
  loop each step
    P->>A: POST /steps/{n}/check (photo)
    A->>M: Spark vision → StepCheck
    A-->>P: pass / correction / escalate
  end
  opt still broken
    P->>A: POST /replan (what happened)
    A->>M: Spark → RepairPlan for next cause
  end
```

## Session state (`data/sessions/<id>/session.json`)

| Field | Meaning |
|---|---|
| `status` | `created` → `running` → `needs_answer` / `ready` / `stopped` / `exhausted` / `error` |
| `stages` | per stage: `waiting`, `running`, `done`, `skipped`, `stopped` + note + ms |
| `object_report`, `diagnosis`, `plan` | validated model outputs |
| `parts` | component id → label, name, found, highlight image |
| `diagrams`, `audio`, `checks` | per step |
| `safety` | level, reason, disclaimer |
| `cause_index`, `history` | re-plan state |
| `cost` | spent / budget / by model |

Files next to it: `photo1..3.jpg`, `parts.jpg`, `part_<id>.jpg`, `diagram_<n>.png`, `voice_<cause>_<n>.mp3`, `check_<cause>_<n>_<try>.jpg`. The voice recording (`voice.wav`) is deleted right after transcription. Whole sessions are deleted after `RETENTION_HOURS` (startup sweep).

## Deployment

```mermaid
flowchart LR
  GH[GitHub repo] -->|push| CI[GitHub Actions: ruff + pytest]
  GH -->|auto deploy| R["Render web service (Docker)<br/>render.yaml"]
  R -->|HTTPS| Phones
  R --> Meta[Meta Model API]
```

- `Dockerfile`: python:3.12-slim + ffmpeg + DejaVu font, runs `uvicorn api.main:app`.
- `render.yaml`: Blueprint with `MODEL_API_KEY`/`BASETEN_API_KEY` (and the optional `IMPACT_TOKEN`, `PUBLIC_BASE_URL` and four WhatsApp values `WA_TOKEN`, `WA_PHONE_NUMBER_ID`, `WA_VERIFY_TOKEN`, `WA_APP_SECRET`) as secret env vars, health check `/health`.
- `docker-compose.yml`: same container locally.
- Storage is the container disk: fine for a demo (sessions are temporary by design). For scale, see ROADMAP (R2).

## Why not Next.js + separate backend (as the first spec said)?
See [DECISIONS.md](DECISIONS.md#d1). Short version: one process, no build step, nothing for a non-developer to break, and judges get one URL.
