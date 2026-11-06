"""Make the four marketing images: real app screenshots composited onto AI-generated photo scenes.

Run from the repo root (needs Pillow, NumPy and ImageMagick 7 `magick` for the perspective warp):
    python docs/launch/make_marketing_images.py                  # all four
    python docs/launch/make_marketing_images.py thumbnail square # only these

Outputs (docs/launch/):
    thumbnail.png        1280x720   pump scene, 10_pump.png, "Photo in. Steps out."
    cover.png            1920x1080  motorbike scene, gallery/id_light_05_result_top.png, "Snap the engine. See the parts marked."
    square.png           1080x1080  rice cooker scene, 11_rice_stop.png, "It knows when to stop."
    poster-vertical.png  1080x1920  scooter tyre scene, 20_javanese_result.png, "Answers in Basa Jawa."

How each image is made
  1. The scene (docs/launch/scenes/, made by an image model from my prompts, see docs/launch/ASSETS.md) is scaled
     with Lanczos to cover the output size (at most 1.41x) and cropped.
  2. The real screenshot from docs/demo/screenshots is warped onto the phone's blank screen with
     `magick -distort Perspective`. The four screen corners were measured by eye on a 4x zoomed grid of each scene
     (SCREEN below, in the scene's own pixels). Only the screen's own bright pixels inside those corners take the
     screenshot, so the fingers that cover the screen stay in front of it. A faint glare and a 0.4 px blur make it sit
     in the photo.
  3. The phones in the scenes are small, so the same screenshot is also shown large in a plain phone frame with a
     "Real app screen" tag, and every image carries an "AI-generated scene" tag.
  4. Headlines are Barlow Condensed 800 (the app's own font, web/fonts) on solid plates; each claim is traced to a
     line in the repo in docs/launch/ASSETS.md.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "launch"
SCENES = OUT / "scenes"
SHOTS = ROOT / "docs" / "demo" / "screenshots"
FONTS = ROOT / "web" / "fonts"

ORANGE = (255, 106, 19)
RED = (200, 32, 30)
ASPHALT = (29, 32, 36)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

Quad = tuple[tuple[float, float], tuple[float, float], tuple[float, float], tuple[float, float]]


@dataclass(frozen=True)
class Spec:
    """One marketing image. Boxes and positions are in output pixels; SCREEN corners are in scene pixels."""
    name: str
    size: tuple[int, int]
    scene: str
    shot: str
    screen: Quad              # phone screen corners in the scene: top-left, top-right, bottom-right, bottom-left
    shot_crop_h: int          # screenshot rows to use (the tyre phone's screen is shorter than 390x844)
    focus_x: float            # 0..1: where to crop horizontally when the scaled scene is wider than the output
    focus_y: float
    lines: tuple[str, ...]    # headline lines
    plate: tuple[int, int, int]
    ink: tuple[int, int, int]
    head_xy: tuple[int, int]
    head_px: int
    inset_box: tuple[int, int, int]   # x, y, width of the large phone frame
    scene_tag: str            # corner for "AI-generated scene": tl, tr, bl, br
    scene_tag_y: int = 0      # extra offset from the top or bottom edge (vertical poster keeps clear of app overlays)
    blur: tuple[tuple[int, int, int, int], ...] = ()  # scene boxes with a brand name the generator painted
    inset_rows: int = 2532    # screenshot rows in the large frame: ends above a half-cut line of text


SPECS = {
    "thumbnail": Spec("thumbnail", (1280, 720), "scene_pump.jpg", "10_pump.png",
                      ((653, 340), (690, 362), (631, 437), (596, 413)), 2532, 0.5, 0.5,
                      ("Photo in.", "Steps out."), ORANGE, BLACK, (500, 28), 108, (1010, 52, 236), "bl", inset_rows=2430),
    "cover": Spec("cover", (1920, 1080), "scene_motor.jpg", "gallery/id_light_05_result_top.png",
                  ((759.5, 252.5), (840.5, 231), (925, 427.5), (826, 421)), 2532, 0.5, 0.5,
                  ("Snap the engine.", "See the parts marked."), ORANGE, BLACK, (72, 64), 112, (110, 352, 300), "br", inset_rows=2430),
    "square": Spec("square", (1080, 1080), "scene_rice.jpg", "11_rice_stop.png",
                   ((313.75, 502.5), (383.75, 482.5), (440, 632.5), (370, 655)), 2532, 0.5, 0.5,
                   ("It knows", "when to stop."), ASPHALT, WHITE, (40, 36), 104, (40, 352, 250), "br"),
    "poster-vertical": Spec("poster-vertical", (1080, 1920), "scene_tyre.jpg", "20_javanese_result.png",
                            ((375.5, 756.5), (419.5, 756.5), (419.5, 833.75), (375.5, 835)), 2073, 0.5, 0.5,
                            ("Answers in", "Basa Jawa."), ORANGE, BLACK, (60, 270), 132, (700, 600, 340), "tr", 250,
                            ((116, 968, 168, 991), (84, 878, 130, 906)), 2430),  # "HONDA" on the engine case, a side badge
}


def font(px: int, face: str = "barlow-condensed-800.woff2") -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / face), px)


def soften(im: Image.Image, box: tuple[int, int, int, int], radius: int = 6) -> Image.Image:
    """Blur a box with a feathered edge, so a painted brand name can not be read and no hard rectangle shows."""
    blurred = im.filter(ImageFilter.GaussianBlur(radius))
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(box, radius=min(box[2] - box[0], box[3] - box[1]) // 2, fill=255)
    return Image.composite(blurred, im, mask.filter(ImageFilter.GaussianBlur(radius * 0.8)))


def cover_scene(spec: Spec) -> tuple[Image.Image, float, tuple[int, int]]:
    """Scale the scene to cover the output size, crop it, and return (image, scale, crop offset)."""
    im = Image.open(SCENES / spec.scene).convert("RGB")
    for box in spec.blur:
        im = soften(im, box)
    W, H = spec.size
    k = max(W / im.width, H / im.height)
    if k > 1.42:
        raise SystemExit(f"{spec.scene}: needs a {k:.2f}x upscale (limit 1.42x); make a larger scene")
    big = im.resize((round(im.width * k), round(im.height * k)), Image.Resampling.LANCZOS)
    ox, oy = round((big.width - W) * spec.focus_x), round((big.height - H) * spec.focus_y)
    return big.crop((ox, oy, ox + W, oy + H)), k, (ox, oy)


def warp_screen(base: Image.Image, spec: Spec, k: float, off: tuple[int, int]) -> Image.Image:
    """Put the real screenshot on the phone's blank screen; fingers over the screen stay in front."""
    quad = [((x * k) - off[0], (y * k) - off[1]) for x, y in spec.screen]
    shot = Image.open(SHOTS / spec.shot).convert("RGB")
    shot = shot.crop((0, 0, shot.width, spec.shot_crop_h))
    sw, sh = shot.size
    with tempfile.TemporaryDirectory() as td:
        src, dst = Path(td) / "shot.png", Path(td) / "warp.png"
        shot.save(src)
        pts = [(0, 0), (sw, 0), (sw, sh), (0, sh)]
        args = " ".join(f"{a},{b} {x:.2f},{y:.2f}" for (a, b), (x, y) in zip(pts, quad))
        subprocess.run(["magick", str(src), "-alpha", "set", "-virtual-pixel", "transparent",
                        "-define", f"distort:viewport={base.width}x{base.height}+0+0",
                        "-filter", "Lanczos", "-distort", "Perspective", args, str(dst)], check=True)
        warped = Image.open(dst).convert("RGBA")
    # where the screenshot may go: inside the measured corners AND a bright, grey-white pixel of the blank screen
    poly = Image.new("L", base.size, 0)
    ImageDraw.Draw(poly).polygon(quad, fill=255)
    arr = np.asarray(base).astype(np.int16)
    bright = (arr.min(axis=2) > 165) & ((arr.max(axis=2) - arr.min(axis=2)) < 45)
    m = Image.fromarray((bright * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))
    mask = Image.fromarray(np.minimum(np.asarray(m), np.asarray(poly)))
    mask = Image.fromarray(np.minimum(np.asarray(mask), np.asarray(warped.split()[3]))).filter(ImageFilter.GaussianBlur(0.6))
    layer = warped.convert("RGB").filter(ImageFilter.GaussianBlur(0.4))
    # faint glare: a white diagonal gradient at up to 8% over the screen
    x0 = min(p[0] for p in quad); x1 = max(p[0] for p in quad)
    g = np.clip((np.arange(base.width)[None, :] - x0) / max(1.0, x1 - x0), 0, 1)
    glare = (0.08 * (1 - g))[..., None]
    la = np.asarray(layer).astype(np.float32)
    la = la * (1 - glare) + 255 * glare
    # match the scene's light a little: the screen sits in daylight, so lift blacks slightly
    la = la * 0.94 + 10
    layer = Image.fromarray(np.clip(la, 0, 255).astype(np.uint8))
    return Image.composite(layer, base, mask)


