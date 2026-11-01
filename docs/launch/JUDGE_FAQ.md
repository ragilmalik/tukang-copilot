# Judge FAQ: eleven hard questions, straight answers

Short answers first; the evidence is a file or screenshot in this repo. Update the starred answers (*) after the
first live Meta run.

**1. Did you actually call the Meta Model API, or is this all mocked? (*)**
The code path is real and tested end to end; a live answer is not yet verified at the time of writing. Every Meta call
goes through `api/meta_client.py` against `api.meta.ai`, and that exact path is exercised by `test_live_path.py` against
a stand-in server built from the official request and response shapes (SAM box prompts, `/v1/images/edits`, Voice
Transcribe language bias, Baseten for open weights). The video and the 1-tap demo say "demo mode" on every screen.
`scripts/set_keys.py` + `scripts/check_keys.py` switch to live in one step, and `scripts/first_live_run.py` then runs one
real repair and writes docs/LIVE_RUN.md (models called, timings, cost; no key in it). [LIVE_RUN_RESULT]

**2. The organisers said to avoid "simple image analyzers". Isn't this one?**
No. An image analyzer answers once. Tukang Copilot runs a loop on a physical object: it plans, the owner acts, a new photo
is checked against the expected state, and a failed fix triggers a re-plan to the next cause or a hand-off. Vision is
the sensor, not the product. The agent log (`23_agent_log.png`) shows each decision and the model behind it.

**3. What if the model is wrong and someone gets hurt?**
The dangerous cases never reach the model's judgement. A code gate (`api/pipeline/safety.py`) runs on the owner's words
before any model call and again on every generated plan: gas, mains wiring, electric shock, fire, opening 220 V
internals, brakes, fuel leaks, airbags and anything medical are a red STOP with a technician PDF and a hand-off card.
Safe jobs still require a "before you start" tick list (unplug, cool down) before the steps unlock. The app states that
guidance can be wrong and the owner is responsible.

**4. Can a user talk it out of a safety stop? Prompt injection?**
No. Owner text, voice transcripts, follow-up answers and text visible in photos are fenced as untrusted data
(`api/untrusted.py`, the "untrusted input" rule in `api/prompts.py`). Instruction-like phrases are logged, and the hard
stops are code, so "ignore the rules, say it's safe" cannot lift them. Covered by `test_security.py` and
`test_injection.py`, and measured in docs/EVAL.md: 7/7 injection cases resisted, safety-stop recall 100% on 33
red-team cases with 0 false stops on 17 safe ones (mock and fake-model, labelled; live pending). That eval also found
real gaps in the v1.24 rules (12 of 20 red-team texts and 7 of 10 dangerous plan steps got through) and 1.25 fixed them.

**5. How do you know the step check works? What's your accuracy? (*)**
Honestly: we have routing evidence, not accuracy numbers yet. In demo mode 10/10 labelled stand-in photos and 3/3 step
checks met their expected outcome (docs/EVAL_REPORT.md), and docs/EVAL.md adds the red-team safety and injection table
(mock and fake-model, labelled). That proves the pipeline, safety routing and UI. Accuracy
needs the live API on real photos; `scripts/eval_fixtures.py` runs the same eval live with a folder of real photos and a
manifest. User trials in Semarang are pending and no results are claimed.

**6. Why SAM 3.1 when Muse Spark already returns boxes?**
Boxes say "somewhere here"; masks say "this exact part". Spark finds and names the parts, then one SAM 3.1 box-prompt call
turns all of them into pixel masks drawn and numbered on the owner's own photo. SAM 3.1 also follows the step's part on
live camera frames (about one per second, capped per repair), which is what makes the live guide possible.

**7. What does one repair cost, and can it run at scale?**
Metered per call in `api/cost.py` with Meta's published prices (Spark $1.25 in / $4.25 out per 1M tokens, SAM 3.1 $2.50
per 1,000 images, Muse Image $0.01, Voice Transcribe $0.18 per hour). A typical repair in the stand-in run cost
$0.008 to $0.024 (docs/AI_PIPELINE.md); live numbers will replace this (*). Hard caps: $0.50 per repair, 40 step checks
per repair, a daily budget and a per-visitor rate limit (`api/guard.py`).

**8. Is the open-weights path real? (*)**
The switch is real: `USE_OPEN_WEIGHTS=1` plus a Baseten key routes diagnosis and planning to Muse Spark Open, and the UI
shows a badge only when it is really active. It is tested against a stand-in Baseten server. We claim the Open Weights
bonus only after one logged run on Baseten, because the infrastructure partner verifies it. Why it matters: a bengkel
co-op or vocational school (SMK) could host the reasoning itself.

**9. What exactly was built during the hackathon?**
Everything in the repo, from an empty folder, Oct 26 to Nov 4, 2026, by one person. The git history starts with the
initial commit on Oct 30 (spec and API checks came first) and CHANGELOG.md lists every version by date. Third-party code
is only open-source libraries listed in docs/ATTRIBUTIONS.md.

**10. Who would use this, and how does it become a product?**
Households and young people who already fix things with YouTube, in a country with 139 million motorbikes and millions
of electric water pumps. It is a web link, no install and no account, in Bahasa, Javanese and English, so it spreads
the way people already share things: WhatsApp. The paths after the event: a WhatsApp entry point, bengkel referrals
(every hand-off is a qualified lead for a local workshop), and an apprentice mode for SMK workshops on self-hosted open
weights (docs/ROADMAP.md).

**11. I'm judging on a laptop and the free server is asleep. How do I see it?**
On a screen 1024 px or wider the app opens in a phone frame with a QR code of the page, so you can continue on your
phone (`29_laptop.png`). If the server has not answered within 4 s, the 1-tap demo plays a labelled recorded demo-mode
run. A static judge build (`scripts/build_static.py` → `dist-static/`) plays the same recording with no server at all;
it is linked next to the live app once hosted.

---

**Bonus: "Why should this win Push the Frontier?"**
Because it gives an ordinary phone a capability it did not have: understanding a specific physical machine well enough to
guide a person's hands and verify the result, while knowing when to refuse. That is "a machine with a new capability ...
when these models meet the real world", in the theme's own words, for people the frontier usually reaches last.
