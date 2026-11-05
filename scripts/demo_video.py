"""The demo video, shot from the real app answering live from the Meta Model API: screen recordings of the phone UI, put in a phone frame on the
app's own concrete background, with Barlow captions, crossfades and a few slow zooms on the moments that matter.

Two halves, both driven by scripts/make_demo_assets.py:

  capture GROUP   Chromium (390x844 @2x, id-ID) runs one part of the story while the DevTools screencast records the
                  screen, about 50-60 frames a second while something moves. Frames go to $TMPDIR/tukang-video/clips/<scene>.
                  Groups: motor (home to SAM parts), steps (safety list to bengkel hand-off), other (live camera, red stop,
                  open weights). Each group starts its own demo server and browser, so one group fits in about a minute.
  render          60 fps frames composed with Pillow and piped to ffmpeg, one cached segment per scene (with its
                  voice-over), then joined. The vertical X clip reuses the same recordings.

Every answer on screen is a live Meta API answer (waits for the models are cut and the real wait is noted); the
photos are AI-generated sample photos, said in the corner of every frame.
"""
from __future__ import annotations

import base64
import bisect
import json
import os
import shutil
import subprocess
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "web" / "fonts"
FIX = ROOT / "api" / "tests" / "fixtures"
WORK = Path(os.environ.get("DEMO_BUILD_DIR", Path(tempfile.gettempdir()) / "tukang-video"))
CLIPS = WORK / "clips"
FPS = 60
XFADE = 0.45  # crossfade at the start of every scene, from the last frame of the one before

# design tokens (docs: work/frontend-skills/DESIGN_DIRECTION.md, web/style.css)
CONCRETE, PLATE, INK, MUTED = (232, 233, 229), (255, 255, 255), (26, 29, 33), (79, 86, 94)
ASPHALT, ASPHALT2, ON_DARK, ON_DARK_MUTED = (29, 32, 36), (39, 43, 48), (238, 240, 242), (169, 176, 184)
TONE = {"act": (255, 106, 19), "stop": (200, 32, 30), "check": (255, 194, 26), "ok": (18, 128, 74), "info": (29, 79, 145)}
DEMO_NOTE = "Live Meta API answers · 5 Nov 2026 · AI-generated sample photos"


# --- fonts and text
@lru_cache(maxsize=64)
def font(kind: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    files = {"body": "barlow-400.woff2", "semi": "barlow-600.woff2", "cond": "barlow-condensed-700.woff2", "black": "barlow-condensed-800.woff2"}
    try:
        return ImageFont.truetype(str(FONTS / files[kind]), size)
    except OSError:
        return ImageFont.truetype("DejaVuSans-Bold.ttf" if kind != "body" else "DejaVuSans.ttf", size)


MISSING = set("→✓⚠▶")  # not in the web subset of Barlow: drawn with DejaVu Sans at the same size


@lru_cache(maxsize=32)
def _fallback(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    return ImageFont.truetype("DejaVuSans.ttf", int(size * 0.92))


def _runs(text: str) -> list[tuple[str, bool]]:
    runs: list[tuple[str, bool]] = []
    for ch in text:
        miss = ch in MISSING
        if runs and runs[-1][1] == miss:
            runs[-1] = (runs[-1][0] + ch, miss)
        else:
            runs.append((ch, miss))
    return runs


def tlen(d: ImageDraw.ImageDraw, text: str, f: Any) -> float:
    return sum(d.textlength(r, font=_fallback(f.size) if miss else f) for r, miss in _runs(text))


def draw_text(d: ImageDraw.ImageDraw, xy: tuple[float, float], text: str, f: Any, fill: Any) -> None:
    x, y = xy
    for r, miss in _runs(text):
        ff = _fallback(f.size) if miss else f
        d.text((x, y + (f.size * 0.12 if miss else 0)), r, font=ff, fill=fill)
        x += d.textlength(r, font=ff)


def wrap(text: str, f: Any, width: int) -> list[str]:
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    lines: list[str] = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split():
            t = (cur + " " + word).strip()
            if tlen(d, t, f) <= width or not cur:
                cur = t
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
    return lines


def text_block(d: ImageDraw.ImageDraw, xy: tuple[float, float], text: str, f: Any, width: int, fill: Any, lh: float,
               align: str = "left") -> float:
    """Draw wrapped text; returns the y under the last line."""
    x, y = xy
    for ln in wrap(text, f, width):
        dx = (width - tlen(d, ln, f)) / 2 if align == "center" else 0
        draw_text(d, (x + dx, y), ln, f, fill)
        y += lh
    return y


def ease(k: float) -> float:
    k = min(1.0, max(0.0, k))
    return 4 * k * k * k if k < 0.5 else 1 - (-2 * k + 2) ** 3 / 2


# --- backgrounds and brand
@lru_cache(maxsize=4)
def concrete(w: int, h: int) -> Image.Image:
    """The app's laptop page: concrete grey with a fine dot grid."""
    im = Image.new("RGB", (w, h), CONCRETE)
    d = ImageDraw.Draw(im)
    for y in range(12, h, 24):
        for x in range(12, w, 24):
            d.ellipse([x - 1.2, y - 1.2, x + 1.2, y + 1.2], fill=(204, 206, 200))
    return im


@lru_cache(maxsize=4)
def asphalt(w: int, h: int) -> Image.Image:
    """Dark title cards: asphalt with a soft light falloff and a little grain."""
    import numpy as np

    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((xx - w * 0.32) / w) ** 2 + ((yy - h * 0.45) / h) ** 2)
    k = np.clip(1 - r * 1.4, 0, 1)[..., None]
    base = np.array(ASPHALT, np.float32) * (1 - k) + np.array(ASPHALT2, np.float32) * k
    base += np.random.default_rng(3).normal(0, 2.2, base.shape)
    return Image.fromarray(np.clip(base, 0, 255).astype("uint8"))


@lru_cache(maxsize=8)
def logo(size: int) -> Image.Image:
    """The orange plate with the Lucide wrench, as in the app header (rendered from the app by `capture`)."""
    p = CLIPS / "logo.png"
    if p.exists():
        im = Image.open(p).convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)
        im.putalpha(ImageChops.multiply(im.getchannel("A"), _round_mask(size, size, int(size * 0.24))))
        return im
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, size - 1, size - 1], radius=size // 4, fill=TONE["act"] + (255,))
    return im


