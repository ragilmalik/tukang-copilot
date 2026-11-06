"""Make the launch assets: YouTube thumbnail (1280x720), architecture diagram (1920x1080) and the one-pager PDF.

Run from the repo root:
    python docs/launch/make_launch_assets.py              # thumbnail + architecture diagram
    python docs/launch/make_launch_assets.py onepager     # docs/launch/one-pager.pdf from ONE_PAGER.md
    python docs/launch/make_launch_assets.py thumbnail architecture onepager

The images need Pillow and the DejaVu fonts (present on most Linux boxes) and use the demo screenshots in
docs/demo/screenshots. The one-pager needs pandoc and WeasyPrint (`pip install weasyprint`); it is styled by
one-pager.css and must stay exactly one A4 page, so the build stops with an error when the text grows past it.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "launch"
SHOTS = ROOT / "docs" / "demo" / "screenshots"
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")

NAVY = (24, 31, 40)
NAVY2 = (36, 46, 58)
ORANGE = (230, 120, 20)
AMBER = (255, 196, 61)
WHITE = (255, 255, 255)
GREY = (190, 198, 208)
RED = (205, 38, 38)
GREEN = (46, 170, 90)
BLUE = (40, 140, 220)
PURPLE = (130, 90, 210)


def font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(str(FONT_DIR / name), size)


def rounded(img: Image.Image, radius: int) -> Image.Image:
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, img.size[0] - 1, img.size[1] - 1], radius, fill=255)
    out = img.convert("RGBA")
    out.putalpha(mask)
    return out


def phone(shot: str, crop_top: int, crop_h: int, width: int) -> Image.Image:
    src = Image.open(SHOTS / shot).convert("RGB")
    src = src.crop((0, crop_top, src.width, crop_top + crop_h))
    h = int(src.height * width / src.width)
    src = src.resize((width, h), Image.LANCZOS)
    bezel = 14
    frame = Image.new("RGB", (width + 2 * bezel, h + 2 * bezel), (12, 14, 18))
    frame.paste(src, (bezel, bezel))
    return rounded(frame, 34)


def paste_shadow(base: Image.Image, im: Image.Image, xy: tuple[int, int], angle: float) -> None:
    rot = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    shadow = Image.new("RGBA", rot.size, (0, 0, 0, 0))
    alpha = rot.split()[3].point(lambda a: int(a * 0.35))
    shadow.putalpha(alpha)
    shadow = shadow.filter(ImageFilter.GaussianBlur(22))
    base.alpha_composite(shadow, (xy[0] + 14, xy[1] + 18))
    base.alpha_composite(rot, xy)


def thumbnail() -> Path:
    W, H = 1280, 720
    img = Image.new("RGBA", (W, H), NAVY + (255,))
    d = ImageDraw.Draw(img)
    # soft diagonal panel behind the phones
    d.polygon([(760, 0), (W, 0), (W, H), (640, H)], fill=NAVY2 + (255,))

    parts = phone("05_parts.png", 300, 1300, 270)
    stop = phone("11_rice_stop.png", 200, 1080, 250)  # from the top of the STOP title
    paste_shadow(img, parts, (730, 60), 4)
    paste_shadow(img, stop, (960, 170), -6)

    d = ImageDraw.Draw(img)
    x = 56
    f_pill = font(26)
    pill = "TUKANG COPILOT"
    pw = int(d.textlength(pill, font=f_pill))
    d.rounded_rectangle([x, 50, x + pw + 44, 96], 23, fill=ORANGE)
    d.text((x + 22, 56), pill, font=f_pill, fill=WHITE)

    d.text((x, 122), "Motor mogok?", font=font(80), fill=AMBER)
    f = font(52)
    d.text((x, 236), "AI finds the part.", font=f, fill=WHITE)
    d.text((x, 306), "Checks every step.", font=f, fill=WHITE)
    w1 = d.textlength("Says ", font=f)
    d.text((x, 376), "Says ", font=f, fill=WHITE)
    d.text((x + w1, 376), "STOP", font=f, fill=(255, 92, 92))
    w2 = d.textlength("STOP ", font=f)
    d.text((x + w1 + w2, 376), "when", font=f, fill=WHITE)
    d.text((x, 446), "it's dangerous.", font=f, fill=WHITE)

    f_tag = font(26, bold=False)
    tag = "Muse Spark + SAM 3.1  |  Bahasa  |  Jawa"
    tw = int(d.textlength(tag, font=f_tag))
    d.rounded_rectangle([x, 590, x + tw + 40, 646], 14, fill=(52, 64, 78, 255))
    d.text((x + 20, 602), tag, font=f_tag, fill=(225, 230, 236))

    out = OUT / "thumbnail.png"
    img.convert("RGB").save(out, optimize=True)
    return out


def box(d: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], title: str, sub: list[str],
        color: tuple[int, int, int], title_size: int = 34, sub_size: int = 24) -> None:
    x0, y0, x1, y1 = xy
    d.rounded_rectangle(xy, 22, fill=(255, 255, 255), outline=color, width=5)
    d.rounded_rectangle([x0, y0, x1, y0 + 14], 7, fill=color)
    d.text((x0 + 24, y0 + 28), title, font=font(title_size), fill=NAVY)
    y = y0 + 28 + title_size + 14
    for line in sub:
        d.text((x0 + 24, y), line, font=font(sub_size, bold=False), fill=(70, 80, 92))
        y += sub_size + 10


def arrow(d: ImageDraw.ImageDraw, a: tuple[int, int], b: tuple[int, int], color=NAVY, width: int = 6,
          label: str | None = None, label_xy: tuple[int, int] | None = None) -> None:
    d.line([a, b], fill=color, width=width)
    import math
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    L = 22
    p1 = (b[0] - L * math.cos(ang - 0.45), b[1] - L * math.sin(ang - 0.45))
    p2 = (b[0] - L * math.cos(ang + 0.45), b[1] - L * math.sin(ang + 0.45))
    d.polygon([b, p1, p2], fill=color)
    if label and label_xy:
        d.text(label_xy, label, font=font(22, bold=False), fill=color)


def architecture() -> Path:
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), (246, 243, 238))
    d = ImageDraw.Draw(img)
    d.text((60, 36), "Tukang Copilot: one agent loop, five Meta models", font=font(52), fill=NAVY)
    d.text((60, 104), "Plan, act, verify, re-plan, escalate. Safety stops are code, not prompts.",
           font=font(28, bold=False), fill=(80, 88, 100))

    # Phone
    box(d, (60, 200, 420, 560), "Phone (PWA)", ["photos / 5-10 s video", "voice note or text", "live camera frames",
                                              "Bahasa, Jawa, English", "no account"], NAVY)
    # Code safety gate
    box(d, (60, 640, 420, 1000), "Safety gate", ["plain code, not a prompt", "runs before any model call", "gas, mains, shock, fire,",
                                                       "brakes, fuel: red STOP",
                                                       "untrusted-text fence"], RED)

    # Agent loop column of stages
    sx0, sx1 = 560, 1180
    stages = [
        ("1 Listen", "Voice Transcribe  |  Spark 1.2 audio (Jawa)", BLUE),
        ("2 Look", "Muse Spark 1.3 vision: parts + boxes", ORANGE),
        ("3 Find parts", "SAM 3.1 masks on your photo", GREEN),
        ("4 Diagnose + plan", "Muse Spark 1.3  or  Spark Open", ORANGE),
        ("5 Illustrate", "Muse Image edits the photo", PURPLE),
        ("6 Verify step", "Muse Spark checks a new photo", ORANGE),
    ]
    y = 200
    bh, gap = 112, 20
    for title, sub, color in stages:
        d.rounded_rectangle((sx0, y, sx1, y + bh), 18, fill=(255, 255, 255), outline=color, width=5)
        d.rectangle((sx0, y, sx0 + 16, y + bh), fill=color)
        d.text((sx0 + 36, y + 16), title, font=font(32), fill=NAVY)
        d.text((sx0 + 36, y + 62), sub, font=font(25, bold=False), fill=(70, 80, 92))
        y += bh + gap
    d.text((sx0, 168 - 4), "api/pipeline/engine.py", font=font(22, bold=False), fill=(110, 118, 130))

    # re-plan loop: from Verify back into Diagnose + plan
    lx = sx1 + 40
    y4 = 200 + 3 * (bh + gap)
    top = y4 + 90
    bot = 200 + 5 * (bh + gap) + bh // 2
    d.line([(sx1, bot), (lx, bot), (lx, top)], fill=ORANGE, width=6)
    arrow(d, (lx, top), (sx1 + 4, top), ORANGE)
    d.text((lx + 14, (top + bot) // 2 - 30), "still broken?", font=font(22), fill=ORANGE)
    d.text((lx + 14, (top + bot) // 2 - 2), "re-plan next cause", font=font(22, bold=False), fill=ORANGE)

    # outputs
    ox0, ox1 = 1470, 1870
    box(d, (ox0, 200, ox1, 470), "Guided repair", ["one step per screen,", "read aloud, hands-free",
                                                  "live camera guide (SAM 3.1)", "agent log: what the AI did"], GREEN,
        title_size=32, sub_size=23)
    box(d, (ox0, 520, ox1, 790), "Bengkel hand-off", ["WhatsApp summary", "nearest workshop search",
                                                     "PDF brief for the mechanic", "on red STOP or no causes left"], RED,
        title_size=32, sub_size=23)
    box(d, (ox0, 840, ox1, 1000), "meta_client.py", ["the only file that calls Meta:", "retries, schemas, cost cap"],
        NAVY, title_size=30, sub_size=22)

    # phone -> Listen, phone -> gate, gate -> plan check
    arrow(d, (420, 256), (sx0 - 6, 256), NAVY)
    arrow(d, (240, 560), (240, 634), RED)
    arrow(d, (420, 760), (sx0 - 6, y4 + 60), RED)
    d.text((430, 586), "checks text", font=font(18, bold=False), fill=RED)
    d.text((430, 608), "+ every plan", font=font(18, bold=False), fill=RED)
    # plan -> outputs
    d.line([(sx1, y4 + 22), (sx1 + 140, y4 + 22)], fill=GREEN, width=6)
    arrow(d, (sx1 + 140, y4 + 22), (ox0 - 6, 335), GREEN)
    d.text((sx1 + 14, 570), "plan ready", font=font(22), fill=GREEN)
    d.line([(sx1, y4 + 56), (sx1 + 140, y4 + 56)], fill=RED, width=6)
    arrow(d, (sx1 + 140, y4 + 56), (ox0 - 6, 655), RED)
    d.text((sx1 + 160, 600), "STOP", font=font(22), fill=RED)

    out = OUT / "architecture.png"
    img.save(out, optimize=True)
    return out


def check_one_page(pages: int) -> None:
    """The one-pager is printed and handed out as a single sheet: anything but exactly one page is an error."""
    if pages != 1:
        raise SystemExit(f"one-pager.pdf would be {pages} pages; shorten ONE_PAGER.md or tighten one-pager.css")


def one_pager() -> Path:
    """ONE_PAGER.md -> HTML (pandoc) -> PDF (WeasyPrint), checked to be exactly one A4 page before it is written."""
    import weasyprint  # optional dependency, only needed for this asset

    src = OUT / "ONE_PAGER.md"
    if "{{" in src.read_text(encoding="utf-8"):
        raise SystemExit("ONE_PAGER.md still has a {{...}} placeholder; fill it before building the PDF")
    html = subprocess.run(["pandoc", str(src), "-f", "markdown", "-t", "html5", "-s", "--css", "one-pager.css"],
                          capture_output=True, text=True, check=True, cwd=OUT).stdout
    doc = weasyprint.HTML(string=html, base_url=str(OUT)).render()
    check_one_page(len(doc.pages))
    out = OUT / "one-pager.pdf"
    doc.write_pdf(str(out))
    return out


BUILDERS = {"thumbnail": thumbnail, "architecture": architecture, "onepager": one_pager}


def main(argv: list[str]) -> int:
    names = argv or ["thumbnail", "architecture"]
    unknown = [n for n in names if n not in BUILDERS]
    if unknown:
        print(f"unknown asset(s): {', '.join(unknown)}; choose from {', '.join(BUILDERS)}", file=sys.stderr)
        return 2
    OUT.mkdir(parents=True, exist_ok=True)
    for name in names:
        print(BUILDERS[name]())
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
