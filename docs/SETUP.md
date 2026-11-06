# How I run it

This is how I run Tukang Copilot on my laptop, switch on the real Meta models, deploy it, and run the checks. Without a key it runs in offline sample mode, which costs nothing and needs no account. If something breaks, look in [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## Offline sample mode on a laptop (10 minutes, free)

You need Python 3.11 or newer and internet for the first install.

```bash
./start.sh          # Mac / Linux
start.bat           # Windows (double-click works too)
```

The first start makes a `.venv`, installs `requirements.txt` (2 to 4 minutes) and copies `.env.example` to `.env`. When the window says `Open http://localhost:8000`, open that in Chrome. An orange *Offline sample mode* line at the top means no key is set. Tap **motor mogok**, **kran menetes** or **rice cooker mati** under the big button, answer the question, then walk through the steps. Ctrl+C stops it.

To try it on a phone on the same Wi-Fi, open `http://<laptop-ip>:8000` (Windows: `ipconfig`, IPv4 Address). Phones only allow camera and mic on https, so over plain Wi-Fi you get the samples and gallery upload only. For the full camera, deploy it or run `cloudflared tunnel --url http://localhost:8000` and open the `https://…trycloudflare.com` link it prints.

## Real Meta models (15 minutes)

1. On https://dev.meta.ai, claim the hackathon credits, add a card under **Billing** and set a spend limit (I use $20).
2. **API keys** → **Create key** → copy it. Don't paste it into any chat.
3. Run `python scripts/set_keys.py` (Windows: `.venv\Scripts\python scripts\set_keys.py`), paste the key (nothing shows while you paste) and press Enter. Press Enter again to skip Baseten.

`set_keys.py` writes `.env` (git ignores it), sets `OFFLINE=0` and checks every model the app uses: key and model list, Muse Spark 1.3 vision and structured output, SAM 3.1, the live camera guide, Muse Image, Muse Voice Transcribe and Muse Spark 1.2 audio, plus a SKIP line for open weights when there is no Baseten key. It should end with ALL GOOD, for well under $0.05. Every FAIL comes with a `fix:` line; a wrong key shows *"Meta says this key is not valid (401)"*. Restart the app and the *Offline sample mode* line is gone.

Later checks: `set_keys.py --check-only`, or `scripts/check_keys.py --no-cost` (key and model list only, free). `scripts/check_keys.py --fake` shows what a pass looks like without a key. After the key works, `python scripts/first_live_run.py` runs one sample repair (a few US cents) and writes `docs/LIVE_RUN.md`.

One repair costs about $0.01 to $0.05. The live camera guide adds about one SAM call per second while it is on, capped by `MAX_TRACK_FRAMES`, and `MAX_COST_PER_SESSION_USD` (default $0.50) stops any single repair that would cost more.

### Optional: open weights on Baseten

With this on, diagnosis and planning run on Muse Spark Open (`meta-models/muse-spark-open`) and the rest stays on the Meta API. Get a key at https://www.baseten.co (**API keys** → **Create**), run `set_keys.py` again and paste it at the second question. That sets `BASETEN_API_KEY` and `USE_OPEN_WEIGHTS=1`, and the check shows "Muse Spark Open on Baseten, open weights … ON". After a restart a blue "🔓 Reasoning: Muse Spark Open (open weights)" badge shows at the top, *Under the hood* says "open weights via Baseten" for Diagnose and Plan, and `/api/health` says `"open_weights": true`. The badge only shows when the switch is on and the key is there. If Baseten lists another model id, add `OPEN_MODEL=<that id>` to `.env`.

## Deploy

[DEPLOY.md](DEPLOY.md) has the Render steps (free plan). Short version: Render → New → Blueprint → repo `ragilmalik/tukang-copilot` → paste `MODEL_API_KEY` (and `BASETEN_API_KEY`) → Apply → wait for Live. Then run `python scripts/deploy_check.py https://<your-app>.onrender.com`; it should say READY, and `--live` also runs real repairs (a few cents). `https://<your-app>/health` says `"mode": "live"` with a key and `"mock"` without one.

If the live API misbehaves during judging, set `OFFLINE` to `1` in Render's Environment. About a minute later the app runs on the pre-written offline sample answers with no spend (the header says so). Set it back to `0` afterwards.

`python scripts/build_static.py` builds `dist-static/`, a server-free copy that plays the recorded demo; `--help` lists hosting steps. WhatsApp setup is in [WHATSAPP.md](WHATSAPP.md) and is optional.

## Checks

```bash
pip install -r requirements-dev.txt
scripts/check_all.sh                  # ruff + mypy strict + all tests, same as CI
python scripts/make_test_report.py    # writes docs/TEST_REPORT.md from a real run
OFFLINE=1 PORT=8765 python app.py        # then, in another terminal:
python scripts/smoke_e2e.py http://127.0.0.1:8765
python scripts/run_eval.py            # writes docs/EVAL.md
python scripts/record_replay.py --check
python scripts/build_static.py --check
```

The browser tests need Chromium on `PATH` (they skip without it) and the jsdom test needs `npm install --prefix /tmp/jd jsdom`. On my 2-CPU box the full suite takes about 10 minutes, so I often run it in parts: the non-browser files in a few groups, then each `test_playwright_*.py` on its own. Set `NO_PROXY=127.0.0.1,localhost` if a proxy is configured.

Demo assets: `python scripts/make_demo_assets.py shots|diagram|voice|video|all` (needs ffmpeg and Chromium). The video step caches segments in `$TMPDIR/tukang-video`; delete that folder after re-shooting screenshots or the old frames come back.

## Settings (`.env`, or Environment on Render)

| Name | Default | Meaning |
|---|---|---|
| `MODEL_API_KEY` | empty | Meta key. Empty = offline sample mode |
| `OFFLINE` / `DEMO_MODE` | 0 | 1 = force offline sample mode even with a key |
| `USE_OPEN_WEIGHTS`, `BASETEN_API_KEY` | 0 / empty | Diagnosis + plan on Muse Spark Open |
| `OPEN_MODEL` | meta-models/muse-spark-open | Baseten model id, only if Baseten shows another |
| `ILLUSTRATE` | 1 | Muse Image diagrams for hidden steps |
| `MAX_DIAGRAMS` | 2 | Max diagrams per repair |
| `DIAGRAM_CHECKER` | 1 | Spark reviews each diagram, redraws once |
| `NARRATION_VOICE` | 1 | Server voice files; 0 = browser voice only |
| `MAX_COST_PER_SESSION_USD` | 0.50 | Hard stop per repair |
| `RATE_LIMIT_PER_HOUR` | 30 | New repairs per visitor per hour on a live site (0 = off) |
| `DAILY_BUDGET_USD` | 10 | Rolling 24 h spend cap for the whole site; new repairs get a friendly "try tomorrow" (0 = off). Erased repairs still count for 24 h |
| `CLIENT_IP_HEADER` | (empty) | A header your edge proxy sets to the visitor's address and overwrites (Cloudflare: `cf-connecting-ip`); the rate limit uses it first. render.yaml sets it. Only set it with such a proxy in front |
| `FORWARDED_HOPS` | 1 | Proxies in front of the app that append to X-Forwarded-For. The rate limit keys on the entry that many places from the right (the one your proxy wrote); 0 ignores the header (nothing in front) |
| `MAX_TRACK_FRAMES` | 120 | Live camera guide: max SAM frames per repair |
| `TRACK_MIN_INTERVAL_S` | 0.6 | Live camera guide: minimum seconds between frames |
| `MAX_CHECK_FAILS` | 2 | Failed step checks before suggesting re-plan / pro |
| `RETENTION_HOURS` | 24 | Photos and sessions auto-delete after this |
| `DATA_DIR` | ./data (Render: /tmp/tukang-data) | Where photos and sessions are kept |
| `PORT` | 8000 | Web port (Render sets its own) |
