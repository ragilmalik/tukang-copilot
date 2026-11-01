# Tukang Copilot, Full Product, Technical & Documentation Spec
Meta Global AI Developer Hackathon (Meta × Cerebral Valley) · Indie Developer track (solo) · Theme: **Push the Frontier** ("give a machine a new capability / understand and control a physical system"), secondary fit: Build for Your World
Owner: Ragil Artza Rozaksyah ("Malik"), Semarang, Indonesia. Cerebral Valley account: ragilmalika.
Malik is NOT a developer. The project agent writes 100% of the code and docs, from zero to a finished, deployed, submitted-ready project. Explain any manual step in plain words with exact clicks.
**Deadline: Wed Nov 4, 2026, 9:00 PM ET = Thu Nov 5, 2026, 09:00 WIB.** Internal target: feature-complete by Nov 3 23:59 WIB.

---

## 1. One-liner
Point your phone camera at something broken, say what's wrong in Bahasa, Javanese or English, and Tukang Copilot finds the exact part, figures out the fault, and walks you through the fix with annotated pictures and voice, checking each step with your camera.

## 2. Problem & impact (Impact = 30%)
- Indonesia runs on motorbikes (~130M), water pumps, rice cookers, fans, and household plumbing. A small fault costs a day's wage at a bengkel or days without water.
- Repair knowledge lives in scattered YouTube videos, mostly not for your exact model, not in your language, and can't see your problem.
- Tukang Copilot sees the actual object, segments the actual parts, and adapts each step to what the camera shows. It also says clearly when a job is unsafe and needs a professional.
- Users: motorbike owners, households, small repair shops (training apprentices), ojol drivers.
- Measurable claims for the pitch: time-to-diagnosis, % of steps verified by camera, money saved vs. shop visit (show as estimates, labelled).

## 3. Hard hackathon requirements → how we satisfy each
| Requirement (from official details page) | Implementation |
|---|---|
| Must incorporate Meta models (Stage 1 pass/fail) | Core pipeline uses Muse Spark (vision + reasoning), SAM 3.1, Muse Image, Muse Voice Transcribe; optional Muse Spark Open (open weights) |
| Fit a problem statement | Push the Frontier: new capability for understanding and repairing physical systems |
| New work only (built Oct 26 – Nov 4) | New public repo; dated commits; README "Built during the hackathon" section |
| Repo must be public | Public GitHub repo, MIT license |
| 3-minute demo video showing only work built during the event | Script in §13 |
| Max team 4, solo allowed | Solo |
| No code/data/assets without rights | Only model output, our own photos, CC0 icons; list sources in docs/ATTRIBUTIONS.md |
| Avoid anti-projects (medical advice, basic RAG, simple image analyzers, education chatbots, political/war) | Physical repair only; it's an interactive multi-step agent with verification, not a single-shot image analyzer; no medical content |

## 4. Judging rubric mapping
- **Impact 30%**: §2 story, real Semarang objects in the demo.
- **Use of Meta AI tooling 25%**: 4–5 Meta models orchestrated; SAM 3.1 part masks driving annotated step cards; Spark verifying each step from a new photo; open-weights mode.
- **Technical depth 20%**: typed pipeline, structured outputs, retries, caching, safety gate, tests, clean architecture.
- **Demo 25%**: live phone demo on a real motorbike/pump; before/after; verification checkmarks.

