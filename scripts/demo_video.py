"""The demo video, shot from the real app playing back answers recorded on the live Meta Model API: screen recordings
of the phone UI in a phone frame on the app's own concrete background, labelled AI-generated scene stills with slow
Ken Burns moves for the people-and-home parts, Barlow captions and crossfades.

Two halves, both driven by scripts/make_demo_assets.py:

  capture GROUP   Chromium (390x844 @2x, id-ID) runs one part of the story while the DevTools screencast records the
                  screen. Frames go to $TMPDIR/tukang-video/clips/<scene>. Groups: motor (home to SAM parts), steps
                  (safety list to bengkel hand-off), other (Muse Image diagram, red stop, Basa Jawa tyre). Each group
                  starts its own demo server and browser.
  render          30 fps frames composed with Pillow and piped to ffmpeg, one cached segment per scene (with its
                  voice-over), then joined; the music goes under the voice in one last mix. The vertical clip reuses
                  the same recordings.

Every answer on screen is a real Meta API answer: with DEMO_RECORDED_DATA set it is played back from answers recorded
on the live API on 6 Nov 2026 (the recorded 1-tap demo and recorded live sessions), and every phone frame says so.
The photos are AI-generated sample photos, said in their corner. Stills of people and homes are AI-generated scenes
and carry that label while they are on screen.
"""
from __future__ import annotations

import base64
import bisect
import json
import os
import shutil
import subprocess
import sys
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
FPS = 30
XFADE = 0.45  # crossfade at the start of every scene, from the last frame of the one before
LEAD = 0.2   # the voice starts this long after the cut, so the picture is there before its first word

# design tokens (docs: work/frontend-skills/DESIGN_DIRECTION.md, web/style.css)
CONCRETE, PLATE, INK, MUTED = (232, 233, 229), (255, 255, 255), (26, 29, 33), (79, 86, 94)
ASPHALT, ASPHALT2, ON_DARK, ON_DARK_MUTED = (29, 32, 36), (39, 43, 48), (238, 240, 242), (169, 176, 184)
TONE = {"act": (255, 106, 19), "stop": (200, 32, 30), "check": (255, 194, 26), "ok": (18, 128, 74), "info": (29, 79, 145)}


def recorded_on() -> str:
    """The day the answers in the clips came from the live API (written by `capture`, WIB), like "6 Nov 2026"; today
    when there are none."""
    p = CLIPS / "recorded.json"
    if p.exists():
        return str(json.loads(p.read_text())["date"])
    return _today_wib()


def played_back() -> bool:
    """True when the clips play recorded live answers (DEMO_RECORDED_DATA) instead of calling the models while filming."""
    p = CLIPS / "recorded.json"
    return p.exists() and json.loads(p.read_text()).get("source") == "recorded"


def _replay_day() -> str:
    """The day the recorded 1-tap demo was recorded on the live API, from web/replay/demo.json ("2026-11-06 14:01 WIB")."""
    from datetime import date

    d = date.fromisoformat(_replay_stamp()[:10])
    return f"{d.day} {d:%b %Y}"


def _replay_stamp() -> str:
    return str(json.loads((ROOT / "web" / "replay" / "demo.json").read_text(encoding="utf-8"))["recorded_at"])


def recorded_time() -> str:
    """The clock time of the recorded live run ("14:01 WIB"); empty for live filming."""
    stamp = _replay_stamp()
    return stamp[11:] if played_back() and len(stamp) > 11 else ""


def _today_wib() -> str:
    from datetime import datetime
    from zoneinfo import ZoneInfo

    d = datetime.now(ZoneInfo("Asia/Jakarta"))
    return f"{d.day} {d:%b %Y}"


def demo_note() -> str:
    """The pill on every phone frame: where the answers come from and that the photos are samples."""
    if played_back():
        return f"Real Meta API output, recorded live {recorded_on()} {recorded_time()} · AI-generated sample photos"
    return f"Live Meta API answers · {recorded_on()} · AI-generated sample photos"


