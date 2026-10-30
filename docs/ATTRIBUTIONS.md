# Attributions

## Meta models (via Meta Model API / Baseten)
Muse Spark 1.3 / 1.2, Muse Image 1.0, Muse Voice Transcribe 1.0, SAM 3.1, optional Muse Spark Open. Used under Meta's Model API terms (https://dev.meta.ai). Outputs generated during use.

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

## System
FFmpeg (LGPL/GPL), DejaVu fonts (free license) in the Docker image.

## Assets
- No third-party images, icons, music or fonts are bundled. UI icons are Unicode emoji rendered by the user's device.
- `samples/*.jpg` and `docs/img/*` are drawn by `api/pipeline/mock.py` (our own code).
- Demo photos/video: taken by Ragil Artza Rozaksyah.
