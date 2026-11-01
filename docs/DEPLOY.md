# Deploy on Render (click by click, no coding)

This gets you a public `https://tukang-copilot.onrender.com` link that works on any phone (camera and microphone need https). It takes about 15 minutes, mostly waiting for the first build, and costs $0 on the free plan.

Render needs two files, and both are in the repo: `render.yaml` (the "Blueprint": what to build, with which settings) and `Dockerfile` (how to build it). The rest is clicking and pasting keys.

## Before you start

- The code has to be on GitHub as `ragilmalik/tukang-copilot`.
- Your Meta key (dev.meta.ai → API keys). Optional: your Baseten key. No key yet? You can still deploy: the app runs in free demo mode, and you add the key later (step 11).
- Copy keys straight from the provider's page into Render. Never paste them into GitHub, a chat, or a screenshot.

## Free or paid plan?

| | Free (default in render.yaml) | Starter (about $7/month) |
|---|---|---|
| Cost | $0 | about $7/month, or use a `HTHON-` credit code (Account → Billing → Redeem code) |
| Sleeps? | Yes, after 15 min with no visitors. The next visit waits about 1 minute while it wakes up. | Never sleeps |
| Photos and shared guide links kept | Until it falls asleep or redeploys (temporary disk; deleted after 24 h anyway) | Until the next redeploy or restart (max 24 h) |
| Good for | Testing, sharing the link, the video | Judging days, so the first judge never waits |

Start on Free. Switching later is one click (step 14) and doesn't need a code redeploy.

## Deploy (first time)

1. Open https://dashboard.render.com and sign in. The easiest way is **Sign in with GitHub**, with the account that owns `ragilmalik/tukang-copilot`.
2. Top right, click **+ New** → **Blueprint**.
3. Under *Connect a repository*: if `tukang-copilot` is not in the list, click **Configure account** (or **Connect GitHub**) → GitHub opens → choose *Only select repositories* → pick **tukang-copilot** → **Install / Save**. You come back to Render.
4. Next to **ragilmalik/tukang-copilot** click **Connect**.
5. *Blueprint Name*: type `tukang-copilot`. *Branch*: `main`. Render reads `render.yaml` and shows one web service, **tukang-copilot** (Docker, Free, Singapore).
6. Render asks for the secret values from render.yaml:
   - **MODEL_API_KEY**: paste your Meta key (or leave empty for demo mode).
   - **BASETEN_API_KEY**: paste your Baseten key, or leave empty.
   - **IMPACT_TOKEN**: optional. Any long random word; it lets you download the trial outcome log later. Empty is fine.
   - **PUBLIC_BASE_URL**: leave empty for now (you get the address in step 9), then fill it in (step 11).
   - **WA_TOKEN**, **WA_PHONE_NUMBER_ID**, **WA_VERIFY_TOKEN**, **WA_APP_SECRET**: optional, for the WhatsApp channel. Leave all four empty to skip it; to turn it on later, follow `docs/WHATSAPP.md`.
7. Click **Deploy Blueprint** (older screens call it **Apply**).
8. Click the **tukang-copilot** service, then **Logs**. The first build takes 5-8 minutes (it installs Python packages and ffmpeg). Wait until the top shows a green **Live** and the log says `Uvicorn running on http://0.0.0.0:10000`.
9. Your link is at the top of the service page, like `https://tukang-copilot.onrender.com` (Render may add a few letters if the name is taken). Open it on your phone over 4G: you should see the app, and no orange *Demo mode* line if you pasted a key.

## Check it (2 minutes)

10. On your computer, in the project folder:
    ```
    python scripts/deploy_check.py https://tukang-copilot.onrender.com
    ```
    You want READY at the end. Each line is PASS / WARN / FAIL; every FAIL has a `fix:` line in plain English. It checks https, `/api/health`, live vs demo mode, open weights, the home page, install-to-home-screen files, security headers (camera allowed), a PDF report, and all five demo repairs end to end.
    - In LIVE mode the PDF and the five repairs make real model calls, so they only run when you add `--live` (well under $1). Do that once after the first deploy.
    - A *"server took 50s to answer (it was asleep)"* WARN is normal on the free plan.
    - A *"LIVE repair silently used demo answers"* FAIL means `DEMO_FALLBACK` covered for a failing live call (almost always a wrong key or no credit). Fix the key; while testing you can set `DEMO_FALLBACK` to `0` so errors show instead.

