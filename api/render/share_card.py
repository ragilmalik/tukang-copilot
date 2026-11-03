"""Share card (1200x630 PNG, the Open Graph size): the link preview WhatsApp, X, Telegram and Facebook show when a
repair guide link is shared. Left: the owner's photo with the parts SAM 3.1 outlined. Right: what it is, the most
likely cause (or, after a re-plan, which plan is being tried), the safety level, and the plan in one line. Demo sessions say so on the card.

Only model output and numbers go on the card, never the owner's own words (same rule as the agent log)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageOps

from . import brand

W, H = 1200, 630
LEVEL = {"green": ((22, 120, 60), {"id": "AMAN", "jv": "AMAN", "en": "SAFE"}),
         "amber": ((176, 104, 0), {"id": "HATI-HATI", "jv": "ATI-ATI", "en": "CAUTION"}),
         "red": ((185, 28, 28), {"id": "STOP", "jv": "MANDHEG", "en": "STOP"})}
TXT = {
    "id": {"plan": "Rencana {n} dari {m}, dicoba sekarang", "likely": "Paling mungkin", "steps": "{n} langkah", "min": "~{m} menit", "save": "hemat Rp{s}",
           "checked": "{v} dari {n} langkah lolos cek kamera", "camera": "Kamera mengecek tiap langkah",
           "demo": "MODE DEMO: jawaban contoh, foto contoh (dibuat AI)",
           "tag": "Foto + cerita, dapat panduan perbaikan", "made": "Meta Muse Spark + SAM 3.1"},
    "jv": {"plan": "Rencana {n} saka {m}, dijajal saiki", "likely": "Sing paling mungkin", "steps": "{n} langkah", "min": "~{m} menit", "save": "irit Rp{s}",
           "checked": "{v} saka {n} langkah lolos priksa kamera", "camera": "Kamera mriksa saben langkah",
           "demo": "MODE DEMO: wangsulan conto, foto conto (digawe AI)",
           "tag": "Foto + crita, oleh tuntunan ndandani", "made": "Meta Muse Spark + SAM 3.1"},
    "en": {"plan": "Plan {n} of {m}, being tried now", "likely": "Most likely", "steps": "{n} steps", "min": "~{m} min", "save": "save Rp{s}",
           "checked": "{v} of {n} steps passed a camera check", "camera": "The camera checks each step",
           "demo": "DEMO MODE: sample answers, AI-generated sample photo",
           "tag": "A photo and a few words, then a repair guide", "made": "Meta Muse Spark + SAM 3.1"},
}
def _panel(im: Image.Image, box: tuple[int, int]) -> Image.Image:
    """The whole photo, uncropped (SAM outlines near the edges stay visible), on a dimmed blurred copy of itself."""
    im = ImageOps.exif_transpose(im).convert("RGB")
    bg = ImageOps.fit(im, box, Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(18))
    bg = Image.blend(bg, Image.new("RGB", box, (20, 22, 26)), 0.55)
    fg = ImageOps.contain(im, (box[0] - 32, box[1] - 32), Image.Resampling.LANCZOS)
    bg.paste(fg, ((box[0] - fg.width) // 2, (box[1] - fg.height) // 2))
    return bg


def _photo(folder: Path, s: dict[str, Any], box: tuple[int, int]) -> Image.Image:
    for name in (s.get("parts_image"), *(s.get("photos") or [])):
        p = folder / str(name or "")
        if name and p.is_file():
            try:
                with Image.open(p) as im:
                    return _panel(im, box)
            except OSError:
                continue
    return Image.new("RGB", box, (60, 64, 72))


def _rupiah(n: Any) -> str:
    try:
        return f"{int(n):,}".replace(",", ".")
    except (TypeError, ValueError):
        return ""


def check_line(s: dict[str, Any], lang: str) -> tuple[str, bool]:
    """The camera-check line: a real count ("2 of 4 steps passed a camera check"), never "every step checked" for a
    plan nobody has checked yet. Returns (text, any step passed)."""
    tx = TXT[lang if lang in TXT else "id"]
    steps = [st for st in ((s.get("plan") or {}).get("steps") or []) if isinstance(st, dict)]
    if not steps:
        return "", False
    checks = s.get("checks") or {}
    v = sum(1 for st in steps if (checks.get(str(st.get("n"))) or {}).get("passed"))
    return ("✓ " + tx["checked"].format(v=v, n=len(steps)), True) if v else (tx["camera"], False)


def _save(img: Image.Image, out: Path) -> None:
    """256-colour PNG: about 170 KB instead of about 480 KB. WhatsApp skips link-preview images much over 300 KB."""
    img.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG).save(out, "PNG", optimize=True)


def _header(img: Image.Image, d: ImageDraw.ImageDraw, x: int, tag: str) -> None:
    brand.wrench_plate(img, x, 40, 50)
    brand.draw(d, (x + 64, 38), "Tukang Copilot", "display", 46, brand.INK)
    brand.draw(d, (x, 104), tag, "body", 23, brand.MUTED)


def _footer(d: ImageDraw.ImageDraw, x: int, right: int, made: str, demo: str) -> None:
    d.line((x, H - 92, right, H - 92), fill=brand.LINE, width=2)
    brand.draw(d, (x, H - 80), made, "semi", 22, brand.MUTED)
    if demo:
        brand.draw(d, (x, H - 46), demo, "semi", 18, brand.ORANGE_TEXT)


def build(s: dict[str, Any], folder: Path, out: Path) -> Path:
    lang = s.get("lang") if s.get("lang") in TXT else "id"
    tx = TXT[str(lang)]
    img = Image.new("RGB", (W, H), brand.BETON)
    img.paste(_photo(folder, s, (560, H)), (0, 0))
    d = ImageDraw.Draw(img)
    x, right = 600, W - 48
    _header(img, d, x, tx["tag"])

    rep = s.get("object_report") or {}
    dx = s.get("diagnosis") or {}
    plan = s.get("plan") or {}
    y = 150
    for line in brand.wrap(d, str(rep.get("object") or ""), "display", 50, right - x, 2):
        brand.draw(d, (x, y), line, "display", 50, brand.INK)
        y += 52
    causes = dx.get("causes") or []
    idx = int(s.get("cause_index") or 0)
    cause = causes[idx] if 0 <= idx < len(causes) else (causes[0] if causes else None)
    if isinstance(cause, dict) and cause.get("title"):
        y += 16
        # after "Still broken" the card shows the cause being worked on, so say which plan it is: under "Most likely"
        # a friend would read "22%" as the best guess when the 70% one was already tried
        label = tx["plan"].format(n=idx + 1, m=len(causes)) if 0 < idx < len(causes) else tx["likely"]
        brand.draw(d, (x, y), label, "semi", 21, brand.MUTED)
        y += 30
        pct = f"{int(cause.get('confidence') or 0)}%"
        pw = brand.draw(d, (x, y - 6), pct, "display", 60, brand.ORANGE_TEXT)
        lines = brand.wrap(d, str(cause["title"]), "cond", 30, right - x - pw - 18, 2)
        ty = y + (14 if len(lines) == 1 else 0)
        for line in lines:
            brand.draw(d, (x + pw + 18, ty), line, "cond", 30, brand.INK)
            ty += 32
        y += 70
    level = str(dx.get("safety_level") or (s.get("safety") or {}).get("level") or "")
    if level in LEVEL:
        y += 6
        words = LEVEL[level][1]
        col, on = brand.LEVEL[level]
        tw = int(brand.length(d, words[str(lang)], "display", 28))
        d.rounded_rectangle((x, y, x + tw + 30, y + 42), radius=9, fill=col)
        brand.draw(d, (x + 15, y + 5), words[str(lang)], "display", 28, on)
        y += 58
    bits = []
    if plan.get("steps"):
        bits.append(tx["steps"].format(n=len(plan["steps"])))
    if dx.get("minutes_estimate"):
        bits.append(tx["min"].format(m=int(dx["minutes_estimate"])))
    if dx.get("diy_saving_idr") and level != "red":
        bits.append(tx["save"].format(s=_rupiah(dx["diy_saving_idr"])))
    if bits:
        brand.draw(d, (x, y), "  ·  ".join(bits), "semi", 25, brand.INK)
        y += 38
    line, passed = check_line(s, str(lang))
    if line and y < H - 120:
        brand.draw(d, (x, y), line, "semi", 22, brand.GREEN if passed else brand.MUTED)
    _footer(d, x, right, tx["made"], tx["demo"] if s.get("mode") == "mock" else "")
    out.parent.mkdir(parents=True, exist_ok=True)
    _save(img, out)
    return out


HOME_TITLE, HOME_MADE = "Tukang Copilot", "Meta Muse Spark + SAM 3.1"
HOME_HEAD = "Apa yang rusak?"
HOME_LINES = ["Foto + cerita, dapat panduan perbaikan", "AI menandai bagiannya (SAM 3.1)", "Tiap langkah dicek kamera",
              "Bahasa Indonesia · Basa Jawa · English"]


def build_home(photo: Path, out: Path, note: str = "Foto contoh (dibuat AI), mode demo") -> Path:
    """Link preview for the app's front page: a labelled sample photo, AI-generated (ideally with SAM outlines) and a few lines.
    scripts/make_og.py renders web/og.png from a demo motorbike session; /og.png falls back to this at runtime."""
    img = Image.new("RGB", (W, H), brand.BETON)
    try:
        with Image.open(photo) as im:
            img.paste(_panel(im, (560, H)), (0, 0))
    except OSError:
        img.paste(Image.new("RGB", (560, H), brand.DARK_2), (0, 0))
    d = ImageDraw.Draw(img)
    nw = int(brand.length(d, note, "body", 20))
    d.rounded_rectangle((16, H - 52, 16 + nw + 24, H - 16), radius=10, fill=brand.DARK)
    brand.draw(d, (28, H - 47), note, "body", 20, brand.WHITE)
    x, right = 600, W - 48
    _header(img, d, x, HOME_LINES[0])
    brand.draw(d, (x, 150), HOME_HEAD, "display", 76, brand.INK)
    y = 262
    for i, line in enumerate(HOME_LINES[1:3], 1):
        d.rounded_rectangle((x, y + 2, x + 34, y + 36), radius=8, fill=brand.GREEN)
        d.line((x + 8, y + 19, x + 15, y + 26, x + 27, y + 11), fill=brand.WHITE, width=4, joint="curve")
        brand.draw(d, (x + 48, y), line, "semi", 28, brand.INK)
        y += 56
    brand.draw(d, (x, y + 14), HOME_LINES[3], "body", 25, brand.MUTED)
    _footer(d, x, right, HOME_MADE, "")
    out.parent.mkdir(parents=True, exist_ok=True)
    _save(img, out)
    return out