def answers_note() -> str:
    """The line on the end card that says where the answers come from."""
    if played_back():
        return (f"App screens: real Meta API output recorded on a live run, {recorded_on()} from {recorded_time()}, "
                "played back in the app. Photos are AI-generated samples; people and homes are AI-generated scenes.")
    return f"Recorded live on the Meta Model API, {recorded_on()}. Model waits are cut; photos are AI-generated samples."


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
    pill(im, (x, 168), demo_note(), font("body", 22), MUTED, PLATE)
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
                 zooms: dict[str, list[tuple[float, float, float]]] | None = None, clip_key: str = ""):
        self.shot, self.size, self.vertical = shot, size, vertical
        self.sc = shot.sc
        self.offset = clip_offset
        self.zooms = zooms
        self.clip_key = clip_key or self.sc.key  # the vertical clip names its scenes differently from the recordings
        card_like = self.sc.image.startswith(("title:", "broll:", "still:")) or self.sc.image == "proof"
        self.clip = Clip(self.clip_key) if has_clip(self.clip_key) and not card_like else None
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
            from make_demo_assets import SHOTS

            self._still = Image.open(SHOTS / f"{self.sc.image}.png").convert("RGB").resize((780, 1688), Image.Resampling.LANCZOS)
        return "still", self._still

    def frame(self, t: float) -> Image.Image:
        img = self.sc.image
        sub = _sub_at(self.shot, t)
        if img.startswith(("broll:", "still:")):
            return broll_frame(self.shot, t, self.size, self.vertical, sub)
        if img == "proof":
            key = ("proof", sub, min(int(t * FPS), int(3.2 * FPS)))  # the rows fade in over the first 3.2 s
            if self._last is None or self._last[0] != key:
                self._last = (key, proof_card(self.shot, t, self.size, self.vertical, sub))
            return self._last[1]
        if img.startswith("title:"):
            key = ("card", sub, min(int(t * FPS), int(2.2 * FPS)))  # every fade is done by 2.2 s
            if self._last is None or self._last[0] != key:
                self._last = (key, close_card(self.sc, t, self.size, self.vertical, sub))
            return self._last[1]
        if self.vertical:
            return self._vframe(t, sub)
        key, screen = self._screen(t)
        z, fy = zoom_at(self.clip_key, t, self.zooms)
        cache_key = (key, sub, round(z, 4), round(fy, 1))
        if self._last is not None and self._last[0] == cache_key:
            return self._last[1]
        im = self._bg(sub).copy()
        ph = LAND_PHONE
        fx, fyc = ph.css_to_canvas(195, fy)
        k = min(1.0, (z - 1) / 0.35) if z > 1 else 0.0
        mid = ph.top + ph.h / 2
        draw_phone(im, ph, screen, z, (fx, fyc), (fx, fyc + (mid - fyc) * k))
        self._last = (cache_key, im)
        return im

    def _vframe(self, t: float, sub: str) -> Image.Image:
        """Vertical phone scene: background, the (maybe zoomed) phone, then the header band and the caption on top,
        so a zoom never covers the words."""
        key, screen = self._screen(t)
        z, fy = zoom_at(self.clip_key, t, self.zooms)
        cache_key = (key, sub, round(z, 4), round(fy, 1))
        if self._last is not None and self._last[0] == cache_key:
            return self._last[1]
        bg = self._bg("")
        im = bg.copy()
        ph = VERT_PHONE
        fx, fyc = ph.css_to_canvas(195, fy)
        k = min(1.0, (z - 1) / 0.35) if z > 1 else 0.0
        mid = ph.top + ph.h / 2
        draw_phone(im, ph, screen, z, (fx, fyc), (fx, fyc + (mid - fyc) * k))
        band = int(ph.top - 12)
        im.paste(bg.crop((0, 0, im.width, band)), (0, 0))
        if sub:
            vsubtitle(im, sub)
        self._last = (cache_key, im)
        return im


# --- cards: AI-generated scene stills (Ken Burns), the proof card and the end card
def _fade(t: float, start: float, dur: float = 0.7) -> float:
    return ease((t - start) / dur)


SCENE_TAG = "AI-generated scene"


def tag(im: Image.Image, text: str, right: int, bottom: int, size: int = 24) -> None:
    """Dark pill with white text in a corner, the look of the "Sample photo (AI-generated)" tag on the sample photos."""
    f = font("semi", size)
    d = ImageDraw.Draw(im, "RGBA")
    w = d.textlength(text, font=f)
    pad_x, pad_y = int(size * 0.6), int(size * 0.35)
    h = size + 2 * pad_y
    d.rounded_rectangle([right - w - 2 * pad_x, bottom - h, right, bottom], radius=h // 2, fill=(20, 22, 26, 190))
    d.text((right - w - pad_x, bottom - h + pad_y - size * 0.08), text, font=f, fill=(255, 255, 255, 245))


@lru_cache(maxsize=16)
def _source(spec: str) -> tuple[Image.Image, bool]:
    """The picture of a b-roll scene and whether it already carries its own "AI-generated scene" tag.

    "broll:<path>" is a labelled 1920x1080 still (docs/launch/broll, tag burned into the bottom-right corner);
    "still:<name>" is a scene of docs/launch/scenes with the real app screenshot warped onto its blank phone
    (docs/launch/make_marketing_images.py), made once into the build folder."""
    kind, _, ref = spec.partition(":")
    if kind == "broll":
        return Image.open(ROOT / ref).convert("RGB"), True
    return scene_still(ref), False


def scene_still(name: str) -> Image.Image:
    """A scene photo (docs/launch/scenes) at its own size with the real screenshot on the phone, cached in WORK."""
    out = WORK / "stills" / f"{name}.png"
    if not out.exists():
        import importlib.util

        spec_ = importlib.util.spec_from_file_location("make_marketing_images", ROOT / "docs" / "launch" / "make_marketing_images.py")
        assert spec_ is not None and spec_.loader is not None
        mmi = importlib.util.module_from_spec(spec_)
        sys.modules["make_marketing_images"] = mmi  # its dataclasses look their module up while the file loads
        spec_.loader.exec_module(mmi)
        spec = mmi.SPECS[name]
        base = Image.open(mmi.SCENES / spec.scene).convert("RGB")
        for box in spec.blur:  # brand names the generator painted
            base = mmi.soften(base, box)
        out.parent.mkdir(parents=True, exist_ok=True)
        mmi.warp_screen(base, spec, 1.0, (0, 0)).save(out)
    return Image.open(out).convert("RGB")


def _kb(src: Image.Image, t: float, dur: float, out: tuple[int, int], anchor: tuple[float, float], z1: float = 1.05) -> Image.Image:
    """Ken Burns: a slow push-in (1.0 to z1 over the scene) on a picture that already has the output's aspect ratio,
    anchored at `anchor` (0..1 of the picture), so that point stays put while the rest grows."""
    z = 1.0 + (z1 - 1.0) * min(1.0, t / max(1.0, dur))  # linear: a steady drift, no ease-in that reads as a jolt
    cw, ch = src.width / z, src.height / z
    x0, y0 = (src.width - cw) * anchor[0], (src.height - ch) * anchor[1]
    return src.resize(out, Image.Resampling.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))


