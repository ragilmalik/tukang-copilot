"""Draw the PWA icons (our own artwork, no third-party assets): orange tile with a white wrench.
Run: python scripts/make_icons.py  -> web/icons/icon-192.png, icon-512.png, maskable-512.png"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "web" / "icons"
ORANGE, WHITE = (255, 122, 0, 255), (255, 255, 255, 255)


def wrench(size: int, pad: float) -> Image.Image:
    """Return a size x size RGBA icon; `pad` is the safe-zone margin as a fraction (maskable needs ~0.1+)."""
    s = 4  # supersample for smooth edges
    W = size * s
    im = Image.new("RGBA", (W, W), ORANGE)
    d = ImageDraw.Draw(im)
    m = W * pad
    inner = W - 2 * m
    # handle: thick diagonal bar from bottom-left to the head
    d.line([(m + inner * 0.18, m + inner * 0.82), (m + inner * 0.62, m + inner * 0.38)], fill=WHITE, width=int(inner * 0.16))
    d.ellipse([m + inner * 0.08, m + inner * 0.72, m + inner * 0.28, m + inner * 0.92], fill=WHITE)
    # head: ring with a notch (open-ended wrench)
    cx, cy, r = m + inner * 0.66, m + inner * 0.34, inner * 0.24
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE)
    n = r * 0.42
    d.polygon([(cx - n * 0.2, cy + n * 0.2), (cx + r * 1.2, cy - r * 1.2 + n), (cx + r * 1.2 - n, cy - r * 1.2), (cx + n * 0.2, cy - n * 0.2)], fill=ORANGE)
    d.ellipse([cx - n, cy - n, cx + n, cy + n], fill=ORANGE)
    return im.resize((size, size), Image.Resampling.LANCZOS)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    wrench(192, 0.12).save(OUT / "icon-192.png")
    wrench(512, 0.12).save(OUT / "icon-512.png")
    wrench(512, 0.22).save(OUT / "maskable-512.png")
    print("icons ->", OUT)


if __name__ == "__main__":
    main()
