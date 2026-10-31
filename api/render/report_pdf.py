"""Printable repair report (SPEC v2: PDF repair report). Pure Pillow, no extra dependency: each A4 page is
drawn as an image and saved as a multi-page PDF. Works the same in demo mode and live mode.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from .. import handoff
from ..trace import build_trace

W, H = 1240, 1754  # A4 at 150 dpi
M = 90  # margin
INK, MUTED, ORANGE = (28, 28, 30), (110, 110, 118), (255, 122, 0)
SAFETY_COLOR = {"green": (34, 150, 80), "amber": (215, 140, 0), "red": (205, 40, 40)}

LABELS: dict[str, dict[str, str]] = {
    "id": {"title": "Laporan Perbaikan", "object": "Barang", "problem": "Masalah", "fix": "Penyebab yang diperbaiki", "safety": "Keselamatan",
           "steps": "Langkah", "verified": "terverifikasi kamera", "tools": "Alat", "parts": "Suku cadang", "total": "Perkiraan biaya suku cadang",
           "shop": "Harga bengkel biasanya (jasa + suku cadang)", "save": "Hemat sendiri (hanya suku cadang)",
           "attempts": "Percobaan", "minutes": "menit", "outcome": "Hasil", "o_fixed": "Beres: sudah jalan lagi (kata pemilik)",
           "o_pro": "Dibawa ke bengkel/teknisi", "status": "Status", "ok": "[OK]", "todo": "[  ]", "photo": "Foto dengan bagian yang ditandai (SAM 3.1)",
           "disclaimer": "Panduan ini hanya untuk perbaikan ringan. Harga adalah perkiraan. Untuk gas, listrik rumah, atau tegangan tinggi, panggil teknisi.",
           "made": "Dibuat dengan Tukang Copilot (Meta Muse Spark + SAM 3.1)", "page": "Hal.", "demo": "Mode demo: jawaban contoh",
           "green": "AMAN", "amber": "HATI-HATI", "red": "STOP",
           "hood": "Di balik layar: model yang dipakai", "before": "Sebelum mulai, pastikan",
           "st_listen": "Dengar suara", "st_gate": "Cek keselamatan teks", "st_look": "Lihat foto", "st_segment": "Tandai bagian",
           "st_diagnose": "Diagnosa", "st_plan": "Susun langkah", "st_safety": "Cek keselamatan rencana", "st_illustrate": "Gambar bantu",
           "st_narrate": "Suara pemandu"},
    "en": {"title": "Repair Report", "object": "Item", "problem": "Problem", "fix": "Cause fixed", "safety": "Safety",
           "steps": "Steps", "verified": "verified by camera", "tools": "Tools", "parts": "Parts", "total": "Estimated parts cost",
           "shop": "Typical shop price (labour + parts)", "save": "Saved by doing it yourself (parts only)",
           "attempts": "Attempts", "minutes": "min", "outcome": "Result", "o_fixed": "Fixed: it works again (owner's word)",
           "o_pro": "Handed to a mechanic/professional", "status": "Status", "ok": "[OK]", "todo": "[  ]", "photo": "Photo with the parts marked (SAM 3.1)",
           "disclaimer": "Light repairs only. Prices are estimates. For gas, house wiring, or high voltage, call a professional.",
           "made": "Made with Tukang Copilot (Meta Muse Spark + SAM 3.1)", "page": "Page", "demo": "Demo mode: sample answers",
           "green": "SAFE", "amber": "CAUTION", "red": "STOP",
           "hood": "Under the hood: models used", "before": "Before you start, make sure",
           "st_listen": "Listen", "st_gate": "Text safety gate", "st_look": "Look at photo", "st_segment": "Mark parts",
           "st_diagnose": "Diagnose", "st_plan": "Plan steps", "st_safety": "Plan safety gate", "st_illustrate": "Helper diagram",
           "st_narrate": "Voice guide"},
}
LABELS["jv"] = dict(LABELS["id"], title="Laporan Ndandani", object="Barang", problem="Masalah", fix="Sing didandani", safety="Keslametan",
                    steps="Langkah", tools="Piranti", made="Digawe nganggo Tukang Copilot (Meta Muse Spark + SAM 3.1)",
                    outcome="Asil", o_fixed="Rampung: wis urip maneh (jarene sing duwe)", o_pro="Digawa menyang bengkel/teknisi")


BRIEF: dict[str, dict[str, str]] = {
    "id": {"title": "Ringkasan untuk mekanik", "sub": "Halaman ini bisa dicetak atau ditunjukkan ke bengkel supaya tidak mulai dari nol.",
           "found": "Yang ditemukan", "issues": "Terlihat di foto", "causes": "Kemungkinan penyebab", "marked": "Bagian yang ditandai",
           "tried": "Yang sudah dicoba", "nothing": "Belum ada: dihentikan sebelum mulai demi keselamatan.", "checks": "Cek kamera per langkah",
           "pass": "OK", "fail": "BELUM", "status": "Status", "red": "STOP keselamatan", "exhausted": "Semua penyebab aman sudah dicoba",
           "requested": "Pemilik minta bantuan mekanik", "photos": "Foto dari pemilik", "photo": "Foto", "check": "Cek langkah"},
    "jv": {"title": "Ringkesan kanggo mekanik", "sub": "Kaca iki bisa dicithak utawa dituduhake menyang bengkel supaya ora miwiti saka nol.",
           "found": "Sing ditemokake", "issues": "Katon ing foto", "causes": "Sebab sing mungkin", "marked": "Perangan sing ditandhani",
           "tried": "Sing wis dijajal", "nothing": "Durung ana: dimandhegake sadurunge miwiti kanggo keslametan.", "checks": "Cek kamera saben langkah",
           "pass": "OK", "fail": "DURUNG", "status": "Status", "red": "MANDHEG keslametan", "exhausted": "Kabeh sebab sing aman wis dijajal",
           "requested": "Sing duwe njaluk bantuan mekanik", "photos": "Foto saka sing duwe", "photo": "Foto", "check": "Cek langkah"},
    "en": {"title": "Mechanic brief", "sub": "Print this page or show it to the workshop so they don't start from zero.",
           "found": "What was found", "issues": "Seen in the photo", "causes": "Likely causes", "marked": "Parts marked",
           "tried": "What was tried", "nothing": "Nothing: stopped before starting, for safety.", "checks": "Camera check per step",
           "pass": "OK", "fail": "NOT YET", "status": "Status", "red": "Safety STOP", "exhausted": "Every safe cause was tried",
           "requested": "Owner asked for a mechanic", "photos": "Owner's photos", "photo": "Photo", "check": "Step check"},
}


def brief_lines(session: dict[str, Any], lang: str) -> list[tuple[str, str]]:
    """The mechanic brief as (kind, text) rows: kind is h (heading), t (text), m (muted). Pure, so it is testable."""
    B = BRIEF.get(lang, BRIEF["id"])
    rep, dx = session.get("object_report") or {}, session.get("diagnosis") or {}
    why = handoff.reason(session)
    rows: list[tuple[str, str]] = [("m", B["sub"]), ("h", B["status"]), ("t", B[why])]
    if why == "red" and session.get("stop_reason"):
        rows.append(("t", str(session["stop_reason"])))
    rows.append(("h", B["found"]))
    obj, brand = str(rep.get("object") or ""), str(rep.get("brand_model_guess") or "")
    if brand and brand.lower().split()[0] not in obj.lower():
        obj = f"{obj} ({brand})".strip()
    if obj:
        rows.append(("t", obj))
    if dx.get("problem_summary"):
        rows.append(("t", str(dx["problem_summary"])))
    if rep.get("visible_issues"):
        rows.append(("m", f"{B['issues']}: " + "; ".join(str(x) for x in rep["visible_issues"])))
    for c in dx.get("causes") or []:
        ev = "; ".join(str(e) for e in c.get("evidence") or [])
        rows.append(("t", f"- {c.get('title', '')} ({int(c.get('confidence') or 0)}%)" + (f": {ev}" if ev else "")))
    marked = [f"{v.get('label')}. {v.get('name')}" for v in (session.get("parts") or {}).values() if v.get("found")]
    if marked:
        rows.append(("m", f"{B['marked']}: " + ", ".join(marked)))
    rows.append(("h", B["tried"]))
    done = handoff.tried(session, why)
    rows += [("t", f"- {x}") for x in done] or [("t", B["nothing"])]
    for a in session.get("history") or []:
        rows.append(("m", f"  {a}"))
    checks = session.get("checks") or {}
    steps = (session.get("plan") or {}).get("steps") or []
    tried_steps = [st for st in steps if checks.get(str(st.get("n")), {}).get("tries")]
    if tried_steps:
        rows.append(("h", B["checks"]))
        for st in tried_steps:
            last = checks[str(st["n"])]["tries"][-1]
            mark = B["pass"] if last.get("passed") else B["fail"]
            n_try = len(checks[str(st["n"])]["tries"])
            rows.append(("t", f"{st['n']}. [{mark}] {st.get('instruction', '')}"))
            rows.append(("m", f"   {last.get('observation', '')}" + (f" ({n_try}x)" if n_try > 1 else "")))
    return rows


def brief_photos(session: dict[str, Any], session_dir: Path, lang: str, limit: int = 6) -> list[tuple[Path, str]]:
    """Owner's photos first, then the newest step-check photos, as (path, caption)."""
    B = BRIEF.get(lang, BRIEF["id"])
    out = [(session_dir / p, f"{B['photo']} {i}") for i, p in enumerate(session.get("photos") or [], 1)]
    checks = []
    for n, rec in (session.get("checks") or {}).items():
        for t in rec.get("tries") or []:
            checks.append((session_dir / str(t.get("photo")), f"{B['check']} {n}: {B['pass'] if t.get('passed') else B['fail']}"))
    out += checks[::-1]
    return [(p, c) for p, c in out if p.exists()][:limit]


