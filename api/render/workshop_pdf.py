"""Workshop sheets: a large-print, one-step-per-page A4 PDF to pin up next to the bike or pump.

Pure Pillow, same look as the repair report. Page 1 is the cover (safety banner, marked photo, tools and
parts as a tick list). Then one page per step with a giant number, the instruction in big type, the
warnings in a red box, what the camera should see, and the step diagram when there is one.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .report_pdf import INK, LABELS, M, MUTED, ORANGE, SAFETY_COLOR, W, _Doc, _font, _wrap, rupiah

TXT: dict[str, dict[str, str]] = {
    "id": {"title": "Lembar Bengkel", "step": "LANGKAH", "of": "dari", "look": "Kalau sudah benar, kamera melihat:", "warn": "HATI-HATI",
           "gather": "Siapkan dulu", "done": "Selesai kalau:", "tick": "Centang setelah selesai", "empty": "Tidak ada langkah"},
    "en": {"title": "Workshop Sheet", "step": "STEP", "of": "of", "look": "When it is right, the camera sees:", "warn": "CAREFUL",
           "gather": "Get these ready", "done": "Done when:", "tick": "Tick when finished", "empty": "No steps"},
    "jv": {"title": "Lembar Bengkel", "step": "LANGKAH", "of": "saka", "look": "Yen wis bener, kamera ndeleng:", "warn": "ATI-ATI",
           "gather": "Cepakna dhisik", "done": "Rampung yen:", "tick": "Centhang yen wis rampung", "empty": "Ora ana langkah"},
}


def _box(doc: _Doc, x: int, y: int, size: int = 44) -> None:
    doc.d.rounded_rectangle([x, y, x + size, y + size], radius=8, outline=INK, width=4)


def _banner(doc: _Doc, level: str, labels: dict[str, str]) -> None:
    col = SAFETY_COLOR.get(level, MUTED)
    label, bf = f"{labels['safety']}: {labels.get(level, level.upper())}", _font(32, True)
    doc.need(70)
    doc.d.rounded_rectangle([M, doc.y, M + 40 + int(doc.d.textlength(label, font=bf)), doc.y + 60], radius=14, fill=col)
    doc.d.text((M + 20, doc.y + 12), label, font=bf, fill="white")
    doc.y += 80


def _cover(doc: _Doc, rep: dict[str, Any], session: dict[str, Any], session_dir: Path, L: dict[str, str], T: dict[str, str]) -> None:
    doc.d.rectangle([0, 0, W, 18], fill=ORANGE)
    doc.text(T["title"], 64, bold=True)
    doc.text(f"{rep.get('object') or ''}", 40, bold=True, color=MUTED)
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
                f = _font(32)
                doc.d.text((M + 58, doc.y - 2), f"{it.get('name', '')}", font=f, fill=INK)
                if price:
                    tag = rupiah(price)
                    doc.d.text((W - M - doc.d.textlength(tag, font=f), doc.y - 2), tag, font=f, fill=MUTED)
                doc.y += 54


def _step_page(doc: _Doc, st: dict[str, Any], total: int, session: dict[str, Any], session_dir: Path, T: dict[str, str]) -> None:
    doc._new_page()
    doc.d.rectangle([0, 0, W, 18], fill=ORANGE)
    n = st.get("n")
    doc.text(f"{T['step']} {n} {T['of']} {total}", 40, bold=True, color=ORANGE)
    doc.text(str(st.get("instruction", "")), 54, bold=True, gap=14)
    if st.get("why"):
        doc.space(6)
        doc.text(str(st["why"]), 30, color=MUTED, gap=10)
    warns = [str(w) for w in st.get("warnings") or [] if w]
    if warns:
        doc.space(14)
        f = _font(30, True)
        lines = [T["warn"]] + [ln for w in warns for ln in _wrap(doc.d, "! " + w, f, W - 2 * M - 60)]
        h = 30 + len(lines) * 42
        doc.need(h)
        doc.d.rounded_rectangle([M, doc.y, W - M, doc.y + h], radius=16, outline=SAFETY_COLOR["red"], width=6)
        yy = doc.y + 18
        for ln in lines:
            doc.d.text((M + 30, yy), ln, font=f, fill=SAFETY_COLOR["red"])
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
    y = 1754 - M - 120
    _box(doc, M, y, 60)
    doc.d.text((M + 84, y + 10), T["tick"], font=_font(32, True), fill=INK)


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
        doc._new_page()
        doc.d.rectangle([0, 0, W, 18], fill=ORANGE)
        doc.text(T["done"], 44, bold=True, color=ORANGE)
        doc.text(str(plan["done_check"]), 50, bold=True, gap=14)
        doc.space(30)
        doc.text(L["disclaimer"], 26, color=MUTED)
    elif not steps:
        doc.text(T["empty"], 32, color=MUTED)
    pages = doc.finish()
    out.parent.mkdir(parents=True, exist_ok=True)
    pages[0].save(out, "PDF", resolution=150.0, save_all=True, append_images=pages[1:])
    return out

