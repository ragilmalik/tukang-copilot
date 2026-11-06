# Attributions

## Meta models (via Meta Model API / Baseten)
Muse Spark 1.3 / 1.2, Muse Image 1.0, Muse Voice Transcribe 1.0, SAM 3.1 and, optionally, Muse Spark Open, used under Meta's Model API terms (https://dev.meta.ai). The models generate their outputs while the app runs.

## Python libraries (requirements.txt)
| Library | License |
|---|---|
| FastAPI | MIT |
| Uvicorn | BSD-3-Clause |
| python-multipart | Apache-2.0 |
| httpx | BSD-3-Clause |
| Pillow | MIT-CMU (HPND) |
| NumPy | BSD-3-Clause |
| Pydantic | MIT |
| python-dotenv | BSD-3-Clause |
| edge-tts | LGPL-3.0 / GPL-3.0 (calls Microsoft Edge's online read-aloud voices) |
| imageio-ffmpeg | BSD-2-Clause (bundles an FFmpeg binary, LGPL/GPL) |
| meta-sam-parser | SAM License (Meta) |
| pytest, ruff (dev) | MIT |

## Browser code
`web/vendor/qrcode.js`: QR Code Generator for JavaScript by Kazuhiko Arase (MIT). Only loaded on wide screens for the laptop view's QR code.

## System
FFmpeg (LGPL/GPL), DejaVu fonts (free license) in the Docker image.

## Fonts and icons
Barlow and Barlow Condensed by Jeremy Tribby, SIL Open Font License 1.1 (https://github.com/jpt/barlow). I took the latin woff2 files (Barlow 400 and 600, Barlow Condensed 700 and 800) from the Fontsource packages and serve them myself from `web/fonts/`, so the app never calls a font CDN. The licence is in `web/fonts/OFL.txt`.

The UI icons are Lucide 1.66.0 (https://lucide.dev), ISC licence, with a few icons from Feather (MIT). `web/app.js` carries the path data for the 52 icons it uses and draws them as inline SVG; the licence text is in `web/vendor/lucide-LICENSE.txt`. The UI strings still contain emoji because the PDF, the WhatsApp text and the share text reuse them, but on screen each one is swapped for its Lucide icon.

## Assets
The app bundles no third-party images or music. The sample photos (`samples/*.jpg` and `api/tests/fixtures/sample_*.jpg`) are AI-generated with an image model, prompted for a phone shot of each broken thing; they are not real repairs, and each copy carries a "Sample photo (AI-generated), offline sample mode" tag on the picture and in its EXIF (`scripts/make_fixtures.py`). The part outlines on them are drawn by hand in `api/pipeline/sample_masks.json`. `docs/img/*` is drawn by my own code. The demo video and screenshots are mine (Ragil Artza Rozaksyah). The people-and-home stills in the video and the
marketing images (`docs/launch/broll/`, `docs/launch/scenes/`) are AI-generated from my prompts and say "AI-generated
scene" while on screen.

## Music in the demo video and the vertical clip
- Title: "Lucky Acoustic"
- Artist: Jesse Keller
- Source: https://www.jamendo.com/track/1540859
- Licence: CC BY 3.0, https://creativecommons.org/licenses/by/3.0/
- Credit line (end card, YouTube description): Music: "Lucky Acoustic" by Jesse Keller (jamendo.com/track/1540859), licensed under CC BY 3.0
- The audio file is not in this repo; the video build reads it from `DEMO_MUSIC`. I changed it only by mixing it under
  the voice-over (level, a 3 dB cut at 2.5 kHz, ducking, fades), as CC BY 3.0 allows with this credit.
- I read the licence from the Openverse record of the Jamendo track (ea4ef155-35a9-46bb-b136-4e4f8f2223d9); the
  Jamendo page I fetched showed the credits but not the licence text. Check the licence on the Jamendo page again
  before publishing the video anywhere new.

The accessibility test (`api/tests/test_playwright_a11y.py`) runs axe-core (MPL-2.0, https://github.com/dequelabs/axe-core) from a local npm install. It is only used by the test and is not shipped with the app.