def _draw_brief(doc: _Doc, session: dict[str, Any], session_dir: Path, lang: str) -> None:
    B = BRIEF.get(lang, BRIEF["id"])
    doc._new_page()
    doc.d.rectangle([0, 0, W, 14], fill=ORANGE)
    doc.text(B["title"], 40, bold=True)
    for kind, txt in brief_lines(session, lang):
        if kind == "h":
            doc.space(8)
            doc.text(txt, 28, bold=True)
        elif kind == "m":
            doc.text(txt, 21, color=MUTED, indent=10)
        else:
            doc.text(txt, 24, indent=10)
    pics = brief_photos(session, session_dir, lang)
    if not pics:
        return
    doc.space(8)
    doc.text(B["photos"], 28, bold=True)
    cell_w, cell_h = (W - 2 * M - 30) // 2, 330
    for i in range(0, len(pics), 2):
        doc.need(cell_h + 40)
        for j, (path, cap) in enumerate(pics[i:i + 2]):
            try:
                with Image.open(path) as src:
                    pic = src.convert("RGB")
            except OSError:
                continue
            pic.thumbnail((cell_w, cell_h))
            x = M + j * (cell_w + 30)
            doc.im.paste(pic, (x, doc.y))
            doc.d.rectangle([x, doc.y, x + pic.width, doc.y + pic.height], outline=(200, 200, 205), width=2)
            doc.d.text((x, doc.y + pic.height + 6), cap, font=_font(20), fill=MUTED)
        doc.y += cell_h + 40


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in (("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"),):
        for folder in ("/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/dejavu"):
            p = Path(folder) / name
            if p.exists():
                return ImageFont.truetype(str(p), size)
    return ImageFont.load_default(size=size)


