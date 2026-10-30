"""Audio helpers.

* `to_wav`: any phone recording -> mono 16-bit PCM WAV, the format Muse Voice Transcribe accepts.
* `speak`: step narration. Meta Model API has no text-to-speech (Muse Voice Transcribe is speech-to-text
  only, https://dev.meta.ai/docs/models), so we use free Microsoft Edge neural voices via `edge-tts`
  (has an Indonesian AND a Javanese voice). If that fails, the browser's own speech voice reads the step.
"""
from __future__ import annotations

import asyncio
import logging
import shutil
import subprocess
import wave
from pathlib import Path

log = logging.getLogger("tukang.media")
SR = 16000
VOICES = {"id": "id-ID-GadisNeural", "jv": "jv-ID-SitiNeural", "en": "en-US-JennyNeural"}


def ffmpeg_exe() -> str:
    """System ffmpeg, else the copy bundled by imageio-ffmpeg (so Windows needs no install)."""
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg

    return str(imageio_ffmpeg.get_ffmpeg_exe())


def to_wav(src: Path, dst: Path, sr: int = SR) -> Path:
    p = subprocess.run([ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y", "-i", str(src),
                        "-ac", "1", "-ar", str(sr), "-c:a", "pcm_s16le", "-map_metadata", "-1", str(dst)],
                       capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"Could not read the recording: {p.stderr[-300:]}")
    return dst


def wav_seconds(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / float(w.getframerate())


def speak(text: str, lang: str, out: Path, timeout: float = 25) -> Path | None:
    """Write an MP3 of `text`; None if edge-tts is missing or offline (the browser voice takes over)."""
    try:
        import edge_tts
    except ImportError:
        return None

    async def _run() -> None:
        await edge_tts.Communicate(text, VOICES.get(lang, VOICES["id"])).save(str(out))

    try:
        asyncio.run(asyncio.wait_for(_run(), timeout=timeout))
        return out if out.exists() and out.stat().st_size > 0 else None
    except Exception as e:
        log.warning("narration skipped: %s", e)
        return None
