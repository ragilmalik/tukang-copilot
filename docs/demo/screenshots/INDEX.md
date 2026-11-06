# Screenshot index

Every screenshot of the app in this folder, what it shows and its pixel size. Phone shots are 390x844 CSS px
at device scale 3 (1170x2532; the kept older ones are scale 2). All answers on screen are recorded answers from the live Meta Model API on the
AI-generated sample photos (labelled on each photo); see the notes at the end for the shots that are not.

Re-make: `python scripts/make_demo_assets.py shots` (numbered set, needs `DEMO_RECORDED_DATA`; the live camera
guide is the only live call) and `python scripts/make_screenshots.py` (gallery, no model calls); then
`python scripts/make_screenshot_index.py` rewrites this file.

## Numbered set (README, video, GIF)

| File | Shows | Size |
|---|---|---|
| `01_home.png` | Capture screen: sample photo picked, problem typed (Bahasa Indonesia) | 1170x2532 |
| `02_progress.png` | Progress while the recorded run streams in | 1170x2532 |
| `04_diagnosis.png` | Diagnosis: likely causes with confidence | 1170x2532 |
| `05_parts.png` | SAM 3.1 masks numbered on the photo | 1170x2532 |
| `06_step.png` | Step card | 1170x2532 |
| `07_check_fail.png` | Step check fails: photo too dark | 1170x2532 |
| `08_check_pass.png` | Step check passes on the step the photo shows | 1170x2532 |
| `09_replan.png` | Re-plan banner after 'still broken' | 1170x2532 |
| `10_pump.png` | Water pump result (recorded live session) | 1170x2532 |
| `11_rice_stop.png` | Rice cooker: red safety stop | 1170x2532 |
| `12_report.png` | Share, PDF and hand-off buttons | 1170x2532 |
| `13_english.png` | Kitchen tap result in English | 1170x2532 |
| `14_garage_jv.png` | Home in Basa Jawa with My garage (full page) | 1170x7734 |
| `15_preflight.png` | Safety tick list before step 1 | 1170x2532 |
| `17_hands_free.png` | Hands-free voice bar | 1170x2532 |
| `18_handoff.png` | Hand-off to a mechanic | 1170x2532 |
| `19_stop_pdf.png` | PDF report of the red stop, page 1 | 910x1287 |
| `20_javanese_result.png` | Scooter tyre result in Basa Jawa | 1170x2532 |
| `22_stop_handoff.png` | Red stop: do this now, service buttons, hand-off | 1170x2532 |
| `23_agent_log.png` | Agent log | 1170x2532 |
| `24_agent_jump.png` | Tap a log line: the step card flashes | 1170x2532 |
| `25_pdf_agent.png` | PDF report page with the agent log | 910x1287 |
| `26_share_card.png` | Share card image (1200x630) | 1200x630 |
| `27_recorded_demo.png` | Recorded demo in English (what a visitor sees while the server sleeps) | 1170x2532 |
| `28_diagram_step.png` | Step with a Muse Image diagram (English) | 1170x2532 |
| `29_laptop.png` | Laptop view: phone frame, QR code, 1-tap demo, language switch | 1280x800 |

## Kept from the previous sample photo set (1.31.1, not re-taken)

These show the old sample photos with the live answers recorded on them on 6 Nov 2026 (before the new photos).
They stay because the current video and GIF use them, until those are re-made. Why they were not re-taken:
the new 1-tap demo recording has no follow-up question (the model was sure), no recorded sample session asked
one, and the live camera guide and the WhatsApp simulator need new live calls that the $1.00 cap of the remake
no longer covered (the live guide run spent $0.05 on 20 SAM 3.1 frames and did not lock on the new pump photo).

| File | Shows | Size |
|---|---|---|
| `03_question.png` | Follow-up question (only when the recorded run asked one) (old sample photo) | 780x1688 |
| `16_live_guide.png` | Live camera guide: SAM 3.1 outline on the camera picture (live call) (old sample photo) | 780x1688 |
| `30_whatsapp_jv_diagnosis.png` | WhatsApp simulator, Basa Jawa: marked photo and likely cause (old sample photo) | 780x1688 |
| `30_whatsapp_jv_steps.png` | WhatsApp simulator, Basa Jawa: step with buttons (old sample photo) | 780x1688 |
| `30_whatsapp_jv_redstop.png` | WhatsApp simulator, Basa Jawa: gas smell, red stop (old sample photo) | 780x1688 |
| `30_whatsapp_en_check.png` | WhatsApp simulator, English: camera check (old sample photo) | 780x1688 |
| `30_whatsapp_en_pdf.png` | WhatsApp simulator, English: PDF report in the chat (old sample photo) | 780x1688 |