def rupiah(n: int | float | None) -> str:
    return "Rp" + f"{int(n or 0):,}".replace(",", ".")


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: Any, width: int) -> list[str]:
    lines: list[str] = []
    for para in (text or "").split("\n"):
        cur = ""
        for word in para.split():
            trial = f"{cur} {word}".strip()
            if draw.textlength(trial, font=font) <= width or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
    return lines


class _Doc:
    def __init__(self, footer: str, page_word: str) -> None:
        self.pages: list[Image.Image] = []
        self.footer, self.page_word = footer, page_word
        self.f_body, self.f_small = _font(26), _font(21)
        self._new_page()

    def _new_page(self) -> None:
        self.im = Image.new("RGB", (W, H), "white")
        self.d = ImageDraw.Draw(self.im)
        self.pages.append(self.im)
        self.y = M

    def need(self, h: int) -> None:
        if self.y + h > H - M - 40:
            self._new_page()

    def text(self, s: str, size: int = 26, bold: bool = False, color: tuple[int, int, int] = INK, indent: int = 0, gap: int = 8) -> None:
        f = _font(size, bold)
        for line in _wrap(self.d, s, f, W - 2 * M - indent):
            self.need(size + gap)
            self.d.text((M + indent, self.y), line, font=f, fill=color)
            self.y += size + gap

    def space(self, h: int = 18) -> None:
        self.y += h

    def rule(self) -> None:
        self.need(20)
        self.d.line([M, self.y + 6, W - M, self.y + 6], fill=(225, 225, 230), width=2)
        self.y += 22

    def image(self, path: Path, max_h: int = 620) -> None:
        try:
            with Image.open(path) as src:
                pic = src.convert("RGB")
        except OSError:
            return
        pic.thumbnail((W - 2 * M, max_h))
        self.need(pic.height + 10)
        self.im.paste(pic, (M, self.y))
        self.y += pic.height + 14

    def finish(self) -> list[Image.Image]:
        n = len(self.pages)
        for i, page in enumerate(self.pages, 1):
            d = ImageDraw.Draw(page)
            d.line([M, H - M - 10, W - M, H - M - 10], fill=(225, 225, 230), width=2)
            d.text((M, H - M), self.footer, font=self.f_small, fill=MUTED)
            tag = f"{self.page_word} {i}/{n}"
            d.text((W - M - d.textlength(tag, font=self.f_small), H - M), tag, font=self.f_small, fill=MUTED)
        return self.pages


