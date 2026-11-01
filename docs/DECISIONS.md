# Decisions (and why)

<a id="d1"></a>
**D1. One FastAPI process serving a plain HTML/JS app, instead of Next.js plus a separate backend** (spec §7 asked for Next.js on Vercel).
Judges get one URL. There is no build step, no CORS, no second deploy, and less for someone who doesn't code to break. The UI has 5 screens and doesn't need a framework. If it grows I'll revisit this; the API already lives under `/api/*`, so a Next.js front end could sit on top without backend changes.

**D2. Session state in one JSON file per session, not SQLite.** Sessions only live 24 h, each one has a single writer (behind a lock), and the file doubles as the debug record. SQLite/R2 is on the roadmap.

**D3. SSE progress with a polling fallback.** SSE is simple over HTTP/1.1 and works through Render. If a proxy drops it, the UI polls instead.

**D4. Narration with edge-tts, browser voice as fallback.** Meta's API has no TTS (Voice Transcribe only goes speech to text). edge-tts is free and has Indonesian and Javanese neural voices. It's the one non-Meta model in the pipeline, and the docs say so.

**D5. Javanese voice through Muse Spark 1.2 audio.** Voice Transcribe's 25 languages don't include Javanese, and Meta's docs recommend 1.2 over 1.3 for audio.

**D6. SAM box prompts from Look, with a phrase fallback.** One SAM call for all parts costs less and keeps the part ids lined up. When Look returns no boxes, phrases recover the parts.

**D7. Muse Image edits the user's photo (no text-to-image), and only for hidden steps.** That keeps the diagrams faithful to the real object and the cost low. Visible steps use the real photo with the SAM highlight, which I trust more than any drawing.

**D8. Safety enforced in code, in three layers, on top of the prompts.** A model can ignore a prompt; it can't ignore a regex gate. False positives (e.g. "gas" in "gas pedal") are acceptable: the user can rephrase, and refusing is the safe way to fail.

**D9. Demo mode is the same engine with mock answers.** The tests and the "Try a sample" links run the real code. A fake Meta server also tests the real HTTP client.

**D10. Standard-mode model ids only.** Contributor mode is cheaper, but it lets Meta train on users' photos. I won't accept that for a household app.

**D11. Per-session cost cap ($0.50 default).** The hackathon credits are $150, and a runaway loop shouldn't be able to drain them.
