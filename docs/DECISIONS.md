# Decisions (and why)

<a id="d1"></a>
**D1 · One FastAPI process serving a plain HTML/JS app, instead of Next.js + separate backend** (spec §7 asked for Next.js on Vercel).
One URL for judges, no build step, no CORS or two deploys, nothing for a non-developer to break. The UI needs no framework (5 screens). Revisit if the UI grows; the API is already separate (`/api/*`) so a Next.js front end can be added without backend changes.

**D2 · Session state in a JSON file per session, not SQLite.** Sessions are temporary (24 h), single-writer per session (lock), and the file doubles as the debug record. SQLite/R2 is on the roadmap.

**D3 · SSE progress with polling fallback.** SSE is simple over HTTP/1.1 and works through Render; the UI falls back to polling if a proxy drops it.

**D4 · Narration with edge-tts, browser voice as fallback.** Meta's API has no TTS (Voice Transcribe is speech-to-text only). edge-tts is free and has Indonesian and Javanese neural voices. Documented as the one non-Meta model in the pipeline.

**D5 · Javanese voice through Muse Spark 1.2 audio.** Voice Transcribe's 25 languages don't include Javanese; Meta's docs recommend 1.2 over 1.3 for audio.

**D6 · SAM box prompts from Look, phrase fallback.** One SAM call for all parts is cheaper and keeps part ids aligned; phrases recover when Look gives no boxes.

**D7 · Muse Image edits the user's photo (not text-to-image), only for hidden steps.** Keeps diagrams faithful to the real object and cost low; visible steps use the SAM-highlighted real photo, which is more trustworthy than any drawing.

**D8 · Safety enforced in code in three layers,** not just in prompts. A prompt can be ignored; a regex gate can't. False positives (e.g. "gas" in "gas pedal") are acceptable: the user can rephrase, and refusing is the safe failure.

**D9 · Demo mode = same engine, mock answers.** Tests and the "Try a sample" links exercise the real code. A fake Meta server additionally tests the real HTTP client.

**D10 · Standard-mode model ids only.** Contributor mode is cheaper but lets Meta train on users' photos; not acceptable for a household app.

**D11 · Per-session cost cap ($0.50 default).** Hackathon credits are $150; a runaway loop must not drain them.
