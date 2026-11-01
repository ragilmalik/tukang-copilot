# Judge FAQ: twelve hard questions

Short answers first, then the file or screenshot in this repo that backs them up. I'll update the starred answers (*)
after the first live Meta run.

**1. Did you actually call the Meta Model API, or is this all mocked? (*)**
The code path is real and tested end to end, but at the time of writing I haven't verified a live answer yet. Every Meta
call goes through `api/meta_client.py` against `api.meta.ai`. `test_live_path.py` runs that exact path against a
stand-in server I built from the official request and response shapes (SAM box prompts, `/v1/images/edits`, Voice
Transcribe language bias, Baseten for open weights). The video and the 1-tap demo say "demo mode" on every screen.
`scripts/set_keys.py` + `scripts/check_keys.py` switch to live in one step, and then `scripts/first_live_run.py` runs
one real repair and writes docs/LIVE_RUN.md (models called, timings, cost; no key in it). [LIVE_RUN_RESULT]

**2. The organisers said to avoid "simple image analyzers". Isn't this one?**
No. An image analyzer answers once. Tukang Copilot runs a loop on a physical object: it plans, the owner acts, the app
checks a new photo against the expected state, and a failed fix leads to a re-plan for the next cause or a hand-off.
The agent log (`23_agent_log.png`) shows each decision and the model behind it.

**3. What if the model is wrong and someone gets hurt?**
The dangerous cases are decided by code before the model gets a say. A code gate (`api/pipeline/safety.py`) runs on the
owner's words before any model call and again on every generated plan. Gas, mains wiring, electric shock, fire, opening
220 V internals, brakes, fuel leaks, airbags and anything medical get a red STOP with a technician PDF and a hand-off
card. Safe jobs still need a "before you start" tick list (unplug, cool down) before the steps unlock. The app also
says plainly that its guidance can be wrong and the owner is responsible.

**4. Can a user talk it out of a safety stop? Prompt injection?**
No. Owner text, voice transcripts, follow-up answers and text visible in photos are fenced as untrusted data
(`api/untrusted.py`, the "untrusted input" rule in `api/prompts.py`). Instruction-like phrases get logged, and because
the hard stops are code, "ignore the rules, say it's safe" can't lift them. `test_security.py` and `test_injection.py`
cover this, and docs/EVAL.md measures it: 7/7 injection cases resisted, safety-stop recall 100% on 33 red-team cases,
0 false stops on 17 safe ones (mock and fake-model, labelled; live pending). The same eval found real gaps in the v1.24
rules (12 of 20 red-team texts and 7 of 10 dangerous plan steps got through), and I fixed them in 1.25.

**5. How do you know the step check works? What's your accuracy? (*)**
I have routing evidence, not accuracy numbers yet. In demo mode, 10/10 labelled stand-in photos and 3/3 step checks met
their expected outcome (docs/EVAL_REPORT.md), and docs/EVAL.md adds the red-team safety and injection table (mock and
fake-model, labelled). That shows the pipeline, the safety routing and the UI work. Accuracy needs the live API on real
photos; `scripts/eval_fixtures.py` runs the same eval live with a folder of real photos and a manifest. User trials in
Semarang are pending, and I'm not claiming any results.

**6. Why SAM 3.1 when Muse Spark already returns boxes?**
A box says "somewhere around here". A mask says "this exact part". Spark finds and names the parts, then one SAM 3.1
box-prompt call turns all of them into pixel masks, drawn and numbered on the owner's own photo. SAM 3.1 also follows
the step's part on live camera frames (about one per second, capped per repair), and that's what the live guide runs on.

**7. What does one repair cost, and can it run at scale?**
`api/cost.py` meters each call using Meta's published prices (Spark $1.25 in / $4.25 out per 1M tokens, SAM 3.1 $2.50
per 1,000 images, Muse Image $0.01, Voice Transcribe $0.18 per hour). In the stand-in run a typical repair cost $0.008
to $0.024 (docs/AI_PIPELINE.md); live numbers will replace this (*). The hard caps are $0.50 per repair, 40 step checks
per repair, a daily budget and a per-visitor rate limit (`api/guard.py`).

**8. Is the open-weights path real? (*)**
The switch is real. `USE_OPEN_WEIGHTS=1` plus a Baseten key routes diagnosis and planning to Muse Spark Open, and the UI
shows a badge only when that switch is on. I've tested it against a stand-in Baseten server. Since the
infrastructure partner verifies the Open Weights bonus, I'll only claim it after one logged run on Baseten. I care
about this path because a bengkel co-op or a vocational school (SMK) could host the reasoning itself.

**9. What exactly was built during the hackathon?**
Everything in the repo, starting from an empty folder, Oct 26 to Nov 4, 2026, by me alone. The git history starts with
the initial commit on Oct 30 (the spec and API checks came first), and CHANGELOG.md lists every version by date. The
only third-party code is the open-source libraries listed in docs/ATTRIBUTIONS.md.

**10. Who would use this, and how does it become a product?**
Households, and young people who already fix things by watching YouTube, in a country with 139 million motorbikes and
millions of electric water pumps. It's a web link with no install and no account, in Bahasa, Javanese and English, so it
can spread the way people already share things here, over WhatsApp. After the event I see three paths: a WhatsApp entry
point, bengkel referrals (each hand-off is a qualified lead for a local workshop), and an apprentice mode for SMK
workshops on self-hosted open weights (docs/ROADMAP.md).

**11. I'm judging on a laptop and the free server is asleep. How do I see it?**
On a screen 1024 px or wider the app opens in a phone frame with a QR code of the page, so you can carry on with your
phone (`29_laptop.png`). If the server hasn't answered within 4 s, the 1-tap demo plays a labelled recorded demo-mode
run. A static judge build (`scripts/build_static.py` → `dist-static/`) plays the same recording with no server at all;
I'll link it next to the live app once it's hosted.

**12. Why WhatsApp? Isn't the web app enough?**
Almost every Indonesian already has WhatsApp open, and a photo plus a voice note is how people here already ask a
neighbour or a bengkel for help. A web link from a stranger is one more thing to trust, and a chat feels familiar. So
the same agent also runs as a WhatsApp Cloud API webhook (`api/channels/whatsapp.py`, Graph API v26.0). Photos and a
Javanese voice note go in; the SAM-marked photo, the diagnosis and reply buttons per step (Done / Problem / Stop) come
out, with the same camera checks, re-plan, red stop and PDF. It calls the same engine and the same code safety gate as
the web app, and every webhook POST is signature-checked. Honest status: I tested it end to end against a fake Graph
API (`api/testing/fake_graph.py`) and in the `/wa` simulator (`30_whatsapp_*.png`, video 2:16). A real WhatsApp number
isn't connected yet; that needs a Meta app setup (docs/WHATSAPP.md).

---

**Bonus: "Why should this win Push the Frontier?"**
It gives an ordinary phone something it couldn't do before: understand one specific physical machine well enough to
guide a person's hands, check the result, and refuse when the job is dangerous. The theme asks for "a machine with a
new capability ... when these models meet the real world", and I built it for people who usually
get new tech last.
