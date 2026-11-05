# Demo assets (generated from the real app, offline sample mode)

`python scripts/make_demo_assets.py all` makes everything here from the app I built during the hackathon, running in
demo (mock) mode with the labelled AI-generated sample photos in `api/tests/fixtures/`. Every frame of the video says
"Offline sample mode · sample answers · AI-generated sample photos", and every sample photo carries "Sample photo (AI-generated),
offline sample mode" in its corner.

A few shots need a note. The live camera guide shots use Chromium's test camera feed playing a sample photo, so the overlay
boxes come from the demo-mode tracker and not from a live SAM 3.1 call. The hands-free shot uses a silent sample for
the browser's speech recogniser, because headless Chromium doesn't have one. The open-weights badge shot shows what the
header looks like with `USE_OPEN_WEIGHTS=1` + a Baseten key, but the answers are still demo answers. My real-phone
recording (docs/DEMO_SCRIPT.md) should replace the main video for the submission; this one is the backup and the source
of the screenshots.

| File | What |
|---|---|
| `tukang-copilot-demo.mp4` | 2:53 (173.5 s by ffprobe, v1.29 cut re-shot on the new UI: phone frame, Barlow captions, crossfades, slow zooms on the marked parts; WhatsApp scene in Basa Jawa at 2:13), 1920×1080 at 60 fps, H.264 + AAC, English voice-over (edge-tts `en-US-AndrewNeural`), English captions burned in. 21 scenes (start times in `TIMESTAMPS.txt`), opening with a 3 s hook title card with the hackathon dates. Covers streaming progress, the safety tick list, the live camera guide, step checks, hands-free, re-plan, the Muse Image diagram step (placeholder drawing), the agent log, the bengkel hand-off, the rice-cooker STOP, WhatsApp in Basa Jawa, open weights and the architecture |
| `TIMESTAMPS.txt` | Scene start times (mm:ss) of the main video; the YouTube chapters in docs/launch/YOUTUBE.md follow it |
| `tukang-copilot-demo.en.srt` | Captions (the voice-over text) as a separate subtitle file for YouTube |
| `tukang-copilot-x-vertical.mp4` | 43.5 s, 1080×1920 at 60 fps, silent, Bahasa headlines with English captions, for the X post (hook, streaming progress, parts, live camera, check, STOP, WhatsApp in Basa Jawa, models, close) |
| `screenshots/01…30_*.png` | 34 shots. Phone screenshots (390×844 @2x) of every stage: home, progress, follow-up question, diagnosis, SAM parts, step, ⚠ check, ✓ check, re-plan, pump, rice-cooker STOP, report/PDF, English, Basa Jawa + garage, 15 safety tick list, 16 live camera guide, 17 hands-free listening, 18 bengkel hand-off, 19 stop report PDF page, 20 Javanese result, 21 open-weights badge, 22 stop card hand-off. 23 = agent log, 24 = tap a log line → that step, 25 = PDF agent-log page, 26 = share card (link preview, 1200×630), 27 = recorded demo, 28 = Muse Image diagram step (placeholder drawing), 29 = laptop phone-frame view with QR code (1280×800). 30 = the WhatsApp simulator (`/wa`, offline sample mode, same handler as the real webhook): `30_whatsapp_jv_diagnosis` (marked photo + likely cause), `30_whatsapp_jv_steps` (step with Done / Problem / Stop buttons), `30_whatsapp_jv_redstop` (gas smell: red stop, no steps), `30_whatsapp_en_check` (camera check passed, step 2), `30_whatsapp_en_pdf` (Stop: workshop link + PDF report) |
| `voice/*.mp3` | One voice-over clip per scene (inputs to the video) |
| `../img/architecture.png` | Architecture diagram used in the video and README |

To regenerate, run the steps in this order: `shots` (needs Chromium; also runs `wa`, the WhatsApp simulator shots) →
`diagram` → `voice` (needs internet; goes direct unless `EDGE_TTS_PROXY` is set; delete a scene's mp3 to re-record it) →
`video` (needs ffmpeg; segments are cached in `$TMPDIR/tukang-video`, so delete that folder after changing screenshots).
