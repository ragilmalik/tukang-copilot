# Tukang Copilot: write-up

## The problem
Indonesia runs on ~130 million motorbikes, plus water pumps, rice cookers and plumbing. A loose plug cap or a pump that lost its prime costs a day's wage at a bengkel, or days without water. Repair videos are rarely for your model or in your language, can't see *your* problem, and never say when a job is dangerous.

## How it works
A phone web app (PWA, no account). Snap photos or a short video and say what's wrong in Bahasa Indonesia, Javanese or English. An agent loop runs **plan → act → verify → re-plan → escalate**: it outlines the exact parts on your photo, diagnoses causes with confidence (asking one question when unsure), and rates safety. A safety tick list unlocks the steps. Steps are read aloud, **hands-free mode** listens for "lanjut" or "cek", and the **live camera guide** outlines the part to touch on the camera picture. After each step a photo is checked (✓ or a specific correction). If it's still broken, it re-plans. When it's a pro's job, the **bengkel hand-off** sends a WhatsApp summary, finds the nearest workshop, and adds a PDF brief for the mechanic.

## Meta models, and why
- **Muse Spark 1.3**: vision, diagnosis, planning and step verification as validated JSON. One model that reasons over photos is what makes verify-and-re-plan possible. **Spark 1.2** audio handles Javanese.
- **SAM 3.1**: pixel masks of the real parts on the user's photo, and tracking on live camera frames (rate-limited, capped per repair).
- **Muse Voice Transcribe**: voice notes and push-to-talk commands, biased toward repair words.
- **Muse Image**: turns the user's own photo into a diagram for hidden steps. Spark reviews it and has a bad one redrawn once.
- **Muse Spark Open via Baseten** (open weights): one switch moves diagnosis and planning to an open-weight model a bengkel co-op or NGO could self-host. A badge shows when it's on.

## Safety
Three layers: a code gate on the text before any model call, the model's safety level, and a code override on the plan. Gas, house wiring, 220 V internals, brakes and fuel leaks always stop and go to a professional. Photos are deleted after 24 h or in one tap. Spend caps apply per repair and per day.

## Impact plan
Five user trials in Semarang (`docs/USER_TRIAL_KIT.md`) log time to fix, the outcome, and money saved against bengkel prices. `scripts/impact_report.py` turns the log into the report.

## Honest status
The demo video runs in **demo mode**: labelled stand-in photos, recorded model answers, and Chromium's fake camera for the live guide. The real Meta code path is tested end to end against a stand-in server built from the official API docs (410 automated tests), and the real api.meta.ai endpoint correctly rejected a dummy key. **No live Meta model answer is verified yet.** That needs the API key. The impact numbers in `docs/IMPACT.md` are mock until the real trials run.
