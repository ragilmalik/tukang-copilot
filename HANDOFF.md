# Handoff

Read this first if you are picking up Tukang Copilot (human or AI).

## State on 2026-10-30 19:20 WIB (v1.1.0)
- **Complete, working app in demo mode, four scenarios:** motorbike (amber), water pump (amber, new), faucet (green), rice cooker (red stop). All stages, the phone UI, safety, verification and re-plan are built.
- **New in v1.1.0:** water pump flow with re-plan to the foot valve; PDF repair report (`/api/sessions/{id}/report.pdf`, button on result + guide pages); "My garage" history on the phone (localStorage); PWA routes; mypy strict clean on `api/`.
- **Checks (real runs, 19:15 WIB):** pytest 103/103 pass (`make_test_report.py`), ruff clean, `python -m mypy api` "no issues in 28 files", `node --check web/app.js` ok, `smoke_e2e.py` ALL PASSED on a local mock server, pump sample in jv + PDF endpoint 200 application/pdf checked by curl, PDF pages inspected visually.
- **Not yet live:** no Meta API key has been used. The real HTTP client is tested against a fake server that follows Meta's documented shapes. First real-key run is the next step.
- **Not yet published:** no GitHub repo, no deploy, no video. Malik must approve the repo and any public post or submission.

## Run it
```bash
./start.sh          # or start.bat on Windows → http://localhost:8000 (demo mode)
python scripts/set_keys.py      # go live
python -m pytest api/tests -q   # tests
python scripts/make_test_report.py   # regenerate docs/TEST_REPORT.md from real runs
```

## Where things are
| Path | What |
|---|---|
| `app.py` | Starts the server |
| `api/main.py` | HTTP endpoints + serves `web/` |
| `api/pipeline/engine.py` | The whole pipeline, session state, check, re-plan, report, cleanup |
| `api/meta_client.py` | The only code that calls Meta (and Baseten) |
| `api/schemas.py` | ObjectReport, Diagnosis, RepairPlan, StepCheck, DiagramReview |
| `api/pipeline/safety.py` | Text gate, plan gate, messages in id/jv/en |
| `api/pipeline/mock.py` | Demo answers + sample photos (motor, faucet, rice) |
| `api/render/overlay.py` | SAM masks → numbered overlay |
| `api/pipeline/media.py` | ffmpeg WAV conversion, edge-tts |
| `api/settings.py`, `api/cost.py`, `api/prompts.py` | Config, cost meter, prompt loader |
| `prompts/*.md` | One versioned prompt per stage |
| `api/testing/fake_meta.py` | Fake Meta API for tests and dry runs |
| `api/tests/` | All tests |
| `scripts/` | set_keys, check_keys, smoke_e2e, make_test_report |
| `web/` | index.html, guide.html, app.js, style.css |
| `docs/` | Everything else (see README map) |
| `docs/SPEC.md` | The original spec |

## Key decisions
See docs/DECISIONS.md. Most important: single FastAPI process + plain JS (no Next.js); JSON per session; edge-tts because Meta has no TTS; Javanese via Spark 1.2 audio; safety in code (3 layers); Standard-mode model ids only.

## Rules for whoever continues
- Ask Malik before creating the repo, creating accounts, spending money, posting publicly, or submitting.
- Never put keys in code or chat. `.env` locally, Render env vars in the cloud.
- Keep Malik's instructions short, numbered, plain English (Bahasa if he prefers). He is not a developer.
- After any change: `python -m pytest api/tests -q`, then `python scripts/make_test_report.py`, then update CHANGELOG.md and TODO.md.
- Check his shift schedule before asking him to do anything (he works nights).

## Next up (Malik, no Malik needed)
1. Video capture (5 to 10 s clip, 3 frames) in web/app.js + engine (owner of engine/web).
2. Open-weights badge chip in the UI and the PDF when `USE_OPEN_WEIGHTS=true`; per-stage model chips.
3. Safety escalation polish: red stop screen with service-centre advice and a PDF; Javanese strings for every remaining UI label.
4. Parallel run (see ../work/COORDINATION.md) owns: Playwright smoke, fixtures, demo video assets, submission checklist, WINNING_PLAN.

## Next 3 actions (need Malik)
1. Get the repo approval → push → CI green.
2. Real key → `check_keys.py` → live run of the three samples → fix differences.
3. Real photos → prompt tuning → deploy → phone test → video.

## Known gaps
Video capture, PDF report, garage history, water-pump fixture, Playwright/mypy, real performance numbers. All in TODO.md.
