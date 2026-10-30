# Setup tutorial (zero coding knowledge needed)

This takes you from nothing to a working app on your phone. Every step says exactly what to click. If something goes wrong, look in [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

**You can do Part 1 right now without any key or money.**

---

## Part 1 · Run it on your computer in demo mode (10 minutes, free)

You need: a Windows or Mac computer and internet.

1. **Install Python.**
   - Windows: open https://www.python.org/downloads/ → click the yellow **Download Python 3.12** button → run the file → **tick "Add python.exe to PATH"** at the bottom of the first screen → click **Install Now**.
   - Mac: same page, download the macOS installer, open it, click Continue until it finishes.
2. **Get the project folder.**
   - From GitHub: open the repo page → green **Code** button → **Download ZIP** → right-click the ZIP → **Extract All**.
3. **Start it.**
   - Windows: open the extracted folder → double-click **start.bat**. A black window opens. The first time it installs things (2–4 minutes). When you see `Open http://localhost:8000`, it's ready. Keep this window open.
   - Mac: open **Terminal** (Cmd+Space, type Terminal), type `cd ` (with a space), drag the folder into the window, press Enter, then type `./start.sh` and press Enter.
4. **Open it.** In Chrome go to **http://localhost:8000**. You'll see an orange line saying *Demo mode*.
5. **Try it.** Under the big button, tap **motor mogok** (or "kran menetes", "rice cooker mati"). Watch the stages tick, answer the question, then walk through the steps.

To stop: close the black window (or press Ctrl+C).

### Try it on your phone (same Wi-Fi)

1. On the computer, find its local address: Windows → open Command Prompt, type `ipconfig`, look for **IPv4 Address** (like `192.168.1.23`). Mac → System Settings → Wi-Fi → Details → IP address.
2. On your phone (same Wi-Fi), open Chrome and go to `http://192.168.1.23:8000` (your number).
3. Camera and microphone need **https** on phones, so over plain Wi-Fi you can only use the samples and photo upload from the gallery. For full camera + mic, use Part 3 (deploy) or a Cloudflare tunnel (below).

**Cloudflare tunnel (you already have Cloudflare):** install `cloudflared` from https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/ then run `cloudflared tunnel --url http://localhost:8000`. It prints an `https://…trycloudflare.com` link that works on any phone.

---

## Part 2 · Switch on the real Meta models (15 minutes)

1. **Claim the hackathon credits** ($150) with the Cerebral Valley form (needs your Meta Team ID). Then in https://dev.meta.ai → **Billing**: add a card and **set a spend limit** (e.g. $20) so you can never be surprised.
2. **Create an API key:** https://dev.meta.ai → sign in → **API keys** (left menu) → **Create key** → name it `tukang-copilot` → **Copy**. Don't paste it in any chat.
3. **Save it into the app (one step):** in the project folder, open a terminal (Windows: click the address bar of the folder, type `cmd`, Enter) and run:
   ```
   .venv\Scripts\python scripts\set_keys.py        (Windows)
   .venv/bin/python scripts/set_keys.py            (Mac)
   ```
   Paste the key when asked (nothing shows while you paste, that's normal), press Enter. Press Enter again to skip the Baseten key for now.
   It saves the key in a file called `.env`, switches demo mode off, and runs a check. You want to see **ALL GOOD** with five green PASS lines. A tiny real call costs under $0.02.
4. Start the app again (start.bat / start.sh). The orange *Demo mode* line is gone: you're live.
5. Want to re-check later (e.g. after topping up credits)? Run `set_keys.py --check-only`. It uses the saved key and prints PASS/FAIL again. Typing a wrong key never breaks anything: `.env` is only written when you paste a key.

**Cost per repair:** about $0.01–0.05 (a few Spark calls, one SAM call, 0–3 diagrams at $0.01). The app stops any single repair that would pass `MAX_COST_PER_SESSION_USD` (default $0.50).

### Optional: open-weights mode (for an open-weights bonus prize; check the exact prize list on the Cerebral Valley page)
1. https://www.baseten.co → sign up → **API keys** → create → copy.
2. Run `set_keys.py` again, paste the Meta key, then the Baseten key when asked. It sets `USE_OPEN_WEIGHTS=1`.
3. Diagnosis and planning now run on **Muse Spark Open** (`meta-models/muse-spark-open`). A blue **🔓 Muse Spark Open (open weights)** badge appears at the top of the app, and the bottom of the result screen shows "open weights via Baseten". Show this badge in the video.
If Baseten's model page shows a different model id, open `.env` in Notepad and add `OPEN_MODEL=<that id>`.

---

## Part 3 · Put it online for judges (20 minutes, uses your Render credits)

1. **Put the code on GitHub** (Malik can do this for you on request): a public repo named `tukang-copilot`.
2. https://render.com → sign in with GitHub → **New +** → **Blueprint** → choose the `tukang-copilot` repo → **Connect**. Render reads `render.yaml` and creates the service.
3. It asks for `MODEL_API_KEY` (and `BASETEN_API_KEY`): paste your keys there. Click **Apply**.
4. Wait for **Live** (5–8 minutes the first time). Your link looks like `https://tukang-copilot.onrender.com`.
5. Redeem a Render credit: **Account → Billing → Redeem code** (your codes start with `HTHON-`).
6. Check it: open the link on your phone over 4G, try a sample, then a real photo + voice.
   A full automatic check: `python scripts/smoke_e2e.py https://tukang-copilot.onrender.com` → **ALL PASSED**.
7. Put the link in README.md (top table) and in docs/SUBMISSION.md.

**Updating later:** any change pushed to GitHub redeploys automatically on Render.

**Is it working?** Open `https://<your-app>/health`. `"mode": "live"` means real Meta models; `"mock"` means the key is missing.

---

## Part 4 · Before you record the demo

- Take 8–10 clear photos of real things in good light: your bike's spark plug area, a water pump, a kitchen tap or hose, a rice cooker (for the red safety stop).
- Do one full run of each on your phone, then follow [DEMO_SCRIPT.md](DEMO_SCRIPT.md).
- Set `DEMO_MODE=1` on Render only if the live API is down during judging: the app keeps working with the recorded answers.

## Settings you might change (`.env` file, open with Notepad)

| Name | Default | Meaning |
|---|---|---|
| `MODEL_API_KEY` | empty | Meta key. Empty = demo mode |
| `MOCK` / `DEMO_MODE` | 0 | 1 = force demo mode even with a key |
| `USE_OPEN_WEIGHTS`, `BASETEN_API_KEY` | 0 / empty | Diagnosis + plan on Muse Spark Open |
| `ILLUSTRATE` | 1 | Muse Image diagrams for hidden steps |
| `MAX_DIAGRAMS` | 2 | Max diagrams per repair |
| `DIAGRAM_CHECKER` | 1 | Spark reviews each diagram, redraws once |
| `NARRATION_VOICE` | 1 | Server voice files; 0 = browser voice only |
| `MAX_COST_PER_SESSION_USD` | 0.50 | Hard stop per repair |
| `MAX_CHECK_FAILS` | 2 | Failed step checks before suggesting re-plan / pro |
| `RETENTION_HOURS` | 24 | Photos and sessions auto-delete after this |
| `PORT` | 8000 | Web port |
