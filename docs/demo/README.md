# Demo assets (generated from the real app, demo mode)

All made by `python scripts/make_demo_assets.py all` from the app built during the hackathon, running in
demo (mock) mode with the labelled stand-in photos in `api/tests/fixtures/`. Every frame says "demo mode ·
labelled stand-in photos". Malik's real-phone recording (docs/DEMO_SCRIPT.md) should replace the main video
for the submission; this one is the backup and the source of screenshots.

| File | What |
|---|---|
| `tukang-copilot-demo.mp4` | 2:37, 1920×1080, H.264 + AAC, English voice-over (edge-tts `en-US-AndrewNeural`), captions burned in |
| `tukang-copilot-demo.en.srt` | Captions (the voice-over text) as a separate subtitle file for YouTube |
| `tukang-copilot-x-vertical.mp4` | 36 s, 1080×1920, silent with Bahasa captions, for the X post |
| `screenshots/01…14_*.png` | Phone screenshots (390×844 @2x) of every stage: home, progress, follow-up question, diagnosis, SAM parts, step, ⚠ check, ✓ check, re-plan, pump, rice-cooker STOP, report/PDF, English, Basa Jawa + garage |
| `voice/*.mp3` | One voice-over clip per scene (inputs to the video) |
| `../img/architecture.png` | Architecture diagram used in the video and README |

Regenerate: `shots` (needs Chromium) → `diagram` → `voice` (needs internet; `EDGE_TTS_PROXY` if behind a proxy) → `video` (needs ffmpeg; segments cached in `$TMPDIR/tukang-video`, delete it after changing screenshots).
