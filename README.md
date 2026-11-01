# Tukang Copilot

Every phone becomes a mechanic's apprentice. You point the phone at something broken and say what's wrong in Bahasa
Indonesia, Javanese or English. Tukang Copilot outlines the exact part on *your* photo (SAM 3.1), works out the fault and
plans the fix (Muse Spark), checks each step you do with the camera, re-plans when it is still broken, and tells you to
STOP when the job is dangerous.

It also works in WhatsApp. Send a photo and a voice note to the WhatsApp number and you get back the marked photo, the
diagnosis, a button per step and the same red stop, from the same agent and safety gate ([docs/WHATSAPP.md](docs/WHATSAPP.md);
there is a simulator at `/wa`). I tested it against a fake Graph API. A real WhatsApp number is still pending setup.

Meta Global AI Developer Hackathon 2026 (Meta x Cerebral Valley) · Indie Developer track · Push the Frontier ·
built solo in Semarang, Oct 26 to Nov 4, 2026.

<table><tr>
<td width="330"><img src="docs/demo/hero.gif" width="320" alt="Phone flow: 1-tap demo, SAM 3.1 parts, agent log, safety tick list, camera step check, live guide, re-plan, red stop, Basa Jawa"></td>
<td>

| | |
|---|---|
| Live app | [LIVE_URL] |
| 3-min video | [YOUTUBE_URL] · repo copy: [docs/demo/tukang-copilot-demo.mp4](docs/demo/tukang-copilot-demo.mp4) (2:55, demo mode, 3 s hook title card, captions + voice-over; chapters in [docs/demo/TIMESTAMPS.txt](docs/demo/TIMESTAMPS.txt)) |
| Code | [GITHUB_URL] (MIT) |
| For judges | [Judging map](docs/JUDGING_MAP.md) (each criterion and where the evidence is) · [Judge FAQ](docs/launch/JUDGE_FAQ.md) · [Eval](docs/EVAL.md) (red-team safety + injection) · [One-pager PDF](docs/launch/one-pager.pdf) |
| Write-up | [docs/WRITEUP.md](docs/WRITEUP.md) · form copy: [docs/SUBMISSION.md](docs/SUBMISSION.md) |
| Launch kit | [YouTube](docs/launch/YOUTUBE.md) · [X thread](docs/launch/X_THREAD.md) · [Community vote](docs/launch/COMMUNITY_VOTE_KIT.md) |

</td></tr></table>

## Try it in 60 seconds

1. Open [LIVE_URL] on a phone. Or run it locally with `./start.sh` and open http://localhost:8000. You don't need a key or an account.
2. Tap **▶ Try the 1-tap demo**. Results stream in as each stage finishes: what Muse Spark saw, the parts SAM 3.1 outlined, the likely cause.
3. Answer the one question it asks (it only asks when it is under 60% sure), tick the safety list, and the steps unlock.
4. Tap **Check this step** and pick the dark sample photo. It gets rejected with a specific fix ("turn on your torch"). Pick the right one and it passes.
5. Tap **Still broken**. It re-plans for the next cause ("Plan 2 of 3").
6. Open **What the AI did**. You see each decision and the Meta model or code rule that made it. Tap a line to jump there.
7. Try the "dead rice cooker" sample ("rice cooker mati" in Bahasa). You get a red STOP with a technician PDF and a bengkel hand-off. Then switch to Basa Jawa at the top.
8. Open `/wa` (the "Also works in WhatsApp" link under the first screen). This is the WhatsApp simulator. Tap a sample chip and the same agent answers as a WhatsApp chat with the marked photo, the diagnosis and step buttons. Try "gas smell" for the red stop. It is demo mode only: it runs the real webhook handler, but not on a real WhatsApp number.

> The free server sleeps and takes about 50 s to wake. If it hasn't answered within 4 s, the 1-tap demo plays a
> recorded demo-mode run, labelled "▶ Recorded demo" on screen (`?replay=1` forces it). Your own photos, the live
> camera and voice commands need the awake server.
>
> The first screen follows the phone's language: English on an English phone, Bahasa Indonesia when Indonesian is in
> the phone's language list. `?lang=en`, `?lang=id` or `?lang=jv` on the link overrides it, and the app remembers the
> switch at the top. Back returns to the first screen and Forward brings you back to the same repair.

