# Tutorial: your first repair with Tukang Copilot

This walks you through Tukang Copilot from zero, the way I would show a friend. You don't need to write code. Plan on 15 minutes for the offline run and 15 more if you want the real Meta models.

**Who this is for:** anyone who wants to see the app work on their own laptop or phone, including judges and people who have never opened a terminal.
**What you get at the end:** the app running on your machine, one full motorbike repair finished (diagnosis, steps, camera check, re-plan), and, if you have a Meta key, the same repair answered by the real models.
**Why it is set up this way:** the app runs with no key at all (offline sample mode), so nobody has to pay or sign up just to look. The real models switch on with one setting.

## Part 1. Run it offline (free, no account)

1. **Install Python 3.11 or newer.** Windows: get it from python.org and tick "Add python.exe to PATH" during install. Mac: `brew install python@3.12`, or the python.org installer.
2. **Get the code.** On https://github.com/ragilmalik/tukang-copilot press **Code**, then **Download ZIP**, and unzip it. Or, if you have git: `git clone https://github.com/ragilmalik/tukang-copilot.git`.
3. **Start it.** Open the folder. Windows: double-click `start.bat`. Mac or Linux: open a terminal in the folder and run `./start.sh`.
   The first start takes 2 to 4 minutes because it installs the Python packages into a private `.venv` folder. Nothing is installed system-wide.
4. **Open it.** When the window says `Open http://localhost:8000`, open that address in Chrome. An orange line at the top says *Offline sample mode*. That means no key is set and every answer comes from pre-written samples, which is exactly what you want for a first look.
5. **Run the 1-tap demo.** Tap **▶ Try the 1-tap demo**. The app takes the motorbike sample photo, asks you one question (answer *No*), then shows:
   - the photo with numbered parts (the coloured shapes are the part masks),
   - the likely causes with a percentage,
   - the safety level (green, orange or red),
   - tools and parts with estimated prices,
   - the step-by-step guide.
6. **Check a step with the camera.** Under a step, tap the sample photo buttons. The dark photo fails on purpose and tells you what to retake. The plug-cap photo is checked against the step it actually shows.
7. **Pretend it is still broken.** At the bottom, type "tried it, still won't start" and tap *Still broken, try another plan*. The plan moves to the next likely cause.
8. **Open the trace.** Tap **🤖 What the AI did** to see each decision: which model ran, what it saw, how sure it was.
9. **Stop the app** with Ctrl+C in the window.

## Part 2. Switch on the real Meta models

You need a Meta Model API key from https://dev.meta.ai. A repair costs about 4 US cents (median from my live run on 5 Nov 2026).

1. On dev.meta.ai, claim the hackathon credits, add a card under **Billing** and set a spend limit. I use $20.
2. **API keys**, then **Create key**, then copy it. Never paste a key into a chat or an issue.
3. In the project folder run `python scripts/set_keys.py` (Windows: `.venv\Scripts\python scripts\set_keys.py`). Paste the key when it asks. Nothing shows while you paste. Press Enter.
4. It writes the key into `.env` (git ignores that file) and checks every model the app uses. It should end with **ALL GOOD** for well under 5 cents.
5. Start the app again. The orange line is gone and the header says live. Now take a real photo of something broken and describe it.

## Part 3. Try it on your phone

- Same Wi-Fi: open `http://<your-laptop-ip>:8000` on the phone. Phones only allow the camera on https, so over plain Wi-Fi you get the samples and gallery upload only.
- Full camera: run `cloudflared tunnel --url http://localhost:8000` and open the `https://…trycloudflare.com` link it prints, or deploy it ([DEPLOY.md](DEPLOY.md)).

## If something goes wrong

[TROUBLESHOOTING.md](TROUBLESHOOTING.md) lists the errors I have hit and what fixes them. The most common one: the port is busy. Start with `PORT=8765 ./start.sh` (Mac/Linux) or set `PORT=8765` in `.env`.

## Where to go next

- [HOW_TO_USE.md](HOW_TO_USE.md): every screen of the app, for owners.
- [HOW_IT_WORKS.md](HOW_IT_WORKS.md): what happens behind each screen, in plain words.
- [SETUP.md](SETUP.md): all settings, checks and deploy commands.
