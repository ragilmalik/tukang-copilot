# Demo assets (generated from the real app, real Meta API answers)

`python scripts/make_demo_assets.py` makes everything here from the app I built during the hackathon, with the labelled
AI-generated sample photos in `api/tests/fixtures/`. Every sample photo carries "Sample photo (AI-generated)" in its
corner, and every frame of the video says where its answers come from.

## Where the answers come from

The answers on screen are real answers from the Meta Model API, recorded on live runs and played back in the app
(the script's recorded mode, `DEMO_RECORDED_DATA`), so nothing on screen is a canned offline answer:

- The motorbike repair is the app's own recorded 1-tap demo (`web/replay/demo.json`). The screenshots use the recording
  made from the live API on the new photos on 6 Nov 2026 at 14:01 WIB; the current video and GIF still show the earlier
  recording of 01:23 WIB on the previous photos. The "Recorded demo" badge is on screen.
- The pump, rice cooker, faucet (with its Muse Image diagram) and Basa Jawa tyre screens are live sessions I recorded
  on 6 Nov 2026, reopened in the app the way it reopens a saved repair.
- The live camera guide (`16_live_guide.png` and the live camera scene) calls SAM 3.1 live while filming, on Chromium's
  test camera feed playing a sample photo. The current `16_live_guide.png` is from the previous photo set: the take on
  the new pump photo on 6 Nov 2026 ran 20 SAM 3.1 frames ($0.05) and did not lock on the part within 30 s.
- The 5 WhatsApp simulator shots (`30_whatsapp_*`) were shot against the live API in the `/wa` simulator, which runs
  the same handler as the real webhook (unchanged since commit a1a77dd, 6 Nov 2026 WIB). No real WhatsApp number was used.
  They show the previous photo set; re-taking them needs new live answers.

The hands-free shot uses a silent stand-in for the browser's speech recogniser, because headless Chromium does not
have one. My real-phone recording (docs/DEMO_SCRIPT.md) would replace the main video if I record one in time.

| File | What |
|---|---|
| `tukang-copilot-demo.mp4` | 2:54 (174.1 s by ffprobe), 1920×1080 at 60 fps, H.264 + AAC, 34.2 MB. Screen recordings of the 1.31.0 phone UI in a phone frame, Barlow captions, crossfades and slow zooms on the marked parts. English voice-over (edge-tts `en-US-AndrewMultilingualNeural`, the owners' lines in Bahasa and Basa Jawa), English captions burned in, about -16 LUFS. 21 scenes (start times in `TIMESTAMPS.txt`): title card with the hackathon dates, hook, intro, streaming progress, question, diagnosis, SAM parts, safety list, live camera guide, step check fail and pass, hands-free, re-plan, Muse Image diagram, agent log, bengkel hand-off, rice-cooker STOP, WhatsApp in Basa Jawa, architecture, close |
| `TIMESTAMPS.txt` | Scene start times (mm:ss) of the main video; the YouTube chapters in docs/launch/YOUTUBE.md follow it |
| `tukang-copilot-demo.en.srt` | Captions (the voice-over text) as a separate subtitle file for YouTube |
| `tukang-copilot-x-vertical.mp4` | 43.5 s, 1080×1920 at 60 fps, silent, 12.1 MB, Bahasa headlines with English captions, for the X post (hook, streaming progress, parts, live camera, step check, STOP, WhatsApp in Basa Jawa, models, close) |
| `hero.gif` | README animation, 640 px wide, 2.2 MB |
| `screenshots/*.png` | 118 shots, every one listed with what it shows in [`screenshots/INDEX.md`](screenshots/INDEX.md). The numbered set (33 files, used by the README, video and GIF): 26 re-shot on 6 Nov 2026 on the new photorealistic sample photos, phone shots at 390×844 @3x (19 and 25 are PDF pages, 26 the 1200×630 share card, 29 the 1280×800 laptop view), plus 7 kept from the previous photo set at @2x and marked in the index: `03_question` (the new recording asked no follow-up question), `16_live_guide` (a live take on the new pump photo did not lock on the part within 30 s) and the 5 `30_whatsapp_*` simulator shots (they need new live answers). There is no 21. The gallery (`screenshots/gallery/`, 85 files from `scripts/make_screenshots.py`, no model calls) shows every screen in Bahasa Indonesia, Basa Jawa and English, the Bahasa Indonesia screens in dark mode, the static build, the laptop view, PDF pages and the share card |
| `voice/*.mp3` | One voice-over clip per scene (inputs to the video), loudness-normalised to -16 LUFS; `script.json` is the text each clip was made from |
| `../img/architecture.png` | Architecture diagram used in the video and README |

## Regenerate

Run the steps in this order: `shots` (needs Chromium; also runs `wa`) → `diagram` → `voice` (needs internet; goes
direct unless `EDGE_TTS_PROXY` is set; a changed line is re-recorded) → `capture motor`, `capture steps`,
`capture other` → `video` → `vertical` → `gif`. Segments are cached in `$TMPDIR/tukang-video`; move that folder away
after changing the recordings. With `DEMO_RECORDED_DATA=<folder with sessions/>` set, the shots and recordings play
recorded live answers and only the live camera guide spends money ($0.0025 per SAM 3.1 frame, about $0.01 when it locks fast and up to $0.05 for a 30 s take that does not lock; printed at the end); without
it every answer is a new live call (about $0.60 for shots and video).
