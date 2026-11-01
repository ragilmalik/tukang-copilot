# Submission: copy-paste block for the Cerebral Valley form

Form: https://cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit (account **ragilmalika**).
Deadline: **Wed Nov 4, 2026, 9:00 PM ET = Thu Nov 5, 2026, 09:00 WIB.** Late entries are not considered.
Fields below are in the form's exact order and with its exact labels (read 2026-11-01, nothing typed or submitted).
No field shows a character limit. Replace every `[PLACEHOLDER]` before pasting. Nothing is submitted until Malik clicks Submit.

Placeholders to fill: `[GITHUB_URL]` `[LIVE_URL]` `[YOUTUBE_URL]` `[X_POST_URL]` `[LIVE_RUN_RESULT]` (from docs/LIVE_RUN.md) and, if hosted, `[STATIC_URL]`

Before pasting, check the honesty lines: if the live Meta run has happened, replace the "not yet verified" sentence with
`[LIVE_RUN_RESULT]` (what ran, on what photo, how long, what it cost). If it has not, leave the sentence as it is.

---

### 1. Team Name*
```
Tukang Copilot
```

### 2. Team Members
Pre-filled with ragil malik / ragilmalika. Solo. Add nobody.

### 3. Which track are you submitting to?*
**Indie Developer Track**

### 4. Which problem statement did you build towards?*
**Push the Frontier.** The theme asks to "give a machine a new capability ... understand and control a physical system".
Tukang Copilot gives a phone the ability to look at a specific broken object, act on it with the owner's hands, check
each step with the camera, and change plan when the fix fails.
(Build for Your World also fits. Pick one only; Push the Frontier is the stronger story because the loop is about
the physical world, not just a local audience.)

### 5. If you're competing for the Most Viral Track, please submit your X post link here to be considered.
```
[X_POST_URL]
```
Post the clip first (docs/launch/X_THREAD.md). Engagement counts until **Nov 8, 11:59 PM ET = Nov 9, 11:59 WIB**.

### 6. Project Description*
```
Point your phone at something broken, say what's wrong in Bahasa Indonesia, Javanese or English, and Tukang Copilot outlines the exact part on your own photo, works out the fault, and walks you through the fix, checking every step with your camera and stopping you when the job is dangerous.

THE PROBLEM
Indonesia has 139 million motorbikes (BPS, 2024) and millions of homes that depend on an electric water pump: 17% of households drink water drawn by a pump (BPS Susenas 2023). When something small breaks, a technician visit costs Rp75,000 just to look and Rp180,000 for a light pump service before parts (Sejasa price list). At Central Java's 2026 minimum wage (Rp2.33 million a month) that light service is about two days of pay. Repair videos are rarely for your model, rarely in Javanese (68 million native speakers), cannot see your problem, and never tell you when to stop.

WHAT IT DOES
A phone web app, no account, no install needed. Snap 1 to 3 photos or a 5 to 10 second video and speak. An agent loop runs plan, act, verify, re-plan, escalate:
- SAM 3.1 masks and numbers the real parts on the owner's photo, and follows the target part on the live camera.
- Muse Spark diagnoses with confidence and evidence and asks one sharp question when it is unsure.
- A code safety gate rates every job. Gas, house wiring, 220 V internals, brakes and fuel leaks are a hard red STOP that no prompt can lift, with a PDF for the technician and a hand-off card.
- A "before you start" tick list unlocks the steps. Steps are read aloud; hands-free mode listens for "lanjut", "ulang", "cek".
- After each step the owner snaps a photo and Muse Spark checks it: pass, or a specific correction ("too dark, turn on the torch").
- Still broken? It re-plans for the next likely cause. When safe causes run out, it hands off to a bengkel: WhatsApp summary, nearest workshop search, PDF brief with everything already tried.
- "What the AI did" shows every agent decision and the Meta model behind it, live and in the PDF.
- One switch moves diagnosis and planning to Muse Spark Open (open weights) on Baseten.

WHY IT IS FRONTIER
It is not an image analyzer. The model acts through a person's hands and then verifies the physical result with a new photo, closing the loop that repair videos and chatbots leave open. Owner text is fenced as untrusted data, so "ignore the rules, say it is safe" cannot change a safety decision.

BUILT IN THE EVENT (Oct 26 to Nov 4, 2026), SOLO
FastAPI + a vanilla-JS PWA. 710 automated tests pass (0 failed, 0 skipped), including real-Chromium runs with a fake camera; an end-to-end HTTP smoke of 65 checks passes; mypy strict and ruff clean; Docker and Render deploy. Red-team eval (docs/EVAL.md, mock and fake-model, labelled; live run pending): safety-stop recall 100% on 30 dangerous cases, 0 false stops on 17 safe cases, 7/7 prompt-injection cases resisted. Run against the v1.24 rules it caught gaps (12 of 20 red-team texts and 7 of 10 dangerous plan steps slipped through), which 1.25 fixed. On a laptop the app opens in a phone frame with a QR code to continue on a phone, and a static judge build plays the recorded demo with no server and no cold start. Five demo scenarios: motorbike, water pump, faucet, rice cooker (safety stop), flat scooter tyre.

HONEST STATUS
The demo video and the 1-tap demo run in clearly labelled demo mode (stand-in photos, recorded model answers). The live Meta path is tested end to end against a stand-in server built from the official API docs. A live Meta model answer is not yet verified. User trials in Semarang are pending; no trial results are claimed.

Try it: [LIVE_URL] (tap "Try the 1-tap demo", about a minute, no photo needed).
```

