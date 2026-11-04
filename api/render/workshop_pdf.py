"""Workshop sheets: a large-print, one-step-per-page A4 PDF to pin up next to the bike or pump.

Pure Pillow, same look as the repair report. Page 1 is the cover (safety banner, marked photo, tools and
parts as a tick list). Then one page per step with a giant number, the instruction in big type, the
warnings in a red box, what the camera should see, and the step diagram when there is one. The "Done when"
check closes the last step page when it fits there.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from . import brand
from .report_pdf import INK, LABELS, M, MUTED, SAFETY_COLOR, W, _Doc, rupiah

ORANGE = brand.ORANGE_TEXT  # orange as text: the darker shade, readable on white paper

TXT: dict[str, dict[str, str]] = {
    "id": {"title": "Lembar Bengkel", "step": "LANGKAH", "of": "dari", "look": "Kalau sudah benar, kamera melihat:", "warn": "HATI-HATI",
           "wait": "Tunggu {n} menit", "gather": "Siapkan dulu", "done": "Selesai kalau:", "tick": "Centang setelah selesai", "empty": "Tidak ada langkah"},
    "en": {"title": "Workshop Sheet", "step": "STEP", "of": "of", "look": "When it is right, the camera sees:", "warn": "CAREFUL",
           "wait": "Wait {n} minutes", "gather": "Get these ready", "done": "Done when:", "tick": "Tick when finished", "empty": "No steps"},
    "jv": {"title": "Lembar Bengkel", "step": "LANGKAH", "of": "saka", "look": "Yen wis bener, kamera ndeleng:", "warn": "ATI-ATI",
           "wait": "Enteni {n} menit", "gather": "Cepakna dhisik", "done": "Rampung yen:", "tick": "Centhang yen wis rampung", "empty": "Ora ana langkah"},
}


def _box(doc: _Doc, x: int, y: int, size: int = 44) -> None:
    doc.d.rounded_rectangle([x, y, x + size, y + size], radius=8, outline=INK, width=4)


def _banner(doc: _Doc, level: str, labels: dict[str, str]) -> None:
    fill, on = brand.LEVEL.get(level, (brand.PLATE_2, INK))
    doc.need(84)
    doc.d.rounded_rectangle([M, doc.y, W - M, doc.y + 72], radius=16, fill=fill)
    tw = brand.draw(doc.d, (M + 24, doc.y + 8), labels.get(level, level.upper()), "display", 52, on)
    brand.draw(doc.d, (M + 24 + tw + 18, doc.y + 24), labels["safety"], "semi", 28, on)
    doc.y += 92


def _cover(doc: _Doc, rep: dict[str, Any], session: dict[str, Any], session_dir: Path, L: dict[str, str], T: dict[str, str]) -> None:
    doc.band(T["title"], f"{rep.get('object') or ''}")
    doc.space(10)
    if rep.get("safety_level"):
        _banner(doc, str(rep["safety_level"]), L)
    for key in ("problem", "fix"):
        if rep.get(key):
            doc.text(L[key], 24, bold=True, color=MUTED, gap=4)
            doc.text(str(rep[key]), 32)
            doc.space(8)
    photo = session_dir / (session.get("parts_image") or "")
    if session.get("parts_image") and photo.exists():
        doc.image(photo, 520)
    rows = [(L["tools"], rep.get("tools") or []), (L["parts"], rep.get("parts") or [])]
    if any(r for _, r in rows):
        doc.rule()
        doc.text(T["gather"], 36, bold=True)
        for head, items in rows:
            for it in items:
                doc.need(60)
                _box(doc, M, doc.y, 36)
                price = int(it.get("est_price_idr") or 0)
                name = brand.wrap(doc.d, str(it.get("name", "")), "body", 32, W - 2 * M - 260, 1)[0]
                brand.draw(doc.d, (M + 58, doc.y - 2), name, "body", 32, INK)
                if price:
                    tag = rupiah(price)
                    brand.draw(doc.d, (W - M - brand.length(doc.d, tag, "semi", 32), doc.y - 2), tag, "semi", 32, MUTED)
                doc.y += 54


def _step_page(doc: _Doc, st: dict[str, Any], total: int, session: dict[str, Any], session_dir: Path, T: dict[str, str]) -> None:
    doc._new_page()
    n = st.get("n")
    doc.text(f"{T['step']} {n} {T['of']} {total}", 44, color=ORANGE, kind="display")
    doc.text(str(st.get("instruction", "")), 56, kind="cond", gap=12)
    if st.get("why"):
        doc.space(6)
        doc.text(str(st["why"]), 30, color=MUTED, gap=10)
    wait = int(st.get("wait_minutes") or 0)
    if wait > 0:
        doc.space(10)
        doc.need(56)
        doc.box(M, doc.y + 2, 40)
        doc.text(T["wait"].replace("{n}", str(wait)), 40, bold=True, color=ORANGE, gap=8, indent=60)
    warns = [str(w) for w in st.get("warnings") or [] if w]
    if warns:
        doc.space(14)
        lines = [ln for w in warns for ln in brand.wrap(doc.d, "! " + w, "semi", 30, W - 2 * M - 60)]
        h = 86 + len(lines) * 42
        doc.need(h)
        doc.d.rounded_rectangle([M, doc.y, W - M, doc.y + h], radius=16, fill=brand.RED_TINT, outline=SAFETY_COLOR["red"], width=6)
        doc.d.rounded_rectangle([M, doc.y, W - M, doc.y + 60], radius=16, fill=SAFETY_COLOR["red"])
        doc.d.rectangle([M, doc.y + 40, W - M, doc.y + 60], fill=SAFETY_COLOR["red"])
        brand.draw(doc.d, (M + 30, doc.y + 6), T["warn"], "display", 40, brand.WHITE)
        yy = doc.y + 76
        for ln in lines:
            brand.draw(doc.d, (M + 30, yy), ln, "semi", 30, brand.RED)
            yy += 42
        doc.y += h + 16
    if st.get("expected_state"):
        doc.space(10)
        doc.text(T["look"], 24, bold=True, color=MUTED, gap=4)
        doc.text(str(st["expected_state"]), 32, gap=10)
    diag = (session.get("diagrams") or {}).get(str(n), {}).get("file")
    pic = diag if diag and (session_dir / diag).exists() else (session.get("parts_image") or "")
    if pic and (session_dir / pic).exists():  # the step diagram, else the marked photo so the page is never empty
        doc.space(10)
        doc.image(session_dir / pic, 560)
    y = TICK_Y
    _box(doc, M, y, 60)
    brand.draw(doc.d, (M + 84, y + 10), T["tick"], "semi", 32, INK)


TICK_Y = 1754 - M - 120  # the "tick when finished" box at the foot of every step page


def _done_height(doc: _Doc, done: str, disclaimer: str) -> int:
    """Height of the "Done when" block as _done_block draws it (heading, check, disclaimer)."""
    width = W - 2 * M
    return (44 + 10 + len(brand.wrap(doc.d, done, "cond", 50, width)) * (50 + 14) + 30
            + len(brand.wrap(doc.d, disclaimer, "body", 26, width)) * (26 + 8))


def _done_block(doc: _Doc, done: str, disclaimer: str, T: dict[str, str]) -> None:
    doc.text(T["done"], 44, color=brand.GREEN, kind="display", gap=10)
    doc.text(done, 50, kind="cond", gap=14)
    doc.space(30)
    doc.text(disclaimer, 26, color=MUTED)


def done_fits(doc: _Doc, done: str, disclaimer: str) -> bool:
    """True when the "Done when" check fits at the foot of the last step page, above the tick box with a little
    air. Otherwise it gets its own page (it used to sit alone on a near-empty one every time)."""
    return doc.y + 40 + _done_height(doc, done, disclaimer) <= TICK_Y - 30


def build(rep: dict[str, Any], session: dict[str, Any], session_dir: Path, out: Path) -> Path:
    """Draw the workshop sheets for one session. `rep` is engine.report(); `session` the full session dict."""
    lang = str(rep.get("lang") or "id")
    if lang not in LABELS:
        lang = "id"
    L, T = LABELS[lang], TXT[lang]
    doc = _Doc(L["made"], L["page"])
    _cover(doc, rep, session, session_dir, L, T)
    plan = session.get("plan") or {}
    steps = plan.get("steps") or []
    for st in steps:
        _step_page(doc, st, len(steps), session, session_dir, T)
    if plan.get("done_check"):
        done, disc = str(plan["done_check"]), str(L["disclaimer"])
        if steps and done_fits(doc, done, disc):
            doc.space(40)
            doc.d.line([M, doc.y - 20, W - M, doc.y - 20], fill=brand.LINE, width=2)
        else:
            doc._new_page()
        _done_block(doc, done, disc, T)
    elif not steps:
        doc.text(T["empty"], 32, color=MUTED)
    pages = doc.finish()
    out.parent.mkdir(parents=True, exist_ok=True)
    pages[0].save(out, "PDF", resolution=150.0, save_all=True, append_images=pages[1:])
    return out

