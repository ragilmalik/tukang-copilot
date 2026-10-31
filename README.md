# 🔧 Tukang Copilot

**Point your phone at something broken, say what's wrong in Bahasa Indonesia, Javanese or English, and Tukang Copilot finds the exact part, works out the fault, and walks you through the fix step by step, checking each step with your camera.**

Meta Global AI Developer Hackathon 2026 (Meta × Cerebral Valley) · Indie Developer track · Theme: **Push the Frontier** (give a machine a new capability: understanding and repairing physical systems).

| | |
|---|---|
| Live app | _add your Render URL here after deploy_ |
| 3-minute demo video | _add YouTube link_ · backup cut in the repo: [docs/demo/tukang-copilot-demo.mp4](docs/demo/tukang-copilot-demo.mp4) (2:50, demo mode, captions + voice-over) |
| X post | _add link_ |
| License | MIT |

| Snap + speak | Parts found (SAM 3.1) | Live camera guide | Check my step |
|---|---|---|---|
| ![home](docs/demo/screenshots/01_home.png) | ![parts](docs/demo/screenshots/05_parts.png) | ![live](docs/demo/screenshots/16_live_guide.png) | ![check](docs/demo/screenshots/07_check_fail.png) |
| **Hands-free** | **Bengkel hand-off** | **Safety stop** | **Basa Jawa** |
| ![hands-free](docs/demo/screenshots/17_hands_free.png) | ![hand-off](docs/demo/screenshots/18_handoff.png) | ![stop](docs/demo/screenshots/11_rice_stop.png) | ![jawa](docs/demo/screenshots/20_javanese_result.png) |

