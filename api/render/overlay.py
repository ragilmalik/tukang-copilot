"""Draws SAM 3.1 masks on the user's own photo: a coloured tint and outline per part plus a numbered badge."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

PALETTE = [(255, 122, 0), (0, 168, 255), (46, 204, 113), (231, 76, 60), (155, 89, 182)]


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in ("DejaVuSans-Bold.ttf", "arialbd.ttf", "Arial Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def full_mask(seg: dict[str, Any], width: int, height: int) -> np.ndarray:
    """SAM masks are box-local (mh x mw). Scale into the box and place on a full-size boolean canvas."""
    canvas = np.zeros((height, width), dtype=bool)
    l, t = max(0, int(seg["left"])), max(0, int(seg["top"]))
    r, b = min(width, int(seg["right"])), min(height, int(seg["bottom"]))
    if r <= l or b <= t:
        return canvas
    raw = seg.get("mask")
    if raw is None:
        canvas[t:b, l:r] = True
        return canvas
    m = raw.astype(np.uint8) if isinstance(raw, np.ndarray) else np.frombuffer(bytes(raw), dtype=np.uint8)
    m = (m.reshape(seg["mh"], seg["mw"]) > 0).astype(np.uint8) * 255
    box = Image.fromarray(m, "L").resize((r - l, b - t), Image.Resampling.NEAREST)
    canvas[t:b, l:r] = np.array(box) > 127
    return canvas


def draw_parts(photo: Path, found: list[dict[str, Any]], out: Path, only: str | None = None) -> Path:
    """found: [{"id": "c1", "label": 1, "name": "cop busi", "segs": [...]}]. `only` highlights one part."""
    base = Image.open(photo).convert("RGB")
    w, h = base.size
    tint = Image.new("RGBA", base.size, (0, 0, 0, 0))
    edges = Image.new("RGBA", base.size, (0, 0, 0, 0))
    badges = []
    for i, part in enumerate(found):
        if only and part.get("id") != only:
            continue
        color = PALETTE[i % len(PALETTE)]
        union = np.zeros((h, w), dtype=bool)
        for seg in part.get("segs", [])[:3]:
            union |= full_mask(seg, w, h)
        if not union.any():
            continue
        ys, xs = np.nonzero(union)
        # Work on the part's bounding box (plus a margin for the outline) instead of the whole photo: the edge
        # filters are the slowest step of the pipeline and the result is identical outside the box.
        x0, y0 = max(0, int(xs.min()) - 4), max(0, int(ys.min()) - 4)
        x1, y1 = min(w, int(xs.max()) + 5), min(h, int(ys.max()) + 5)
        m = Image.fromarray((union[y0:y1, x0:x1] * 255).astype(np.uint8), "L")
        size = (x1 - x0, y1 - y0)
        tint.paste(Image.new("RGBA", size, color + (90,)), (x0, y0), m)
        edge = m.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(5))
        edges.paste(Image.new("RGBA", size, color + (255,)), (x0, y0), edge)
        # where the badge may go: the part pixel nearest its top-left box corner first, then the other corners
        spots = []
        for cx_, cy_ in ((xs.min(), ys.min()), (xs.max(), ys.min()), (xs.min(), ys.max()), (xs.max(), ys.max())):
            k = int(np.argmin((xs - cx_) ** 2 + (ys - cy_) ** 2))
            spots.append((int(xs[k]), int(ys[k])))
        badges.append((part["label"], spots, color))
    img = Image.alpha_composite(Image.alpha_composite(base.convert("RGBA"), tint), edges)
    d = ImageDraw.Draw(img)
    r = max(14, w // 40)
    f = _font(int(r * 1.2))
    placed: list[tuple[int, int]] = []
    for label, spots, color in badges:
        # the badge sits just above-left of the part, so it never hides a small part (a valve stem, a plug); when that
        # spot is taken by another badge (two parts sharing a corner, as a tap body and its wall flange do), it moves
        # to the part's next corner, so no number is ever hidden under another
        def at(x: int, y: int) -> tuple[int, int]:
            return min(max(x - r * 3 // 4, r), w - r), min(max(y - r * 3 // 4, r), h - r)

        cands = [at(x, y) for x, y in spots]
        free = [c for c in cands if all((c[0] - px) ** 2 + (c[1] - py) ** 2 >= (2.2 * r) ** 2 for px, py in placed)]
        cx, cy = free[0] if free else cands[0]
        if not free:  # every corner is taken: step down until clear of the others
            while any((cx - px) ** 2 + (cy - py) ** 2 < (2.2 * r) ** 2 for px, py in placed) and cy < h - r:
                cy = min(h - r, cy + r)
        placed.append((cx, cy))
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color + (255,), outline=(255, 255, 255, 255), width=3)
        d.text((cx, cy), str(label), fill=(255, 255, 255, 255), font=f, anchor="mm")
    img.convert("RGB").save(out, "JPEG", quality=90)
    return out


def normalize_photo(src: Path, dst: Path, max_side: int = 1536) -> Path:
    """Apply EXIF rotation (SAM needs the displayed size), cap at 1536 px, save JPEG."""
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    im.thumbnail((max_side, max_side))
    im.save(dst, "JPEG", quality=90)
    return dst
