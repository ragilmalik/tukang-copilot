# Demo assets (generated from the real app, real Meta API answers)

`python scripts/make_demo_assets.py` makes everything here from the app and the labelled AI-generated sample photos in
`api/tests/fixtures/`. Every sample photo carries "Sample photo (AI-generated)" in its corner, and every phone frame of
the video says where its answers come from.

## Where the answers come from

The app screens show real answers from the Meta Model API, recorded on a live run on 6 Nov 2026 and played back in the
app (the script's recorded mode, `DEMO_RECORDED_DATA`), so nothing on screen is a canned offline answer:

- The motorbike repair is the app's own recorded 1-tap demo (`web/replay/demo.json`), recorded from the live API on
  the new photos on 6 Nov 2026 at 14:01 WIB. The "Recorded demo" badge is on screen. The model was 85 to 88% sure, so
  this recording asked no follow-up question.
- The pump, rice cooker (red stop), faucet (with its Muse Image diagram) and Basa Jawa tyre screens are live sessions
  I recorded on 6 Nov 2026 between 14:01 and 14:05 WIB, reopened in the app the way it reopens a saved repair.
- The film and the vertical clip were made from these recordings only. Recording them spent $0.00 (the app's cost
  meter, printed by each `capture` run); no model was called.
- The live camera guide (`16_live_guide.png`) calls SAM 3.1 live while filming, on Chromium's test camera feed playing
  a sample photo. That shot is still from the previous photo set: the take on the new pump photo on 6 Nov 2026 ran
  20 SAM 3.1 frames ($0.05) and did not lock on the part within 30 s. It is not in the video.
- The 5 WhatsApp simulator shots (`30_whatsapp_*`) were shot against the live API in the `/wa` simulator, which runs
  the same handler as the real webhook. No real WhatsApp number was used. They show the previous photo set and are not
  in the video.

The people-and-home stills in the film (`docs/launch/broll/`, and `docs/launch/scenes/` with a real screenshot warped
onto the phone) are AI-generated scenes. Each one says "AI-generated scene" while it is on screen. Upload with
YouTube's "altered or synthetic content" box ticked.

| File | What |
|---|---|
| `tukang-copilot-demo.mp4` | 2:25 (145.8 s by ffprobe), 1920×1080 at 30 fps, H.264 (CRF 20) + AAC 192 kbps, +faststart, 31.4 MB (29.9 MiB). 21 scenes (start times in `TIMESTAMPS.txt`): a broken pump and a motorbike that won't start at home (AI-generated scenes, owner's line in Bahasa Indonesia), what the app does, then one repair end to end on real recorded screens (home, photo and text, results streaming in, diagnosis, SAM 3.1 parts, safety list, steps, step check fail and pass, re-plan, bengkel hand-off), the Muse Image diagram (faucet, English), the red stop (rice cooker), the tyre in Basa Jawa (owner's line in Basa Jawa), the measured numbers, and the repo link with the music credit. English captions burned in. Loudness -16.0 LUFS integrated, true peak -3.6 dBFS, LRA 4.7 LU (ffmpeg ebur128 on the finished file) |
| `tukang-copilot-demo.en.srt` | The same captions as a subtitle file for YouTube; owner lines are given in English in quotes |
| `TIMESTAMPS.txt` | Scene start times (mm:ss); the YouTube chapters in docs/launch/YOUTUBE.md follow it |
| `tukang-copilot-x-vertical.mp4` | The 9:16 cut for X, Reels and Shorts: see the numbers below. Its own short voice lines over the same recordings, the same music, English captions at 46 px inside the area the apps leave free (250 px kept clear at the bottom) |
| `hero.gif` | README animation from the same recordings: 640×1200, 6 frames a second, one palette for the whole loop (see below) |
| `screenshots/*.png` | 118 shots, every one listed with what it shows in [`screenshots/INDEX.md`](screenshots/INDEX.md). 26 of the 33 numbered shots were re-shot on 6 Nov 2026 on the new sample photos; 7 are from the previous photo set and marked in the index (`03_question`, `16_live_guide`, the 5 `30_whatsapp_*`). None of those 7 is in the video or the GIF. The gallery (`screenshots/gallery/`, 85 files from `scripts/make_screenshots.py`) shows every screen in Bahasa Indonesia, Basa Jawa and English |
| `voice/*.mp3` | One voice-over clip per scene of the film and of the vertical cut, loudness-normalised to -16 LUFS; `script.json` is the text each clip was made from, `timing.json` where each caption starts and ends in its clip |

## How the film is made

The script is `SCENES` in `scripts/make_demo_assets.py` (hook, problem, promise, the app in action, proof, call to
action). Numbers on the proof card come only from the repo's reports:

| On the card | Source |
|---|---|
| 83 s median per repair | docs/EVAL.md headline table, live column: 83492.4 ms median (run of 5 Nov 2026, 23:22 WIB) |
| $0.044 median per repair | docs/EVAL.md, same row set: $0.0437 median |
| 33 / 33 dangerous cases stopped | docs/EVAL.md: 23/23 red-team owner texts + 10/10 dangerous plan steps |
| 0 / 17 everyday jobs stopped | docs/EVAL.md: "0 of 17 safe cases stopped" |
| 1,096 tests | docs/TEST_REPORT.md: 1096 passed, 0 failed, 0 skipped (last full run, v1.32.0) |

The eval ran on the earlier set of sample photos, before the photos in this video; the card and the voice-over say so.

**Voice.** edge-tts `en-US-AndrewMultilingualNeural` at -8% (about 150 words a minute; the A/B is in my working notes),
owners' lines in `id-ID-GadisNeural` (Bahasa Indonesia) and `jv-ID-DimasNeural` (Basa Jawa) at -4%. Each sentence is
its own take, joined with 0.32 s between sentences and 0.45 s after an owner's line, so the read pauses where a person
would. edge-tts takes no SSML here, so the pauses come from the joins. A few written forms are spoken differently
(`SPOKEN`: "$0.044" as "four point four cents", "1,096", "220-volt", "SAM 3.1"); the captions keep the written form.
The voice starts 0.2 s after each cut.

**Music.** "Lucky Acoustic" by Jesse Keller (https://www.jamendo.com/track/1540859), licensed under CC BY 3.0
(https://creativecommons.org/licenses/by/3.0/). The credit is on the end card, in `TIMESTAMPS.txt`, in
docs/ATTRIBUTIONS.md and in the YouTube description. I read the licence from Openverse's record of the Jamendo track;
the Jamendo page I fetched did not show the licence text, so check it on the Jamendo page before publishing anywhere
new. The audio file is not in the repo: point `DEMO_MUSIC` at it.

**Mix.** The music is set to -9.5 dB, cut 3 dB around 2.5 kHz, and ducked by the voice with a sidechain compressor
(threshold 0.03, ratio 5, attack 20 ms, release 450 ms); it fades in over 1.5 s and out over the last 3 s. Measured on
the stems (`MUSIC_DB` and the same graph, 400 ms RMS windows): while the narrator speaks the music sits a median
20.5 dB under the voice (10th to 90th percentile 6.7 to 29.3 dB), and in pauses it comes up about 11 dB. The whole mix
then gets a two-pass loudnorm to -16 LUFS, true peak -1.5 dBTP. No silence of 0.8 s or more at -50 dB anywhere.

**Checks I ran on the finished files.** ffprobe durations and streams, ebur128 loudness, a contact sheet of the whole
film (one frame every 2 s) and spot frames looked at for caption overlap, labels and old photos, and speech-to-text
with faster-whisper `base.en` against the narration (owner lines left out): see the numbers below. Nobody has listened
to the film by ear yet; the voice, the music level and the owner lines need a listen before upload.

Speech-to-text (faster-whisper `base.en`, CPU) found 281 of the 307 narration words of the film (91.5%) and 277 of
307 (90.2%) on the voice track alone, so the music does not cost words. What it missed is mostly local names and
numbers it writes differently: "Tukang Copilot" (heard as "a con co-pilot"), "bengkel" ("bankle"), "Bahasa",
"Muse", "SAM 3.1", spoken numbers written as digits, "centre" spelled "center". In the tyre scene it heard "Javanese"
as "Japanese"; the same sentence rendered on its own was transcribed correctly, so this is a weak spot of the small STT
model or a soft word in the take. Worth a listen.

### Vertical clip and GIF numbers

| File | Numbers (measured on the finished files) |
|---|---|
| `tukang-copilot-x-vertical.mp4` | 31.4 s, 1080×1920 at 30 fps, H.264 CRF 20 + AAC, 8.7 MB. Six scenes: broken pump (AI-generated scene, owner's line in Bahasa Indonesia), parts on the photo, step check passed, red stop, Basa Jawa tyre, end card with the repo link and the music credit. -16.0 LUFS integrated, true peak -3.5 dBFS. Music at `MUSIC_DB_VERTICAL` (-12 dB): a median 19.2 dB under the voice. STT 51 of 57 narration words (89.5%) |
| `hero.gif` | 640×1200, 78 frames at 6 fps (13 s loop), 64 colours, 2.9 MB (2.78 MiB; the build stops above 3 MiB): results streaming in, diagnosis, SAM 3.1 parts, a passed step check, the red stop, the tyre in Basa Jawa. Every frame is from the recordings above |

## Regenerate

```
export DEMO_RECORDED_DATA=<copy of the live run's data folder with sessions/>
export DEMO_MUSIC=<path to lucky_acoustic_jesse_keller.mp3>
python scripts/make_demo_assets.py voice            # needs internet; a changed line is re-recorded
python scripts/make_demo_assets.py capture motor    # then: capture steps, capture other (Chromium, no model calls)
python scripts/make_demo_assets.py video            # segments are cached in $DEMO_BUILD_DIR or $TMPDIR/tukang-video
python scripts/make_demo_assets.py vertical
python scripts/make_demo_assets.py gif
```

`video KEY ...` renders only those scenes; move a cached segment (`segments/NN_key.mkv`) away to render it again. The
film and the vertical clip refuse to build from live clips, because the narration says the answers were recorded. The
screenshots: `shots` (needs Chromium; in recorded mode only the live camera guide calls SAM 3.1, about $0.01 to $0.05)
and `scripts/make_screenshots.py` for the gallery.