def brand_row(im: Image.Image, x: int, y: int, dark: bool = False, size: int = 52) -> None:
    d = ImageDraw.Draw(im)
    im.paste(logo(size), (x, y), logo(size))
    d.text((x + size + 16, y + size / 2), "Tukang Copilot", font=font("black", int(size * 0.86)), fill=ON_DARK if dark else INK, anchor="lm")


def pill(im: Image.Image, xy: tuple[int, int], text: str, f: Any, fg: Any, bg: Any, pad: tuple[int, int] = (14, 7)) -> int:
    d = ImageDraw.Draw(im)
    x, y = xy
    w = d.textlength(text, font=f)
    a, b = f.getmetrics() if hasattr(f, "getmetrics") else (f.size, 0)
    h = a + b
    d.rounded_rectangle([x, y, x + w + 2 * pad[0], y + h + 2 * pad[1]], radius=(h + 2 * pad[1]) // 2, fill=bg)
    d.text((x + pad[0], y + pad[1]), text, font=f, fill=fg)
    return int(x + w + 2 * pad[0])


# --- the phone
@dataclass
class Phone:
    """Where the phone sits at zoom 1: screen top-left (cx, cy is the frame centre) and CSS-pixel scale."""
    cx: float
    top: float
    scale: float = 1.0
    strip: int = 36      # status strip above the app (holds the island)
    bezel: int = 13
    radius: int = 62

    @property
    def w(self) -> float:
        return (390 + 2 * self.bezel) * self.scale

    @property
    def h(self) -> float:
        return (844 + self.strip + 2 * self.bezel) * self.scale

    def css_to_canvas(self, x: float, y: float) -> tuple[float, float]:
        """A point of the app viewport (CSS px) at zoom 1."""
        left = self.cx - self.w / 2 + self.bezel * self.scale
        return left + x * self.scale, self.top + (self.bezel + self.strip + y) * self.scale


@lru_cache(maxsize=8)
def _body(scale_key: int) -> tuple[Image.Image, Image.Image]:
    """Phone body (dark bezel) and its soft shadow, drawn at 2x for clean edges when zoomed."""
    s = 2.0
    bz, strip, rad = 13, 36, 62
    w, h = int((390 + 2 * bz) * s), int((844 + strip + 2 * bz) * s)
    body = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(body)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=int(rad * s), fill=(20, 22, 25, 255))
    d.rounded_rectangle([3 * s, 3 * s, w - 1 - 3 * s, h - 1 - 3 * s], radius=int((rad - 3) * s), outline=(58, 62, 68, 255), width=int(2 * s))
    pad = 90
    sh = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([pad, pad + 24, pad + w, pad + h + 24], radius=int(rad * s), fill=(20, 22, 26, 95))
    return body, sh.filter(ImageFilter.GaussianBlur(34))


@lru_cache(maxsize=32)
def _round_mask(w: int, h: int, r: int) -> Image.Image:
    m = Image.new("L", (w * 2, h * 2), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w * 2 - 1, h * 2 - 1], radius=r * 2, fill=255)
    return m.resize((w, h), Image.Resampling.LANCZOS)


def draw_phone(canvas: Image.Image, ph: Phone, screen: Image.Image, z: float = 1.0, focus: tuple[float, float] | None = None,
               target: tuple[float, float] | None = None, alpha: float = 1.0) -> None:
    """Paste the phone with `screen` (780x1688 frame of the app) into canvas, zoomed by z around focus (canvas px),
    with the focus point moved to target."""
    fx, fy = focus or (ph.cx, ph.top + ph.h / 2)
    tx, ty = target or (fx, fy)

    def tr(x: float, y: float) -> tuple[float, float]:
        return tx + z * (x - fx), ty + z * (y - fy)

    x0, y0 = tr(ph.cx - ph.w / 2, ph.top)
    W, H = ph.w * z, ph.h * z
    body, shadow = _body(0)
    pad = 90 * W / body.width
    ox, oy = int(x0 - pad), int(y0 - pad)  # the layer only covers the phone and its shadow
    sw, sh_ = int(W + 2 * pad), int(H + 2 * pad)
    layer = shadow.resize((sw, sh_), Image.Resampling.BILINEAR)
    b = body.resize((max(1, int(W)), max(1, int(H))), Image.Resampling.BILINEAR)
    layer.paste(b, (int(x0) - ox, int(y0) - oy), b)
    # screen: status strip in the app's top colour, then the app frame, rounded
    sx, sy = x0 + ph.bezel * ph.scale * z, y0 + ph.bezel * ph.scale * z
    swd, shd = int(390 * ph.scale * z), int((844 + ph.strip) * ph.scale * z)
    strip_h = int(ph.strip * ph.scale * z)
    scr = Image.new("RGB", (swd, shd), screen.getpixel((6, 6)))
    scr.paste(screen.resize((swd, shd - strip_h), Image.Resampling.BILINEAR), (0, strip_h))
    d = ImageDraw.Draw(scr)
    iw, ih = 104 * ph.scale * z, 26 * ph.scale * z
    d.rounded_rectangle([swd / 2 - iw / 2, strip_h / 2 - ih / 2 - 1, swd / 2 + iw / 2, strip_h / 2 + ih / 2 - 1], radius=ih / 2, fill=(14, 15, 17))
    layer.paste(scr, (int(sx) - ox, int(sy) - oy), _round_mask(swd, shd, int((ph.radius - ph.bezel) * ph.scale * z)))
    if alpha < 1:
        layer.putalpha(ImageChops.multiply(layer.getchannel("A"), Image.new("L", layer.size, int(255 * alpha))))
    canvas.paste(layer, (ox, oy), layer)


# --- recordings
class Clip:
    """A screen recording: JPEG frames with their times, shown as a step function (hold the last frame)."""

    def __init__(self, key: str):
        self.dir = CLIPS / key
        meta = json.loads((self.dir / "index.json").read_text())
        self.times = [float(t) for t, _ in meta["frames"]]
        self.files = [self.dir / f for _, f in meta["frames"]]
        self.length = float(meta.get("length", self.times[-1] if self.times else 0))
        self.marks: dict[str, float] = meta.get("marks", {})
        self._cache: tuple[Path, Image.Image] | None = None

    def at(self, t: float) -> tuple[Path, Image.Image]:
        i = max(0, bisect.bisect_right(self.times, t) - 1)
        p = self.files[i]
        if self._cache is None or self._cache[0] != p:
            im = Image.open(p).convert("RGB")
            if im.size != (780, 1688):
                im = im.resize((780, 1688), Image.Resampling.LANCZOS)
            self._cache = (p, im)
        return self._cache