<sub>Honest status: the video, screenshots and 1-tap demo run in clearly labelled demo mode, with stand-in photos and
recorded model answers and no API calls. The live guide uses Chromium's fake camera. I tested the live Meta path end to
end against a stand-in server built from the official API docs (768 automated tests pass; red-team eval in docs/EVAL.md,
mock and fake-model). A live Meta model answer is not yet verified because I still need the API key. Impact numbers in
docs/IMPACT.md are mock data until real trials run.</sub>

### Where each Meta model is used

| Stage | Meta model | Code | What it does |
|---|---|---|---|
| Listen | Muse Voice Transcribe `muse-voice-transcribe-1.0` | [`meta_client.transcribe`](api/meta_client.py) ← [`engine.stage_listen`](api/pipeline/engine.py) | Indonesian/English voice note → text with repair-keyword biasing; push-to-talk voice commands ([`engine.voice_command`](api/pipeline/engine.py)) |
| Listen (Javanese) | Muse Spark 1.2 audio input | [`meta_client.transcribe_with_spark_audio`](api/meta_client.py) | Javanese is not one of Voice Transcribe's languages, so Spark 1.2 transcribes it |
| Look | Muse Spark 1.3 vision + structured output | [`engine.stage_look`](api/pipeline/engine.py) → [`meta_client.chat_json`](api/meta_client.py) | Photos → `ObjectReport` JSON (object, parts with boxes, visible issues) |
| Find parts | SAM 3.1 `sam-3.1` | [`engine.stage_segment`](api/pipeline/engine.py) → [`meta_client.segment`](api/meta_client.py) → [`render/overlay.py`](api/render/overlay.py) | One box-prompt call for all parts → pixel masks → numbered overlay on *your* photo |
| Live guide | SAM 3.1 | [`pipeline/track.py`](api/pipeline/track.py) | Tracks the step's part on live camera frames (~1/s, capped per repair) |
| Diagnose / plan / re-plan | Muse Spark 1.3 or Muse Spark Open (open weights, Baseten) | [`engine.stage_diagnose`](api/pipeline/engine.py), [`stage_plan`](api/pipeline/engine.py), [`replan`](api/pipeline/engine.py) | `Diagnosis` + `RepairPlan` JSON; asks one question under 60 % confidence; next cause when it is still broken |
| Illustrate | Muse Image `muse-image-1.0` | [`engine.make_diagram`](api/pipeline/engine.py) → [`meta_client.edit_image`](api/meta_client.py) | Turns your photo into a diagram for hidden steps; Spark reviews it and a bad one is redrawn once |
| Verify | Muse Spark 1.3 vision | [`engine.check_step`](api/pipeline/engine.py) | New photo vs. the expected state → ✓ or a specific correction |

Every Meta call goes through one file, [`api/meta_client.py`](api/meta_client.py), which handles retries, timeouts, JSON-schema validation and the per-repair cost cap. The safety gates are plain code in [`api/pipeline/safety.py`](api/pipeline/safety.py), and [`api/untrusted.py`](api/untrusted.py) fences the owner's text as untrusted data.

The WhatsApp channel uses Meta's WhatsApp Cloud API (Graph API v26.0). [`api/channels/whatsapp.py`](api/channels/whatsapp.py) is a webhook: photos, a text or a voice note come in and go through the same `engine.create` / `engine.run` as the web app, with the same models and the same safety gate. Answers go back as WhatsApp messages with reply buttons per step, the marked photo and the PDF report. Each webhook POST is checked against `X-Hub-Signature-256`. I test it against a fake Graph API ([`api/testing/fake_graph.py`](api/testing/fake_graph.py)), and `/wa` is a simulator page that runs the same handler in demo mode. Setup: [docs/WHATSAPP.md](docs/WHATSAPP.md).