@lru_cache(maxsize=8)
def _covered(spec: str, w: int, h: int, focus_x: float, focus_y: float) -> Image.Image:
    """The picture cropped to the output's aspect ratio (no scaling yet), cropped around the focus point."""
    src, _ = _source(spec)
    r = w / h
    if src.width / src.height > r:
        cw, ch = src.height * r, float(src.height)
    else:
        cw, ch = float(src.width), src.width / r
    x0, y0 = (src.width - cw) * focus_x, (src.height - ch) * focus_y
    return src.crop((round(x0), round(y0), round(x0 + cw), round(y0 + ch)))


@lru_cache(maxsize=4)
def _blur_bg(spec: str, w: int, h: int) -> Image.Image:
    """A blurred, darkened copy of a picture that does not have the frame's shape, to fill the frame behind it."""
    from PIL import ImageEnhance

    return ImageEnhance.Brightness(_covered(spec, w, h, 0.5, 0.5).resize((w, h), Image.Resampling.BILINEAR)
                                   .filter(ImageFilter.GaussianBlur(40))).enhance(0.45)


@lru_cache(maxsize=2)
def _left_shade(w: int, h: int) -> Image.Image:
    """Dark gradient on the left 60 % of a 16:9 still, under the headline."""
    import numpy as np

    g = np.clip(0.82 - np.linspace(0, 1, w) * 1.5, 0.0, 0.82)[None, :].repeat(h, 0)
    sh = Image.new("RGBA", (w, h), ASPHALT + (255,))
    sh.putalpha(Image.fromarray((g * 255).astype("uint8"), "L"))
    return sh