def has_clip(key: str) -> bool:
    return (CLIPS / key / "index.json").exists()


# --- zoom plans: (time s, zoom, focus y in CSS px of the 390x844 viewport); interpolated with an ease
ZOOMS: dict[str, list[tuple[float, float, float]]] = {
    "parts": [(0.0, 1.0, 300), (1.6, 1.0, 300), (3.2, 1.55, 300), (5.4, 1.55, 300), (6.4, 1.45, 300)],
    "check_pass": [(0.0, 1.0, 400), (0.5, 1.0, 400), (1.3, 1.45, 400), (2.6, 1.45, 400), (4.0, 1.0, 422)],
    "rice": [(0.0, 1.0, 300), (4.8, 1.0, 300), (6.4, 1.4, 300), (9.1, 1.46, 300)],
    "live": [(0.0, 1.0, 300), (3.0, 1.0, 300), (4.6, 1.45, 300), (9.6, 1.45, 300), (10.7, 1.3, 300)],
    "diagnosis": [(0.0, 1.0, 420), (6.6, 1.0, 420), (8.2, 1.18, 560), (9.1, 1.18, 560)],
    "ow": [(0.0, 1.0, 125), (1.0, 1.0, 125), (2.6, 1.7, 125), (6.4, 1.7, 125), (7.8, 1.0, 300)],
}


def zoom_at(key: str, t: float, plan: dict[str, list[tuple[float, float, float]]] | None = None) -> tuple[float, float]:
    kf = (plan or ZOOMS).get(key)
    if not kf:
        return 1.0, 422.0
    if t <= kf[0][0]:
        return kf[0][1], kf[0][2]
    for (t0, z0, y0), (t1, z1, y1) in zip(kf, kf[1:]):
        if t <= t1:
            k = ease((t - t0) / max(1e-6, t1 - t0))
            return z0 + (z1 - z0) * k, y0 + (y1 - y0) * k
    return kf[-1][1], kf[-1][2]


# --- scene frames
@dataclass
class Shot:
    """What a scene needs to draw: the Scene from make_demo_assets plus its length and sentence timings."""
    sc: Any
    dur: float
    subs: list[tuple[float, float, str]]  # (start, end, sentence)


def _panel(sc: Any, sub: str, size: tuple[int, int]) -> Image.Image:
    """Concrete page + side panel (brand, headline, caption, voice caption) for a phone scene, landscape."""
    w, h = size
    im = concrete(w, h).copy()
    d = ImageDraw.Draw(im)
    x, width = 1010, 790
    brand_row(im, x, 92, size=50)
    pill(im, (x, 168), DEMO_NOTE, font("body", 22), MUTED, PLATE)
    head = sc.head or sc.caption
    hf = font("black", 92)
    lines = wrap(head, hf, width)
    y = 300
    d.rectangle([x - 34, y + 8, x - 24, y + 8 + len(lines) * 88 - 14], fill=TONE.get(sc.tone, TONE["act"]))
    for ln in lines:
        draw_text(d, (x, y), ln, hf, INK)
        y += 88
    text_block(d, (x, y + 22), sc.caption, font("body", 34), width - 20, MUTED, 46)
    if sub:
        _subtitle(im, sub, x - 34, 1000, width + 34)
    return im


def _subtitle(im: Image.Image, text: str, x: int, bottom: int, width: int, size: int = 33) -> None:
    d = ImageDraw.Draw(im)
    f = font("body", size)
    lines = wrap(text, f, width - 56)
    lh = int(size * 1.36)
    top = bottom - lh * len(lines) - 40
    d.rounded_rectangle([x, top, x + width, bottom], radius=20, fill=INK)
    y = top + 20
    for ln in lines:
        draw_text(d, (x + 28, y), ln, f, (244, 245, 246))
        y += lh


def _sub_at(shot: Shot, t: float) -> str:
    for a, b, s in shot.subs:
        if a <= t < b:
            return s
    return shot.subs[-1][2] if shot.subs and t >= shot.subs[-1][0] else ""


LAND_PHONE = Phone(cx=590, top=(1080 - 906) / 2)


class Renderer:
    """Frame source for one scene. frame(t) returns an RGB image of `size`."""

    def __init__(self, shot: Shot, size: tuple[int, int], vertical: bool = False, clip_offset: float = 0.0,
                 zooms: dict[str, list[tuple[float, float, float]]] | None = None):
        self.shot, self.size, self.vertical = shot, size, vertical
        self.sc = shot.sc
        self.offset = clip_offset
        self.zooms = zooms
        self.clip = Clip(self.sc.key) if has_clip(self.sc.key) and not self.sc.image.startswith(("title:", "wa:", "arch")) else None
        self._bg_cache: dict[str, Image.Image] = {}
        self._still: Image.Image | None = None
        self._last: tuple[Any, Image.Image] | None = None

    # backgrounds with text, cached per voice sentence
    def _bg(self, sub: str) -> Image.Image:
        if sub not in self._bg_cache:
            self._bg_cache[sub] = (_vpanel if self.vertical else _panel)(self.sc, sub, self.size)
        return self._bg_cache[sub]

    def _screen(self, t: float) -> tuple[Any, Image.Image]:
        if self.clip is not None:
            return self.clip.at(t + self.offset)
        if self._still is None:
            from make_demo_assets import SHOTS  # type: ignore[import-not-found]

            self._still = Image.open(SHOTS / f"{self.sc.image}.png").convert("RGB").resize((780, 1688), Image.Resampling.LANCZOS)
        return "still", self._still

    def frame(self, t: float) -> Image.Image:
        img = self.sc.image
        if img.startswith("title:"):
            if self.sc.key != "hook" and t > 2.2:  # every fade is done: the card no longer changes
                if self._last is None or self._last[0] != "card":
                    self._last = ("card", card(self.sc, t, self.shot, self.size, self.vertical))
                return self._last[1]
            return card(self.sc, t, self.shot, self.size, self.vertical)
        if img == "arch":
            return arch_card(self.shot, t, self.size, self.vertical)
        if img.startswith("wa:"):
            return wa_card(self.shot, t, self.size, self.vertical)
        sub = self.shot.subs and (self.shot.subs[0][2] if self.vertical else _sub_at(self.shot, t)) or ""
        key, screen = self._screen(t)
        z, fy = zoom_at(self.sc.key, t, self.zooms)
        cache_key = (key, sub, round(z, 4), round(fy, 1))
        if self._last is not None and self._last[0] == cache_key:
            return self._last[1]
        im = self._bg(sub).copy()
        ph = VERT_PHONE if self.vertical else LAND_PHONE
        fx, fyc = ph.css_to_canvas(195, fy)
        k = min(1.0, (z - 1) / 0.35) if z > 1 else 0.0
        mid = (ph.top + ph.h / 2) if not self.vertical else (ph.top + ph.h / 2)
        draw_phone(im, ph, screen, z, (fx, fyc), (fx, fyc + (mid - fyc) * k))
        self._last = (cache_key, im)
        return im


