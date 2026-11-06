# Troubleshooting

| What you see | Why | Fix |
|---|---|---|
| `'python' is not recognized` (Windows) | Python is not on PATH | Reinstall Python and tick "Add python.exe to PATH" |
| start.bat window closes at once | An install error | Open `cmd` in the folder and run `start.bat` there so you can read the message |
| Orange "Offline sample mode" line though you added a key | `.env` missing, key empty, or `OFFLINE=1` | Run `python scripts/set_keys.py` again; `/health` should say `"mode":"live"` |
| check_keys: FAIL 401 | Wrong or revoked key | Create a new key on dev.meta.ai (API keys) and run set_keys.py |
| check_keys: FAIL 402 / billing | No card, or the credits are used up | dev.meta.ai, Billing: add a card, check the credits, raise the spend limit |
| check_keys: FAIL 403 / model not enabled | That model is not enabled for your team | dev.meta.ai, Models: note which model failed and get it enabled for the team |
| 429 errors | Rate limit | The app retries with backoff. Wait a minute |
| "Terlalu banyak permintaan" / "Too many requests" (429) or "daily usage limit" (503) | A live site hit `RATE_LIMIT_PER_HOUR` or `DAILY_BUDGET_USD` | Wait, or raise the value in the Render env vars (set `DAILY_BUDGET_USD` to what you can afford) |
| "Job budget … reached" | `MAX_COST_PER_SESSION_USD` hit | Raise it in `.env` (e.g. 1.00) or lower `MAX_DIAGRAMS` |
| Mic button does nothing on the phone | Phones only allow mic and camera on https | Use the Render link or a Cloudflare tunnel |
| "Microphone unavailable" | Permission denied | Chrome ⋮ > Settings > Site settings > Microphone > allow |
| Parts show "(?)" | SAM didn't find that part in the photo | Take a closer, brighter photo of that area |
| Step check always ⚠️ | Photo dark or blurry, or the wrong area | Turn on the torch, get closer, hold still |
| No voice | No internet for edge-tts | The phone's own voice takes over; or set `NARRATION_VOICE=0` |
| Render shows "Deploy failed" | Build error | Check Render > Logs. Most often it's a missing env var |
| Render app slow on first open | The free/starter instance is waking up | Open it a minute before the demo |
| Tests: local calls return 404 | A proxy intercepts localhost | `export NO_PROXY=127.0.0.1,localhost` |
| `ffmpeg not found` | Missing binary | `pip install imageio-ffmpeg` (it's in requirements) |
