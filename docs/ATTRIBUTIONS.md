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
I don't bundle any third-party images or music. `samples/*.jpg` and `docs/img/*` are drawn by my own code in `api/pipeline/mock.py`. The demo photos and video are mine (Ragil Artza Rozaksyah).