## Gallery: Bahasa Indonesia, light

| File | Shows | Size |
|---|---|---|
| `gallery/id_light_01_home.png` | First screen (Bahasa Indonesia) | 1170x2532 |
| `gallery/id_light_02_capture.png` | Capture: sample photo picked and the problem typed, nothing sent yet (Bahasa Indonesia) | 1170x2532 |
| `gallery/id_light_03_progress.png` | Progress: each stage streams in, SAM 3.1 outline already on the photo (Bahasa Indonesia) | 1170x2532 |
| `gallery/id_light_05_result_top.png` | Result, top: object, safety level, recorded-demo badge (Bahasa Indonesia) | 1170x2532 |
| `gallery/id_light_06_diagnosis.png` | Diagnosis: likely causes with confidence (Bahasa Indonesia) | 1170x2532 |
| `gallery/id_light_07_parts.png` | Parts: SAM 3.1 masks numbered on the photo (Bahasa Indonesia) | 1170x2532 |
| `gallery/id_light_08_safety.png` | Safety: before-you-start list to tick (Bahasa Indonesia) | 1170x2532 |
| `gallery/id_light_09_step.png` | Step card (Bahasa Indonesia) | 1170x2532 |
| `gallery/id_light_10_check_fail.png` | Step check fails: photo too dark (Bahasa Indonesia) | 1170x2532 |
| `gallery/id_light_11_check_pass.png` | Step check passes on the step the photo shows (Bahasa Indonesia) | 1170x2532 |
| `gallery/id_light_12_hands_free.png` | Hands-free voice bar on (Bahasa Indonesia) | 1170x2532 |
| `gallery/id_light_13_replan.png` | Re-plan: next cause after 'still broken' (Bahasa Indonesia) | 1170x2532 |
| `gallery/id_light_14_agent_log.png` | Agent log: every model call and decision (Bahasa Indonesia) | 1170x2532 |
| `gallery/id_light_15_report_actions.png` | Share, PDF report and hand-off buttons (Bahasa Indonesia) | 1170x2532 |
| `gallery/id_light_16_handoff.png` | Hand-off to a mechanic (WhatsApp text) (Bahasa Indonesia) | 1170x2532 |
| `gallery/id_light_20_red_stop.png` | Rice cooker: red safety stop, Bahasa Indonesia | 1170x2532 |
| `gallery/id_light_21_red_stop_handoff.png` | Red stop: do this now, service buttons, hand-off | 1170x2532 |
| `gallery/id_light_22_pump_result.png` | Water pump result, Bahasa Indonesia | 1170x2532 |
| `gallery/id_light_23_faucet_result_en.png` | Kitchen tap result, English | 1170x2532 |
| `gallery/id_light_24_diagram_step_en.png` | Step with a Muse Image diagram, English | 1170x2532 |
| `gallery/id_light_25_tire_result_jv.png` | Scooter tyre result, Basa Jawa | 1170x2532 |
| `gallery/id_light_26_share_page.png` | Share link page (/guide/<id>) of the pump repair | 1170x2532 |
| `gallery/id_light_27_gone_404.png` | 404: a share link whose guide was deleted (HTTP 404 page) | 1170x2532 |
| `gallery/id_light_28_garage.png` | Garage: repairs opened on this phone | 1170x2532 |
| `gallery/id_light_35_offline.png` | Offline: the bar the phone shows when it loses its connection | 1170x2532 |
| `gallery/id_light_34_error_retry.png` | Error and Retry: a real failed run (Meta API unreachable, forced for this shot) | 1170x2532 |

## Gallery: Basa Jawa, light