def broll_frame(shot: Shot, t: float, size: tuple[int, int], vertical: bool, sub: str) -> Image.Image:
    """An AI-generated scene still with a slow push-in, the headline, the burned-in caption and the scene tag."""
    sc = shot.sc
    w, h = size
    src, tagged = _source(sc.image)
    anchor = {"br": (1.0, 1.0), "bl": (0.0, 1.0), "c": (0.5, 0.5), "tr": (1.0, 0.0), "r": (1.0, 0.5)}[getattr(sc, "move", "br") or "br"]
    k1, k2 = _fade(t, 0.15), _fade(t, 0.5)
    if not vertical:
        if abs(src.width / src.height - w / h) < 0.03:  # 16:9 already: full frame
            im = _kb(src, t, shot.dur, size, anchor)
            box = (0, 0, w, h)
        else:  # square or portrait scene: the whole picture on the right, a blurred copy behind it
            im = _blur_bg(sc.image, w, h).copy()
            ph = h - 80
            pw = round(src.width * ph / src.height)
            x0 = w - pw - 120
            im.paste(_kb(src, t, shot.dur, (pw, ph), (0.5, 0.5)), (x0, 40))
            box = (x0, 40, x0 + pw, 40 + ph)
        im = Image.alpha_composite(im.convert("RGBA"), _left_shade(w, h))
        layer = Image.new("RGBA", size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        x, y = 120, 150.0
        if sc.head:
            y = text_block(d, (x, y + 18 * (1 - k1)), sc.head, font("black", 112), 900, ON_DARK + (int(255 * k1),), 108)
        if sc.caption:
            d.rectangle([x, y + 30, x + 10, y + 30 + 46], fill=TONE.get(sc.tone, TONE["act"]) + (int(255 * k2),))
            text_block(d, (x + 30, y + 28), sc.caption, font("semi", 38), 820, ON_DARK + (int(240 * k2),), 50)
        im.alpha_composite(layer)
        im = im.convert("RGB")
        if not tagged or box != (0, 0, w, h):  # the burned-in tag of a 16:9 still stays in its corner (anchored there)
            tag(im, SCENE_TAG + ("" if tagged else " · real app screen on the phone"), box[2] - 22, box[3] - 22, 24)
        if sub:  # beside a picture that does not fill the frame, the caption stays left of it (its tag stays readable)
            _subtitle(im, sub, 120, h - 60, 1280 if box == (0, 0, w, h) else min(1280, box[0] - 160), size=36)
        return im
    # vertical: the picture as a band at the top (or full frame when it is portrait), headline under it
    im = asphalt(w, h).copy()
    portrait = src.height > src.width
    if portrait:  # the tyre scene: full frame, at most a 1.41x scale
        pic = _kb(_covered(sc.image, w, h, 0.5, 0.5), t, shot.dur, size, (0.5, 0.4))
        im.paste(pic, (0, 0))
        im = Image.alpha_composite(im.convert("RGBA"), _vshade(w, h)).convert("RGB")
        box = (0, 0, w, h)
        head_y = 250
    else:
        bh = 1100  # a near-square crop of the 16:9 still (about 1.02x scale): big enough to read on a phone
        # cropped from the right edge and anchored bottom-right: a still's own burned-in tag stays whole in its corner
        pic = _kb(_covered(sc.image, w, bh, 1.0, 0.5), t, shot.dur, (w, bh), (1.0, 1.0))
        im.paste(pic, (0, 250))
        box = (0, 250, w, 250 + bh)
        head_y = 250 + bh + 50
    brand_row(im, 60, 80, dark=True, size=64)
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    y = head_y
    if sc.head:
        y = text_block(d, (70, y + 18 * (1 - k1)), sc.head, font("black", 104), w - 140, ON_DARK + (int(255 * k1),), 100)
    if sc.caption and not portrait:
        text_block(d, (70, y + 16), sc.caption, font("semi", 42), w - 140, ON_DARK_MUTED + (int(255 * k2),), 54)
    im = Image.alpha_composite(im.convert("RGBA"), layer).convert("RGB")
    if not tagged or portrait:
        tag(im, SCENE_TAG + ("" if tagged else " · real app screen"), box[2] - 24, box[3] - 24 if not portrait else 230, 28)
    if sub:
        vsubtitle(im, sub)
    return im


@lru_cache(maxsize=2)
def _vshade(w: int, h: int) -> Image.Image:
    """Dark top band on a full-frame vertical still, under the brand and the headline."""
    import numpy as np

    g = np.clip(0.9 - np.linspace(0, 1, h) * 1.8, 0.0, 0.9)[:, None].repeat(w, 1)
    sh = Image.new("RGBA", (w, h), ASPHALT + (255,))
    sh.putalpha(Image.fromarray((g * 255).astype("uint8"), "L"))
    return sh


def proof_card(shot: Shot, t: float, size: tuple[int, int], vertical: bool, sub: str) -> Image.Image:
    """The measured numbers, one row each, with where they come from in small print. Only numbers from the repo's
    own reports (make_demo_assets.PROOF)."""
    from make_demo_assets import PROOF, PROOF_NOTE

    w, h = size
    im = asphalt(w, h).copy()
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x = 150 if not vertical else 80
    y = 80 if not vertical else 300  # 16:9: the rows and the source note end above a two-line caption
    k0 = _fade(t, 0.05)
    d.text((x, y), shot.sc.head, font=font("black", 92 if not vertical else 96), fill=ON_DARK + (int(255 * k0),))
    y += 140 if not vertical else 150
    big, small = font("black", 80 if not vertical else 88), font("body", 36 if not vertical else 38)
    num_w = 460 if not vertical else 0
    for i, (num, label) in enumerate(PROOF):
        k = _fade(t, 0.4 + 0.45 * i)
        a = int(255 * k)
        d.text((x, y + 10 * (1 - k)), num, font=big, fill=TONE["act"] + (a,))
        if vertical:
            text_block(d, (x, y + 92), label, small, w - 2 * x, ON_DARK + (a,), 46)
            y += 200
        else:
            text_block(d, (x + num_w, y + 24), label, small, w - x - num_w - 150, ON_DARK + (a,), 46)
            y += 106
    kn = _fade(t, 0.4 + 0.45 * len(PROOF))
    text_block(d, (x, y + 20), PROOF_NOTE, font("body", 26 if not vertical else 30), w - 2 * x, ON_DARK_MUTED + (int(230 * kn),), 36 if not vertical else 40)
    im.paste(layer, (0, 0), layer)
    if sub:
        if vertical:
            vsubtitle(im, sub)
        else:
            _subtitle(im, sub, 260, h - 30, w - 520)
    return im


def close_card(sc: Any, t: float, size: tuple[int, int], vertical: bool, sub: str) -> Image.Image:
    """End card: name, promise, the repo link (the one action), the source of the answers and the music credit."""
    from make_demo_assets import MUSIC_CREDIT, REPO_URL

    w, h = size
    im = asphalt(w, h).copy()
    big, small = sc.image[6:].split("|")
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x, y = (130, 120) if not vertical else (80, 260)
    lw = 1020 if not vertical else w - 160
    k1, k2, k3 = _fade(t, 0.1), _fade(t, 0.45), _fade(t, 0.8)
    brand_row(layer, x, int(y + 18 * (1 - k1)), dark=True, size=96 if not vertical else 110)
    yy = text_block(d, (x, y + 160 + 18 * (1 - k2)), big, font("black", 88 if not vertical else 96), lw, ON_DARK + (int(255 * k2),), 90)
    yy = text_block(d, (x, yy + 22), small, font("body", 34 if not vertical else 40), lw, ON_DARK_MUTED + (int(255 * k2),), 46)
    url_f = font("black", 58 if not vertical else 56)
    end = pill(layer, (x, int(yy + 36)), REPO_URL, url_f, (16, 18, 20, int(255 * k3)), TONE["act"] + (int(255 * k3),), (26, 12))
    del end
    yy += 36 + 58 + 24 + 40
    yy = text_block(d, (x, yy), answers_note(), font("body", 25 if not vertical else 30), lw, ON_DARK_MUTED + (int(220 * k3),), 34 if not vertical else 40)
    text_block(d, (x, yy + 14), MUSIC_CREDIT, font("body", 25 if not vertical else 30), lw, ON_DARK_MUTED + (int(220 * k3),), 34 if not vertical else 40)
    _close_phones(im, t, vertical)
    im.paste(layer, (0, 0), layer)
    if sub:
        if vertical:
            vsubtitle(im, sub)
        else:
            _subtitle(im, sub, 130, h - 40, 1040)
    return im


def _close_phones(im: Image.Image, t: float, vertical: bool) -> None:
    """Three moments of the app on the end card: parts on the photo, a passed check, the red stop (new photos)."""
    names = ["05_parts", "08_check_pass", "11_rice_stop"]
    sc = 0.6 if not vertical else 0.5
    xs = [1330, 1570, 1790] if not vertical else [250, 540, 830]
    top = 150 if not vertical else 1040
    for i, name in enumerate(names):
        k = _fade(t, 0.4 + 0.25 * i, 0.7)
        if k <= 0:
            continue
        screen = _shot_png(name)
        draw_phone(im, Phone(cx=xs[i], top=top + (60 if i == 1 else 0) + 30 * (1 - k), scale=sc), screen, alpha=k)


@lru_cache(maxsize=8)
def _shot_png(name: str) -> Image.Image:
    from make_demo_assets import SHOTS

    return Image.open(SHOTS / f"{name}.png").convert("RGB").resize((780, 1688), Image.Resampling.LANCZOS)


# --- vertical (9:16) layout
VERT_PHONE = Phone(cx=540, top=430, scale=1.18)
# X / Reels / Shorts draw their own buttons and text over the edges of a 9:16 video: captions stay inside this box
VERT_SAFE_BOTTOM = 1920 - 250
VERT_SAFE_SIDE = 60
VERT_CAPTION_PX = 46  # 46 px on a 1920 px tall frame: readable on a phone held upright


def vsubtitle(im: Image.Image, text: str) -> None:
    """The English caption of the vertical clip, drawn last (over the phone) and inside the safe area."""
    _subtitle(im, text, VERT_SAFE_SIDE, VERT_SAFE_BOTTOM, im.width - 2 * VERT_SAFE_SIDE, size=VERT_CAPTION_PX)


def _vpanel(sc: Any, sub: str, size: tuple[int, int]) -> Image.Image:
    w, h = size
    im = concrete(w, h).copy()
    d = ImageDraw.Draw(im)
    brand_row(im, 80, 70, size=56)
    pill(im, (80, 150), demo_note(), font("body", 21), MUTED, PLATE)
    hf = font("black", 74)
    y = 225
    lines = wrap(sc.head or sc.caption, hf, w - 180)[:2]
    d.rectangle([60, y + 8, 70, y + 8 + len(lines) * 72 - 12], fill=TONE.get(sc.tone, TONE["act"]))
    for ln in lines:
        draw_text(d, (90, y), ln, hf, INK)
        y += 72
    if sub:
        vsubtitle(im, sub)
    return im


# --- encode
def render_segment(shot: Shot, out: Path, size: tuple[int, int], audio: Path | None, prev_last: Path | None,
                   renderer: Renderer, last_png: Path) -> None:
    """Pipe 30 fps frames into ffmpeg (H.264 veryfast, CRF 20) with the scene's voice-over, which starts LEAD s after
    the cut; save the last frame for the next crossfade."""
    n = int(round(shot.dur * FPS))
    a_in = ["-i", str(audio)] if audio else ["-f", "lavfi", "-t", f"{shot.dur:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
    fade_out = max(0.0, shot.dur - 0.12)
    delay = int(LEAD * 1000) if audio else 0
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{size[0]}x{size[1]}", "-r", str(FPS), "-i", "-",
           *a_in, "-filter_complex",
           f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={delay}|{delay},apad=whole_dur={shot.dur:.3f},"
           f"afade=t=in:d=0.04,afade=t=out:st={fade_out:.3f}:d=0.12[a]",
           "-map", "0:v", "-map", "[a]", "-t", f"{shot.dur:.3f}",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS), "-g", str(FPS * 2),
           "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", str(out) + ".part.mkv"]
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
    os.replace(str(out) + ".part.mkv", out)
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
    late = [m for m, t in rec.marks.items() if t > length - 1.0]
    if late:
        raise SystemExit(f"scene {key}: {late} happened at {[round(rec.marks[m], 1) for m in late]} s, after its "
                         f"{length:.1f} s end (less than 1 s on screen): shorten the scene's actions")
    wait_until(length)
    rec.stop(key, length)


