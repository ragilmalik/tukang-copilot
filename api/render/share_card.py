"""Share card (1200x630 PNG, the Open Graph size): the link preview WhatsApp, X, Telegram and Facebook show when a
repair guide link is shared. Left: the owner's photo with the parts SAM 3.1 outlined. Right: what it is, the most
likely cause, the safety level, and the plan in one line. Demo sessions say so on the card.

Only model output and numbers go on the card, never the owner's own words (same rule as the agent log)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

W, H = 1200, 630
INK, MUTED, ORANGE, PAPER = (28, 32, 38), (95, 99, 110), (180, 83, 9), (255, 250, 244)
LEVEL = {"green": ((22, 120, 60), {"id": "AMAN", "jv": "AMAN", "en": "SAFE"}),
         "amber": ((176, 104, 0), {"id": "HATI-HATI", "jv": "ATI-ATI", "en": "CAUTION"}),
         "red": ((185, 28, 28), {"id": "STOP", "jv": "MANDHEG", "en": "STOP"})}
TXT = {
    "id": {"likely": "Paling mungkin", "steps": "{n} langkah", "min": "~{m} menit", "save": "hemat Rp{s}",
           "checked": "Tiap langkah dicek kamera", "demo": "MODE DEMO: jawaban contoh, foto pengganti",
           "tag": "Foto + cerita → panduan perbaikan", "made": "Meta Muse Spark + SAM 3.1"},
    "jv": {"likely": "Sing paling mungkin", "steps": "{n} langkah", "min": "~{m} menit", "save": "irit Rp{s}",
           "checked": "Saben langkah dipriksa kamera", "demo": "MODE DEMO: wangsulan conto, foto gantosan",
           "tag": "Foto + crita → tuntunan ndandani", "made": "Meta Muse Spark + SAM 3.1"},
    "en": {"likely": "Most likely", "steps": "{n} steps", "min": "~{m} min", "save": "save Rp{s}",
           "checked": "Every step camera-checked", "demo": "DEMO MODE: sample answers, stand-in photo",
           "tag": "Photo + a few words → a repair guide", "made": "Meta Muse Spark + SAM 3.1"},
}
_FONT_DIRS = ("/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/dejavu", "")


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    for d in _FONT_DIRS:
        try:
            return ImageFont.truetype(str(Path(d) / name) if d else name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: Any, width: int, max_lines: int) -> list[str]:
    words, lines, cur = (text or "").split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=font) <= width:
            cur = trial
            continue
        if cur:
            lines.append(cur)
        cur = w
        if len(lines) == max_lines:
            break
    if cur and len(lines) < max_lines:
        lines.append(cur)
    if len(lines) == max_lines and " ".join(lines) != " ".join(words):  # cut: end the last line with an ellipsis
        last = lines[-1]
        while last and draw.textlength(last + "…", font=font) > width:
            last = last[:-1]
        lines[-1] = last.rstrip(" ,;:.") + "…"
    return lines


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


def build(s: dict[str, Any], folder: Path, out: Path) -> Path:
    lang = s.get("lang") if s.get("lang") in TXT else "id"
    tx = TXT[str(lang)]
    img = Image.new("RGB", (W, H), PAPER)
    img.paste(_photo(folder, s, (560, H)), (0, 0))
    d = ImageDraw.Draw(img)
    x, right = 600, W - 48
    d.text((x, 44), "Tukang Copilot", font=_font(40, True), fill=INK)
    d.text((x, 96), tx["tag"], font=_font(24), fill=MUTED)

    rep = s.get("object_report") or {}
    dx = s.get("diagnosis") or {}
    plan = s.get("plan") or {}
    y = 150
    for line in _wrap(d, str(rep.get("object") or ""), _font(42, True), right - x, 2):
        d.text((x, y), line, font=_font(42, True), fill=INK)
        y += 54
    causes = dx.get("causes") or []
    idx = int(s.get("cause_index") or 0)
    cause = causes[idx] if 0 <= idx < len(causes) else (causes[0] if causes else None)
    if isinstance(cause, dict) and cause.get("title"):
        y += 10
        d.text((x, y), f"{tx['likely']}:", font=_font(24), fill=MUTED)
        y += 34
        for line in _wrap(d, f"{cause['title']} ({int(cause.get('confidence') or 0)}%)", _font(32, True), right - x, 2):
            d.text((x, y), line, font=_font(32, True), fill=ORANGE)
            y += 42
    level = str(dx.get("safety_level") or (s.get("safety") or {}).get("level") or "")
    if level in LEVEL:
        y += 14
        col, words = LEVEL[level]
        f = _font(26, True)
        tw = int(d.textlength(words[str(lang)], font=f))
        d.rounded_rectangle((x, y, x + tw + 32, y + 44), radius=22, fill=col)
        d.text((x + 16, y + 7), words[str(lang)], font=f, fill=(255, 255, 255))
        y += 60
    bits = []
    if plan.get("steps"):
        bits.append(tx["steps"].format(n=len(plan["steps"])))
    if dx.get("minutes_estimate"):
        bits.append(tx["min"].format(m=int(dx["minutes_estimate"])))
    if dx.get("diy_saving_idr") and level != "red":
        bits.append(tx["save"].format(s=_rupiah(dx["diy_saving_idr"])))
    if bits:
        d.text((x, y), "  ·  ".join(bits), font=_font(26), fill=INK)
        y += 40
    if plan.get("steps"):
        d.text((x, y), "✓ " + tx["checked"], font=_font(24), fill=(22, 120, 60))
    # footer: models + an honest demo label
    d.line((x, H - 92, right, H - 92), fill=(230, 222, 210), width=2)
    d.text((x, H - 78), tx["made"], font=_font(22, True), fill=MUTED)
    if s.get("mode") == "mock":
        d.text((x, H - 46), tx["demo"], font=_font(19), fill=ORANGE)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG", optimize=True)
    return out


HOME_TITLE, HOME_MADE = "Tukang Copilot", "Meta Muse Spark + SAM 3.1"
HOME_LINES = ["Foto + cerita → panduan perbaikan", "AI menandai bagiannya (SAM 3.1)", "Tiap langkah dicek kamera",
              "Bahasa Indonesia · Basa Jawa · English"]


def build_home(photo: Path, out: Path, note: str = "Foto contoh (pengganti)") -> Path:
    """Link preview for the app's front page: a labelled stand-in photo (ideally with SAM outlines) and four lines.
    scripts/make_og.py renders web/og.png from a demo motorbike session; /og.png falls back to this at runtime."""
    img = Image.new("RGB", (W, H), PAPER)
    try:
        with Image.open(photo) as im:
            img.paste(_panel(im, (560, H)), (0, 0))
    except OSError:
        img.paste(Image.new("RGB", (560, H), (60, 64, 72)), (0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((16, H - 52, 16 + int(d.textlength(note, font=_font(20))) + 24, H - 16), radius=14, fill=(0, 0, 0))
    d.text((28, H - 47), note, font=_font(20), fill=(255, 255, 255))
    x = 600
    d.text((x, 70), HOME_TITLE, font=_font(54, True), fill=INK)
    y = 170
    for i, line in enumerate(HOME_LINES):
        d.text((x, y), ("✓ " if i in (1, 2) else "") + line, font=_font(28, i == 0), fill=ORANGE if i == 0 else INK)
        y += 62
    d.line((x, H - 92, W - 48, H - 92), fill=(230, 222, 210), width=2)
    d.text((x, H - 78), HOME_MADE, font=_font(22, True), fill=MUTED)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG", optimize=True)
    return out