| File | Shows | Size |
|---|---|---|
| `gallery/jv_light_01_home.png` | First screen (Basa Jawa) | 1170x2532 |
| `gallery/jv_light_02_capture.png` | Capture: sample photo picked and the problem typed, nothing sent yet (Basa Jawa) | 1170x2532 |
| `gallery/jv_light_03_progress.png` | Progress: each stage streams in, SAM 3.1 outline already on the photo (Basa Jawa) | 1170x2532 |
| `gallery/jv_light_05_result_top.png` | Result, top: object, safety level, recorded-demo badge (Basa Jawa) | 1170x2532 |
| `gallery/jv_light_06_diagnosis.png` | Diagnosis: likely causes with confidence (Basa Jawa) | 1170x2532 |
| `gallery/jv_light_07_parts.png` | Parts: SAM 3.1 masks numbered on the photo (Basa Jawa) | 1170x2532 |
| `gallery/jv_light_08_safety.png` | Safety: before-you-start list to tick (Basa Jawa) | 1170x2532 |
| `gallery/jv_light_09_step.png` | Step card (Basa Jawa) | 1170x2532 |
| `gallery/jv_light_10_check_fail.png` | Step check fails: photo too dark (Basa Jawa) | 1170x2532 |
| `gallery/jv_light_11_check_pass.png` | Step check passes on the step the photo shows (Basa Jawa) | 1170x2532 |
| `gallery/jv_light_12_hands_free.png` | Hands-free voice bar on (Basa Jawa) | 1170x2532 |
| `gallery/jv_light_13_replan.png` | Re-plan: next cause after 'still broken' (Basa Jawa) | 1170x2532 |
| `gallery/jv_light_14_agent_log.png` | Agent log: every model call and decision (Basa Jawa) | 1170x2532 |
| `gallery/jv_light_15_report_actions.png` | Share, PDF report and hand-off buttons (Basa Jawa) | 1170x2532 |
| `gallery/jv_light_16_handoff.png` | Hand-off to a mechanic (WhatsApp text) (Basa Jawa) | 1170x2532 |

## Gallery: English, light

| File | Shows | Size |
|---|---|---|
| `gallery/en_light_01_home.png` | First screen (English) | 1170x2532 |
| `gallery/en_light_02_capture.png` | Capture: sample photo picked and the problem typed, nothing sent yet (English) | 1170x2532 |
| `gallery/en_light_03_progress.png` | Progress: each stage streams in, SAM 3.1 outline already on the photo (English) | 1170x2532 |
| `gallery/en_light_05_result_top.png` | Result, top: object, safety level, recorded-demo badge (English) | 1170x2532 |
| `gallery/en_light_06_diagnosis.png` | Diagnosis: likely causes with confidence (English) | 1170x2532 |
| `gallery/en_light_07_parts.png` | Parts: SAM 3.1 masks numbered on the photo (English) | 1170x2532 |
| `gallery/en_light_08_safety.png` | Safety: before-you-start list to tick (English) | 1170x2532 |
| `gallery/en_light_09_step.png` | Step card (English) | 1170x2532 |
| `gallery/en_light_10_check_fail.png` | Step check fails: photo too dark (English) | 1170x2532 |
| `gallery/en_light_11_check_pass.png` | Step check passes on the step the photo shows (English) | 1170x2532 |
| `gallery/en_light_12_hands_free.png` | Hands-free voice bar on (English) | 1170x2532 |
| `gallery/en_light_13_replan.png` | Re-plan: next cause after 'still broken' (English) | 1170x2532 |
| `gallery/en_light_14_agent_log.png` | Agent log: every model call and decision (English) | 1170x2532 |
| `gallery/en_light_15_report_actions.png` | Share, PDF report and hand-off buttons (English) | 1170x2532 |
| `gallery/en_light_16_handoff.png` | Hand-off to a mechanic (WhatsApp text) (English) | 1170x2532 |

## Gallery: Bahasa Indonesia, dark

