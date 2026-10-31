# Setup tutorial (zero coding knowledge needed)

Everything is built and tested. Only the steps below need you (your keys, your Render account). Every step says exactly what to click. If something goes wrong, look in [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## Your remaining steps (about 45 minutes in total)

1. **Meta key → `set_keys.py`** (15 min). Create the key on dev.meta.ai and paste it into `python scripts/set_keys.py`. You want **ALL GOOD** at the end. Details: [Part 2](#part-2--switch-on-the-real-meta-models-15-minutes).
2. **Optional: Baseten key** for open weights (10 min). Paste it as the second answer in `set_keys.py`; the blue open-weights badge appears. Details: [Part 2b](#part-2b--optional-open-weights-muse-spark-open-on-baseten-3-steps).
3. **Deploy on Render** (15 min, free plan = $0). Click-by-click: [DEPLOY.md](DEPLOY.md). Paste the same keys in Render's Environment.
4. **Check the live link:** `python scripts/deploy_check.py https://<your-app>.onrender.com` → **READY** (add `--live` once to also test real repairs, a few cents).

You can do Part 1 right now without any key or money.

---

## Part 1 · Run it on your computer in demo mode (10 minutes, free)

You need: a Windows or Mac computer and internet.

1. **Install Python.**
   - Windows: open https://www.python.org/downloads/ → click the yellow **Download Python 3.12** button → run the file → **tick "Add python.exe to PATH"** at the bottom of the first screen → click **Install Now**.
   - Mac: same page, download the macOS installer, open it, click Continue until it finishes.
2. **Get the project folder.** From GitHub: open the repo page → green **Code** button → **Download ZIP** → right-click the ZIP → **Extract All**.
3. **Start it.**
   - Windows: open the extracted folder → double-click **start.bat**. A black window opens. The first time it installs things (2–4 minutes). When you see `Open http://localhost:8000`, it's ready. Keep this window open.
   - Mac: open **Terminal** (Cmd+Space, type Terminal), type `cd ` (with a space), drag the folder into the window, press Enter, then type `./start.sh` and press Enter.
4. **Open it.** In Chrome go to **http://localhost:8000**. You'll see an orange line saying *Demo mode*.
5. **Try it.** Under the big button, tap **motor mogok** (or "kran menetes", "rice cooker mati"). Watch the stages tick, answer the question, then walk through the steps.

To stop: close the black window (or press Ctrl+C).

### Try it on your phone (same Wi-Fi)

1. On the computer, find its local address: Windows → open Command Prompt, type `ipconfig`, look for **IPv4 Address** (like `192.168.1.23`). Mac → System Settings → Wi-Fi → Details → IP address.
2. On your phone (same Wi-Fi), open Chrome and go to `http://192.168.1.23:8000` (your number).
3. Camera and microphone need **https** on phones, so over plain Wi-Fi you can only use the samples and photo upload from the gallery. For full camera + mic, deploy (step 3) or use a Cloudflare tunnel: install `cloudflared` from https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/ then run `cloudflared tunnel --url http://localhost:8000`. It prints an `https://…trycloudflare.com` link that works on any phone.

---

## Part 2 · Switch on the real Meta models (15 minutes)

1. **Claim the hackathon credits** ($150) with the Cerebral Valley form (needs your Meta Team ID). Then in https://dev.meta.ai → **Billing**: add a card and **set a spend limit** (e.g. $20) so you can never be surprised.
2. **Create an API key:** https://dev.meta.ai → sign in → **API keys** (left menu) → **Create key** → name it `tukang-copilot` → **Copy**. Don't paste it in any chat.
3. **Save it into the app (one step):** in the project folder, open a terminal (Windows: click the address bar of the folder, type `cmd`, Enter) and run:
   ```
   .venv\Scripts\python scripts\set_keys.py        (Windows)
   .venv/bin/python scripts/set_keys.py            (Mac)
   ```
   Paste the key when asked (nothing shows while you paste, that's normal), press Enter. Press Enter again to skip the Baseten key (or paste it, see Part 2b).
   It saves the key in a file called `.env` (never uploaded to GitHub), sets `MOCK=0` (demo mode off), and checks every Meta model the app uses. You want **ALL GOOD** with these green PASS lines (well under $0.05 in total):
   - API key + model list
   - Muse Spark 1.3 vision + structured output (look, diagnose, plan, check my step)
   - SAM 3.1 segmentation (numbered parts on the photo)
   - Live camera guide (SAM 3.1 on a small camera frame, also shows if it is fast enough)
   - Muse Image (step diagrams)
   - Muse Voice Transcribe (voice notes)
   - Muse Spark 1.2 audio (Basa Jawa voice notes)
   - and one line for open weights: **SKIP** if you have no Baseten key (that's fine)
   Every FAIL line comes with a `fix:` line in plain English. A wrong key shows *"Meta says this key is not valid (401)"*.
4. Start the app again (start.bat / start.sh). The orange *Demo mode* line is gone: you're live.
5. Re-check any time (e.g. after topping up credits): `set_keys.py --check-only`, or the free version `scripts/check_keys.py --no-cost` (key + model list only). Want to see what a pass looks like without a key? `scripts/check_keys.py --fake`.

**Cost per repair:** about $0.01–0.05 (a few Spark calls, one SAM call, 0–3 diagrams at $0.01; the live camera guide adds about one SAM call per second while it is on, capped at `MAX_TRACK_FRAMES`). The app stops any single repair that would pass `MAX_COST_PER_SESSION_USD` (default $0.50).

## Part 2b · Optional: open weights (Muse Spark Open on Baseten), 3 steps

This is for the Open Weight bonus prize. Diagnosis and planning then run on **Muse Spark Open** (`meta-models/muse-spark-open`); everything else stays on the Meta API.

1. **Get a Baseten key:** https://www.baseten.co → sign up → **API keys** → **Create** → copy.
2. **Save it:** run `set_keys.py` again, paste the Meta key, then paste the Baseten key at the second question. It sets `BASETEN_API_KEY` and `USE_OPEN_WEIGHTS=1`, and the check now shows a green line **"Muse Spark Open on Baseten, open weights … ON: the open-weights badge will show"**. On Render, add the same two values in Environment (`BASETEN_API_KEY`, and change `USE_OPEN_WEIGHTS` to `1`).
3. **See the badge:** restart the app (Render restarts by itself) and open it. A blue **🔓 Reasoning: Muse Spark Open (open weights)** badge shows at the top (Indonesian: *Penalaran: …*), the *Under the hood* panel says "open weights via Baseten" for Diagnose and Plan, and `/api/health` says `"open_weights": true`. Show this badge in the video.

The badge only appears when it is really active (switch on **and** key present), so it can never be shown by mistake. If Baseten's model page shows a different model id, open `.env` in Notepad and add `OPEN_MODEL=<that id>` (on Render: add it in Environment).

---

## Part 3 · Put it online for judges

Follow **[DEPLOY.md](DEPLOY.md)** (numbered clicks, free plan, how to check, how to roll back). Short version: Render → New → Blueprint → repo `ragilmalik/tukang-copilot` → paste `MODEL_API_KEY` (and `BASETEN_API_KEY`) → Apply → wait for **Live** → `python scripts/deploy_check.py https://<your-app>.onrender.com`.

**Is it working?** Open `https://<your-app>/health`. `"mode": "live"` means real Meta models; `"mock"` means the key is missing or `MOCK=1`.

---

## Part 4 · Before you record the demo

- Take 8–10 clear photos of real things in good light: your bike's spark plug area, a water pump, a kitchen tap or hose, a rice cooker (for the red safety stop).
- Do one full run of each on your phone, then follow [DEMO_SCRIPT.md](DEMO_SCRIPT.md).
- If the live API misbehaves during judging: Render → your service → Environment → set `MOCK` to `1` → Save. In about a minute the app runs on the recorded demo answers (no spend). Set it back to `0` afterwards.

## Settings you might change (`.env` file, open with Notepad; on Render: Environment)

| Name | Default | Meaning |
|---|---|---|
| `MODEL_API_KEY` | empty | Meta key. Empty = demo mode |
| `MOCK` / `DEMO_MODE` | 0 | 1 = force demo mode even with a key |
| `USE_OPEN_WEIGHTS`, `BASETEN_API_KEY` | 0 / empty | Diagnosis + plan on Muse Spark Open |
| `OPEN_MODEL` | meta-models/muse-spark-open | Baseten model id, only if Baseten shows another |
| `ILLUSTRATE` | 1 | Muse Image diagrams for hidden steps |
| `MAX_DIAGRAMS` | 2 | Max diagrams per repair |
| `DIAGRAM_CHECKER` | 1 | Spark reviews each diagram, redraws once |
| `NARRATION_VOICE` | 1 | Server voice files; 0 = browser voice only |
| `MAX_COST_PER_SESSION_USD` | 0.50 | Hard stop per repair |
| `RATE_LIMIT_PER_HOUR` | 30 | New repairs per visitor per hour on a live site (0 = off) |
| `DAILY_BUDGET_USD` | 10 | Rolling 24 h spend cap for the whole site; new repairs get a friendly "try tomorrow" (0 = off) |
| `MAX_TRACK_FRAMES` | 120 | Live camera guide: max SAM frames per repair |
| `TRACK_MIN_INTERVAL_S` | 0.6 | Live camera guide: minimum seconds between frames |
| `MAX_CHECK_FAILS` | 2 | Failed step checks before suggesting re-plan / pro |
| `RETENTION_HOURS` | 24 | Photos and sessions auto-delete after this |
| `DATA_DIR` | ./data (Render: /tmp/tukang-data) | Where photos and sessions are kept |
| `PORT` | 8000 | Web port (Render sets its own) |