| Snap + speak | Parts found (SAM 3.1) | What the AI did | Check my step |
|---|---|---|---|
| ![home](docs/demo/screenshots/01_home.png) | ![parts](docs/demo/screenshots/05_parts.png) | ![agent log](docs/demo/screenshots/23_agent_log.png) | ![check](docs/demo/screenshots/07_check_fail.png) |
| Live camera guide | Bengkel hand-off | Safety stop | Basa Jawa |
| ![live](docs/demo/screenshots/16_live_guide.png) | ![hand-off](docs/demo/screenshots/18_handoff.png) | ![stop](docs/demo/screenshots/11_rice_stop.png) | ![jawa](docs/demo/screenshots/20_javanese_result.png) |

<sub>All 34 screenshots are in [docs/demo/screenshots](docs/demo/screenshots) (demo mode, labelled stand-in photos), including `28_diagram_step.png` (Muse Image diagram step, stand-in drawing), `29_laptop.png` (laptop phone-frame view with QR code) and `30_whatsapp_*.png` (the WhatsApp simulator: Javanese diagnosis, step buttons, red stop; English step check and PDF). The video's 21 scenes and their start times are in [docs/demo/TIMESTAMPS.txt](docs/demo/TIMESTAMPS.txt).</sub>

## Why I built it

Indonesia runs on 139 million motorbikes (BPS 2024), electric water pumps (17% of households drink pumped water, BPS 2023), rice cookers, fans and household plumbing. A small fault costs a day's wage at a bengkel, or days without water. Repair videos are rarely for your exact model and rarely in your language, and they can't see *your* problem.

Tukang Copilot looks at the actual object, marks the actual parts on your own photo and checks each step you do. When a job is dangerous and needs a professional, it says so plainly, in your language.

## What it does

