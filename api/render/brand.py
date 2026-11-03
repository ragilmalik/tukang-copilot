"""The app's look for everything drawn with Pillow (PDF report, workshop sheets, share card): Barlow and Barlow
Condensed (OFL, the same fonts as web/fonts, kept here as TTF so Pillow never needs WOFF2 support) and the safety
colours from web/style.css. A character Barlow does not have (an arrow, a model writing "≥") is drawn with DejaVu
instead of an empty box."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from PIL import ImageDraw, ImageFont

FONTS = Path(__file__).parent / "fonts"
RGB = tuple[int, int, int]

# web/style.css tokens (light theme)
BETON: RGB = (232, 233, 229)
PLATE: RGB = (255, 255, 255)
PLATE_2: RGB = (243, 244, 241)
DARK: RGB = (34, 38, 43)
DARK_2: RGB = (46, 51, 57)
INK: RGB = (26, 29, 33)
MUTED: RGB = (79, 86, 94)
LINE: RGB = (214, 216, 212)
ORANGE: RGB = (255, 106, 19)
ORANGE_LEDGE: RGB = (184, 74, 8)
ORANGE_TEXT: RGB = (163, 63, 6)
RED: RGB = (200, 32, 30)
RED_TINT: RGB = (252, 233, 231)
YELLOW: RGB = (255, 194, 26)
YELLOW_TINT: RGB = (255, 245, 214)
GREEN: RGB = (18, 128, 74)
GREEN_TINT: RGB = (227, 243, 234)
BLUE: RGB = (29, 79, 145)
WHITE: RGB = (255, 255, 255)

# safety level -> (plate colour, text colour on it): ANSI Z535, black on yellow, white on red and green
LEVEL: dict[str, tuple[RGB, RGB]] = {"green": (GREEN, WHITE), "amber": (YELLOW, INK), "red": (RED, WHITE)}

_FILES = {"body": "barlow-400.ttf", "semi": "barlow-600.ttf", "cond": "barlow-condensed-700.ttf", "display": "barlow-condensed-800.ttf"}
# code points every bundled Barlow file has (latin subset); anything else falls back to DejaVu
_COVER = ((0x20, 0x7E), (0xA0, 0xFF), (0x131, 0x131), (0x152, 0x153), (0x2013, 0x2014), (0x2018, 0x201A), (0x201C, 0x201E),
          (0x2022, 0x2022), (0x2026, 0x2026), (0x2032, 0x2033), (0x2039, 0x203A), (0x20AC, 0x20AC), (0x2122, 0x2122), (0x2212, 0x2212))


def covered(ch: str) -> bool:
    o = ord(ch)
    return any(a <= o <= b for a, b in _COVER)


@lru_cache(maxsize=64)
def _dejavu(size: int, bold: bool) -> Any:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    for d in ("/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/dejavu"):
        p = Path(d) / name
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default(size=size)


@lru_cache(maxsize=128)
def font(kind: str, size: int) -> Any:
    """kind: body (Barlow 400), semi (Barlow 600), cond (Barlow Condensed 700), display (Barlow Condensed 800)."""
    try:
        return ImageFont.truetype(str(FONTS / _FILES[kind]), size)
    except (OSError, KeyError):
        return _dejavu(size, kind != "body")


def _runs(text: str) -> list[tuple[str, bool]]:
    out: list[tuple[str, bool]] = []
    for ch in text:
        ok = covered(ch) or ch in "\n\t"
        if out and out[-1][1] == ok:
            out[-1] = (out[-1][0] + ch, ok)
        else:
            out.append((ch, ok))
    return out


def _fb(kind: str, size: int) -> Any:
    return _dejavu(max(8, int(size * 0.86)), kind != "body")


def length(d: ImageDraw.ImageDraw, text: str, kind: str, size: int) -> float:
    return sum(d.textlength(s, font=font(kind, size) if ok else _fb(kind, size)) for s, ok in _runs(text))


def draw(d: ImageDraw.ImageDraw, xy: tuple[float, float], text: str, kind: str, size: int, fill: Any) -> float:
    """Draw one line; returns its width. Missing glyphs come from DejaVu, nudged onto the same baseline."""
    x, y = xy
    for s, ok in _runs(text):
        f = font(kind, size) if ok else _fb(kind, size)
        d.text((x, y + (0 if ok else size * 0.12)), s, font=f, fill=fill)
        x += d.textlength(s, font=f)
    return x - xy[0]


def wrap(d: ImageDraw.ImageDraw, text: str, kind: str, size: int, width: float, max_lines: int = 0) -> list[str]:
    """Greedy word wrap by real glyph widths; with max_lines the last kept line ends in an ellipsis when cut."""
    lines: list[str] = []
    for para in (text or "").split("\n"):
        cur = ""
        for word in para.split():
            trial = f"{cur} {word}".strip()
            if length(d, trial, kind, size) <= width or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and length(d, last + "…", kind, size) > width:
            last = last[:-1].rstrip()
        lines[-1] = last + "…"
    return lines


def plate(d: ImageDraw.ImageDraw, box: tuple[float, float, float, float], fill: Any, radius: int = 22) -> None:
    d.rounded_rectangle(box, radius=radius, fill=fill)


@lru_cache(maxsize=8)
def _plate_img(side: int) -> Any:
    from PIL import Image

    with Image.open(Path(__file__).parent / "assets" / "plate.png") as im:  # the header icon (Lucide wrench, ISC)
        return im.convert("RGBA").resize((side, round(side * im.height / im.width)), Image.Resampling.LANCZOS)


def wrench_plate(img: Any, x: int, y: int, side: int) -> None:
    """Paste the app's header icon: an orange plate with a ledge and the Lucide wrench."""
    pic = _plate_img(side)
    img.paste(pic, (x, y), pic)