# --- cards (title, hook, close), WhatsApp and the architecture
def _fade(t: float, start: float, dur: float = 0.7) -> float:
    return ease((t - start) / dur)


def card(sc: Any, t: float, shot: Shot, size: tuple[int, int], vertical: bool) -> Image.Image:
    w, h = size
    if sc.key == "hook":
        return hook_card(shot, t, size, vertical)
    im = asphalt(w, h).copy()
    big, small = sc.image[6:].split("|")
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x = 150 if not vertical else 90
    y = 300 if not vertical else 560
    k1, k2, k3 = _fade(t, 0.1), _fade(t, 0.45), _fade(t, 0.8)
    lw = 1000 if not vertical else 900
    if sc.key == "close" and not vertical:
        lw = 1010
    if sc.key == "close":
        brand_row(layer, x, int(y - 10 + 18 * (1 - k1)), dark=True, size=96 if not vertical else 110)
        yy = y + 170
        yy = text_block(d, (x, yy + 18 * (1 - k2)), small.replace("'", "’"), font("black", 84 if not vertical else 92), lw, ON_DARK + (int(255 * k2),), 86)
        yy = text_block(d, (x, yy + 36), sc.caption, font("body", 32 if not vertical else 38), lw - 20, ON_DARK_MUTED + (int(255 * k3),), 44)
        text_block(d, (x, yy + 18), "Recorded live on the Meta Model API, 5 Nov 2026. Model waits are cut; photos are AI-generated samples.", font("body", 26 if not vertical else 32),
                   lw, ON_DARK_MUTED + (int(200 * k3),), 36)
    else:  # opening title
        brand_row(layer, x, int(y - 40 + 18 * (1 - k1)), dark=True, size=110 if not vertical else 120)
        yy = y + 150
        yy = text_block(d, (x, yy + 18 * (1 - k2)), big.replace(". ", ".\n"), font("black", 96 if not vertical else 100), 960, ON_DARK + (int(255 * k2),), 94)
        yy = text_block(d, (x, yy + 30), small, font("body", 30 if not vertical else 36), 860, ON_DARK_MUTED + (int(255 * k3),), 42)
        xx, chip = x, font("semi", 26 if not vertical else 30)
        for name in ("Muse Spark", "SAM 3.1", "Muse Image", "Voice Transcribe"):
            xx = pill(layer, (xx, int(yy + 34)), name, chip, ON_DARK + (int(255 * k3),), (255, 255, 255, int(26 * k3))) + 12
    if not vertical and sc.key == "title":
        _title_photo(layer, t)
    if sc.key == "close":
        _close_phones(im, t, vertical)
    im.paste(layer, (0, 0), layer)
    return im


@lru_cache(maxsize=2)
def _parts_photo() -> Image.Image | None:
    p = CLIPS / "parts_photo.jpg"
    return Image.open(p).convert("RGB") if p.exists() else None


def _title_photo(layer: Image.Image, t: float) -> None:
    """The masked sample photo on a plate, right side of the title card."""
    ph = _parts_photo()
    if ph is None:
        return
    k = _fade(t, 0.3, 1.0)
    w = 640
    im = ph.resize((w, int(ph.height * w / ph.width)), Image.Resampling.LANCZOS)
    plate = Image.new("RGBA", (w + 24, im.height + 24 + 46), (39, 43, 48, int(255 * k)))
    m = _round_mask(*plate.size, 26)
    plate.paste(im, (12, 12))
    d = ImageDraw.Draw(plate)
    d.text((16, im.height + 22), "Live SAM 3.1 masks on an AI-generated sample photo", font=font("body", 21), fill=ON_DARK_MUTED + (int(255 * k),))
    plate.putalpha(ImageChops.multiply(m, Image.new("L", plate.size, int(255 * k))))
    layer.alpha_composite(plate, (1180, int(250 + 20 * (1 - k))))


def _close_phones(im: Image.Image, t: float, vertical: bool) -> None:
    """Three moments of the app on the right of the end card: parts on the photo, a passed check, the red stop."""
    from make_demo_assets import SHOTS  # type: ignore[import-not-found]

    names = ["05_parts", "08_check_pass", "11_rice_stop"]
    sc = 0.6 if not vertical else 0.56
    xs = [1300, 1540, 1780] if not vertical else [250, 540, 830]
    top = 170 if not vertical else 1080
    for i, name in enumerate(names):
        k = _fade(t, 0.4 + 0.25 * i, 0.7)
        if k <= 0:
            continue
        screen = Image.open(SHOTS / f"{name}.png").convert("RGB").resize((780, 1688), Image.Resampling.LANCZOS)
        draw_phone(im, Phone(cx=xs[i], top=top + (60 if i == 1 else 0) + 30 * (1 - k), scale=sc), screen, alpha=k)


@lru_cache(maxsize=1)
def _hook_src() -> Image.Image:
    src = Image.open(ROOT / "samples" / "motor.jpg").convert("RGB")
    return src.crop((0, int(src.height * 0.07), src.width, src.height))  # its own corner tag; this card has its own label


