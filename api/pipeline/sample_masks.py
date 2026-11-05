"""Hand-drawn part outlines for the AI-generated sample photos (offline sample mode only).

Mock SAM used to return one ellipse in a fixed box per phrase, whatever the picture. With real-looking sample
photos that looks wrong, so each sample photo has its parts outlined by hand in sample_masks.json (points in
percent of width and height). A photo is recognised by a 64-bit difference hash, which survives the resize and
re-encode the server does on upload. Any other photo (the owner's own, in mock mode) keeps the old fixed boxes.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw

LABEL = "Sample photo (AI-generated)"
MASKS_FILE = Path(__file__).with_name("sample_masks.json")
MAX_BITS = 70  # of 256: a resized or re-encoded copy differs by 0-5 bits, a live camera frame (cropped, drifting) by 30-66,
# two different sample scenes by 90+ and unrelated photos by about 128


def dhash(im: Image.Image) -> str:
    """256-bit difference hash (16 x 16 brightness steps), as 64 hex digits."""
    g = np.asarray(im.convert("L").resize((17, 16), Image.Resampling.LANCZOS), dtype=np.int16)
    bits = (g[:, 1:] > g[:, :-1]).flatten()
    return f"{int(''.join('1' if b else '0' for b in bits), 2):064x}"


@lru_cache(maxsize=1)
def _photos() -> dict[str, dict[str, Any]]:
    try:
        data: dict[str, dict[str, Any]] = json.loads(MASKS_FILE.read_text())["photos"]
    except (OSError, ValueError, KeyError):
        return {}
    return data


@lru_cache(maxsize=64)
def _match(key: str) -> str | None:
    best, name = MAX_BITS + 1, None
    h = int(key, 16)
    for n, entry in _photos().items():
        if entry.get("dhash"):
            d = bin(h ^ int(entry["dhash"], 16)).count("1")
            if d < best:
                best, name = d, n
    return name


def lookup(image_path: Path) -> dict[str, Any] | None:
    """The outlines for this photo if it is one of the sample photos, else None."""
    try:
        with Image.open(image_path) as im:
            name = _match(dhash(im))
    except OSError:
        return None
    return _photos()[name] if name else None


def _raster(shapes: list[dict[str, Any]], w: int, h: int) -> np.ndarray:
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    for sh in shapes:
        pts = [(x / 100 * w, y / 100 * h) for x, y in sh["points"]]
        if sh["type"] == "line":
            lw = max(2, int(float(sh["width"]) / 100 * w))
            d.line(pts, fill=255, width=lw, joint="curve")
            for x, y in (pts[0], pts[-1]):
                d.ellipse([x - lw / 2, y - lw / 2, x + lw / 2, y + lw / 2], fill=255)
        else:
            d.polygon(pts, fill=0 if sh["type"] == "hole" else 255)
    return np.asarray(m) > 127


def segment(entry: dict[str, Any], phrase: str, w: int, h: int) -> list[dict[str, Any]]:
    """SAM-shaped records (box plus box-local mask) for one part of a known sample photo; [] when that part
    is not in this picture, as SAM answers when nothing matches."""
    shapes = entry.get("parts", {}).get(phrase)
    if not shapes:
        return []
    full = _raster(shapes, w, h)
    ys, xs = np.nonzero(full)
    if not len(xs):
        return []
    l, t, r, b = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
    return [{"object_id": 1, "left": l, "top": t, "right": r, "bottom": b, "mask": full[t:b, l:r].astype(np.uint8),
             "mw": r - l, "mh": b - t, "confidence": 0.93}]


def box(entry: dict[str, Any], phrase: str) -> list[float] | None:
    """Normalised [x1, y1, x2, y2] around the part (what Look would hand SAM as a box prompt)."""
    shapes = entry.get("parts", {}).get(phrase)
    if not shapes:
        return None
    pts = [p for sh in shapes if sh["type"] != "hole" for p in sh["points"]]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return [round(max(0.0, min(xs)) / 100, 3), round(max(0.0, min(ys)) / 100, 3), round(min(100.0, max(xs)) / 100, 3), round(min(100.0, max(ys)) / 100, 3)]
