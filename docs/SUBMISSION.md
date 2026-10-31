# Submission: copy-paste block for Cerebral Valley

Form: https://cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit (account **ragilmalika**).
Deadline: **Wed Nov 4, 2026, 9:00 PM ET = Thu Nov 5, 2026, 09:00 WIB.** Fields are in the form's order. Replace each `[…]` before pasting. Nothing here is submitted until Malik clicks Submit.

---

### 1. Team Name *
```
Tukang Copilot
```

### 2. Team Members
Auto-filled (ragil malik / ragilmalika). Solo, nothing to add.

### 3. Which track are you submitting to? *
**Indie Developer Track**

### 4. Which problem statement did you build towards? *
**Push the Frontier**. Why: it gives a phone a new physical-world ability. It sees the real part (SAM 3.1 masks on the photo and the live camera), plans a repair, checks each step from a new photo, and re-plans: an agent that acts on physical objects.
*Alternative:* **Build for Your World** also fits (Indonesian motorbikes, pumps and rice cookers, in Bahasa and Javanese). Pick that one if the frontier framing feels like a stretch. The write-up works for both.

### 5. X post link (Most Viral, optional)
```
[paste the X post URL after posting: draft below]
```

### 6. Project Description *
```
Tukang Copilot: point your phone at something broken, say what's wrong in Bahasa Indonesia, Javanese or English, and it finds the exact part, works out the fault, and walks you through the fix, checking every step with your camera.

Problem: Indonesia runs on ~130 million motorbikes plus water pumps, rice cookers and plumbing. A small fault costs a day's wage at a bengkel (repair shop) or days without water. Repair videos aren't for your model, aren't in your language, can't see your problem, and never say when a job is dangerous.

How it works: an installable phone web app (no account). Snap photos or a 5–10 s video and speak. An agent loop runs plan → act → verify → re-plan → escalate:
• Outlines the real parts on your own photo (SAM 3.1), diagnoses causes with confidence and evidence, asks one question when unsure.
• Rates safety. Gas, house wiring, 220 V internals, brakes and fuel leaks are a hard STOP enforced in code, with a PDF and a hand-off card.
• A safety tick list unlocks the steps. Steps are read aloud. Hands-free mode listens for "lanjut / ulang / cek". The live camera guide outlines the part to touch on the camera picture.
• After each step you snap a photo and the model checks it (✓ or a specific correction). If it's still broken, it re-plans for the next cause.
• Bengkel hand-off: a WhatsApp summary, the nearest workshop, and a PDF brief for the mechanic. It also shows the bengkel price against the DIY cost, a PDF repair report, and "My garage" on the phone.
• Diagnosis and planning can run on Muse Spark Open (open weights) via Baseten with one switch.

Built from scratch during the hackathon (Oct 26 – Nov 4, 2026): FastAPI + vanilla-JS PWA, 470 automated tests (incl. real-Chromium tests with a fake camera), strict typing, Docker/Render deploy. Honest status: the demo video runs in labelled demo mode (stand-in photos, recorded answers). The live Meta path is tested against a stand-in server built from the official API docs [update after the first live-key run].
```

### 7. Public GitHub Repository *
```
https://github.com/ragilmalik/tukang-copilot
```

### 8. 3-Minute Demo Video *
```
[https://youtube.com/watch?v=… : upload docs/demo/tukang-copilot-demo.mp4 (2:57) or the real-phone recording; Unlisted is fine, check it opens logged-out]
```

### 9. Describe your use of Meta products to build the submitted project *
```
Five Meta models in one agent loop, all through the Meta Model API (one client file with retries, timeouts, JSON-schema validation and a per-repair cost cap):
• Muse Spark 1.3 (vision + structured output): reads the photos into an ObjectReport, then produces the Diagnosis and RepairPlan as validated JSON, verifies each repair step from a new photo, re-plans when the fix fails, and reviews generated diagrams. Muse Spark 1.2 audio transcribes Javanese, which Voice Transcribe doesn't cover.
• SAM 3.1: one box-prompt call segments every part the vision step located (phrase fallback). The masks become numbered highlights on the user's own photo, and SAM 3.1 also tracks the target part on live camera frames for the live guide (rate-limited, capped at 120 frames per repair).
• Muse Voice Transcribe: Indonesian/English voice notes with repair-keyword biasing, plus push-to-talk voice commands for hands-free mode on phones without continuous speech recognition.
• Muse Image (/images/edits): edits the user's own photo into a clean instructional diagram for steps the photo can't show. Muse Spark checks the diagram and has a bad one redrawn once.
• Muse Spark Open (open weights) on Baseten: USE_OPEN_WEIGHTS=1 moves diagnosis and planning to the open-weight model. The app shows a badge.
Muse Code was not used.
```
*(Delete the last line if you did use Muse Code.)*

### 10. Why are Meta's models important to your solution? *
```
The product only works if one system can see a specific physical object, reason about it, and check the result. Muse Spark reasons over photos and returns strict JSON, so the same model can diagnose, plan, and then judge "is this step actually done?" from a new photo. That is what closes the agent loop. SAM 3.1 gives pixel-accurate masks of the user's real part. That is the difference between "here is a generic diagram of a carburettor" and "this orange thing on YOUR photo, number 2". It is also fast enough to follow a live camera. Muse Image edits the user's own photo instead of drawing a stock picture. Muse Spark Open matters for Indonesia: a bengkel co-op, a vocational school or an NGO can self-host the reasoning on open weights, without per-call dependence on a foreign API. And Voice Transcribe + Spark audio cover Indonesian and Javanese, the languages people actually use in a workshop.
```