LIVE_MS = 240_000  # live Meta answers take up to a couple of minutes; the wait is cut from the clip (Recorder.cut)

# --- what each recorded scene does (scene clock in seconds; lengths come from the voice-over)
GROUPS = {"motor": ["home", "capture", "progress", "diagnosis", "parts"],
          "steps": ["preflight", "steps", "check_fail", "check_pass", "replan", "handoff"],
          "other": ["diagram", "rice", "tyre"]}


def capture(group: str, lengths: dict[str, float]) -> None:
    from playwright.sync_api import sync_playwright

    import make_demo_assets as mda
    from api.main import _dark_photo
    from api.settings import settings

    CLIPS.mkdir(parents=True, exist_ok=True)
    base, srv = mda._server()
    rec, origin = mda.recorded(), mda.site(base)
    spent_before = mda.spent_total() if rec else 0.0
    (CLIPS / "recorded.json").write_text(json.dumps({"date": _replay_day() if rec else _today_wib(), "source": "recorded" if rec else "live"}))
    settings.mock_pace_s = 0.6
    dark = Path(tempfile.mkdtemp()) / "dark.jpg"
    dark.write_bytes(_dark_photo("motor"))
    args = ["--no-proxy-server", "--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream"]
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=mda._chromium(), args=args)
        ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True, locale="id-ID",
                            timezone_id=mda.TZ)
        ctx.grant_permissions(["camera", "microphone"], origin=origin)
        ctx.add_init_script(mda.SR_STUB)
        ctx.add_init_script(TAP_JS)
        page_errors: list[str] = []
        if rec:
            mda.serve_as_public(ctx, base)    # pages at the public address, answered by this server
            mda.no_new_runs(ctx, page_errors)  # anything that would start new model work fails the take
        else:
            mda.public_links(ctx, base)  # the hand-off message links read like the public site's, not 127.0.0.1
        pg = ctx.new_page()
        mda._console_watch(pg, page_errors)
        recorder = Recorder(ctx, pg)
        rec_now = recorder.now

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

        def go_to_step(n: int) -> None:
            """Walk the step card to step n of the live plan (0 = stay)."""
            for _ in range(12):
                if not n or pg.inner_text("#stepNo").strip() == str(n):
                    break
                pg.click("#nextBtn" if int(pg.inner_text("#stepNo").strip() or 1) < n else "#prevBtn")
                pg.wait_for_timeout(350)

        def motor_to_result() -> None:
            settings.mock_pace_s = 0.0
            if rec:  # the recorded 1-tap demo: the motorbike sample, played back
                pg.goto(origin + "/?replay=1")
                pg.wait_for_selector("#goBtn")
                pg.click('button.sample[data-sample="motor"]')
            else:
                pg.goto(base + "/")
                pg.wait_for_selector("#goBtn")
                pg.set_input_files("#photo", str(FIX / "sample_motor_plug_area.jpg"))
                pg.fill("#text", "Motor saya Honda Beat susah hidup, distarter cuma bunyi tapi mesin nggak nyala.")
                pg.click("#goBtn")
            pg.wait_for_selector("#question:not(.hidden), #result:not(.hidden)", timeout=LIVE_MS)
            if pg.is_visible("#question"):
                pg.fill("#answerText", mda.ANSWER)
                pg.click("#answerBtn")
            pg.wait_for_selector("#result:not(.hidden)", timeout=LIVE_MS)
            pg.evaluate("window.scrollTo(0, 0)")
            settings.mock_pace_s = 0.6

        if group == "motor":
            pg.goto(origin + ("/?replay=1" if rec else "/"))
            pg.wait_for_selector("#goBtn")
            pg.wait_for_timeout(600)
            logo = pg.locator(".brand .plate").first
            logo.screenshot(path=str(CLIPS / "logo.png"))

            def home(at: Callable[[float], None]) -> None:
                # the first screen, then a slow scroll to the photo box and the language chips
                at(1.2)
                scroll_to("#photoBox", -260, 1600)

            def capture_(at: Callable[[float], None]) -> None:
                # pick the photo and type the problem like an owner would; nothing is sent here (the next scene
                # plays the recorded 1-tap demo of this same photo)
                at(0.3)
                scroll_to("#photoBox", -70, 800)
                at(1.2)
                pg.set_input_files("#photo", str(FIX / "sample_motor_plug_area.jpg"))
                at(2.0)
                pg.click('#cats button[data-cat="motor"]')
                at(2.5)
                scroll_to("#text", -520, 800)
                pg.click("#text")
                pg.keyboard.type("Motor saya susah hidup, distarter cuma bunyi.", delay=40)
                pg.evaluate("document.activeElement && document.activeElement.blur()")
                if rec:
                    at(max(rec_now() + 0.3, lengths["capture"] - 1.6))
                    scroll_to('button.sample[data-sample="motor"]', -520, 1000)

            def progress(at: Callable[[float], None]) -> None:
                at(0.3)
                pg.click('button.sample[data-sample="motor"]' if rec else "#goBtn")
                pg.wait_for_selector("#progress:not(.hidden)")
                at(0.9)
                scroll_to("#stageList", -110, 800)
                recorder.cut(lambda: pg.wait_for_selector("#lf-segment img", timeout=LIVE_MS))
                pg.wait_for_function("() => document.querySelector('#lf-segment img').naturalWidth > 0", timeout=10000)
                recorder.mark("sam")
                pg.wait_for_timeout(700)
                scroll_by(330, 1100)

            def diagnosis(at: Callable[[float], None]) -> None:
                if pg.is_visible("#question"):  # a recording that asked its follow-up: answer it like the owner did
                    pg.fill("#answerText", mda.ANSWER)
                    pg.click("#answerBtn")
                recorder.cut(lambda: pg.wait_for_selector("#result:not(.hidden)", timeout=LIVE_MS))
                pg.evaluate("window.scrollTo(0, 0)")
                recorder.mark("result")
                at(4.2)
                scroll_by(420, 1500)

            def parts(at: Callable[[float], None]) -> None:
                at(0.2)
                scroll_to("#partsWrap", -96, 1100)

            plan = {"home": home, "capture": capture_, "progress": progress, "diagnosis": diagnosis, "parts": parts}
            for key in GROUPS["motor"]:
                run_scene(recorder, key, lengths[key], plan[key])
            src = pg.evaluate("document.querySelector('#partsImg') && document.querySelector('#partsImg').src")
            if src:  # the marked photo for the title and close cards (and web/og.png, scripts/make_og.py)
                # page.request skips the context's routes, so a public-address URL is fetched from this server directly
                got = pg.request.get(src.replace(mda.PUBLIC_BASE, base, 1) if rec else src)
                if not got.ok or not got.headers.get("content-type", "").startswith("image/"):
                    raise SystemExit(f"marked photo {src} answered {got.status} {got.headers.get('content-type')}")
                (CLIPS / "parts_photo.jpg").write_bytes(got.body())

        elif group == "steps":
            motor_to_result()

            def preflight(at: Callable[[float], None]) -> None:
                at(0.2)
                scroll_to("#preflight", -90, 1000)
                at(1.6)
                tick_all(600)

            def steps(at: Callable[[float], None]) -> None:
                at(0.2)
                scroll_to("#stepCard", -70, 1000)
                at(2.6)
                pg.click("#nextBtn")
                at(4.4)
                pg.click("#prevBtn")

            def check_fail(at: Callable[[float], None]) -> None:
                at(0.6)
                if rec:
                    pg.click("#sampleBad")  # the recorded check of the too-dark sample photo
                else:
                    pg.set_input_files("#stepPhoto", str(dark))
                recorder.cut(lambda: pg.wait_for_function("() => !document.querySelector('#checkResult').textContent.includes('…')", timeout=LIVE_MS))
                at(2.0)
                scroll_to("#checkResult", -330, 900)

            def check_pass(at: Callable[[float], None]) -> None:
                # the step card is already on the step the photo shows (moved between the scenes, under the crossfade),
                # so the short scene has room for the check and its result
                # the upload and the live check are one cut: the clip keeps 0.8 s of "Checking photo…" and then the
                # verdict, so it lands early in this short scene. The verdict is the isPass/isFail class the app sets
                # when the answer arrives (cleared before the scene, so a class left from check_fail cannot count).
                at(0.2)

                def upload_and_check() -> None:
                    if rec:
                        pg.click("#sampleGood")  # the recorded check of the plug cap sample photo
                    else:
                        pg.set_input_files("#stepPhoto", str(FIX / "sample_motor_step_cap_on.jpg"))
                    pg.wait_for_function("() => { const el = document.querySelector('#checkResult');"
                                         " return (el.classList.contains('isPass') || el.classList.contains('isFail'))"
                                         " && !el.textContent.includes('…'); }", timeout=LIVE_MS)

                recorder.cut(upload_and_check)
                recorder.mark("pass")

            def replan(at: Callable[[float], None]) -> None:
                at(0.3)
                scroll_to("#stuckText", -300, 1000)
                at(1.5)
                pg.click("#stuckText")
                pg.keyboard.type("Sudah dicoba, mesin tetap tidak nyala.", delay=26)
                at(3.2)
                pg.click("#stuckBtn")
                recorder.cut(lambda: pg.wait_for_function(
                    "() => document.querySelector('#stuckMsg').textContent.length > 3 && !document.querySelector('#stuckBtn').disabled", timeout=LIVE_MS))
                pg.wait_for_selector("#planBanner:not(.hidden)")
                at(4.6)
                scroll_top(1200)

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

            plan = {"preflight": preflight, "steps": steps, "check_fail": check_fail, "check_pass": check_pass,
                    "replan": replan, "handoff": handoff}
            for key in GROUPS["steps"]:
                if key == "check_pass":  # the after-photo shows the plug cap pushed back on: check it on that step
                    go_to_step(mda.sample_step_n(pg, "motor"))
                    pg.evaluate("() => { const el = document.querySelector('#stepPhotoLabel');"
                                " window.scrollTo(0, Math.max(0, el.getBoundingClientRect().top + scrollY - 330));"
                                " document.querySelector('#checkResult').classList.remove('isPass', 'isFail'); }")
                    pg.wait_for_timeout(400)
                run_scene(recorder, key, lengths[key], plan[key])

        else:  # the Muse Image diagram on the faucet (en), the red stop on the rice cooker (id), the tyre in Basa Jawa
            # DEMO_ONLY=diagram (comma list) re-records only those scenes of this group, so one bad take costs one scene
            only = {k.strip() for k in os.environ.get("DEMO_ONLY", "").split(",") if k.strip()} or set(GROUPS["other"])

            def rice(at: Callable[[float], None]) -> None:
                settings.mock_pace_s = 0.35
                at(0.4)
                if rec:  # the recorded rice cooker repair opens the way the app reopens one (no new model call)
                    pg.evaluate("(sid) => { history.pushState({ tc: 1 }, '', '#' + sid); show('progress'); startElapsed(); follow(sid); }",
                                mda.recorded_session("rice", "id"))
                else:
                    pg.click('button.sample[data-sample="rice"]')
                recorder.cut(lambda: pg.wait_for_selector("#stopBox:not(.hidden)", timeout=LIVE_MS))
                pg.evaluate("window.scrollTo(0, 0)")
                recorder.mark("stop")

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

            def tyre(at: Callable[[float], None]) -> None:
                # the Basa Jawa tyre repair: the result, then down to the parts on the photo and the first step
                at(1.6)
                scroll_to("#partsWrap", -96, 1400)
                at(max(rec_now() + 0.3, lengths["tyre"] * 0.55))
                scroll_to("#preflight", -90, 1400)

            if "diagram" in only:  # the English faucet repair, where Muse Image draws the washer swap
                settings.mock_pace_s = 0.0
                if rec:
                    mda.open_recorded(pg, origin, mda.recorded_session("faucet", "en", diagram=True), "en")
                    for box in pg.locator("#preList input").all():
                        box.check()
                else:
                    mda.faucet_with_diagram(pg, base)
                settings.mock_pace_s = 0.6
                pg.evaluate("window.scrollTo(0, 0)")
                run_scene(recorder, "diagram", lengths["diagram"], diagram)
            if "rice" in only:
                pg.goto(origin + "/")
                pg.select_option("#lang", "id")
                pg.evaluate("document.querySelector('button.sample[data-sample=\"rice\"]').scrollIntoView({block: 'center'})")
                pg.wait_for_timeout(400)
                run_scene(recorder, "rice", lengths["rice"], rice)
            if "tyre" in only:
                if not rec:
                    raise SystemExit("the tyre scene plays the recorded Basa Jawa session: set DEMO_RECORDED_DATA")
                mda.open_recorded(pg, origin, mda.recorded_session("tire", "jv"), "jv")
                pg.evaluate("window.scrollTo(0, 0)")
                pg.wait_for_timeout(500)
                run_scene(recorder, "tyre", lengths["tyre"], tyre)
        b.close()
    srv.should_exit = True
    if rec:
        print(f"live spend of this take (app cost meter): ${mda.spent_total() - spent_before:.4f}", flush=True)
    if page_errors:
        raise SystemExit(f"page errors while recording {group}:\n" + "\n".join(page_errors))