@lru_cache(maxsize=2)
def _hook_shade(w: int, h: int, vertical: bool) -> Image.Image:
    import numpy as np

    if not vertical:
        g = np.clip(1.0 - (np.linspace(0, 1, w) - 0.36) * 2.2, 0.08, 0.96)[None, :].repeat(h, 0)
    else:
        g = np.clip(np.linspace(0.95, 0.15, h) ** 1.3, 0.15, 0.92)[:, None].repeat(w, 1)
    a = Image.fromarray((g * 255).astype("uint8"), "L")
    sh = Image.new("RGBA", (w, h), ASPHALT + (255,))
    sh.putalpha(a)
    return sh


def hook_card(shot: Shot, t: float, size: tuple[int, int], vertical: bool) -> Image.Image:
    w, h = size
    src = _hook_src()
    z = 1.0 + 0.06 * (t / max(1.0, shot.dur))
    im = Image.new("RGB", size, ASPHALT)
    if not vertical:  # photo fills the height on the right; the text side fades into asphalt
        pw = int(h * src.width / src.height)
        cw, ch = src.width / z, src.height / z
        ph = src.resize((pw, h), Image.Resampling.BILINEAR, box=((src.width - cw) * 0.5, (src.height - ch) * 0.45, (src.width - cw) * 0.5 + cw, (src.height - ch) * 0.45 + ch))
        im.paste(ph, (w - pw, 0))
    else:
        scale = max(w / src.width, h / src.height) * z
        cw, ch = w / scale, h / scale
        x0 = min(max(0.0, src.width * 0.48 - cw / 2), src.width - cw)
        im = src.resize((w, h), Image.Resampling.BILINEAR, box=(x0, 0, x0 + cw, ch))
    im = Image.alpha_composite(im.convert("RGBA"), _hook_shade(w, h, vertical)).convert("RGB")
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    big, small = shot.sc.image[6:].split("|")
    x, y = (140, 210) if not vertical else (80, 220)
    k1, k2, k3 = _fade(t, 0.1), _fade(t, 0.6), _fade(t, 1.2)
    yy = text_block(d, (x, y + 20 * (1 - k1)), big.replace(". ", ".\n"), font("black", 128 if not vertical else 120), 1000, ON_DARK + (int(255 * k1),), 120)
    yy = text_block(d, (x, yy + 34), small, font("body", 40), 900, ON_DARK + (int(235 * k2),), 52)
    d.rectangle([x, yy + 34, x + 10, yy + 34 + 44], fill=TONE["act"] + (int(255 * k3),))
    text_block(d, (x + 28, yy + 34), shot.sc.caption, font("semi", 32), 860, ON_DARK + (int(255 * k3),), 44)
    pill(layer, (w - 470 if not vertical else 60, h - 70 if not vertical else 120), "Sample photo (AI-generated)", font("body", 22),
         ON_DARK, (20, 22, 26, 170))
    im.paste(layer, (0, 0), layer)
    sub = _sub_at(shot, t) if not vertical else ""
    if sub:
        _subtitle(im, sub, x - 10, h - 110, 1000)
    return im


def wa_card(shot: Shot, t: float, size: tuple[int, int], vertical: bool) -> Image.Image:
    from make_demo_assets import SHOTS, WA_LABELS  # type: ignore[import-not-found]

    sc = shot.sc
    sub = (_sub_at(shot, t) if not vertical else "")
    im = (_panel(sc, sub, size) if not vertical else _vpanel(sc, shot.subs[0][2] if shot.subs else "", size)).copy()
    names = sc.image[3:].split(",")
    scale = 0.62 if not vertical else 0.80
    gap = 34 if not vertical else 10
    ph_w = (390 + 26) * scale
    total = len(names) * ph_w + (len(names) - 1) * gap
    x_start = (930 - total) / 2 + 20 if not vertical else (size[0] - total) / 2
    top = 250 if not vertical else 620
    d = ImageDraw.Draw(im)
    for i, name in enumerate(names):
        k = _fade(t, 0.15 + 0.35 * i, 0.6)
        if k <= 0:
            continue
        cx = x_start + i * (ph_w + gap) + ph_w / 2
        ph = Phone(cx=cx, top=top + 30 * (1 - k), scale=scale)
        screen = Image.open(SHOTS / f"{name}.png").convert("RGB").resize((780, 1688), Image.Resampling.LANCZOS)
        draw_phone(im, ph, screen, alpha=k)
        lab = WA_LABELS[i] if i < len(WA_LABELS) else ""
        lf = font("semi", 26 if not vertical else 24)
        d.text((cx - d.textlength(lab, font=lf) / 2, top - 52), lab, font=lf, fill=INK + (int(255 * k),))
    if not vertical:
        d.text((x_start, top + (906 * scale) + 30), "WhatsApp simulator (/wa) · same handler as the Cloud API webhook · live Meta answers",
               font=font("body", 22), fill=MUTED)
    return im