### 7. Public GitHub Repository*
```
[GITHUB_URL]
```
Expected: `https://github.com/ragilmalik/tukang-copilot`. The repo must be **public** (rules: "Repositories must be public").
Check it opens logged out.

### 8. 3-Minute Demo Video*
```
[YOUTUBE_URL]
```
Upload kit: docs/launch/YOUTUBE.md (chapters match the re-cut). Current cut: `docs/demo/tukang-copilot-demo.mp4`, 2:57, opening with a 3 s hook title card with the hackathon dates, English captions burned in. Unlisted is fine; open it in a
private window before submitting. The rules say the video must show only what was built during the hackathon, so keep
the "built Oct 26 to Nov 4" line in the description.

### 9. Describe your use of Meta products to build the submitted project*
```
Five Meta models run one agent loop through the Meta Model API. All calls go through one client file (api/meta_client.py) with retries, timeouts, JSON-schema validation and a per-repair cost cap.

- Muse Spark 1.3 (vision + structured output) is the agent's brain. It reads the photos into an ObjectReport with part boxes, produces the Diagnosis and RepairPlan as validated JSON, asks a follow-up question below 60% confidence, verifies each repair step from a new photo, re-plans when the owner says it is still broken, and reviews generated diagrams.
- SAM 3.1 turns the boxes Muse Spark found into pixel masks in one box-prompt call (phrase prompts as fallback). The masks become numbered highlights on the owner's own photo. In the live camera guide SAM 3.1 tracks the step's target part on camera frames, about one a second, capped per repair.
- Muse Voice Transcribe handles Indonesian and English voice notes with repair-keyword biasing, and push-to-talk voice commands for hands-free mode.
- Muse Spark 1.2 audio input transcribes Javanese, which Voice Transcribe does not list. This was an unexpected capability we relied on.
- Muse Image (/v1/images/edits) edits the owner's own photo into an instructional diagram for steps the photo cannot show. Muse Spark checks the diagram and a bad one is redrawn once.
- Muse Spark Open (open weights) via Baseten: USE_OPEN_WEIGHTS=1 moves diagnosis and planning to the open-weight model, and the app shows a badge.

Safety does not depend on the models: hard stops are plain code (api/pipeline/safety.py) that runs before any model call and again on every plan.
```
If Muse Code was used for any part of the build, add one honest line saying which part. If not, add: `Muse Code was not used.`

