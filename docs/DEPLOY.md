# Deploy on Render (click by click, no coding)

Result: a public `https://tukang-copilot.onrender.com` link that works on any phone (camera and microphone need https).
Time: about 15 minutes, most of it waiting for the first build. Cost: $0 on the free plan.

Everything Render needs is already in the repo: `render.yaml` (the "Blueprint": what to build and which settings) and `Dockerfile` (how to build). You only click and paste your keys.

## Before you start

- The code must be on GitHub as **`ragilmalik/tukang-copilot`** (Malik can push it once you say yes).
- Your Meta key (dev.meta.ai → API keys). Optional: your Baseten key. No key yet? You can still deploy: the app runs in free demo mode, and you add the key later (step 11).
- Copy keys straight from the provider's page into Render. Never paste them into GitHub, a chat, or a screenshot.

## Free or paid plan?

| | Free (default in render.yaml) | Starter (about $7/month) |
|---|---|---|
| Cost | $0 | about $7/month, or use a `HTHON-` credit code (Account → Billing → Redeem code) |
| Sleeps? | Yes, after 15 min with no visitors. The next visit waits about 1 minute while it wakes up. | Never sleeps |
| Photos and shared guide links kept | Until it falls asleep or redeploys (temporary disk; deleted after 24 h anyway) | Until the next redeploy or restart (max 24 h) |
| Good for | Testing, sharing the link, the video | Judging days, so the first judge never waits |

Start on Free. Switching later is one click (step 14) and needs no redeploy of code.

## Deploy (first time)

1. Open **https://dashboard.render.com** and sign in. Easiest: **Sign in with GitHub** using the account that owns `ragilmalik/tukang-copilot`.
2. Top right, click **+ New** → **Blueprint**.
3. Under *Connect a repository*: if `tukang-copilot` is not in the list, click **Configure account** (or **Connect GitHub**) → GitHub opens → choose *Only select repositories* → pick **tukang-copilot** → **Install / Save**. You come back to Render.
4. Next to **ragilmalik/tukang-copilot** click **Connect**.
5. *Blueprint Name*: type `tukang-copilot`. *Branch*: `main`. Render reads `render.yaml` and shows one web service, **tukang-copilot** (Docker, Free, Singapore).
6. Render asks for the secret values from render.yaml:
   - **MODEL_API_KEY**: paste your Meta key (or leave empty for demo mode).
   - **BASETEN_API_KEY**: paste your Baseten key, or leave empty.
7. Click **Deploy Blueprint** (older screens call it **Apply**).
8. Click the **tukang-copilot** service, then **Logs**. The first build takes 5–8 minutes (it installs Python packages and ffmpeg). Wait until the top shows a green **Live** and the log says `Uvicorn running on http://0.0.0.0:10000`.
9. Your link is at the top of the service page, like `https://tukang-copilot.onrender.com` (Render may add a few letters if the name is taken). Open it on your phone over 4G: you should see the app, and no orange *Demo mode* line if you pasted a key.

## Check it (2 minutes)

10. On your computer, in the project folder:
    ```
    python scripts/deploy_check.py https://tukang-copilot.onrender.com
    ```
    You want **READY** at the end. Each line is PASS / WARN / FAIL; every FAIL has a `fix:` line in plain English. It checks https, `/api/health`, live vs demo mode, open weights, the home page, install-to-home-screen files, security headers (camera allowed), a PDF report, and all five demo repairs end to end.
    - In LIVE mode the PDF and the five repairs make real model calls, so they only run when you add `--live` (well under $1). Do that once after the first deploy.
    - A *"server took 50s to answer (it was asleep)"* WARN is normal on the free plan.

## Change settings or add a key later

11. Service page → **Environment** (left menu) → find the name (e.g. `MODEL_API_KEY`) → **Edit** → paste → **Save, rebuild, and deploy** (or **Save and deploy**). It is live again in about a minute.
    - Turn on open weights: set `USE_OPEN_WEIGHTS` to `1` and make sure `BASETEN_API_KEY` is filled.
    - Emergency switch if the live Meta API misbehaves during judging: set `MOCK` to `1`. The app keeps working on recorded demo answers at no cost. Set it back to `0` afterwards.
    - Spend caps are already set: `MAX_COST_PER_SESSION_USD` 0.50 per repair, `DAILY_BUDGET_USD` 10 per 24 h for the whole site, `RATE_LIMIT_PER_HOUR` 30 new repairs per visitor. Also set a spend limit on dev.meta.ai → Billing.

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
| Build failed in Logs | Click **Manual Deploy → Deploy latest commit** once (network hiccups happen). Still red: roll back (step 13) and tell Malik the last 20 log lines. |
| App says *Demo mode* | `MODEL_API_KEY` is empty or `MOCK` is `1`: step 11. |
| *Too many repairs / daily budget* message | The public spend guard worked. Raise `RATE_LIMIT_PER_HOUR` or `DAILY_BUDGET_USD` in Environment if you want. |
| Camera does not open on the phone | Use the `https://` link, and allow camera in the browser's site settings. |
| Shared guide link says *not found* | Render's disk is temporary: photos and guides vanish on every redeploy, restart, and (free plan) every time it falls asleep. Start a new repair. Starter keeps them until the next redeploy. |
| First visit is slow | Free plan was asleep; it wakes in about a minute (or switch to Starter, step 14). |

## Run the same container on your own computer (optional)

With Docker Desktop installed: `docker compose up --build` in the project folder → http://localhost:8000. It uses your `.env` if there is one (demo mode if not). This is exactly what Render runs.