def arch_card(shot: Shot, t: float, size: tuple[int, int], vertical: bool) -> Image.Image:
    from make_demo_assets import ARCH  # type: ignore[import-not-found]

    w, h = size
    a = Image.open(ARCH).convert("RGB")
    if not vertical:
        # the diagram's own footnotes sit near the bottom: shrink it a little so the caption box never covers them
        z = 0.86 + 0.02 * ease(t / max(1.0, shot.dur))
        dw, dh = int(w * z), int(h * z)
        im = concrete(w, h).copy()
        im.paste(a.resize((dw, dh), Image.Resampling.BILINEAR), ((w - dw) // 2, max(0, int(h * 0.88) - dh - 8)))
        sub = _sub_at(shot, t)
        if sub:
            _subtitle(im, sub, 260, h - 36, w - 520)
        return im
    im = _vpanel(shot.sc, shot.subs[0][2] if shot.subs else "", size).copy()
    aw = w - 40
    im.paste(a.resize((aw, int(a.height * aw / a.width)), Image.Resampling.LANCZOS), (20, 700))
    return im


# --- vertical (9:16) layout
VERT_PHONE = Phone(cx=540, top=430, scale=1.3)


def _vpanel(sc: Any, sub: str, size: tuple[int, int]) -> Image.Image:
    w, h = size
    im = concrete(w, h).copy()
    d = ImageDraw.Draw(im)
    brand_row(im, 80, 70, size=56)
    pill(im, (80, 150), DEMO_NOTE, font("body", 24), MUTED, PLATE)
    hf = font("black", 74)
    y = 225
    lines = wrap(sc.caption, hf, w - 180)[:3]
    d.rectangle([60, y + 8, 70, y + 8 + len(lines) * 72 - 12], fill=TONE.get(sc.tone, TONE["act"]))
    for ln in lines:
        draw_text(d, (90, y), ln, hf, INK)
        y += 72
    if sub:
        _subtitle(im, sub, 60, h - 80, w - 120, size=40)
    return im


# --- encode
def render_segment(shot: Shot, out: Path, size: tuple[int, int], audio: Path | None, prev_last: Path | None,
                   renderer: Renderer, last_png: Path) -> None:
    """Pipe 60 fps frames into ffmpeg (H.264, CRF 18) with the scene's voice-over; save the last frame for the next crossfade."""
    n = int(round(shot.dur * FPS))
    a_in = ["-i", str(audio)] if audio else ["-f", "lavfi", "-t", f"{shot.dur:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
    fade_out = max(0.0, shot.dur - 0.12)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{size[0]}x{size[1]}", "-r", str(FPS), "-i", "-",
           *a_in, "-filter_complex", f"[1:a]aresample=48000,apad=whole_dur={shot.dur:.3f},afade=t=in:d=0.04,afade=t=out:st={fade_out:.3f}:d=0.12[a]",
           "-map", "0:v", "-map", "[a]", "-t", f"{shot.dur:.3f}",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS), "-g", str(FPS * 2),
           "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2", str(out) + ".part.mp4"]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    assert p.stdin is not None
    prev = Image.open(prev_last).convert("RGB").resize(size) if prev_last and prev_last.exists() else None
    last: Image.Image | None = None
    for i in range(n):
        t = i / FPS
        im = renderer.frame(t)
        if prev is not None and t < XFADE:
            im = Image.blend(prev, im, ease(t / XFADE))
        p.stdin.write(im.tobytes())
        last = im
    p.stdin.close()
    if p.wait() != 0:
        raise SystemExit(f"ffmpeg failed on {out.name}")
    os.replace(str(out) + ".part.mp4", out)
    if last is not None:
        last.save(last_png)


# --- capture (Playwright + DevTools screencast)
TAP_JS = """(() => {
  window.__ss = (y, ms) => new Promise((r) => { document.documentElement.style.scrollBehavior = 'auto'; const y0 = scrollY, t0 = performance.now();
    const f = (t) => { const k = Math.min(1, (t - t0) / ms); const e = k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
      scrollTo(0, y0 + (y - y0) * e); k < 1 ? requestAnimationFrame(f) : r(); }; requestAnimationFrame(f); });
  addEventListener('pointerdown', (e) => {
    const d = document.createElement('div');
    d.style.cssText = `position:fixed;left:${e.clientX - 24}px;top:${e.clientY - 24}px;width:48px;height:48px;border-radius:50%;` +
      'background:rgba(26,29,33,.22);border:2px solid rgba(255,255,255,.85);pointer-events:none;z-index:2147483647;' +
      'transition:transform .5s ease-out,opacity .5s ease-out';
    document.body.appendChild(d);
    requestAnimationFrame(() => { d.style.transform = 'scale(1.7)'; d.style.opacity = '0'; });
    setTimeout(() => d.remove(), 650);
  }, true);
})();"""


class Recorder:
    def __init__(self, ctx: Any, pg: Any):
        self.pg = pg
        self.cdp = ctx.new_cdp_session(pg)
        self.frames: list[tuple[float, bytes]] = []
        self.t0 = 0.0
        self.marks: dict[str, float] = {}
        self.cuts: list[tuple[float, float]] = []
        self.waits: list[float] = []
        self.cdp.on("Page.screencastFrame", self._on)

    def _on(self, ev: dict[str, Any]) -> None:
        self.frames.append((float(ev["metadata"]["timestamp"]), base64.b64decode(ev["data"])))
        try:
            self.cdp.send("Page.screencastFrameAck", {"sessionId": ev["sessionId"]})
        except Exception:
            pass

    def start(self) -> None:
        self.frames = []
        self.marks = {}
        self.cuts = []
        self.waits = []
        first = self.pg.screenshot(type="jpeg", quality=92)
        self.t0 = time.time()
        self.frames.append((self.t0, first))
        self.cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 92, "maxWidth": 780, "maxHeight": 1688, "everyNthFrame": 1})

    def mark(self, name: str) -> None:
        self.marks[name] = self.now()

    def now(self) -> float:
        """Scene clock: wall time since start minus the model waits cut out so far."""
        return time.time() - self.t0 - sum(b - a for a, b in self.cuts)

    def cut(self, wait: Callable[[], Any], keep: float = 0.8) -> None:
        """Run a wait for a live model answer and cut it from the clip, keeping `keep` seconds of the spinner at each
        end. The real wait is printed and kept in index.json ("cuts"), so the video can say how long it really took."""
        a = time.time()
        wait()
        b = time.time()
        if b - a > 2 * keep + 0.5:
            self.cuts.append((a + keep, b - keep))
            self.waits.append(round(b - a, 1))

    def stop(self, key: str, length: float) -> None:
        self.cdp.send("Page.stopScreencast")
        out = CLIPS / key
        shutil.rmtree(out, ignore_errors=True)
        out.mkdir(parents=True)
        rows = []
        cuts = sorted(self.cuts)
        for i, (ts, data) in enumerate(sorted(self.frames, key=lambda f: f[0])):
            if any(a < ts < b for a, b in cuts):
                continue  # inside a cut-out model wait
            t = max(0.0, ts - self.t0 - sum(b - a for a, b in cuts if b <= ts))
            name = f"f{i:05}.jpg"
            (out / name).write_bytes(data)
            rows.append([round(t, 4), name])
        (out / "index.json").write_text(json.dumps({"frames": rows, "length": length, "marks": self.marks, "live_waits_s": self.waits}))
        print(f"clip {key}: {len(rows)} frames, {length:.1f}s, live model waits cut: {self.waits}", flush=True)


def run_scene(rec: Recorder, key: str, length: float, actions: Callable[[Callable[[float], None]], None]) -> None:
    """Record `length` seconds; actions get wait_until(t) to place each step on the scene clock."""
    rec.start()

    def wait_until(t: float) -> None:
        left = t - rec.now()
        if left > 0:
            rec.pg.wait_for_timeout(int(left * 1000))

    actions(wait_until)
    wait_until(length)
    rec.stop(key, length)