def build(rep: dict[str, Any], session: dict[str, Any], session_dir: Path, out: Path) -> Path:
    """Draw the report for one session. `rep` is engine.report(); `session` the full session dict."""
    lang = str(rep.get("lang") or "id")
    if lang not in LABELS:
        lang = "id"
    L = LABELS[lang]
    doc = _Doc(L["made"], L["page"])
    doc.d.rectangle([0, 0, W, 14], fill=ORANGE)
    doc.text(f"Tukang Copilot: {L['title']}", 46, bold=True)
    doc.text(f"#{rep.get('id', '')}" + (f"   {L['demo']}" if session.get("mode") == "mock" else ""), 22, color=MUTED)
    doc.rule()

    level = rep.get("safety_level") or ""
    if level:
        doc.need(60)
        col = SAFETY_COLOR.get(level, MUTED)
        label, bf = f"{L['safety']}: {L.get(level, level.upper())}", _font(26, True)
        doc.d.rounded_rectangle([M, doc.y, M + 36 + int(doc.d.textlength(label, font=bf)), doc.y + 48], radius=12, fill=col)
        doc.d.text((M + 18, doc.y + 9), label, font=bf, fill="white")
        doc.y += 64
        reason = (session.get("safety") or {}).get("reason") or ""
        if reason:
            doc.text(reason, 24, color=MUTED)
    if session.get("stop_reason"):
        doc.text(str(session["stop_reason"]), 26, bold=True, color=SAFETY_COLOR["red"])

    for key, val in (("object", rep.get("object")), ("problem", rep.get("problem")), ("fix", rep.get("fix"))):
        if val:
            doc.space(6)
            doc.text(L[key], 22, bold=True, color=MUTED, gap=4)
            doc.text(str(val), 28)

    photo = session_dir / (session.get("parts_image") or "")
    if session.get("parts_image") and photo.exists():
        doc.space(10)
        doc.text(L["photo"], 22, bold=True, color=MUTED, gap=4)
        doc.image(photo, 560)

    pre = [str(x) for x in ((session.get("diagnosis") or {}).get("before_you_start") or []) if x]
    if pre:
        doc.space(6)
        doc.text(L["before"], 24, bold=True, color=MUTED, gap=4)
        for x in pre:
            doc.text(f"{L['todo']}  {x}", 24, indent=10)

    steps = (session.get("plan") or {}).get("steps", [])
    if steps:
        doc.rule()
        doc.text(f"{L['steps']} ({rep.get('steps_verified', 0)}/{rep.get('steps_total', 0)} {L['verified']})", 30, bold=True)
        checks = session.get("checks") or {}
        for st in steps:
            ok = bool(checks.get(str(st.get("n")), {}).get("passed"))
            doc.text(f"{L['ok'] if ok else L['todo']}  {st.get('n')}. {st.get('instruction', '')}", 25, color=INK if ok else (60, 60, 66), indent=0)
            if st.get("expected_state"):
                doc.text(f"-> {st['expected_state']}", 22, color=MUTED, indent=70)
        done = (session.get("plan") or {}).get("done_check")
        if done:
            doc.space(6)
            doc.text(done, 24, bold=True)

    items = [(L["tools"], rep.get("tools") or []), (L["parts"], rep.get("parts") or [])]
    if any(v for _, v in items):
        doc.rule()
        total = 0
        for head, rows in items:
            if not rows:
                continue
            doc.text(head, 28, bold=True)
            for r in rows:
                price = int(r.get("est_price_idr") or 0)
                total += price
                doc.text(f"- {r.get('name', '')}   {rupiah(price) if price else ''}", 24, indent=10)
            doc.space(6)
        parts_total = sum(int(r.get("est_price_idr") or 0) for r in items[1][1]) if len(items) > 1 else total
        shown = rep.get("cost_estimate_idr") or parts_total
        mins = rep.get("minutes_estimate")
        doc.text(f"{L['total']}: {rupiah(shown)}" + (f"   ~{mins} {L['minutes']}" if mins else ""), 26, bold=True)
        shop, saving = int(rep.get("shop_cost_estimate_idr") or 0), int(rep.get("diy_saving_idr") or 0)
        if shop:
            doc.text(f"{L['shop']}: {rupiah(shop)}", 24)
            if saving:
                doc.text(f"{L['save']}: {rupiah(saving)}", 24)

    oc = rep.get("outcome") or {}
    if oc.get("result") in ("fixed", "pro"):
        doc.rule()
        doc.text(f"{L['outcome']}: {L['o_' + oc['result']]}", 28, bold=True)
        if oc.get("saved_idr"):
            doc.text(f"{L['save']}: {rupiah(int(oc['saved_idr']))}", 24)

    if rep.get("attempts"):
        doc.rule()
        doc.text(L["attempts"], 28, bold=True)
        for a in rep["attempts"]:
            doc.text(f"- {a}", 23, indent=10)

    rows = [r for r in build_trace(session) if r["status"] == "done"]
    if rows:
        doc.rule()
        doc.text(L["hood"], 26, bold=True)
        for r in rows:
            secs = f"  {r['ms'] / 1000:.1f}s" if (r.get("ms") or 0) >= 100 else ""
            doc.text(f"- {L.get('st_' + r['stage'], r['stage'])}: {r['tool']}{secs}", 20, color=MUTED, indent=10)
    doc.rule()
    doc.text(L["disclaimer"], 22, color=MUTED)
    _draw_brief(doc, session, session_dir, lang)
    pages = doc.finish()
    out.parent.mkdir(parents=True, exist_ok=True)
    pages[0].save(out, "PDF", resolution=150.0, save_all=True, append_images=pages[1:])
    return out
