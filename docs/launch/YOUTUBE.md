# YouTube upload kit

Upload the real-phone recording if I have one by then, otherwise `docs/demo/tukang-copilot-demo.mp4` (2:54, real Meta API answers recorded on a live run).
Unlisted is fine for judging, but Public helps with Most Viral and Community Vote. Open the link in a private window
before pasting it into the form. For captions, upload `docs/demo/tukang-copilot-demo.en.srt` as English subtitles.
The thumbnail is `docs/launch/thumbnail.png` (1280x720); custom thumbnails need a phone-verified YouTube account.

## Title options
1. Tukang Copilot: AI finds the broken part and checks every repair step (Muse Spark + SAM 3.1)
2. Motor mogok? This AI outlines the exact part and checks your repair with the camera
3. Every phone becomes a mechanic's apprentice: Tukang Copilot (Bahasa, Jawa, English)
4. Plan, act, verify, re-plan: an AI repair agent for Indonesian homes

I'm going with option 1. It says what the app does, names the Meta models the judges score, and at 92 characters it
fits YouTube's 100-character limit.

## Description (paste as is, then fill the placeholders)
```
Point your phone at something broken and say what's wrong in Bahasa Indonesia, Javanese or English. Tukang Copilot outlines the exact part on your own photo, walks you through the fix, checks each step with your camera, and says STOP when the job is dangerous.

I built it solo for the Meta Global AI Developer Hackathon (Indie track, Push the Frontier). Everything in this video was built during the event, Oct 26 to Nov 4, 2026.

Every answer in this video is a real answer from the Meta Model API, recorded on a live run on 6 Nov 2026 and played back in the app; the live camera guide called SAM 3.1 live while I filmed. The photos are AI-generated samples and say so in their corner.

Try it (1-tap demo, no photo needed): [LIVE_URL]
Code (MIT): https://github.com/ragilmalik/tukang-copilot

Chapters
[paste the chapter block for the cut you upload, from below]

How it works
- Muse Spark 1.3 looks at the object, diagnoses, plans, checks each step from a new photo and re-plans
- SAM 3.1 draws pixel masks of the real parts on your photo and tracks them on the live camera
- Muse Voice Transcribe and Muse Spark 1.2 audio handle Indonesian, English and Javanese voice
- Muse Image turns your photo into a diagram for hidden steps
- Muse Spark Open (open weights) on Baseten can take over diagnosis and planning with one switch
- The safety stops (gas, house wiring, 220 V internals, brakes, fuel) are plain code that runs before any model call
- On the WhatsApp Cloud API the same agent answers a WhatsApp chat (shown in the simulator; a real number is not connected yet)

Why I built it: Indonesia has 139 million motorbikes (BPS 2024) and millions of homes on an electric water pump. A light pump service costs about two days of Central Java's minimum wage before parts. Repair videos can't see your problem and usually aren't in your language.

#MetaAI #MuseSpark #SAM3 #AIagents #Indonesia #BahasaJawa #DIY #hackathon
```

## Chapters

YouTube's rules: the first chapter starts at 0:00, there are at least 3 chapters, and each one lasts at least 10 seconds.

### A. Current backup cut (`tukang-copilot-demo.mp4`, 2:54, real Meta API answers recorded on a live run on 6 Nov 2026, timings from `docs/demo/TIMESTAMPS.txt`)
```
0:00 A small fault costs a day's wage
0:20 Photo and voice in, results stream in
0:38 One question, diagnosis and SAM 3.1 parts
0:58 Safety tick list and live camera guide
1:14 Check my step: the camera verifies
1:28 Hands-free, re-plan and a Muse Image diagram
1:51 What the AI did and the bengkel hand-off
2:07 Safety STOP, then WhatsApp in Basa Jawa
2:34 How it works: the Meta models
```
I checked each chapter against the scene starts in `docs/demo/TIMESTAMPS.txt`, and all of them are at least 10 s long
(the shortest, 1:14 to 1:28, is 14 s). If the video gets re-cut, re-read that file and move the chapters with it.

### B. Real-phone recording (timings from docs/DEMO_SCRIPT.md)
```
0:00 Motor mogok, bengkel tutup
0:12 Meet Tukang Copilot
0:22 Snap and speak, one question
0:40 Parts on my own photo, safety list
0:55 Live camera guide
1:15 Hands-free and step check
1:35 It runs again
1:45 Safety STOP and bengkel hand-off
2:05 Basa Jawa and open weights
2:15 Five Meta models, one agent loop
2:45 Every phone becomes a mechanic's apprentice
```
Adjust these to the real edit, and keep the total under 3:00 (the form field is "3-Minute Demo Video").

## Tags (YouTube tags box, comma separated, under 500 characters)
```
Tukang Copilot, Meta AI, Muse Spark, SAM 3.1, Segment Anything, Meta Model API, Muse Spark Open, open weights, AI agent, agentic AI, repair assistant, DIY repair, Indonesia, Bahasa Indonesia, Basa Jawa, Javanese, motorbike repair, water pump repair, pompa air, motor mogok, hackathon, Cerebral Valley
```

## Upload checklist
- [ ] Title option 1, description with [LIVE_URL] filled (repo link is already in)
- [ ] Chapters block matching the uploaded cut
- [ ] English subtitles from the `.srt`
- [ ] Thumbnail `docs/launch/thumbnail.png`
- [ ] "Not made for kids", category Science & Technology
- [ ] Opens logged out; the link goes into form field 8 and the README