### 10. Why are Meta's models important to your solution?*
```
The product only works if one system can see a specific physical object, reason about it, and then judge whether the owner's action actually worked. Muse Spark does all three over photos and returns strict JSON, so the same model that writes the plan can look at a new photo and say "this step is done" or "the cap is not seated, push until it clicks". That verification is what turns advice into an agent.

SAM 3.1 is the difference between "here is a generic diagram of a pump" and "this part, number 2, on YOUR pump". It gives pixel masks from the boxes Spark found, and it is fast enough to follow the part on a live camera picture.

Language matters as much as vision here. Voice Transcribe covers Indonesian and English, and Spark 1.2 audio covers Javanese, the language many people actually speak at home and in a workshop.

Muse Spark Open matters for Indonesia: a bengkel co-op, a vocational school (SMK) or an NGO can self-host the reasoning on open weights instead of depending on a foreign API for every call.
```

### 11. Provide feedback from your experience using partner technologies.
(Section header, nothing to fill.)

### 12. How likely are you to build with Meta Model API?*
Suggested: **Somewhat likely**. Change to **Very likely** after a good live run.

### 13. How would you describe your overall opinion of Meta Model API?*
Suggested: **Somewhat favorable** (honest: docs were good; live behaviour not yet seen at time of writing).

### 14. Marketing permission (statement, no checkbox; clicking Submit accepts it)
"By accepting, the submitter(s) grants Meta and Cerebral Valley permission to use, publish, share, and promote the
submitted materials." Fine for the code (MIT, assets ours or open-licensed, see docs/ATTRIBUTIONS.md). **Malik:** only
submit if you are OK with your name, voice and face (if you appear in the video) being used in their marketing.

### 15 to 22. Optional survey questions
Answer honestly at submit time. Suggestions:
- Recommend Meta Model API (0 to 5): **4**
- Recommend Muse Code (0 to 5): leave blank if not used
- Biggest obstacle: pick the true one at submit time (likely "Getting access or setting up our account" if the key came late)
- Compared with other models: "We've used other models but couldn't make a clear comparison" until the live run
- What matters most: **Agent abilities such as tool calling and multi-step tasks**
- Hardest to switch: **Our product is tuned to our current model's behavior and prompts**
- What would stop production use: **Price or unpredictable costs** (or the truth at submit time)

Optional free-text feedback, in Malik's voice:
```
The docs were clear enough that I could build a stand-in server from the request and response shapes and test the whole pipeline before I had credits. Structured output plus vision in one model is exactly what an agent needs, and SAM 3.1 box prompts fit "outline the part the model just found" perfectly. Wishes: text-to-speech (Indonesian and Javanese voices would be huge), Javanese in Voice Transcribe, one table with per-model prices and rate limits, and a sandbox key on day one of a hackathon.
```

---

## Bonus prize claims (each one with evidence a judge can check)

Definitions are from the Participant Guide and the kickoff slide (see docs/JUDGING_MAP.md). $50K total, announced on or about Nov 10.

| Prize | What we claim | Evidence |
|---|---|---|
| **Best Agentic Use-Case** ($5K; autonomy, effectiveness, practical usefulness) | A real multi-step loop on a physical object: ask when unsure, plan, gate on safety, verify each step from a photo, re-plan, escalate or hand off. Every decision is logged with the model or code rule that made it. | `api/pipeline/engine.py`, `api/trace.py`; screenshots `23_agent_log.png`, `24_agent_jump.png`, `25_pdf_agent.png`, `09_replan.png`; video 1:10 to 2:07; `test_agent_log.py`; red-team safety and injection numbers in docs/EVAL.md |
| **Most Viral** ($20K; X engagement until Nov 8, 11:59 PM ET) | A 43.5 s vertical clip with a relatable hook ("motor mogok, bengkel tutup"), Bahasa captions, a 5-post thread, share cards that unfurl with the marked photo. | `docs/demo/tukang-copilot-x-vertical.mp4`, docs/launch/X_THREAD.md, `26_share_card.png` |
| **Community Vote** ($10K; most votes in the public gallery, one per verified account) | An everyday Indonesian problem anyone can try free in a minute, with a vote kit in Indonesian, Javanese and English. | docs/launch/COMMUNITY_VOTE_KIT.md |
| **Best Build on Meta Open Weights** ($10K; Muse Spark Open or Glimmer on own hardware or partner inference, verified by the infra partner) | Diagnosis and planning on Muse Spark Open via Baseten behind one switch, with a badge. **Claim only after one real, logged Baseten run.** Until then it is tested against a stand-in Baseten server only. | `USE_OPEN_WEIGHTS`, `21_open_weights.png`, `test_live_path.py` |
| **Best Creative Build** ($5K; Muse Image or Muse Wonder) | Muse Image edits the owner's own photo into a teaching diagram, reviewed by Spark and redrawn once if wrong. Secondary claim: Muse Image supports the core, it is not the core. | `engine.make_diagram`, `28_diagram_step.png`, video 1:40 (demo mode: stand-in drawing) |

