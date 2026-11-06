# YouTube upload kit

Upload `docs/demo/tukang-copilot-demo.mp4` (2:25, 1920x1080; app screens are real Meta API output recorded on a live
run on 6 Nov 2026 and played back). For captions, upload `docs/demo/tukang-copilot-demo.en.srt` as English subtitles.
The thumbnail is `docs/launch/thumbnail.png` (1280x720, 1.3 MB): the real pump result screen on an AI-generated scene,
labelled "AI-generated scene" (docs/launch/ASSETS.md); custom thumbnails need a phone-verified YouTube account.

The video opens on AI-generated scenes of people and homes (labelled on screen), so tick "Altered or synthetic
content: Yes" when uploading (YouTube Help, "Disclosing use of altered or synthetic content").

## Title options
1. Tukang Copilot: AI finds the broken part and checks every repair step (Muse Spark + SAM 3.1)
2. Motor mogok? This AI outlines the exact part and checks your repair with the camera
3. Every phone becomes a mechanic's apprentice: Tukang Copilot (Bahasa, Jawa, English)
4. Plan, act, verify, re-plan: an AI repair agent for Indonesian homes

I'm going with option 1. It says what the app does, names the Meta models it runs on, and at 92 characters it
fits YouTube's 100-character limit.

## Description (paste as is, then fill the placeholders)
```
Point your phone at something broken and say what's wrong in Bahasa Indonesia, Javanese or English. Tukang Copilot outlines the exact part on your own photo, walks you through the fix, checks each step with your camera, and says STOP when the job is dangerous.

The app screens in this video are real output from the Meta Model API, recorded on a live run on 6 Nov 2026 (from 14:01 WIB) and played back in the app. The photos inside the app are AI-generated samples and say so in their corner. The people and homes at the start are AI-generated scenes, labelled on screen.

Try it (1-tap demo, no photo needed): [LIVE_URL]
Code (MIT): https://github.com/ragilmalik/tukang-copilot

Chapters
0:00 A broken pump, a bike that won't start
0:23 Photo and voice in, results stream in
0:45 Diagnosis and SAM 3.1 parts on your photo
0:59 Safety list, steps and the camera check
1:22 Re-plan, bengkel hand-off, Muse Image diagram
1:39 Red stop and Basa Jawa
1:58 What I measured, and the code

How it works
- Muse Spark 1.3 looks at the object, diagnoses, plans, checks each step from a new photo and re-plans
- SAM 3.1 draws pixel masks of the real parts on your photo and tracks them on the live camera
- Muse Voice Transcribe and Muse Spark 1.2 audio handle Indonesian, English and Javanese voice
- Muse Image turns your photo into a diagram for hidden steps
- Muse Spark Open (open weights) on Baseten can take over diagnosis and planning with one switch
- The safety stops (gas, house wiring, 220 V internals, brakes, fuel) are plain code that runs before any model call

Numbers (docs/EVAL.md, live eval of 5 Nov 2026 on the earlier sample photos): median 83 s and $0.044 per repair, 33 of 33 dangerous cases stopped, 0 of 17 everyday jobs stopped. 1104 automated tests passed in the last full run (docs/TEST_REPORT.md, v1.33.0).

Music: "Lucky Acoustic" by Jesse Keller (https://www.jamendo.com/track/1540859), licensed under CC BY 3.0 (https://creativecommons.org/licenses/by/3.0/)

#MetaAI #MuseSpark #SAM3 #AIagents #Indonesia #BahasaJawa #DIY
```
Before publishing, open the Jamendo page and check the licence again: I read CC BY 3.0 from Openverse's record of the
track, and the Jamendo page I fetched did not show the licence text.

## Chapters

YouTube's rules: the first chapter starts at 0:00, there are at least 3 chapters, and each one lasts at least 10 seconds.
The block in the description follows the scene starts in `docs/demo/TIMESTAMPS.txt` (2:25 cut of 6 Nov 2026):

| Chapter | Scenes (TIMESTAMPS.txt) | Length |
|---|---|---|
| 0:00 A broken pump, a bike that won't start | hook, problem, promise | 23 s |
| 0:23 Photo and voice in, results stream in | home, capture, progress | 22 s |
| 0:45 Diagnosis and SAM 3.1 parts on your photo | diagnosis, parts | 14 s |
| 0:59 Safety list, steps and the camera check | preflight, steps, check_fail, check_pass | 23 s |
| 1:22 Re-plan, bengkel hand-off, Muse Image diagram | replan, handoff, diagram | 17 s |
| 1:39 Red stop and Basa Jawa | rice_broll, rice, tyre_broll, tyre | 19 s |
| 1:58 What I measured, and the code | proof, close | 27 s |

The end card alone (2:16 to 2:25) is shorter than 10 s, so it shares the last chapter. If the video is re-cut, re-read
TIMESTAMPS.txt and move the chapters with it.

## Tags (YouTube tags box, comma separated, under 500 characters)
```
Tukang Copilot, Meta AI, Muse Spark, SAM 3.1, Segment Anything, Meta Model API, Muse Spark Open, open weights, AI agent, agentic AI, repair assistant, DIY repair, Indonesia, Bahasa Indonesia, Basa Jawa, Javanese, motorbike repair, water pump repair, pompa air, motor mogok
```

## Upload checklist
- [ ] Title option 1, description with [LIVE_URL] filled (repo link is already in)
- [ ] Chapters block matching the uploaded cut
- [ ] English subtitles from the `.srt`
- [ ] Thumbnail `docs/launch/thumbnail.png`
- [ ] "Not made for kids", category Science & Technology
- [ ] "Altered or synthetic content": Yes (AI-generated scenes at the start)
- [ ] Music licence checked on https://www.jamendo.com/track/1540859 (CC BY 3.0) and the credit line in the description
- [ ] Opens logged out; the link goes into the README ([YOUTUBE_URL])