## 5. Core user flow (must work end to end, on a phone browser)
1. **Start**: big camera button + mic button. Language picker: Bahasa Indonesia (default), Basa Jawa, English. Category chips: Motor, Pompa air, Elektronik rumah, Pipa/keran, Lainnya.
2. **Capture**: take 1–3 photos (or a 5–10 s video; extract 3 frames) + hold-to-talk voice description (≤60 s). Text fallback.
3. **Understand** (progress UI with named stages): Listening → Looking → Finding the parts → Diagnosing.
4. **Diagnosis card**: object identified (e.g., "Honda Beat 2019 carburetor area"), top 3 likely causes with confidence and why, parts highlighted on the user's own photo (SAM masks, labelled), tools needed, difficulty (1–5), time estimate, estimated cost of parts (labelled as estimate), **Safety level** (green: DIY ok / amber: caution / red: stop, call a professional, e.g., gas, mains wiring inside walls, brakes hydraulics, airbags).
5. **Guided repair mode**: one step per screen: annotated image (user's photo with SAM mask + arrows/numbers rendered), short instruction, voice readout, "why" expandable, warning icons. Button "Check my step" → user snaps a photo → Spark compares against expected state → ✅ next / ⚠️ correction ("the clamp is still on the left hose, loosen it first").
6. **Stuck / didn't work**: user says what happened; agent re-plans (branches to next likely cause).
7. **Finish**: summary report (problem, fix, parts used, time) shareable as a link/PDF; "Save to my garage" history (local storage, no account).
8. **Workshop mode (stretch)**: generate a clean illustrated guide from a session (Muse Image renders a tidy diagram version) to share with others.

## 6. AI pipeline (Meta models)
All model calls go through `meta_client.py` (single place for auth, retries, timeouts, logging, cost tracking). **Before writing integration code, read current docs at dev.meta.ai (Overview, Quickstart, Model list, Cookbook, API cookbook, API fundamentals, Muse code recipes, OSS model cookbook) and record verified endpoints/model ids in docs/META_API_NOTES.md. Never invent endpoints or parameters.** If a model in this table isn't available via the API, document it and pick the closest Meta alternative.

| # | Stage | Model | In → Out |
|---|---|---|---|
| 1 | Listen | Muse Voice Transcribe | audio → transcript, language |
| 2 | Look | Muse Spark (vision) | photos + transcript + category → `ObjectReport` JSON: object, brand/model guess, visible components with approx. locations (point or box prompts), visible damage |
| 3 | Find parts | SAM 3.1 | photo + point/box/text prompts from step 2 → masks per component; overlay rendered server-side (Pillow/OpenCV) with labels |
| 4 | Diagnose | Muse Spark (reasoning), toggle to Muse Spark Open on Baseten (`meta-models/muse-spark-open-1026`) via `USE_OPEN_WEIGHTS=true` | ObjectReport + transcript → `Diagnosis` JSON (causes, confidence, safety level, tools, parts, difficulty) |
| 5 | Plan | Muse Spark | Diagnosis → `RepairPlan` JSON: ordered steps, each with target component id (→ mask), action, expected visual state, warnings, voice text |
| 6 | Illustrate | Muse Image | for steps where the user's photo can't show the action (e.g., inside view), generate a clean instructional diagram consistent with the object; otherwise use the annotated real photo |
| 7 | Narrate | Meta TTS if offered by Model API; else open-source TTS (document choice) | step voice text → audio |
| 8 | Verify step (agentic loop) | Muse Spark (vision) + SAM 3.1 | new photo + expected state → pass/fail + correction; on repeated fail → re-plan (step 5) or escalate to "call a professional" |
| 9 | Safety gate | Muse Spark | runs on Diagnosis and every plan; forces red level and stops guidance for gas lines, mains/house wiring, high-voltage (microwave caps, CRT), brake hydraulics, fuel system leaks near heat, anything involving the human body |

### Structured schemas (pydantic, JSON mode / function calling)
```python
class Component(BaseModel): id: str; name: str; prompt_point: tuple[float,float] | None; prompt_box: tuple[float,float,float,float] | None; condition: str
class ObjectReport(BaseModel): object: str; brand_model_guess: str | None; category: Literal["motor","pump","appliance","plumbing","other"]; components: list[Component]; visible_issues: list[str]
class Cause(BaseModel): title: str; confidence: float; evidence: list[str]; component_ids: list[str]
class Diagnosis(BaseModel): causes: list[Cause]; safety_level: Literal["green","amber","red"]; safety_reason: str; tools: list[str]; parts: list[dict]; difficulty: int; minutes_estimate: int; cost_estimate_idr: int | None
class Step(BaseModel): n: int; component_id: str | None; instruction: str; why: str; expected_state: str; warnings: list[str]; voice_text: str; needs_diagram: bool
class RepairPlan(BaseModel): cause_title: str; steps: list[Step]
class StepCheck(BaseModel): passed: bool; observation: str; correction: str | None
```
Validate every model response; on invalid JSON retry once with the validation error appended; then fail gracefully.

## 7. Tech stack & architecture
- **Frontend**: Next.js 14+ (App Router, TypeScript), Tailwind, mobile-first PWA (installable), camera via `<input capture>` + MediaRecorder for audio. i18n (id, jv, en) with all UI strings in `/web/locales`.
- **Backend**: Python 3.11 FastAPI. Endpoints: `POST /sessions`, `POST /sessions/{id}/analyze`, `GET /sessions/{id}/events` (SSE progress), `POST /sessions/{id}/steps/{n}/check`, `POST /sessions/{id}/replan`, `GET /sessions/{id}/report`.
- **Storage**: SQLite (SQLModel) for sessions; images/audio on disk or Cloudflare R2 (Malik has Cloudflare). Auto-delete uploads after 24 h.
- **Deploy**: Frontend on Vercel; backend on Render or Modal (Malik has Render credits; Modal $100 if granted). Single `docker-compose.yml` for local run. Public HTTPS URL for judges.
- **Config**: `.env` → META_API_KEY, META_API_BASE, BASETEN_API_KEY, USE_OPEN_WEIGHTS, STORAGE_BACKEND, R2_*, PUBLIC_BASE_URL, MAX_COST_PER_SESSION_USD.
- **Cost control**: per-session budget, image downscaling (max 1536 px), cache by image hash, `DEMO_MODE=true` replays 2 recorded sessions if APIs are down during judging.
- **Observability**: structured logs per stage with latency and cost; `/health` endpoint.

## 8. Demo scenarios to build and test against (use real photos Malik can take in Semarang)
1. Motorbike won't start: spark plug fouled / loose plug cap (Honda Beat or Yamaha Mio). Green.
2. Water pump (Shimizu/Sanyo) runs but no water: loss of prime / clogged foot valve. Green/amber.
3. Leaking kitchen faucet / hose clamp. Green.
4. Rice cooker not heating: show RED safety stop when the plan would require opening mains-powered internals → recommends service center. (Demonstrates safety gate.)
Include ~10 test images in `tests/fixtures` (Malik's own photos or self-generated; no copyrighted images).

## 9. Quality bar
- Lint/format: ruff + black (Python), ESLint + Prettier (TS). Type checks: mypy (strict on pipeline), tsc.
- Tests: pytest unit tests for schemas, safety gate, overlay renderer, meta_client (mocked); one integration test with recorded fixtures; Playwright smoke test for the main flow (mocked backend).
- CI: GitHub Actions running lint + tests on push.
- Accessibility: large tap targets, voice readout, high contrast, works one-handed.
- Performance target: diagnosis card < 25 s on 4G; each step check < 8 s.

## 10. Repository layout
```
tukang-copilot/
  README.md
  LICENSE
  .env.example
  docker-compose.yml
  .github/workflows/ci.yml
  web/            Next.js app (app/, components/, lib/, locales/)
  api/
    main.py
    meta_client.py
    pipeline/ listen.py look.py segment.py diagnose.py plan.py illustrate.py narrate.py verify.py safety.py
    render/overlay.py
    schemas.py  db.py  settings.py
    tests/
  prompts/        all prompts as versioned .md files
  docs/           (see §11)
  scripts/        seed_demo.py, record_fixture.py
```

## 11. Documentation requirements (all mandatory, written for a non-developer AND for judges)
1. **README.md**: pitch, demo GIF, live URL, 3-min video link, screenshots, features, Meta models used and how, architecture diagram, quick start (local + cloud), "Built during the hackathon" (dated list of what was built Oct 26 – Nov 4), team, license.
2. **docs/SETUP_FOR_MALIK.md**: zero-knowledge, click-by-click guide: create accounts/keys (Meta Model API, Baseten, Vercel, Render/Modal, Cloudflare R2), where to paste each key, how to deploy, how to update, how to check it's working, common errors and fixes. Screens described in plain words.
3. **docs/ARCHITECTURE.md**: component diagram (Mermaid), sequence diagram of a full session, data flow, storage, deployment.
4. **docs/AI_PIPELINE.md**: each stage, model, prompt file, input/output schema, retries, failure modes, why each Meta model was chosen; open-weights mode explanation.
5. **docs/META_API_NOTES.md**: verified endpoints, model ids, request/response examples, rate limits, pricing notes, links to the official docs pages used.
6. **docs/API.md**: every backend endpoint with request/response examples (curl).
7. **docs/SAFETY.md**: safety levels, hard-stop categories, how the gate works, disclaimers shown in the UI, privacy (data retention 24 h, no accounts, no PII).
8. **docs/TESTING.md**: how to run tests, fixtures, manual QA checklist per demo scenario with expected results.
9. **docs/DEMO_SCRIPT.md**: 3-minute video script with timestamps and shot list (§13), plus a backup plan.
10. **docs/SUBMISSION.md**: final submission text: title, tagline (≤100 chars), description (problem, solution, how it works, Meta models, impact, what's next), "what we built during the hackathon", links; plus X post drafts (§14).
11. **docs/ROADMAP.md**: after-hackathon plan (offline mode, more object types, bengkel marketplace, WhatsApp bot).
12. **docs/ATTRIBUTIONS.md**: every third-party asset/library and license.
13. **CHANGELOG.md**: dated entries per day of the build.
14. Inline code docs: docstrings on every public function; comments on non-obvious logic.
Deliver a PDF bundle of README + SETUP_FOR_MALIK + SUBMISSION to Malik in the project chat at the end.

## 12. Build plan (fit around Malik's shifts; read his work-schedule memory first. He works nights: e.g., Fri Oct 30 21:00–06:00, Sat Oct 31 22:00–07:00, Sun Nov 1 off; check Nov 2–4)
- **Day 1 (Oct 30)**: verify Meta API docs + write META_API_NOTES; scaffold repo, CI, settings; meta_client with one working call per model; Malik claims $150 credits and creates API key (guide him).
- **Day 2 (Oct 31)**: Listen + Look + SAM segmentation + overlay rendering working from CLI on fixtures.
- **Day 3 (Nov 1)**: Diagnose + Plan + Safety gate + Verify loop (CLI end to end). Tests.
- **Day 4 (Nov 2)**: Web UI (capture, progress SSE, diagnosis card, guided steps, check-my-step), i18n, deploy staging.
- **Day 5 (Nov 3)**: Muse Image diagrams, narration, report/share, open-weights toggle, polish, DEMO_MODE, all docs.
- **Day 6 (Nov 4)**: Malik records demo with real objects (guided by DEMO_SCRIPT), edit video, publish X post, submit on Cerebral Valley. Done well before Nov 5 09:00 WIB.
- **Cut list if behind** (in this order): workshop mode, narration audio, Muse Image diagrams (keep at least one), PWA install, Javanese UI strings (keep Javanese voice input).

## 13. 3-minute demo video (script outline)
- 0:00–0:15 Hook: Malik's motorbike won't start in a Semarang alley; "Bengkelnya tutup."
- 0:15–0:30 Problem stats + one line on Tukang Copilot.
- 0:30–1:45 Live phone capture: photo + voice in Bahasa → parts highlighted on his own bike → diagnosis → 3 guided steps with "Check my step" ✅ and one ⚠️ correction → engine starts.
- 1:45–2:15 Second quick case: water pump prime, or the rice cooker RED safety stop.
- 2:15–2:45 Under the hood: diagram of Meta models (Voice Transcribe → Spark vision → SAM 3.1 masks → Spark plan → Muse Image → Spark verify), open-weights toggle on Muse Spark Open.
- 2:45–3:00 Impact + close: "Tukang Copilot, every phone becomes a mechanic's apprentice." Repo + live link.
Only show work built during the hackathon.

## 14. Prizes targeted & promotion
- Indie track (1st $150K … 5th $25K).
- Best Agentic Use-Case ($5K): plan → act → verify → re-plan loop.
- Best Build on Meta Open Weight Models ($10K): Muse Spark Open via Baseten mode, documented and shown in demo.
- Most Viral Project on X ($20K, engagement until Nov 8 EOD): 30–45 s vertical clip of the bike fix; 3 X post drafts (EN + ID), tag @AIatMeta and @cerebral_valley (verify handles), submit the post link on the platform.
- Community Vote ($10K): share gallery link in Indonesian dev communities (drafts only; Malik posts).

## 15. Submission checklist
- [ ] $150 Meta Model API credits claimed (Team ID on form), card on Meta billing, spend limit set
- [ ] API keys set in deployment; live URL works on a phone over 4G
- [ ] Repo public, all docs in §11 present, CI green
- [ ] 3-min video uploaded and publicly viewable
- [ ] X post live, link ready
- [ ] Submitted on Cerebral Valley (account ragilmalika) with all fields from docs/SUBMISSION.md, before Nov 5 09:00 WIB

## 16. Ground rules for the project agent
- Ask Malik before: creating the GitHub repo, creating accounts, spending money, posting anything publicly, submitting the hackathon entry.
- Never put API keys in code or chat; use .env and the platform's secret settings.
- Keep Malik's instructions short, numbered, and in plain English (offer Bahasa if he prefers).
- Report progress at the end of each build day with what's done, what's next, and anything he must do.

---

## 17. v2 Winning Improvements (added 2026-10-30 18:50 WIB, from official sources)

### What the judges score (verified)
Sources: official page https://dev.meta.ai/events/global-hackathon (fetched 2026-10-30) and the Official Rules as summarised by https://madrobot.blog/2026/10/03/meta-global-ai-developer-hackathon-1-million-prizes-muse-model-api/ (the waiver/rules page itself needs sign-in).
- **Impact 30%**: real-world potential, who benefits, how much it matters, whether it could become a product.
- **Creative use of Meta AI tools 25%** (Muse Spark series, Muse Image, SAM 3.1, Voice Transcribe, open weights / Muse Spark Open, Muse Code).
- **Demo, including the video 25%**.
- **Technical depth & execution 20%**.
- Indie track lens (official page): "creativity, technical ambition, and **whether it works**".
- Prizes: Indie $150K / $100K / $75K / $50K / $25K. **Bonus prizes up to $50K total** "for standout projects or community achievements, such as a public vote or the most viral project", announced ~Nov 10. ✅ Verified 2026-11-01 from the Participant Guide (cerebralvalley.ai/e/meta-ai-developer-hackathon/details) and the kickoff slide: Most Viral $20K, Best Build on Meta Open Weights $10K, Community Vote $10K, Best Agentic Use-Case $5K, Best Creative Build (Muse Image or Muse Wonder) $5K. Exact judging rules per prize: docs/JUDGING_MAP.md.
- Timeline: submissions due Nov 4 9:00 PM ET (= Nov 5 09:00 WIB); judging Nov 4–8; live finals Nov 9.

### Criterion → concrete features
| Criterion | Feature (status) |
|---|---|
| Impact 30% | 4 Indonesian scenarios incl. **water pump no-flow** (spec §8 #2); **PDF repair report** + **"My garage" history** (proves real reuse); money-saved estimate vs bengkel visit; Bahasa/Jawa strings everywhere |
| Meta tools 25% | Spark vision → SAM 3.1 masks → Spark plan → Muse Image diagram → Spark verify loop; **open-weights badge** (visible "Muse Spark Open" chip when `USE_OPEN_WEIGHTS=true`); per-stage model chips in the UI and report |
| Demo 25% | **Flawless mock/demo mode** end to end (no key needed); scripted 2–3 min **video with captions + voiceover** generated from the real UI; screenshots; vertical 30–45 s clip for X |
| Technical depth 20% | mypy strict clean, ruff, pytest, **Playwright smoke** of the main flow, CI, one-step real-key swap with `scripts/set_keys.py` + `scripts/check_keys.py`, safety gate in code (3 layers) |
| "Whether it works" | Safety escalation polish (red stop screen with service-centre advice), PWA installable, **video capture → 3 frames**, ~10 clearly labelled stand-in photo fixtures for tests |

### Build order (top items first)
1. Checks green incl. mypy strict (CI enforces). 2. Water pump flow. 3. PDF report + garage. 4. Open-weights badge. 5. Fixtures + Playwright smoke. 6. Demo assets (video, captions, voiceover, screenshots, diagram), write-up, setup guide, submission checklist. 7. PWA, video capture, id/jv strings, safety polish.
Details and status: tukang-copilot/docs/WINNING_PLAN.md.