### 11–13. Feedback on partner technologies
**How likely are you to build with Meta Model API? *** → suggested: **Somewhat likely** *(change to Very likely after a good first live run)*
**Overall opinion of Meta Model API? *** → suggested: **Somewhat favorable** *(honest: the docs were good, live behaviour not yet seen)*

Draft feedback in Malik's voice (for the optional comment fields, or Discord/office hours):
```
The docs were clear enough that I could build a stand-in server from the request/response shapes alone and test my whole pipeline before I had credits. That was a big help. Structured output with JSON schemas plus vision in one model is exactly what an agent needs. SAM 3.1's box prompts are a great fit for "outline the part the model just found". Wishes: text-to-speech (I had to use another voice for reading steps aloud, and Indonesian/Javanese TTS would be huge here), Javanese in Voice Transcribe, clearer per-model pricing and rate limits in one table, and a cheap sandbox key for hackathons so live testing can start on day one.
```

### 14. Marketing / IP permission
Accepting lets Meta and Cerebral Valley use, publish and promote the submission. Fine for us: the repo is MIT-licensed, every asset is ours or open-licensed (docs/ATTRIBUTIONS.md), and the stand-in photos are synthetic. **Malik:** only accept if you're OK with your name and face (if you're in the real video) being used in their marketing.

### 15–22. Optional survey questions
Answer honestly at submit time. Suggested: recommend Meta Model API **4/5**; biggest obstacle: **"Something else: getting API credits/keys in time to test live"**; comparison: leave Neutral until the live run.

---

## Draft X post (Most Viral; attach docs/demo/tukang-copilot-x-vertical.mp4, ~250 chars)
```
Motor mogok, bengkel tutup. So I built Tukang Copilot: snap it, say what's wrong in Bahasa or Javanese, and it outlines the exact part on your camera, checks every step, and says STOP when it's dangerous. 🔧🇮🇩 Built with @AIatMeta Muse Spark + SAM 3.1
```
Reply to your own post with the repo link and the live link (keeps the main post under 280). Check that the @AIatMeta and @cerebral_valley handles are right before posting. Longer drafts (Bahasa, technical thread) are below.

**Bahasa version:** Motor mogok, bengkel tutup. Saya bikin Tukang Copilot: foto, ceritakan masalahnya (Bahasa/Jawa), AI-nya menandai bagian yang rusak di kamera kamu, mengecek tiap langkah, dan bilang STOP kalau bahaya. 🔧 Dibuat dengan Muse Spark + SAM 3.1 dari @AIatMeta

**Thread starter:** How Tukang Copilot works in 5 Meta models: 1/ Voice Transcribe hears the problem 2/ Muse Spark sees the object 3/ SAM 3.1 outlines the part on your photo and live camera 4/ Spark plans, Muse Image draws hidden steps 5/ Spark checks each step from a photo and re-plans, or hands off to a bengkel

---

## Bonus prizes we target (one line of evidence each)
| Prize | Evidence |
|---|---|
| **Most Viral** ($20K) | 45 s vertical clip with Bahasa captions (docs/demo/tukang-copilot-x-vertical.mp4). A relatable hook ("motor mogok, bengkel tutup") and a draft post ready. Every shared repair link unfurls as a preview card (Open Graph), so each share advertises the app. |
| **Best Build on Open Weight Models** ($10K) | `USE_OPEN_WEIGHTS=1` runs diagnosis + plan on Muse Spark Open via Baseten. Tested end to end against a stand-in Baseten server (14 calls, smoke ALL PASSED), with a badge in the UI. |
| **Community Vote** ($10K) | Solves an everyday Indonesian problem in Bahasa and Javanese, and anyone can try it free in demo mode from the live link. A shared guide link previews as a card in WhatsApp/X (marked photo, likely cause, safety level; `/api/sessions/{id}/card.png`), and the front page has its own preview card. |
| **Best Agentic Use-Case** ($5K) | A real multi-step loop: asks a follow-up when unsure → plans → verifies each step from a camera photo → re-plans for the next cause → escalates or hands off to a bengkel. The safety gate is enforced in code. The **agent-trace panel "🤖 What the AI did"** shows every decision with the Meta model (or code rule) that made it, live on the progress screen, on the result, and in the PDF report. Results **stream in** as each stage finishes (what it saw, the SAM 3.1 outlines, the top cause), and **every log line is tappable**: it jumps to the stage, photo or exact camera-checked step it describes. The **1-tap demo** runs the whole loop in about a minute with no photo: question → plan → a rejected and an accepted check photo → re-plan. |
| **Best Creative Build** ($5K, Muse Image) | Muse Image edits the user's *own* photo into an instructional diagram, and Muse Spark reviews it and redraws a bad one. A creative use of image editing as a teaching tool. (Weakest claim: Muse Image is a supporting feature, not the core.) |

## Try it in 60 seconds (for the gallery / judges)
Open the live link on a phone → tap **▶ Coba demo 1 ketuk** (1-tap demo; the tips guide you through question → check photos → re-plan, and *🤖 Yang dilakukan AI* shows each decision). Or under *Coba contoh* tap "motor mogok" → answer the one question → tick the safety list → try **🎯 Panduan kamera langsung** and **Mode tangan bebas** → tap *Cek langkah ini* and snap anything → tap "rice cooker mati" to see the red STOP with its PDF and hand-off card. Without a key the app runs in labelled demo mode.
