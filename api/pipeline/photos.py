"""Photo intake helpers: accept what real phones produce.

iPhones (and some Android cameras set to "high efficiency") save HEIC/HEIF. Browsers usually convert
these to JPEG on upload, but not always, so the server converts them itself when the optional
`pillow-heif` package is installed. Without it, HEIC is refused with a clear message instead of a
crash. Everything else (JPG, PNG, WebP, also `.jfif`) goes straight through Pillow."""
from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image, ImageOps

log = logging.getLogger("tukang.photos")

HEIF_EXTS = {".heic", ".heif"}
BASE_EXTS = {".jpg", ".jpeg", ".jfif", ".png", ".webp"}

HEIF_OK = False
try:  # optional dependency
    from pillow_heif import register_heif_opener

    register_heif_opener()
    HEIF_OK = True
except Exception:  # pragma: no cover - depends on the environment
    log.info("pillow-heif not installed: HEIC photos will be refused with a friendly message")


def allowed_exts() -> set[str]:
    """Extensions the upload endpoints accept (HEIC is listed so it can get a friendly refusal)."""
    return BASE_EXTS | HEIF_EXTS


def is_heif(path: Path) -> bool:
    return path.suffix.lower() in HEIF_EXTS


def heif_to_jpeg(src: Path) -> Path:
    """Convert a HEIC/HEIF file to a JPEG next to it (EXIF rotation applied). Raises OSError if it
    cannot be read or the optional decoder is missing."""
    if not HEIF_OK:
        raise OSError("HEIC photos are not supported on this server. Set the phone camera to JPG, or take a screenshot of the photo.")
    dst = src.with_suffix(".jpg")
    with Image.open(src) as im:
        ImageOps.exif_transpose(im).convert("RGB").save(dst, "JPEG", quality=90)
    return dst
