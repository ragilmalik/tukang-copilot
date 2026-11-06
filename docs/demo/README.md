# Demo assets (generated from the real app, real Meta API answers)

`python scripts/make_demo_assets.py` makes everything here from the app I built during the hackathon, with the labelled
AI-generated sample photos in `api/tests/fixtures/`. Every sample photo carries "Sample photo (AI-generated)" in its
corner, and every frame of the video says where its answers come from.

## Where the answers come from

The answers on screen are real answers from the Meta Model API, recorded on live runs and played back in the app
(the script's recorded mode, `DEMO_RECORDED_DATA`), so nothing on screen is a canned offline answer:

- The motorbike repair is the app's own recorded 1-tap demo (`web/replay/demo.json`), recorded from the live API on
  6 Nov 2026 at 01:23 WIB. The "Recorded demo" badge is on screen.
- The pump, rice cooker, faucet (with its Muse Image diagram) and Basa Jawa tyre screens are live sessions I recorded
  on 6 Nov 2026, reopened in the app the way it reopens a saved repair.
- The live camera guide (`16_live_guide.png` and the live camera scene) calls SAM 3.1 live while filming, on Chromium's
  test camera feed playing a sample photo.
- The 5 WhatsApp simulator shots (`30_whatsapp_*`) were shot against the live API in the `/wa` simulator, which runs
  the same handler as the real webhook (unchanged since commit a1a77dd, 6 Nov 2026 WIB). No real WhatsApp number was used.

The hands-free shot uses a silent stand-in for the browser's speech recogniser, because headless Chromium does not
have one. My real-phone recording (docs/DEMO_SCRIPT.md) would replace the main video if I record one in time.

| File | What |
|---|---|
| `tukang-copilot-demo.mp4` | {{VIDEO_LEN}} ({{VIDEO_S}} s by ffprobe), 1920×1080 at 60 fps, H.264 + AAC, {{VIDEO_MB}} MB. Screen recordings of the 1.31.0 phone UI in a phone frame, Barlow captions, crossfades and slow zooms on the marked parts. English voice-over (edge-tts `en-US-AndrewMultilingualNeural`, the owners' lines in Bahasa and Basa Jawa), English captions burned in, about -16 LUFS. 21 scenes (start times in `TIMESTAMPS.txt`): title card with the hackathon dates, hook, intro, streaming progress, question, diagnosis, SAM parts, safety list, live camera guide, step check fail and pass, hands-free, re-plan, Muse Image diagram, agent log, bengkel hand-off, rice-cooker STOP, WhatsApp in Basa Jawa, architecture, close |
| `TIMESTAMPS.txt` | Scene start times (mm:ss) of the main video; the YouTube chapters in docs/launch/YOUTUBE.md follow it |
| `tukang-copilot-demo.en.srt` | Captions (the voice-over text) as a separate subtitle file for YouTube |
| `tukang-copilot-x-vertical.mp4` | {{VERT_S}} s, 1080×1920 at 60 fps, silent, {{VERT_MB}} MB, Bahasa headlines with English captions, for the X post (hook, streaming progress, parts, live camera, step check, STOP, WhatsApp in Basa Jawa, models, close) |
| `hero.gif` | README animation, 640 px wide, {{GIF_MB}} MB |
| `screenshots/*.png` | {{SHOTS_N}} shots. 28 phone screenshots (390×844 @2x; 26 is the 1200×630 share card, 19 a PDF page, 29 the 1280×800 laptop view) re-shot on the 1.31.0 screens: 01 home, 02 progress, 03 follow-up question, 04 diagnosis, 05 SAM parts, 06 step, 07 ⚠ check, 08 ✓ check, 09 re-plan, 10 pump, 11 rice-cooker STOP, 12 report, 13 English, 14 Basa Jawa + My garage, 15 safety tick list, 16 live camera guide, 17 hands-free, 18 bengkel hand-off, 19 STOP report PDF page, 20 Javanese result, 22 STOP card hand-off, 23 agent log, 24 tap a log line → that step, 25 PDF agent-log page, 26 share card, 27 recorded demo, 28 Muse Image diagram step, 29 laptop phone-frame view with QR code. The 5 WhatsApp simulator shots: `30_whatsapp_jv_diagnosis` (marked photo + likely cause), `30_whatsapp_jv_steps` (step with Done / Problem / Stop buttons), `30_whatsapp_jv_redstop` (gas smell: red stop, no steps), `30_whatsapp_en_check` (camera check passed), `30_whatsapp_en_pdf` (Stop: workshop link + PDF report). There is no 21: the open-weights badge shot was removed on 5 Nov 2026, and Muse Spark Open has not run on Baseten yet |
| `voice/*.mp3` | One voice-over clip per scene (inputs to the video), loudness-normalised to -16 LUFS; `script.json` is the text each clip was made from |
| `../img/architecture.png` | Architecture diagram used in the video and README |

## Regenerate

Run the steps in this order: `shots` (needs Chromium; also runs `wa`) → `diagram` → `voice` (needs internet; goes
direct unless `EDGE_TTS_PROXY` is set; a changed line is re-recorded) → `capture motor`, `capture steps`,
`capture other` → `video` → `vertical` → `gif`. Segments are cached in `$TMPDIR/tukang-video`; move that folder away
after changing the recordings. With `DEMO_RECORDED_DATA=<folder with sessions/>` set, the shots and recordings play
recorded live answers and only the live camera guide spends money (about $0.01 per take, printed at the end); without
it every answer is a new live call (about $0.60 for shots and video).
