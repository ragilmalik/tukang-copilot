# Marketing images

Four images for the YouTube video, the repo cover and social posts. Each one is a real app screenshot on top of a
photo scene an image model made from my prompts in November 2026. The scene is not a real person or a real repair, and
every image says "AI-generated scene" in a corner. The phone screens are real: the screenshot is warped onto the
phone in the scene and shown again, large, in a plain phone frame tagged "Real app screen".

Re-make all four: `python docs/launch/make_marketing_images.py` (Pillow, NumPy and ImageMagick 7). The same command
runs for `python docs/launch/make_launch_assets.py thumbnail`. The script's docstring explains each step; the screen
corners were measured by eye on a 4x zoomed grid of each scene, and `api/tests/test_launch_assets.py` checks that
each corner quad has the shape of the screenshot it takes, so the warp does not stretch the UI.

| File | Size | Scene (AI-generated) | Real screen | Headline |
|---|---|---|---|---|
| `thumbnail.png` | 1280x720, 1.3 MB (YouTube takes under 2 MB) | `scenes/scene_pump.jpg`: a man crouching by a jet water pump on a kampung terrace, phone in hand | `docs/demo/screenshots/10_pump.png` (pump result, Bahasa Indonesia) | Photo in. Steps out. |
| `cover.png` | 1920x1080 | `scenes/scene_motor.jpg`: a man photographing a scooter engine with the body panels off | `docs/demo/screenshots/gallery/id_light_05_result_top.png` (1-tap demo result with SAM 3.1 parts and the "Demo rekaman" badge) | Snap the engine. See the parts marked. |
| `square.png` | 1080x1080 | `scenes/scene_rice.jpg`: a woman at a kitchen counter with a rice cooker, plug pulled out | `docs/demo/screenshots/11_rice_stop.png` (red safety stop) | It knows when to stop. |
| `poster-vertical.png` | 1080x1920 | `scenes/scene_tyre.jpg`: a man crouching by a scooter's rear tyre in an alley | `docs/demo/screenshots/20_javanese_result.png` (tyre result in Basa Jawa) | Answers in Basa Jawa. |

Notes on the scenes
- The prompts were not saved with the files. What each scene shows is written above.
- The generator painted brand marks on two scenes. A scooter model badge and the rice cooker brand were blurred in
  the scene files before this pass (docs/launch/broll/README.md). On the tyre scene the script blurs two more marks it
  missed: "HONDA" on the engine case and a garbled badge on the side cover (`Spec.blur`). I checked the pump and
  motorbike scenes at full size and found no readable brand (the round mark on the scooter is its key slot). The
  motorbike model name the model wrote in its own answer stays on the real screen as it was recorded.
- The scenes do not match the app's sample photos (for example, the pump in the scene is not the pump in the sample
  photo on the screen). The scene sets the mood; the screen shows what the app did with its own labelled sample photo.
- The scenes were made at 1376x768 (768x1376, 1024x1024) and are scaled with Lanczos by at most 1.41x.

## Claims on the images

Every word on an image and where it is backed. The percentages and texts inside the phone screens are recorded model
answers, shown exactly as the screenshot captured them, never typed by hand.

| On the image | Where it is backed |
|---|---|
| "Photo in. Steps out." | README.md lines 3-5: you point the phone at something broken, the app works out the fault and plans the fix, then checks each step |
| "Snap the engine. See the parts marked." | README.md line 4: "outlines the exact part on *your* photo (SAM 3.1)"; the screen shows 5 parts numbered by SAM 3.1 on the 1-tap demo photo |
| "It knows when to stop." | README.md lines 5-6: "tells you to STOP when the job is dangerous"; the screen is the rice cooker red stop from a live session (docs/demo/README.md lines 15-16, docs/demo/screenshots/INDEX.md line 24) |
| "Answers in Basa Jawa." | README.md lines 3-4 (Bahasa Indonesia, Javanese or English) and line 79 (`?lang=jv`); the screen is a live tyre session answered in Basa Jawa (docs/demo/screenshots/INDEX.md line 32) |
| "Real app screen" | The screenshots named in the table above, made by `scripts/make_demo_assets.py shots` and `scripts/make_screenshots.py` from Meta API answers recorded on live runs (docs/demo/README.md lines 9-16) |
| "AI-generated scene" | This file: every scene came from an image model |
| 75% (pump), 85% (motorbike), 88% (tyre) on the screens | Recorded live answers on 6 Nov 2026 (CHANGELOG.md line 7 for the 1-tap demo's 85 to 88%; the pump and tyre sessions are the recorded live sessions in docs/demo/README.md lines 15-16) |
| "Demo rekaman" badge (cover screen) | The app marks the recorded 1-tap demo (docs/demo/README.md lines 12-14) |

If the sample photos or recordings change, re-take the screenshots first and then re-run the script, so a screen never
shows answers from a different photo than the one on it.
