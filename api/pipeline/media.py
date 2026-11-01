"""Audio and video helpers.

* `extract_frames`: a 5-10 s phone video -> the 3 sharpest frames (one per third of the clip), used as photos.

* `to_wav`: any phone recording -> mono 16-bit PCM WAV, the format Muse Voice Transcribe accepts.
* `speak`: step narration. Meta Model API has no text-to-speech (Muse Voice Transcribe is speech-to-text
  only, https://dev.meta.ai/docs/models), so narration uses the free Microsoft Edge neural voices via `edge-tts`
  (it has both an Indonesian and a Javanese voice). If that fails, the browser's own speech voice reads the step.
"""
from __future__ import annotations

import asyncio
import logging
import shutil
import subprocess
import re
import tempfile
import wave
from pathlib import Path

import numpy as np
from PIL import Image

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


MAX_VIDEO_SECONDS = 30.0


def video_seconds(src: Path) -> float:
    """Clip length from ffmpeg's own header read (works with the bundled ffmpeg, which has no ffprobe)."""
    p = subprocess.run([ffmpeg_exe(), "-hide_banner", "-i", str(src)], capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", p.stderr)
    if not m:
        raise RuntimeError("Could not read that video. Try a short MP4 or take photos instead.")
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


def sharpness(img: Image.Image) -> float:
    """Variance of a Laplacian on the grey image: higher = sharper (less motion blur)."""
    g = np.asarray(img.convert("L").resize((320, int(320 * img.height / max(1, img.width)))), dtype=np.float32)
    lap = -4 * g[1:-1, 1:-1] + g[:-2, 1:-1] + g[2:, 1:-1] + g[1:-1, :-2] + g[1:-1, 2:]
    return float(lap.var())


def extract_frames(src: Path, out_dir: Path, n: int = 3, per_part: int = 4, max_px: int = 1536) -> list[Path]:
    """Sample n*per_part frames evenly across the clip in a single ffmpeg call, then keep the sharpest frame
    of each of the n equal parts, so the photos cover the whole clip and avoid motion blur."""
    dur = video_seconds(src)
    if dur <= 0.2:
        raise RuntimeError("That video is too short. Record 5-10 seconds.")
    if dur > MAX_VIDEO_SECONDS:
        raise RuntimeError(f"That video is too long ({dur:.0f} s). Record 5-10 seconds.")
    total = n * per_part
    fps = total / dur
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        p = subprocess.run([ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y", "-i", str(src), "-an",
                            "-vf", f"fps={fps:.5f},scale='min({max_px},iw)':-2", "-frames:v", str(total), "-q:v", "3",
                            str(Path(td) / "f%03d.jpg")], capture_output=True, text=True)
        cands = sorted(Path(td).glob("f*.jpg"))
        if p.returncode != 0 or not cands:
            raise RuntimeError("Could not read that video. Try a short MP4 or take photos instead.")
        size = max(1, len(cands) // n)
        out: list[Path] = []
        for i in range(n):
            part = cands[i * size:(i + 1) * size] if i < n - 1 else cands[i * size:]
            if not part:
                continue
            best = max(part, key=lambda c: sharpness(Image.open(c)))
            dst = out_dir / f"video_frame{i + 1}.jpg"
            Image.open(best).convert("RGB").save(dst, "JPEG", quality=90)
            out.append(dst)
    return out


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