## Change settings or add a key later

11. Service page → **Environment** (left menu) → find the name (e.g. `MODEL_API_KEY`) → **Edit** → paste → **Save, rebuild, and deploy** (or **Save and deploy**). It is live again in about a minute.
    - **PUBLIC_BASE_URL**: set it to your https Render address from step 9 (e.g. `https://tukang-copilot.onrender.com`, no slash at the end). The mechanic hand-off and WhatsApp links use it.
    - Other settings already in render.yaml: `MAX_TRACK_FRAMES` 120 (live camera frames per repair, about $0.30 of SAM at most), `TRACK_MIN_INTERVAL_S` 0.6 (at most ~1.6 frames a second), `DEMO_FALLBACK` 1 (a failing live call uses the labelled demo answer for that step so a judge never sees a dead end), `IMPACT_TOKEN` (optional, to download `/api/impact/outcomes.jsonl` with header `X-Impact-Token`).
    - Turn on open weights: set `USE_OPEN_WEIGHTS` to `1` and make sure `BASETEN_API_KEY` is filled.
    - Emergency switch if the live Meta API misbehaves during judging: set `MOCK` to `1`. The app keeps working on recorded demo answers at no cost. Set it back to `0` afterwards.
    - Spend caps are already set: `MAX_COST_PER_SESSION_USD` 0.50 per repair, `DAILY_BUDGET_USD` 10 per 24 h for the whole site, `RATE_LIMIT_PER_HOUR` 30 new repairs per visitor, `FOLLOWUP_RATE_PER_HOUR` 240 model calls inside repairs per visitor, `MAX_STEP_CHECKS` 40 photo checks per repair. Also set a spend limit on dev.meta.ai → Billing.

## Updates

12. Every push to the `main` branch on GitHub redeploys automatically (`autoDeploy: true`). Watch **Events** for *Deploy live*. Run `deploy_check.py` again after big changes.

## Roll back (if a new version breaks)

13. Service page → **Events** (left menu) → find the last deploy that says **Deploy live** and worked → click **Rollback** next to it → confirm. The old version is back in about a minute. (A rollback turns auto-deploy off for safety; turn it back on in **Settings → Build & Deploy → Auto-Deploy: Yes** after the fix is pushed.)
    - Quicker in an emergency: set `MOCK` to `1` (step 11).

## Switch to the always-on plan (optional, before judging)

14. Service page → **Settings** → **Instance Type** → **Starter** → **Save**. Redeem a credit first if you have one: **Account (top right) → Billing → Redeem code** (`HTHON-…`). To go back to $0, choose **Free** the same way.

## Troubleshooting

| What you see | What to do |
|---|---|
| Build failed in Logs | Click **Manual Deploy → Deploy latest commit** once (network hiccups happen). Still red: roll back (step 13) and read the last 20 log lines for the error. |
| App says *Demo mode* | `MODEL_API_KEY` is empty or `MOCK` is `1`: step 11. |
| *Too many repairs / daily budget* message | The public spend guard did its job. Raise `RATE_LIMIT_PER_HOUR` or `DAILY_BUDGET_USD` in Environment if you want. |
| Camera does not open on the phone | Use the `https://` link, and allow camera in the browser's site settings. |
| Shared guide link says *not found* | Render's disk is temporary: photos and guides vanish on every redeploy, restart, and (free plan) every time it falls asleep. Start a new repair. Starter keeps them until the next redeploy. |
| First visit is slow | Free plan was asleep; it wakes in about a minute (or switch to Starter, step 14). |

## Run the same container on your own computer (optional)

With Docker Desktop installed: `docker compose up --build` in the project folder → http://localhost:8000. It uses your `.env` if there is one (demo mode if not). It's the same container Render runs.
