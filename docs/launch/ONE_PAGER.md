---
title: "Tukang Copilot"
---

# Tukang Copilot

**Every phone becomes a mechanic's apprentice.** Point your phone at something broken, say what's wrong in Bahasa
Indonesia, Javanese or English. It outlines the exact part on your own photo, walks you through the fix, checks every
step with your camera, and says STOP when the job is dangerous.

<div class="tag">Meta Global AI Developer Hackathon 2026 · Indie track · Push the Frontier · solo, Semarang</div>

## The problem
- **139 million** motorbikes in Indonesia (BPS 2024); **17%** of households drink water drawn by an electric pump (BPS 2023).
- A pump technician charges **Rp180,000** for a light service before parts (Sejasa), about **two days** of Central Java's 2026 minimum wage.
- Repair videos can't see *your* problem, rarely speak **Javanese** (68 million native speakers), and never say when to stop.

## What it does: an agent loop on a physical object

<div class="cols">
<div>

1. **See:** Muse Spark reads the photo; **SAM 3.1** masks and numbers the real parts.
2. **Ask:** one sharp question when confidence is under 60%.
3. **Gate:** code safety rules; a tick list unlocks the steps.
4. **Act:** one step per screen, read aloud, hands-free, live camera guide.
5. **Verify:** a new photo after each step, checked by Muse Spark.
6. **Re-plan or hand off:** next cause, or a bengkel hand-off (WhatsApp, nearest workshop, PDF brief).

</div>
<div>

![](../demo/screenshots/05_parts.png){width=31%} ![](../demo/screenshots/08_check_pass.png){width=31%} ![](../demo/screenshots/11_rice_stop.png){width=31%}

</div>
</div>

![](architecture.png){width=74%}

## Why it is frontier, and safe
- **Verification closes the loop:** the model judges whether a human's physical action worked, then changes plan.
- **Five Meta models, one client file:** Muse Spark 1.3 and 1.2 audio, SAM 3.1 (photos and live camera), Voice Transcribe, Muse Image, **Muse Spark Open** on Baseten (open weights, one switch).
- **Safety in code, not prompts:** gas, mains, 220 V internals, brakes, fuel = red STOP before any model call; untrusted-text fence against prompt injection.

## Evidence
**599** automated tests pass (0 failed, 0 skipped; real Chromium + jsdom) · **66-check** HTTP smoke passes · mypy strict, ruff clean ·
red-team eval: **100%** safety-stop recall on 30 cases, **0** false stops on 17 safe, **7/7** injections resisted (mock/fake-model) ·
5 scenarios · 3 languages · 2:57 captioned demo video.
**Honest status:** demo assets run in labelled demo mode; a live Meta answer is not yet verified; Semarang user trials pending.

<div class="links">Try it: [LIVE_URL] · Code (MIT): [GITHUB_URL] · Video: [YOUTUBE_URL]</div>
