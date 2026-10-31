# Demo assets (generated from the real app, demo mode)

All made by `python scripts/make_demo_assets.py all` from the app built during the hackathon, running in
demo (mock) mode with the labelled stand-in photos in `api/tests/fixtures/`. Every frame says "demo mode ·
labelled stand-in photos". The live camera guide shots use Chromium's fake camera playing a stand-in photo (the
overlay boxes are the demo-mode tracker, not a live SAM 3.1 call); the hands-free shot uses a silent stand-in for the
browser's speech recogniser (headless Chromium has none); the open-weights badge shot shows what the header looks like with
`USE_OPEN_WEIGHTS=1` + a Baseten key (answers are still demo answers). Malik's real-phone recording (docs/DEMO_SCRIPT.md) should replace the main video
for the submission; this one is the backup and the source of screenshots.

| File | What |
|---|---|
| `tukang-copilot-demo.mp4` | 2:57 (177 s, v1.23), 1920×1080, H.264 + AAC, English voice-over (edge-tts `en-US-AndrewNeural`), captions burned in. 22 scenes incl. streaming progress, agent-log jump, PDF agent log, share card, live camera guide, hands-free, bengkel hand-off, stop PDF, Javanese, open weights |
| `tukang-copilot-demo.en.srt` | Captions (the voice-over text) as a separate subtitle file for YouTube |
| `tukang-copilot-x-vertical.mp4` | 45 s, 1080×1920, silent with Bahasa captions, for the X post (hook, streaming progress, parts, live camera, check, share card, STOP, models, close) |
| `screenshots/01…26_*.png` | 23 = agent log, 24 = tap a log line → that step, 25 = PDF agent-log page, 26 = share card (link preview, 1200×630).  Phone screenshots (390×844 @2x) of every stage: home, progress, follow-up question, diagnosis, SAM parts, step, ⚠ check, ✓ check, re-plan, pump, rice-cooker STOP, report/PDF, English, Basa Jawa + garage, **15** safety tick list, **16** live camera guide, **17** hands-free listening, **18** bengkel hand-off, **19** stop report PDF page, **20** Javanese result, **21** open-weights badge, **22** stop card hand-off |
| `voice/*.mp3` | One voice-over clip per scene (inputs to the video) |
| `../img/architecture.png` | Architecture diagram used in the video and README |

Regenerate: `shots` (needs Chromium) → `diagram` → `voice` (needs internet; goes direct unless `EDGE_TTS_PROXY` is set; delete a scene's mp3 to re-record it) → `video` (needs ffmpeg; segments cached in `$TMPDIR/tukang-video`, delete it after changing screenshots).
