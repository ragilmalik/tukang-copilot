# Troubleshooting

| What you see | Why | Fix |
|---|---|---|
| `'python' is not recognized` (Windows) | Python not on PATH | Reinstall Python and tick **Add python.exe to PATH** |
| start.bat window closes at once | An install error | Open `cmd` in the folder, run `start.bat` there to read the message |
| Orange "Demo mode" line though you added a key | `.env` missing, key empty, or `MOCK=1` | Run `python scripts/set_keys.py` again; check `/health` says `"mode":"live"` |
| check_keys: **FAIL 401** | Wrong or revoked key | Create a new key on dev.meta.ai → API keys, run set_keys.py |
| check_keys: **FAIL 402 / billing** | No card or credits used up | dev.meta.ai → Billing: add card, check credits, raise spend limit |
| check_keys: **FAIL 403 / model not enabled** | Model not on your team | dev.meta.ai → Models; note which one, tell Malik |
| **429** errors | Rate limit | The app retries with backoff; wait a minute |
| "Job budget … reached" | `MAX_COST_PER_SESSION_USD` hit | Raise it in `.env` (e.g. 1.00) or lower `MAX_DIAGRAMS` |
| Mic button does nothing on phone | Phones only allow mic/camera on **https** | Use the Render link or a Cloudflare tunnel |
| "Microphone unavailable" | Permission denied | Chrome → ⋮ → Settings → Site settings → Microphone → allow |
| Parts show "(?)" | SAM didn't find that part in the photo | Take a closer, brighter photo of that area |
| Step check always ⚠️ | Photo dark/blurry or wrong area | Use the torch, get closer, hold still |
| No voice | No internet for edge-tts | The phone's own voice is used; or set `NARRATION_VOICE=0` |
| Render shows "Deploy failed" | Build error | Render → Logs; most often a missing env var |
| Render app slow on first open | Free/starter instance waking up | Open it 1 minute before the demo |
| Tests: local calls return 404 | A proxy intercepts localhost | `export NO_PROXY=127.0.0.1,localhost` |
| `ffmpeg not found` | Missing binary | `pip install imageio-ffmpeg` (in requirements) |