1. Snap and speak. Take 1–3 photos or a 5–10 s video (the server keeps the sharpest frame from each third, and the clip's sound can be the voice note), then record a voice note (≤60 s) or type. Pick a category chip (Motor, Pompa air, Elektronik rumah, Pipa/keran, Lainnya).
2. Finds the parts. SAM 3.1 segments each relevant part, and the app tints and numbers them on your photo.
3. Diagnoses. You get the top causes with confidence and evidence, tools and parts with estimated rupiah prices, difficulty 1–5, a time estimate and a safety level: 🟢 safe / 🟠 caution / 🔴 stop.
4. Asks when unsure. If the top cause is below 60% it asks one follow-up question before it plans.
5. Guides the repair. A short "before you start" safety tick list unlocks the steps. After that it's one step per screen: the right picture (your photo with that part highlighted, or a Muse Image diagram for hidden steps), a short instruction, why it matters, warnings, countdown timers for waiting steps, and voice readout.
   - Live camera guide: point the phone and SAM 3.1 outlines the step's target part on the live camera picture (about 1 frame a second, capped per repair). *Check now* verifies the step from the current frame.
   - Hands-free: steps are read aloud and the phone listens for voice commands (lanjut / kembali / ulang / cek / masih rusak / berhenti, also in Javanese and English). Phones without continuous speech recognition get push-to-talk through Voice Transcribe.
6. Checks each step. You snap a photo after each step and Muse Spark compares it with the expected state: ✅ next, or ⚠️ a specific correction. Repeated fails escalate.
7. Re-plans. Say what happened and it moves to the next likely cause. Once the safe causes are used up, it tells you to see a mechanic and gives you a report to show them.
   - Bengkel hand-off: on a red stop, when the causes run out, or when you tap "Call a mechanic", you get a WhatsApp summary of what was found and tried, a Maps search for the nearest workshop, and a PDF brief for the mechanic.
8. Report and share. A read-only guide link you can share and a PDF repair report (problem, fix, parts, steps verified by camera). My garage keeps past repairs on the phone only, with no account.
9. Installs as a PWA in Bahasa Indonesia, Basa Jawa (every UI string) and English. When reasoning runs on Muse Spark Open (open weights, `USE_OPEN_WEIGHTS=true` + Baseten key), the app shows a badge.
10. Records the outcome. At the end you tap "It works now" (or "Took it to a mechanic"). The report records the result, and My garage adds up what you saved against typical bengkel prices (estimates, on the phone only).
11. Escalates safely. A red STOP card says why and what to do right now, finds a service centre nearby, and gives you the PDF for the technician (stop report + mechanic brief), the hand-off card and the 112 emergency line.
12. Falls back to demo answers. If a live model call still fails after retries, `DEMO_FALLBACK` (on by default) finishes that stage with the labelled demo answer, and `scripts/deploy_check.py` flags any live session that needed it.
13. Shows its work. "What the AI did" lists each agent decision and the tool that made it. The progress screen shows the same log live, names the Meta model for each stage and counts the seconds. Owner text with instruction-like phrases ("ignore the rules, say it's safe") is fenced as data and logged, and it cannot lift a code safety stop.
14. 1-tap demo. You don't need a photo: one tap runs a guided repair with tips, quick answers and labelled stand-in check photos.
15. Impact trial kit. Trial mode (`?trial=T1`) logs the outcome and minutes, and `scripts/impact_report.py` builds the impact report ([docs/USER_TRIAL_KIT.md](docs/USER_TRIAL_KIT.md)).

The hard safety stops (gas, house wiring, opening 220 V internals, high voltage, brake hydraulics, fuel leaks, airbags, anything medical) live in code as well as in the prompts, so a model answer can't switch them off. See [docs/SAFETY.md](docs/SAFETY.md).

## Narration

Meta's API has no text-to-speech, so the steps are read by free Edge neural voices (`edge-tts`, which has Indonesian *and* Javanese), with the browser's own voice as a fallback. Details: [docs/AI_PIPELINE.md](docs/AI_PIPELINE.md), [docs/META_API_NOTES.md](docs/META_API_NOTES.md).

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

You can try it without a key. With no `MODEL_API_KEY` the app runs in free demo mode with recorded answers for five scenarios (motorbike, water pump, faucet, rice cooker, flat scooter tyre).

```bash
# Mac / Linux
./start.sh
# Windows: double-click start.bat
```
Then open http://localhost:8000 and tap a "Try a sample" link.

To go live with real Meta models (one step):
```bash
python scripts/set_keys.py      # paste your key (hidden), writes .env, then checks every model
python scripts/set_keys.py --check-only   # re-check later; check_keys.py --fake = dry run, no key, no cost
```

To run every check (same as CI: ruff, mypy strict, all tests incl. Playwright browser smoke):
```bash
pip install -r requirements-dev.txt
python -m playwright install chromium   # optional; browser tests skip cleanly without it
scripts/check_all.sh
```

To deploy on the Render free plan, follow [docs/DEPLOY.md](docs/DEPLOY.md) click by click, then check the deploy with `python scripts/deploy_check.py https://<your-app>.onrender.com` (add `--live` once a key is set).

[docs/SETUP.md](docs/SETUP.md) is how I run it: demo mode, keys, the Render deploy, phone testing and the checks. The end-user guide is [docs/HOW_TO_USE.md](docs/HOW_TO_USE.md).

## Documentation map

| Doc | For |
|---|---|
| [TODO.md](TODO.md) | What is left, in order |
| [CHANGELOG.md](CHANGELOG.md) | Dated build log |
| [docs/SETUP.md](docs/SETUP.md) | How I run it: demo mode, keys, deploy, checks, settings |
| [docs/HOW_TO_USE.md](docs/HOW_TO_USE.md) | Using the app (English + Bahasa) |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Components, sequence, data, deployment |
| [docs/AI_PIPELINE.md](docs/AI_PIPELINE.md) | Each stage, model, prompt, schema, failure mode |
| [docs/META_API_NOTES.md](docs/META_API_NOTES.md) | Verified endpoints, model ids, prices, doc links |
| [docs/API.md](docs/API.md) | HTTP endpoints with curl examples |
| [docs/SAFETY.md](docs/SAFETY.md) | Safety levels, hard stops, privacy |
| [docs/TESTING.md](docs/TESTING.md) | How to test, manual QA checklist |
| [docs/TEST_REPORT.md](docs/TEST_REPORT.md) | Latest automated test results |
| [docs/VERIFICATION_REPORT.md](docs/VERIFICATION_REPORT.md) | Each requirement → evidence, and what is still unverified |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Errors and fixes |
| [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) | 3-minute video script + shot list + backup plan |
| [docs/SUBMISSION.md](docs/SUBMISSION.md) | Field-by-field copy for the live Cerebral Valley form, sourced problem numbers, bonus prize claims |
| [docs/WRITEUP.md](docs/WRITEUP.md) | Write-up (~850 words): problem, user, demo, how it works, safety, eval, honest status, what's next |
| [docs/JUDGING_MAP.md](docs/JUDGING_MAP.md) | Official criteria and bonus prize rules → evidence in the repo, and the open gaps |
| [docs/launch/](docs/launch/) | Launch kit: YouTube (title, chapters, thumbnail), X thread, community vote kit (id/jv/en), judge FAQ, one-pager PDF, architecture diagram |
| [docs/DEPLOY.md](docs/DEPLOY.md) | Render deploy click by click, settings, roll back |
| [docs/WHATSAPP.md](docs/WHATSAPP.md) | Optional WhatsApp channel: Meta app setup click by click, settings, simulator, how it is tested |
| [docs/USER_TRIAL_KIT.md](docs/USER_TRIAL_KIT.md) | 5-person user trial kit → impact report |
| [docs/ROADMAP.md](docs/ROADMAP.md) | After the hackathon |
| [docs/ATTRIBUTIONS.md](docs/ATTRIBUTIONS.md) | Third-party libraries and assets |
| [docs/DECISIONS.md](docs/DECISIONS.md) | Why things are built the way they are |
| [docs/SUBMISSION_CHECKLIST.md](docs/SUBMISSION_CHECKLIST.md) | Each step to submit, who does it, how to check it |
| [docs/demo/README.md](docs/demo/README.md) | Demo video, vertical X clip, screenshots, how to regenerate |

## Built during the hackathon

I wrote everything in this repository from scratch during the event window (Oct 26 to Nov 4, 2026). [CHANGELOG.md](CHANGELOG.md) has the dated list, and the git history shows the commit dates.

- 2026-11-02 (v1.27): WhatsApp channel (Cloud API webhook, same engine and safety gate, simulator at `/wa`, fake Graph API tests), and an owner token so a shared guide link cannot answer or erase for the owner.
- 2026-10-31 (v1.22): agent log "What the AI did", 1-tap guided demo, prompt-injection hardening, follow-up rate limit + photo-check cap, Javanese demo answers, WCAG AA contrast, model chips + elapsed time on progress, 8× faster overlay rendering.
- 2026-10-31: live camera guide (SAM 3.1 on camera frames), hands-free voice commands, bengkel hand-off (WhatsApp + Maps + mechanic brief PDF), demo fallback, impact trial kit, Render free-plan deploy readiness + `deploy_check.py`, safety tick list, outcome buttons, timers, bengkel price vs DIY, HEIC photos, offline handling, accessibility, privacy erase, regenerated demo video/screenshots (v1.8 → v1.21).
- 2026-10-30 (evening): water pump scenario, PDF report, My garage, PWA, video capture (sharpest frames), full Basa Jawa strings, open-weights badge, safety escalation card, mypy strict, 10 labelled stand-in fixtures, Playwright browser smoke tests, generated demo video/screenshots/architecture diagram, one-step key swap (`set_keys.py --stdin`).
- 2026-10-30: spec, Meta API verification, backend pipeline (listen → look → SAM → diagnose → plan → safety → illustrate → narrate → verify → re-plan), phone web app, fake Meta server, 77 automated tests, CI, Docker/Render deploy files, docs.

## Team

Just me: Ragil Artza Rozaksyah ("Malik"), Semarang, Indonesia.

## License

MIT, see [LICENSE](LICENSE). Third-party notices are in [docs/ATTRIBUTIONS.md](docs/ATTRIBUTIONS.md).

> Tukang Copilot gives AI-generated guidance that can be wrong. You are responsible for your safety. For gas, house wiring, or high voltage, call a professional.