LIVE_MS = 240_000  # live Meta answers take up to a couple of minutes; the wait is cut from the clip (Recorder.cut)
# the plan step whose finished state the sample after-photo shows (spark plug cap pushed back on)
CAP_STEP_JS = """(() => { const st = (S && S.plan && S.plan.steps) || [];
  const hit = st.find((x) => /cop busi|plug cap|cap/i.test(x.instruction) && /(dorong|pasang|tancap|push|refit|klik)/i.test(x.instruction));
  return hit ? hit.n : 0; })()"""

# --- what each recorded scene does (scene clock in seconds; lengths come from the voice-over)
GROUPS = {"motor": ["intro", "progress", "question", "diagnosis", "parts"],
          "steps": ["preflight", "check_fail", "check_pass", "handsfree", "replan", "agent", "handoff"],
          "other": ["live", "rice", "diagram"]}


def capture(group: str, lengths: dict[str, float]) -> None:
    from playwright.sync_api import sync_playwright

    import make_demo_assets as mda  # type: ignore[import-not-found]
    from api.main import _dark_photo
    from api.settings import settings

    CLIPS.mkdir(parents=True, exist_ok=True)
    base, srv = mda._server()
    settings.mock_pace_s = 0.6
    dark = Path(tempfile.mkdtemp()) / "dark.jpg"
    dark.write_bytes(_dark_photo("motor"))
    args = ["--no-proxy-server", "--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream"]
    if group == "other":
        args.append(f"--use-file-for-fake-video-capture={mda._fake_camera_y4m(FIX / 'sample_pump_overview.jpg')}")
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=mda._chromium(), args=args)
        ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True, locale="id-ID")
        ctx.grant_permissions(["camera", "microphone"], origin=base)
        ctx.add_init_script(mda.SR_STUB)
        ctx.add_init_script(TAP_JS)
        pg = ctx.new_page()
        rec = Recorder(ctx, pg)

        def scroll_to(sel: str, off: int = -80, ms: int = 900) -> None:
            pg.evaluate("([s, o, ms]) => { const el = document.querySelector(s); const y = el.getBoundingClientRect().top + scrollY + o;"
                        " return __ss(Math.max(0, y), ms); }", [sel, off, ms])

        def scroll_by(dy: int, ms: int = 900) -> None:
            pg.evaluate("([dy, ms]) => __ss(Math.max(0, scrollY + dy), ms)", [dy, ms])

        def scroll_top(ms: int = 700) -> None:
            pg.evaluate("(ms) => __ss(0, ms)", ms)

        def tick_all(gap: int = 450) -> None:
            for box in pg.locator("#preList input").all():
                box.check()
                pg.wait_for_timeout(gap)

        def go_to_step(find_js: str) -> None:
            """Walk the step card to the step `find_js` picks from the live plan (1-based; 0 = stay)."""
            n = int(pg.evaluate(find_js) or 0)
            for _ in range(12):
                if not n or pg.inner_text("#stepNo").strip() == str(n):
                    break
                pg.click("#nextBtn" if int(pg.inner_text("#stepNo").strip() or 1) < n else "#prevBtn")
                pg.wait_for_timeout(350)

        def motor_to_result() -> None:
            settings.mock_pace_s = 0.0
            pg.goto(base + "/")
            pg.wait_for_selector("#goBtn")
            pg.set_input_files("#photo", str(FIX / "sample_motor_plug_area.jpg"))
            pg.fill("#text", "Motor saya Honda Beat susah hidup, distarter cuma bunyi tapi mesin nggak nyala.")
            pg.click("#goBtn")
            pg.wait_for_selector("#question:not(.hidden), #result:not(.hidden)", timeout=LIVE_MS)
            if pg.is_visible("#question"):
                pg.fill("#answerText", "Ya, ada bau bensin")
                pg.click("#answerBtn")
            pg.wait_for_selector("#result:not(.hidden)", timeout=LIVE_MS)
            pg.evaluate("window.scrollTo(0, 0)")
            settings.mock_pace_s = 0.6

        if group == "motor":
            pg.goto(base + "/")
            pg.wait_for_selector("#goBtn")
            pg.wait_for_timeout(600)
            logo = pg.locator(".brand .plate").first
            logo.screenshot(path=str(CLIPS / "logo.png"))

            def intro(at: Callable[[float], None]) -> None:
                at(0.6)
                scroll_to("#photoBox", -70, 1000)
                at(1.8)
                pg.set_input_files("#photo", str(FIX / "sample_motor_plug_area.jpg"))
                at(2.5)
                pg.click('#cats button[data-cat="motor"]')
                at(2.9)
                scroll_to("#text", -540, 800)
                pg.click("#text")
                pg.keyboard.type("Motor saya Honda Beat susah hidup, distarter cuma bunyi.", delay=34)
                pg.evaluate("document.activeElement && document.activeElement.blur()")

            def progress(at: Callable[[float], None]) -> None:
                at(0.3)
                pg.click("#goBtn")
                pg.wait_for_selector("#progress:not(.hidden)")
                at(0.9)
                scroll_to("#stageList", -110, 800)
                rec.cut(lambda: pg.wait_for_selector("#lf-segment img", timeout=LIVE_MS))
                pg.wait_for_function("() => document.querySelector('#lf-segment img').naturalWidth > 0", timeout=10000)
                rec.mark("sam")
                pg.wait_for_timeout(700)
                scroll_by(330, 1100)

            def question(at: Callable[[float], None]) -> None:
                rec.cut(lambda: pg.wait_for_selector("#question:not(.hidden), #result:not(.hidden)", timeout=LIVE_MS))
                if not pg.is_visible("#question"):
                    raise SystemExit("this live run did not ask a follow-up question: run `capture motor` again")
                scroll_to("#question", -120, 700)
                at(1.6)
                pg.click("#answerText")
                pg.keyboard.type("Ya, ada bau bensin", delay=60)

            def diagnosis(at: Callable[[float], None]) -> None:
                at(0.3)
                pg.click("#answerBtn")
                rec.cut(lambda: pg.wait_for_selector("#result:not(.hidden)", timeout=LIVE_MS))
                pg.evaluate("window.scrollTo(0, 0)")
                rec.mark("result")
                at(4.2)
                scroll_by(420, 1500)

            def parts(at: Callable[[float], None]) -> None:
                at(0.2)
                scroll_to("#partsWrap", -96, 1100)

            plan = {"intro": intro, "progress": progress, "question": question, "diagnosis": diagnosis, "parts": parts}
            for key in GROUPS["motor"]:
                run_scene(rec, key, lengths[key], plan[key])
            src = pg.evaluate("document.querySelector('#partsImg') && document.querySelector('#partsImg').src")
            if src:
                (CLIPS / "parts_photo.jpg").write_bytes(pg.request.get(src).body())

        elif group == "steps":
            motor_to_result()

            def preflight(at: Callable[[float], None]) -> None:
                at(0.2)
                scroll_to("#preflight", -90, 1000)
                at(1.6)
                tick_all(700)
                at(3.6)
                scroll_to("#stepCard", -70, 1000)

            def check_fail(at: Callable[[float], None]) -> None:
                at(0.6)
                pg.set_input_files("#stepPhoto", str(dark))
                rec.cut(lambda: pg.wait_for_function("() => !document.querySelector('#checkResult').textContent.includes('…')", timeout=LIVE_MS))
                at(2.0)
                scroll_to("#checkResult", -330, 900)

            def check_pass(at: Callable[[float], None]) -> None:
                at(0.2)
                go_to_step(CAP_STEP_JS)  # the after-photo shows the plug cap pushed back on: check it on that step
                pg.set_input_files("#stepPhoto", str(FIX / "sample_motor_step_cap_on.jpg"))
                pg.wait_for_timeout(500)
                rec.cut(lambda: pg.wait_for_function("() => !document.querySelector('#checkResult').textContent.includes('…')", timeout=LIVE_MS))
                rec.mark("pass")

            def handsfree(at: Callable[[float], None]) -> None:
                at(0.8)
                scroll_to("#handsFree", -420, 900)
                at(2.0)
                pg.click("#handsFree")
                pg.wait_for_selector("#voiceBar:not(.hidden)", timeout=5000)
                at(3.4)
                scroll_to("#voiceBar", -380, 900)

            def replan(at: Callable[[float], None]) -> None:
                pg.uncheck("#handsFree")
                at(0.3)
                scroll_to("#stuckText", -300, 1000)
                at(1.5)
                pg.click("#stuckText")
                pg.keyboard.type("Sudah dicoba, mesin tetap tidak nyala.", delay=26)
                at(3.2)
                pg.click("#stuckBtn")
                rec.cut(lambda: pg.wait_for_function(
                    "() => document.querySelector('#stuckMsg').textContent.length > 3 && !document.querySelector('#stuckBtn').disabled", timeout=LIVE_MS))
                pg.wait_for_selector("#planBanner:not(.hidden)")
                at(4.6)
                scroll_top(1200)

            def agent(at: Callable[[float], None]) -> None:
                at(0.2)
                scroll_to("#agent", -70, 1200)
                at(2.4)
                scroll_by(520, 4200)

            def handoff(at: Callable[[float], None]) -> None:
                at(0.2)
                scroll_to("#mechBtn", -420, 1200)
                at(1.8)
                pg.click("#mechBtn")
                pg.wait_for_selector("#handoff:not(.hidden)", timeout=10000)
                pg.evaluate("document.querySelector('#handoff details') && (document.querySelector('#handoff details').open = true)")
                at(2.6)
                scroll_to("#mechBtn", -90, 1200)
                at(5.6)
                scroll_by(320, 2200)

            plan = {"preflight": preflight, "check_fail": check_fail, "check_pass": check_pass, "handsfree": handsfree,
                    "replan": replan, "agent": agent, "handoff": handoff}
            for key in GROUPS["steps"]:
                run_scene(rec, key, lengths[key], plan[key])

        else:  # live camera on the pump, red stop on the rice cooker, open-weights badge
            settings.mock_pace_s = 0.0
            pg.goto(base + "/")
            pg.click('button.sample[data-sample="pump"]')
            pg.wait_for_selector("#result:not(.hidden)", timeout=LIVE_MS)
            for box in pg.locator("#preList input").all():
                box.check()
            pg.evaluate("document.querySelector('#stepCard').scrollIntoView({block: 'start'}); window.scrollBy(0, -70)")
            settings.mock_pace_s = 0.6

            def live(at: Callable[[float], None]) -> None:
                at(0.3)
                scroll_to("#liveBtn", -120, 900)
                at(1.6)
                pg.click("#liveBtn")
                pg.wait_for_selector("#live:not(.hidden)")
                at(2.4)
                scroll_to("#liveBtn", -90, 700)

            def rice(at: Callable[[float], None]) -> None:
                settings.mock_pace_s = 0.35
                at(0.4)
                pg.click('button.sample[data-sample="rice"]')
                rec.cut(lambda: pg.wait_for_selector("#stopBox:not(.hidden)", timeout=LIVE_MS))
                pg.evaluate("window.scrollTo(0, 0)")
                rec.mark("stop")

            def diagram(at: Callable[[float], None]) -> None:
                at(0.2)
                scroll_to("#stepCard", -70, 900)
                at(1.2)
                for _ in range(10):  # walk to the step Muse Image drew a diagram for
                    if "diagram" in (pg.get_attribute("#stepImg", "src") or "") and pg.is_visible("#stepImg"):
                        break
                    pg.click("#nextBtn")
                    pg.wait_for_timeout(500)
                pg.wait_for_timeout(300)
                scroll_to("#stepCard", -70, 700)

            run_scene(rec, "live", lengths["live"], live)
            pg.click("#liveClose")
            pg.goto(base + "/")
            pg.evaluate("document.querySelector('button.sample[data-sample=\"rice\"]').scrollIntoView({block: 'center'})")
            pg.wait_for_timeout(400)
            run_scene(rec, "rice", lengths["rice"], rice)
            # diagram: the English faucet repair, where Muse Image draws the washer swap
            pg.goto(base + "/")
            pg.select_option("#lang", "en")
            pg.wait_for_timeout(300)
            pg.click('button.sample[data-sample="faucet"]')
            pg.wait_for_selector("#result:not(.hidden)", timeout=LIVE_MS)
            for box in pg.locator("#preList input").all():
                box.check()
            pg.evaluate("window.scrollTo(0, 0)")
            run_scene(rec, "diagram", lengths["diagram"], diagram)
        b.close()
    srv.should_exit = True