def rounded(im: Image.Image, r: int) -> Image.Image:
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=r, fill=255)
    out = im.convert("RGBA")
    out.putalpha(m)
    return out


def inset_phone(base: Image.Image, spec: Spec) -> Image.Image:
    """The same screenshot, large and flat, in a plain dark phone frame with a shadow and a 'Real app screen' tag."""
    x, y, w = spec.inset_box
    shot = Image.open(SHOTS / spec.shot).convert("RGB")
    shot = shot.crop((0, 0, shot.width, min(spec.inset_rows, round(shot.width * 844 / 390))))
    bez = max(8, w // 26)
    sw = w - 2 * bez
    sh = round(sw * shot.height / shot.width)
    screen = rounded(shot.resize((sw, sh), Image.Resampling.LANCZOS), max(10, sw // 11))
    frame = Image.new("RGBA", (w, sh + 2 * bez), (0, 0, 0, 0))
    ImageDraw.Draw(frame).rounded_rectangle((0, 0, w - 1, sh + 2 * bez - 1), radius=max(14, w // 8), fill=ASPHALT + (255,))
    frame.alpha_composite(screen, (bez, bez))
    canvas = base.convert("RGBA")
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((x + 10, y + 18, x + w + 10, y + frame.height + 18), radius=max(14, w // 8),
                                             fill=(0, 0, 0, 120))
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(18)))
    canvas.alpha_composite(frame, (x, y))
    tag(canvas, "Real app screen", (x + w // 2, y + frame.height + 14), anchor="mt", px=max(18, w // 11))
    return canvas


def tag(canvas: Image.Image, text: str, xy: tuple[int, int], anchor: str, px: int) -> None:
    """Dark pill with white text, the same look as the 'Sample photo (AI-generated)' tag on the app's sample photos."""
    f = font(px, "barlow-600.woff2")
    d = ImageDraw.Draw(canvas)
    l, t, r, b = (round(v) for v in d.textbbox((0, 0), text, font=f))
    pad = px // 2
    bw, bh = r - l + 2 * pad, b - t + 2 * pad
    x, y = xy
    if anchor[0] == "m":
        x -= bw // 2
    elif anchor[0] == "r":
        x -= bw
    if anchor[1] == "b":
        y -= bh
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.rounded_rectangle((x, y, x + bw, y + bh), radius=bh // 2, fill=(20, 22, 26, 175))
    ld.text((x + pad - l, y + pad - t), text, font=f, fill=(255, 255, 255, 240))
    canvas.alpha_composite(layer)


def headline(canvas: Image.Image, spec: Spec) -> None:
    """Each line on its own solid plate (left-aligned), so the text never sits on a busy part of the photo."""
    f = font(spec.head_px)
    d = ImageDraw.Draw(canvas)
    x, y = spec.head_xy
    padx, pady = spec.head_px // 5, spec.head_px // 9
    for line in spec.lines:
        l, t, r, b = (round(v) for v in d.textbbox((0, 0), line, font=f))
        d.rectangle((x, y, x + (r - l) + 2 * padx, y + (b - t) + 2 * pady), fill=spec.plate + (255,))
        d.text((x + padx - l, y + pady - t), line, font=f, fill=spec.ink)
        y += (b - t) + 2 * pady + max(6, spec.head_px // 14)


def scene_tag(canvas: Image.Image, spec: Spec) -> None:
    W, H = canvas.size
    px = max(18, round(min(W, H * 16 / 9) / 64))
    m = max(14, W // 70)
    c = spec.scene_tag
    x = m if c[1] == "l" else W - m
    y = (m + spec.scene_tag_y) if c[0] == "t" else H - m - spec.scene_tag_y
    tag(canvas, "AI-generated scene", (x, y), anchor=("l" if c[1] == "l" else "r") + ("t" if c[0] == "t" else "b"), px=px)


def build(name: str) -> Path:
    spec = SPECS[name]
    base, k, off = cover_scene(spec)
    base = warp_screen(base, spec, k, off)
    canvas = inset_phone(base, spec)
    headline(canvas, spec)
    scene_tag(canvas, spec)
    out = OUT / f"{spec.name}.png"
    canvas.convert("RGB").save(out, optimize=True)
    if name == "thumbnail" and out.stat().st_size >= 2_000_000:  # YouTube custom thumbnail limit
        raise SystemExit(f"{out.name} is {out.stat().st_size} bytes, YouTube takes under 2 MB")
    print(f"{out.relative_to(ROOT)} {spec.size[0]}x{spec.size[1]} {out.stat().st_size // 1024} KB")
    return out


def main(argv: list[str]) -> int:
    names = argv or list(SPECS)
    bad = [n for n in names if n not in SPECS]
    if bad:
        print(f"unknown: {bad}; choose from {list(SPECS)}")
        return 2
    for n in names:
        build(n)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
