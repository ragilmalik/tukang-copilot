# Submission (ready to paste on Cerebral Valley)

**Title:** Tukang Copilot

**Tagline (≤100 chars):** Point your phone at anything broken. It finds the part, plans the fix, and checks every step.

**Track:** Indie Developer · **Theme:** Push the Frontier

**Description**

*Problem.* Indonesia runs on ~130 million motorbikes, water pumps, rice cookers and household plumbing. A small fault costs a day's wage at a repair shop or days without water. Repair videos are rarely for your model, rarely in your language, and can't see your problem.

*Solution.* Tukang Copilot is an installable phone web app (PWA). Snap 1–3 photos or a 5–10 s video and describe the problem by voice in Bahasa Indonesia, Javanese or English. It identifies the object, highlights the exact parts on your own photo, diagnoses the likely causes with confidence and evidence, rates safety (green / amber / red), and walks you through the repair one step at a time with voice. After each step you snap a photo and it verifies the result or tells you exactly what to correct. If the fix doesn't work, it re-plans for the next cause. When a job is dangerous (gas, house wiring, 220 V internals, brake hydraulics) it refuses and tells you who to call. It shows what the same job would cost at a bengkel versus doing it yourself (labelled estimates), asks you to tick a short safety checklist (unplugged, engine cool) before step 1 unlocks, starts a countdown timer for steps that need waiting (engine cooling, glue drying), and prints large-print workshop sheets to pin up next to the job. At the end you tap "It works now", get a PDF repair report to keep or show a mechanic, and "My garage" on the phone adds up what you saved (no account; uploads can be erased in one tap and are deleted after 24 h anyway).

*How it works (Meta models).*
- **Muse Voice Transcribe**: voice notes in Indonesian/English, keyword-biased to repair vocabulary; **Muse Spark 1.2** audio for Javanese.
- **Muse Spark 1.3 (vision + structured output)**: looks at the photos, diagnoses, plans, and verifies each step from a new photo; every output is a validated JSON schema.
- **SAM 3.1**: one box-prompt call segments every relevant part; masks are rendered as numbered highlights on the user's photo and reused per step.
- **Muse Image**: edits the user's own photo into a clean instructional diagram for steps a photo can't show; Muse Spark reviews each diagram and triggers a redraw if it's wrong.
- **Muse Spark Open (open weights) on Baseten**: one switch moves diagnosis and planning to the open-weight model.
- An agent loop of plan → act → verify → re-plan → escalate, with a three-layer safety gate enforced in code.

*Impact.* Saves a shop visit for common faults, teaches people to fix things themselves, and works in local languages including Javanese. Every claim about savings in the demo is labelled as an estimate.

*What's next.* Offline mode on Muse Glimmer, more object types (fans, washing machines, bicycles), a bengkel handoff that sends the report to a nearby mechanic, and a WhatsApp version.

**Try it in 60 seconds (judges):** open the live link on a phone → tap "pompa tidak keluar air" or "motor mogok" under *Coba contoh* → answer the one question → tap *Cek langkah ini* and snap anything → tap "rice cooker mati" to see the red safety stop. Without a key the app runs in labelled demo mode; the repo also has a 2:37 demo-mode video in docs/demo/.

**Built during the hackathon:** all code, prompts and docs, from scratch, Oct 26 – Nov 4, 2026 (see CHANGELOG.md and commit history).

**Links:** Repo: _github.com/…/tukang-copilot_ · Live: _https://…onrender.com_ · Video: _YouTube_ · X post: _link_

---

# X post drafts (Malik posts; tag handles verified before posting)

**1 (EN, main, with the 30–45 s clip)**
My motorbike wouldn't start and the bengkel was closed. So I built an AI that looks at it with my phone camera, finds the exact part, and checks every step of the fix. 🔧🇮🇩

Built with Muse Spark + SAM 3.1 from @AIatMeta for the @cerebral_valley hackathon.
Bahasa, Javanese and English. Knows when to say "call a pro".

**2 (ID)**
Motor mogok, bengkel tutup. Saya bikin Tukang Copilot: foto, ceritakan masalahnya, AI-nya menandai bagian yang rusak di foto kamu dan mengecek tiap langkah perbaikan pakai kamera. Bisa Bahasa, Jawa, English. 🔧

Dibuat dengan model Meta (Muse Spark, SAM 3.1) untuk hackathon @cerebral_valley @AIatMeta

**3 (EN, technical thread starter)**
How Tukang Copilot works in 5 Meta models:
1/ Voice Transcribe hears the problem
2/ Muse Spark sees the object
3/ SAM 3.1 masks the exact parts on your photo
4/ Spark plans, Muse Image draws hidden steps
5/ Spark verifies each step from a new photo, then re-plans if it's still broken