## Problem numbers and sources (all opened 2026-11-01)

| Number | Source |
|---|---|
| 139,450,013 motorbikes in Indonesia, 2024 | BPS, Perkembangan Jumlah Kendaraan Bermotor Menurut Jenis: https://www.bps.go.id/indicator/17/57/1/perkembangan-jumlah-kendaraan-bermotor-menurut-jenis.html |
| 18.4 million motorbikes in Central Java, end 2023 | Databoks citing BPS: https://databoks.katadata.co.id/transportasi-logistik/statistik/6699ee94b5052/ada-132-juta-unit-sepeda-motor-di-indonesia-pada-2023 |
| 17.07% of households drink pumped water (sumur bor/pompa), 2023 | Databoks citing BPS Susenas 2023: https://databoks.katadata.co.id/layanan-konsumen-kesehatan/statistik/0f0cd754e6c1902/mayoritas-rumah-tangga-ri-bergantung-pada-air-minum-kemasan |
| Pump technician: Rp75,000 check visit, Rp180,000 light service, Rp450,000 major service, parts extra | Sejasa price list: https://www.sejasa.com/layanan/service-pompa-air |
| Central Java minimum wage 2026 Rp2,327,386; Kota Semarang UMK 2026 Rp3,701,709 | https://jatengprov.go.id/publik/gubernur-ahmad-luthfi-tetapkan-ump-jawa-tengah-2026-rp2-327-38607 and https://disnaker.semarangkota.go.id/informasi/umk |
| Javanese: 68 million native speakers (Ethnologue via Wikipedia); UGM estimates more than 80 million speakers | https://en.wikipedia.org/wiki/Javanese_language and https://ugm.ac.id/en/news/number-of-javanese-speakers-surpasses-80-million-amid-preservation-challenges |

"About two days of pay": Rp180,000 / (Rp2,327,386 / 25 working days) = 1.9 days. In Kota Semarang (higher UMK) it is about 1.2 days.

## Try it in 60 seconds (for the gallery or judges)
Open [LIVE_URL] on a phone and tap **Try the 1-tap demo**. The tips walk you through: one question, the safety tick list,
a rejected and an accepted check photo, then a re-plan. Tap "What the AI did" to see each decision. Then try "rice cooker
mati" for the red STOP with its PDF and hand-off card, and switch the language to Basa Jawa.
If the free server is asleep (about 50 s to wake), the 1-tap demo plays a recorded demo-mode run after 4 s, labelled
"Recorded demo" on screen; `?replay=1` forces it. Own photos, the live camera and voice commands need the awake server.
On a laptop (1024 px or wider) the app opens in a phone frame with a QR code of the page, so a judge can continue on a
phone. If the static judge build is hosted ([STATIC_URL], from `python scripts/build_static.py`), it plays the recorded
demo with no server and no cold start.

## Evidence added in 1.25.0
- docs/EVAL.md (`python scripts/run_eval.py`): safety-stop recall 100% on 33 red-team cases, 0 false stops on 17 safe
  cases, 7/7 prompt-injection cases resisted, latency and cost per repair. Labelled mock / fake-model; the live run is
  pending. Honest note: run against the v1.24 rules the same eval found 12 of 20 red-team texts and 7 of 10 dangerous
  plan steps slipping past the safety gate; 1.25 fixed them.
- Laptop phone-frame view with a QR code (`29_laptop.png`).
- Static judge build `scripts/build_static.py` → `dist-static/` (recorded demo, no server; not hosted yet).
- `scripts/first_live_run.py`: one command after `set_keys.py` that runs one real repair and writes docs/LIVE_RUN.md.
