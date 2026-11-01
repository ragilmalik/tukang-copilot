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

## Assets
I don't bundle any third-party images, icons, music or fonts. The UI icons are Unicode emoji, drawn by the user's own device. `samples/*.jpg` and `docs/img/*` are drawn by my own code in `api/pipeline/mock.py`. The demo photos and video are mine (Ragil Artza Rozaksyah).