<sub>Demo-mode screenshots with clearly labelled stand-in photos (no real API calls; the live guide uses Chromium's fake camera). All 22 in [docs/demo/screenshots](docs/demo/screenshots). Short write-up: [docs/WRITEUP.md](docs/WRITEUP.md).</sub>

---

## Why

Indonesia runs on ~130 million motorbikes, water pumps, rice cookers, fans and household plumbing. A small fault costs a day's wage at a bengkel, or days without water. Repair videos are rarely for your exact model, rarely in your language, and they can't see *your* problem.

Tukang Copilot looks at the actual object, marks the actual parts on your own photo, and checks every step you do. It also says clearly, in your language, when a job is dangerous and needs a professional.

## What it does

1. **Snap + speak.** 1–3 photos **or a 5–10 s video** (the server keeps the sharpest frame from each third, and the clip's sound can be the voice note) and a voice note (≤60 s) or typed text. Pick a category chip (Motor, Pompa air, Elektronik rumah, Pipa/keran, Lainnya).
2. **Sees the parts.** SAM 3.1 segments each relevant part; they're tinted and numbered on your photo.
3. **Diagnoses.** Top causes with confidence and evidence, tools and parts with estimated rupiah prices, difficulty 1–5, time estimate, and a **safety level**: 🟢 safe / 🟠 caution / 🔴 stop.
4. **Asks when unsure.** If the top cause is below 60% it asks one sharp follow-up question before planning (agentic).
5. **Guided repair.** A short "before you start" safety tick list unlocks the steps. Then one step per screen: the right picture (your photo with that part highlighted, or a Muse Image diagram for hidden steps), short instruction, why it matters, warnings, countdown timers for waiting steps, and voice readout.
   - **Live camera guide.** Point the phone and SAM 3.1 outlines the step's target part on the live camera picture (about 1 frame a second, capped per repair); *Check now* verifies the step from the current frame.
   - **Hands-free.** Steps are read aloud and the phone listens for voice commands (lanjut / kembali / ulang / cek / masih rusak / berhenti, also in Javanese and English). Phones without continuous speech recognition get push-to-talk through Voice Transcribe.
6. **Check my step.** Snap a photo after each step; Muse Spark compares it to the expected state: ✅ next, or ⚠️ a specific correction. Repeated fails escalate.
7. **Still broken?** Say what happened and it re-plans for the next likely cause. When every safe cause is used up, it tells you to see a mechanic and gives you the report to show them.
   - **Bengkel hand-off.** On a red stop, when the causes run out, or on "Call a mechanic": a WhatsApp summary of what was found and tried, a Maps search for the nearest workshop, and a PDF with a brief for the mechanic.
8. **Report + share.** A shareable read-only guide link and a **PDF repair report** (problem, fix, parts, steps verified by camera), plus **My garage**: past repairs kept on the phone only, no account.
9. **Installable (PWA)** in Bahasa Indonesia, **Basa Jawa** (every UI string) and English. When reasoning runs on **Muse Spark Open** (open weights, `USE_OPEN_WEIGHTS=true` + Baseten key) the app shows a visible badge.
10. **Closes the loop.** At the end you tap "It works now" (or "Took it to a mechanic"); the report records the result and My garage adds up what you saved against typical bengkel prices (estimates, on the phone only).
11. **Safety escalation.** A red STOP card says why, what to do right now, finds a service centre nearby, gives the technician the PDF (stop report + mechanic brief), the hand-off card, and the 112 emergency line.
12. **Never a dead end.** If a live model call still fails after retries, `DEMO_FALLBACK` (on by default) finishes that stage on the labelled demo answer; `scripts/deploy_check.py` flags any live session that needed it.
13. **Impact trial kit.** Trial mode (`?trial=T1`) logs outcome and minutes; `scripts/impact_report.py` builds the impact report ([docs/USER_TRIAL_KIT.md](docs/USER_TRIAL_KIT.md)).

Hard safety stops (gas, house wiring, opening 220 V internals, high voltage, brake hydraulics, fuel leaks, airbags, anything medical) are enforced in code, not just in prompts. See [docs/SAFETY.md](docs/SAFETY.md).

## Meta models used (and how)

| Stage | Meta model | What it does here |
|---|---|---|
| Listen | **Muse Voice Transcribe** (`muse-voice-transcribe-1.0`) | Indonesian/English voice note → text, with repair keywords as biasing; push-to-talk voice commands in hands-free mode |
| Listen (Javanese) | **Muse Spark 1.2** audio input | Javanese isn't one of Voice Transcribe's 25 languages, so Spark 1.2 transcribes it |
| Look | **Muse Spark 1.3** vision + structured output | Photos → `ObjectReport`: object, visible components (with boxes), visible issues |
| Find parts | **SAM 3.1** (`sam-3.1`) | One box-prompt call for all located parts (phrase fallback) → pixel masks → numbered overlay; also tracks the target part on live camera frames (live guide) |
| Diagnose / Plan | **Muse Spark 1.3**, or **Muse Spark Open** on Baseten (`USE_OPEN_WEIGHTS=1`) | `Diagnosis` and `RepairPlan` JSON, re-plan on failure |
| Illustrate | **Muse Image** (`muse-image-1.0`, `/v1/images/edits`) | Edits the user's own photo into a clean diagram for steps the photo can't show; Spark reviews and redraws a bad one once |
| Verify | **Muse Spark 1.3** vision | New photo vs. expected state → pass / correction |

Narration: Meta's API has no text-to-speech, so steps are read by free Edge neural voices (`edge-tts`, has Indonesian *and* Javanese) with the browser's voice as fallback. Details: [docs/AI_PIPELINE.md](docs/AI_PIPELINE.md), [docs/META_API_NOTES.md](docs/META_API_NOTES.md).

## Architecture (short)

```mermaid
flowchart LR
  Phone["Phone browser<br/>web/ (HTML+JS, no build)"] -->|photos, voice, text| API["FastAPI<br/>api/main.py"]
  API --> Engine["Pipeline<br/>api/pipeline/engine.py"]
  Engine --> MC["meta_client.py<br/>(only file that calls Meta)"]
  MC --> ASR[Muse Voice Transcribe]
  MC --> Spark[Muse Spark 1.3 / 1.2]
  MC --> SAM[SAM 3.1]
  MC --> Img[Muse Image]
  MC -.optional.-> Open[Muse Spark Open on Baseten]
  Engine --> Disk[("data/sessions/&lt;id&gt;<br/>auto-deleted after 24 h")]
  API -->|SSE progress, JSON, images| Phone
```

![Architecture: one agent loop, five Meta models](docs/img/architecture.png)

Full diagrams: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Quick start

**No key needed to try it.** Without `MODEL_API_KEY` the app runs in free **demo mode** with recorded answers for five scenarios (motorbike, water pump, faucet, rice cooker, flat scooter tyre).

```bash
# Mac / Linux
./start.sh
# Windows: double-click start.bat
```
Then open http://localhost:8000 and tap a "Try a sample" link.

Go live with real Meta models (one step):
```bash
python scripts/set_keys.py      # paste your key (hidden), writes .env, then checks every model
python scripts/set_keys.py --check-only   # re-check later; check_keys.py --fake = dry run, no key, no cost
```

Run every check (same as CI: ruff, mypy strict, all tests incl. Playwright browser smoke):
```bash
pip install -r requirements-dev.txt
python -m playwright install chromium   # optional; browser tests skip cleanly without it
scripts/check_all.sh
```

Deploy (Render free plan, click by click): **[docs/DEPLOY.md](docs/DEPLOY.md)**, then check it with `python scripts/deploy_check.py https://<your-app>.onrender.com` (add `--live` once a key is set).

Step-by-step for non-developers (accounts, keys, deploy to Render, phone testing): **[docs/SETUP_FOR_MALIK.md](docs/SETUP_FOR_MALIK.md)**. End-user guide: **[docs/HOW_TO_USE.md](docs/HOW_TO_USE.md)**.

## Documentation map

| Doc | For |
|---|---|
| [HANDOFF.md](HANDOFF.md) | Anyone picking the project up: state, decisions, what's left |
| [TODO.md](TODO.md) | Remaining work, ordered, with owner |
| [CHANGELOG.md](CHANGELOG.md) | Dated build log |
| [docs/SETUP_FOR_MALIK.md](docs/SETUP_FOR_MALIK.md) | Click-by-click tutorial: keys, run, deploy, update |
| [docs/HOW_TO_USE.md](docs/HOW_TO_USE.md) | Using the app (English + Bahasa) |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Components, sequence, data, deployment |
| [docs/AI_PIPELINE.md](docs/AI_PIPELINE.md) | Every stage, model, prompt, schema, failure mode |
| [docs/META_API_NOTES.md](docs/META_API_NOTES.md) | Verified endpoints, model ids, prices, doc links |
| [docs/API.md](docs/API.md) | HTTP endpoints with curl examples |
| [docs/SAFETY.md](docs/SAFETY.md) | Safety levels, hard stops, privacy |
| [docs/TESTING.md](docs/TESTING.md) | How to test, manual QA checklist |
| [docs/TEST_REPORT.md](docs/TEST_REPORT.md) | Latest automated test results |
| [docs/VERIFICATION_REPORT.md](docs/VERIFICATION_REPORT.md) | Every requirement → evidence, and what is still unverified |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Errors and fixes |
| [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) | 3-minute video script + shot list + backup plan |
| [docs/SUBMISSION.md](docs/SUBMISSION.md) | Field-by-field copy-paste block for the Cerebral Valley form + X post |
| [docs/WRITEUP.md](docs/WRITEUP.md) | ~400-word write-up: problem, how it works, models, safety, impact, honest status |
| [docs/DEPLOY.md](docs/DEPLOY.md) | Render deploy click by click, settings, roll back |
| [docs/USER_TRIAL_KIT.md](docs/USER_TRIAL_KIT.md) | 5-person user trial kit → impact report |
| [docs/ROADMAP.md](docs/ROADMAP.md) | After the hackathon |
| [docs/ATTRIBUTIONS.md](docs/ATTRIBUTIONS.md) | Third-party libraries and assets |
| [docs/DECISIONS.md](docs/DECISIONS.md) | Why things are built the way they are |
| [docs/WINNING_PLAN.md](docs/WINNING_PLAN.md) | Official judging criteria → features, with status |
| [docs/SUBMISSION_CHECKLIST.md](docs/SUBMISSION_CHECKLIST.md) | Every step to submit, who does it, how to check it |
| [docs/demo/README.md](docs/demo/README.md) | Demo video, vertical X clip, screenshots, how to regenerate |

## Built during the hackathon

Everything in this repository was written from scratch during the event window (Oct 26 – Nov 4, 2026). Dated list in [CHANGELOG.md](CHANGELOG.md); the git history shows the commit dates.

- 2026-10-31: live camera guide (SAM 3.1 on camera frames), hands-free voice commands, bengkel hand-off (WhatsApp + Maps + mechanic brief PDF), demo fallback, impact trial kit, Render free-plan deploy readiness + `deploy_check.py`, safety tick list, outcome buttons, timers, bengkel price vs DIY, HEIC photos, offline handling, accessibility, privacy erase, regenerated demo video/screenshots (v1.8 → v1.21).
- 2026-10-30 (evening): water pump scenario, PDF report, My garage, PWA, video capture (sharpest frames), full Basa Jawa strings, open-weights badge, safety escalation card, mypy strict, 10 labelled stand-in fixtures, Playwright browser smoke tests, generated demo video/screenshots/architecture diagram, one-step key swap (`set_keys.py --stdin`).
- 2026-10-30: spec, Meta API verification, backend pipeline (listen → look → SAM → diagnose → plan → safety → illustrate → narrate → verify → re-plan), phone web app, fake Meta server, 77 automated tests, CI, Docker/Render deploy files, full docs.

## Team

Ragil Artza Rozaksyah ("Malik"), Semarang, Indonesia. Solo.

## License

MIT, see [LICENSE](LICENSE). Third-party notices in [docs/ATTRIBUTIONS.md](docs/ATTRIBUTIONS.md).

> Tukang Copilot gives AI-generated guidance that can be wrong. You are responsible for your safety. For gas, house wiring, or high voltage, call a professional.