| File | Shows | Size |
|---|---|---|
| `gallery/id_dark_01_home.png` | First screen (Bahasa Indonesia, dark) | 1170x2532 |
| `gallery/id_dark_02_capture.png` | Capture: sample photo picked and the problem typed, nothing sent yet (Bahasa Indonesia, dark) | 1170x2532 |
| `gallery/id_dark_03_progress.png` | Progress: each stage streams in, SAM 3.1 outline already on the photo (Bahasa Indonesia, dark) | 1170x2532 |
| `gallery/id_dark_05_result_top.png` | Result, top: object, safety level, recorded-demo badge (Bahasa Indonesia, dark) | 1170x2532 |
| `gallery/id_dark_06_diagnosis.png` | Diagnosis: likely causes with confidence (Bahasa Indonesia, dark) | 1170x2532 |
| `gallery/id_dark_07_parts.png` | Parts: SAM 3.1 masks numbered on the photo (Bahasa Indonesia, dark) | 1170x2532 |
| `gallery/id_dark_08_safety.png` | Safety: before-you-start list to tick (Bahasa Indonesia, dark) | 1170x2532 |
| `gallery/id_dark_09_step.png` | Step card (Bahasa Indonesia, dark) | 1170x2532 |
| `gallery/id_dark_10_check_fail.png` | Step check fails: photo too dark (Bahasa Indonesia, dark) | 1170x2532 |
| `gallery/id_dark_11_check_pass.png` | Step check passes on the step the photo shows (Bahasa Indonesia, dark) | 1170x2532 |
| `gallery/id_dark_12_hands_free.png` | Hands-free voice bar on (Bahasa Indonesia, dark) | 1170x2532 |
| `gallery/id_dark_13_replan.png` | Re-plan: next cause after 'still broken' (Bahasa Indonesia, dark) | 1170x2532 |
| `gallery/id_dark_14_agent_log.png` | Agent log: every model call and decision (Bahasa Indonesia, dark) | 1170x2532 |
| `gallery/id_dark_15_report_actions.png` | Share, PDF report and hand-off buttons (Bahasa Indonesia, dark) | 1170x2532 |
| `gallery/id_dark_16_handoff.png` | Hand-off to a mechanic (WhatsApp text) (Bahasa Indonesia, dark) | 1170x2532 |
| `gallery/id_dark_20_red_stop.png` | Rice cooker: red safety stop, Bahasa Indonesia (dark) | 1170x2532 |
| `gallery/id_dark_21_red_stop_handoff.png` | Red stop: do this now, service buttons, hand-off (dark) | 1170x2532 |
| `gallery/id_dark_28_garage.png` | Garage: repairs opened on this phone (dark) | 1170x2532 |

## Gallery: Static build (no server)

| File | Shows | Size |
|---|---|---|
| `gallery/static_01_home_en.png` | Static build (no server): first screen with the recorded-demo badge, English | 1170x2532 |
| `gallery/static_02_result_en.png` | Static build: recorded motorbike result, English | 1170x2532 |

## Gallery: Laptop

| File | Shows | Size |
|---|---|---|
| `gallery/laptop_home_en.png` | Laptop: phone frame plus side panel (QR code, 1-tap demo, language switch) | 2560x1600 |
| `gallery/laptop_home_en_dark.png` | Laptop: phone frame plus side panel (QR code, 1-tap demo, language switch) (dark) | 2560x1600 |

## Gallery: PDF pages and share card

| File | Shows | Size |
|---|---|---|
| `gallery/pdf_30_report_pdf_id_p1.png` | PDF report, motorbike, Bahasa Indonesia, page 1 of 4 | 910x1287 |
| `gallery/pdf_30_report_pdf_id_p2.png` | PDF report, motorbike, Bahasa Indonesia, page 2 of 4 | 910x1287 |
| `gallery/pdf_31_report_pdf_en_p1.png` | PDF report, motorbike, English, page 1 of 3 | 910x1287 |
| `gallery/pdf_31_report_pdf_en_p2.png` | PDF report, motorbike, English, page 2 of 3 | 910x1287 |
| `gallery/pdf_32_stop_pdf_p1.png` | PDF report of the red stop (rice cooker), page 1 of 3 | 910x1287 |
| `gallery/pdf_32_stop_pdf_p2.png` | PDF report of the red stop (rice cooker), page 2 of 3 | 910x1287 |
| `gallery/pdf_33_share_card_id.png` | Share card image (link preview), motorbike, Bahasa Indonesia | 1200x630 |

## Notes

- `gallery/id_light_34_error_retry.png` is a real failed run: for that one run the server's Meta API address
  pointed at a closed local port, so the app's own error message and Retry button show. Nothing reached Meta.
- `gallery/id_light_35_offline.png` is Chromium switched offline; the bar is the page's own offline handling.
- The motorbike flow is the app's recorded 1-tap demo ("Recorded demo" badge on screen). In this recording
  the model was sure of the cause (plug cap off the spark plug) in every language, so it asked no follow-up
  question. The four recorded sample sessions did not ask either, so there is no current question screen.
- 118 PNG files listed.
