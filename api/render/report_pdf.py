"""Printable repair report (SPEC v2: PDF repair report). Pure Pillow, no extra dependency: each A4 page is
drawn as an image and saved as a multi-page PDF. Works the same in demo mode and live mode.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from .. import handoff
from . import brand
from ..trace import build_trace

W, H = 1240, 1754  # A4 at 150 dpi
M = 90  # margin
INK, MUTED, ORANGE = brand.INK, brand.MUTED, brand.ORANGE
SAFETY_COLOR = {"green": brand.GREEN, "amber": brand.YELLOW, "red": brand.RED}

LABELS: dict[str, dict[str, str]] = {
    "id": {"title": "Laporan Perbaikan", "object": "Barang", "problem": "Masalah", "fix": "Penyebab yang ditangani", "safety": "Keselamatan",
           "steps": "Langkah", "verified": "terverifikasi kamera", "tools": "Alat", "parts": "Suku cadang", "total": "Perkiraan biaya suku cadang",
           "shop": "Harga bengkel biasanya (jasa + suku cadang)", "save": "Hemat sendiri (hanya suku cadang)",
           "attempts": "Percobaan", "minutes": "menit", "outcome": "Hasil", "o_fixed": "Beres: sudah jalan lagi (kata pemilik)",
           "o_pro": "Dibawa ke bengkel/teknisi", "status": "Status", "ok": "[OK]", "todo": "[  ]", "photo": "Foto dengan bagian yang ditandai (SAM 3.1)",
           "disclaimer": "Panduan ini hanya untuk perbaikan ringan. Harga adalah perkiraan. Untuk gas, listrik rumah, atau tegangan tinggi, panggil teknisi.",
           "made": "Dibuat dengan Tukang Copilot (Meta Muse Spark + SAM 3.1)", "page": "Hal.", "demo": "Mode demo: jawaban contoh",
           "fallback": "Jawaban contoh (API live tidak tersedia) untuk",
           "green": "AMAN", "amber": "HATI-HATI", "red": "STOP",
           "hood": "Di balik layar: model yang dipakai", "before": "Sebelum mulai, pastikan",
           "st_listen": "Dengar suara", "st_gate": "Cek keselamatan teks", "st_look": "Lihat foto", "st_segment": "Tandai bagian",
           "st_diagnose": "Diagnosa", "st_plan": "Susun langkah", "st_safety": "Cek keselamatan rencana", "st_illustrate": "Gambar bantu",
           "st_narrate": "Suara pemandu", "code_tool": "aturan di kode", "causes": "Kemungkinan penyebab", "tried_mark": "sudah dicoba"},
    "en": {"title": "Repair Report", "object": "Item", "problem": "Problem", "fix": "Cause worked on", "safety": "Safety",
           "steps": "Steps", "verified": "verified by camera", "tools": "Tools", "parts": "Parts", "total": "Estimated parts cost",
           "shop": "Typical shop price (labour + parts)", "save": "Saved by doing it yourself (parts only)",
           "attempts": "Attempts", "minutes": "min", "outcome": "Result", "o_fixed": "Fixed: it works again (owner's word)",
           "o_pro": "Handed to a mechanic/professional", "status": "Status", "ok": "[OK]", "todo": "[  ]", "photo": "Photo with the parts marked (SAM 3.1)",
           "disclaimer": "Light repairs only. Prices are estimates. For gas, house wiring, or high voltage, call a professional.",
           "made": "Made with Tukang Copilot (Meta Muse Spark + SAM 3.1)", "page": "Page", "demo": "Demo mode: sample answers",
           "fallback": "Demo answer (live API unavailable) for",
           "green": "SAFE", "amber": "CAUTION", "red": "STOP",
           "hood": "Under the hood: models used", "before": "Before you start, make sure",
           "st_listen": "Listen", "st_gate": "Text safety gate", "st_look": "Look at photo", "st_segment": "Mark parts",
           "st_diagnose": "Diagnose", "st_plan": "Plan steps", "st_safety": "Plan safety gate", "st_illustrate": "Helper diagram",
           "st_narrate": "Voice guide", "code_tool": "rules in code", "causes": "Likely causes", "tried_mark": "tried"},
}
# Basa Jawa: every label a Javanese owner reads in the PDF (the app screen already speaks Javanese; the rest of the
# PDF used to fall back to Indonesian). Wording follows web/app.js. api/tests/test_report_pdf_jv.py guards it.
LABELS["jv"] = dict(
    LABELS["id"], title="Laporan Ndandani", object="Barang", problem="Masalah", fix="Sabab sing ditangani", safety="Keslametan",
    steps="Langkah", verified="wis dicek kamera", tools="Piranti", parts="Suku cadang", total="Kira-kira rega suku cadang",
    shop="Rega bengkel biasane (jasa + suku cadang)", save="Irit yen digarap dhewe (suku cadang thok)",
    attempts="Sing wis dijajal", minutes="menit", outcome="Asil", o_fixed="Rampung: wis urip maneh (jarene sing duwe)",
    o_pro="Digawa menyang bengkel/teknisi", photo="Foto karo bagean sing ditandhani (SAM 3.1)",
    disclaimer="Pandhuan iki mung kanggo ndandani sing entheng. Rega mung kira-kira. Yen ana gas, listrik omah, utawa tegangan dhuwur, celuk teknisi.",
    made="Digawe nganggo Tukang Copilot (Meta Muse Spark + SAM 3.1)", page="Kaca", demo="Mode demo: wangsulan conto",
    fallback="Wangsulan conto (API live ora kasedhiya) kanggo", green="AMAN", amber="ATI-ATI", red="MANDHEG",
    hood="Ing mburi layar: model sing dipakai", before="Sadurunge miwiti, priksa dhisik",
    st_listen="Rungokake swara", st_gate="Priksa slamet teks", st_look="Delok foto", st_segment="Tandhani bagean",
    st_diagnose="Diagnosa", st_plan="Nyusun langkah", st_safety="Priksa slamet rencana", st_illustrate="Gambar bantu",
    st_narrate="Swara panuntun", code_tool="aturan ing kode", causes="Sebab sing mungkin", tried_mark="wis dijajal")


BRIEF: dict[str, dict[str, str]] = {
    "id": {"title": "Ringkasan untuk mekanik", "sub": "Halaman ini bisa dicetak atau ditunjukkan ke bengkel supaya tidak mulai dari nol.",
           "found": "Yang ditemukan", "issues": "Terlihat di foto", "causes": "Kemungkinan penyebab", "marked": "Bagian yang ditandai",
           "tried": "Yang sudah dicoba", "nothing": "Belum ada: dihentikan sebelum mulai demi keselamatan.", "checks": "Cek kamera per langkah",
           "pass": "OK", "fail": "BELUM", "status": "Status", "red": "STOP keselamatan", "exhausted": "Semua penyebab aman sudah dicoba",
           "requested": "Pemilik minta bantuan mekanik", "photos": "Foto dari pemilik", "photo": "Foto", "check": "Cek langkah",
           "fixed": "Pemilik bilang sudah jalan lagi",
           "open": "Masih dikerjakan pemilik, belum ada hasil", "now": "Sedang dicoba sekarang"},
    "jv": {"title": "Ringkesan kanggo mekanik", "sub": "Kaca iki bisa dicithak utawa dituduhake menyang bengkel supaya ora miwiti saka nol.",
           "found": "Sing ditemokake", "issues": "Katon ing foto", "causes": "Sebab sing mungkin", "marked": "Perangan sing ditandhani",
           "tried": "Sing wis dijajal", "nothing": "Durung ana: dimandhegake sadurunge miwiti kanggo keslametan.", "checks": "Cek kamera saben langkah",
           "pass": "OK", "fail": "DURUNG", "status": "Status", "red": "MANDHEG keslametan", "exhausted": "Kabeh sebab sing aman wis dijajal",
           "requested": "Sing duwe njaluk bantuan mekanik", "photos": "Foto saka sing duwe", "photo": "Foto", "check": "Cek langkah",
           "fixed": "Sing duwe kandha wis urip maneh",
           "open": "Isih didandani dhewe karo sing duwe, durung ana asile", "now": "Lagi dijajal saiki"},
    "en": {"title": "Mechanic brief", "sub": "Print this page or show it to the workshop so they don't start from zero.",
           "found": "What was found", "issues": "Seen in the photo", "causes": "Likely causes", "marked": "Parts marked",
           "tried": "What was tried", "nothing": "Nothing: stopped before starting, for safety.", "checks": "Camera check per step",
           "pass": "OK", "fail": "NOT YET", "status": "Status", "red": "Safety STOP", "exhausted": "Every safe cause was tried",
           "requested": "Owner asked for a mechanic", "photos": "Owner's photos", "photo": "Photo", "check": "Step check",
           "fixed": "Owner says it works again",
           "open": "The owner is still on it, no result yet", "now": "Being tried now"},
}


# Agent log lines for the PDF, mirrored from web/app.js (ag_* strings) so the PDF reads like the screen.
# api/tests/test_report_pdf.py checks the two stay in sync.
AGENT: dict[str, dict[str, str]] = {
    "id": {
        "agentTitle": "Yang dilakukan AI",
        "ag_listen": "Mendengar suaramu dan mengubahnya jadi teks",
        "ag_gate_ok": "Cek kata berbahaya (gas, listrik rumah, rem…): aman, lanjut",
        "ag_gate_stop": "Kata berbahaya terdeteksi ({category}): berhenti sebelum memanggil model",
        "ag_look": "Melihat foto: {object}, {n} bagian dikenali",
        "ag_segment": "Menandai {found} dari {of} bagian di fotomu (masker piksel)",
        "ag_diagnose": "Paling mungkin: {cause} ({conf}%), dari {n} kemungkinan",
        "ag_ask": "Baru yakin {conf}% (di bawah {threshold}%): bertanya satu hal dulu, bukan menebak",
        "ag_answer": "Jawabanmu diterima, diagnosa diulang",
        "ag_plan": "Menyusun {steps} langkah untuk: {cause}",
        "ag_guard_ok": "Rencana dicek aturan keselamatan di kode: lolos ({level})",
        "ag_guard_stop": "Rencana ditolak aturan keselamatan: STOP",
        "ag_illustrate": "Menggambar {made} dari {of} diagram dari fotomu",
        "ag_redrawn": ", {redrawn} digambar ulang setelah diperiksa",
        "ag_check_ok": "Langkah {step} dicek dari foto baru: benar",
        "ag_check_fail": "Langkah {step} dicek dari foto baru: belum pas, diberi koreksi",
        "ag_check_esc": " (gagal berulang, menyarankan rencana lain)",
        "ag_replan": "Masih rusak: rencana baru {steps} langkah untuk {cause}",
        "ag_esc_red": "Terlalu berbahaya dikerjakan sendiri: diarahkan ke teknisi + laporan",
        "ag_esc_exhausted": "Semua sebab yang aman sudah dicoba: diserahkan ke bengkel dengan laporan",
        "ag_fallback": "Model live gagal setelah dicoba ulang: tahap {stage} memakai jawaban demo (diberi label)",
        "ag_input_guard": "Ada kalimat berupa perintah di inputmu: diperlakukan sebagai data dan diabaikan",
        "ag_outcome_fixed": "Kamu konfirmasi: sudah beres",
        "ag_outcome_pro": "Kamu memilih membawa ke bengkel",
        "ag_retry": "Mencoba ulang tahap yang gagal (ke-{n})",
        "agCode": "kode",
    },
    "jv": {
        "agentTitle": "Sing ditindakake AI",
        "ag_listen": "Ngrungokake swaramu lan ngowahi dadi tulisan",
        "ag_gate_ok": "Priksa tembung mbebayani (gas, listrik omah, rem…): aman, terus",
        "ag_gate_stop": "Ana tembung mbebayani ({category}): mandheg sadurunge takon model",
        "ag_look": "Ndeleng foto: {object}, {n} perangan ditemokake",
        "ag_segment": "Nandhani {found} saka {of} perangan ing fotomu (masker piksel)",
        "ag_diagnose": "Sing paling mungkin: {cause} ({conf}%), saka {n} kemungkinan",
        "ag_ask": "Lagi yakin {conf}% (ing ngisor {threshold}%): takon siji bab dhisik, ora ngira-ira",
        "ag_answer": "Wangsulanmu ditampa, diagnosa dibaleni",
        "ag_plan": "Nyusun {steps} langkah kanggo: {cause}",
        "ag_guard_ok": "Rencana dipriksa aturan keslametan ing kode: lolos ({level})",
        "ag_guard_stop": "Rencana ditolak aturan keslametan: MANDHEG",
        "ag_illustrate": "Nggambar {made} saka {of} diagram saka fotomu",
        "ag_redrawn": ", {redrawn} digambar maneh sawise dipriksa",
        "ag_check_ok": "Langkah {step} dipriksa saka foto anyar: bener",
        "ag_check_fail": "Langkah {step} dipriksa saka foto anyar: durung pas, diwenehi koreksi",
        "ag_check_esc": " (gagal bola-bali, nyaranake rencana liya)",
        "ag_replan": "Isih rusak: rencana anyar {steps} langkah kanggo {cause}",
        "ag_esc_red": "Kebangeten mbebayani yen digarap dhewe: diarahake menyang teknisi + laporan",
        "ag_esc_exhausted": "Kabeh sebab sing aman wis dijajal: dipasrahake menyang bengkel karo laporan",
        "ag_fallback": "Model live gagal sawise dijajal maneh: tahap {stage} nganggo wangsulan demo (ana labele)",
        "ag_input_guard": "Ana ukara prentah ing inputmu: dianggep data lan ora digatekake",
        "ag_outcome_fixed": "Sampeyan ngonfirmasi: wis rampung",
        "ag_outcome_pro": "Sampeyan milih nggawa menyang bengkel",
        "ag_retry": "Nyoba maneh tahap sing gagal (kaping {n})",
        "agCode": "kode",
    },
    "en": {
        "agentTitle": "What the AI did",
        "ag_listen": "Listened to your voice note and turned it into text",
        "ag_gate_ok": "Scanned your words for hazards (gas, mains, brakes…): clear",
        "ag_gate_stop": "Hazard words found ({category}): stopped before any model call",
        "ag_look": "Looked at the photo: {object}, {n} parts located",
        "ag_segment": "Outlined {found} of {of} parts on your photo (pixel masks)",
        "ag_diagnose": "Most likely: {cause} ({conf}%), out of {n} causes",
        "ag_ask": "Only {conf}% sure (below {threshold}%): asked one question instead of guessing",
        "ag_answer": "Got your answer, re-ran the diagnosis",
        "ag_plan": "Planned {steps} steps for: {cause}",
        "ag_guard_ok": "Plan checked by safety rules in code: passed ({level})",
        "ag_guard_stop": "Plan blocked by safety rules: STOP",
        "ag_illustrate": "Drew {made} of {of} helper diagrams from your photo",
        "ag_redrawn": ", {redrawn} redrawn after review",
        "ag_check_ok": "Step {step} checked from your new photo: correct",
        "ag_check_fail": "Step {step} checked from your new photo: not yet, sent a correction",
        "ag_check_esc": " (repeated fails, suggested another plan)",
        "ag_replan": "Still broken: new {steps}-step plan for {cause}",
        "ag_esc_red": "Too dangerous to do alone: handed off to a professional with a report",
        "ag_esc_exhausted": "Every safe cause tried: handed off to a workshop with a report",
        "ag_fallback": "Live model failed after retries: {stage} used the labelled demo answer",
        "ag_input_guard": "Your input contained instruction-like text: treated as data and ignored",
        "ag_outcome_fixed": "You confirmed: it works now",
        "ag_outcome_pro": "You chose to take it to a mechanic",
        "ag_retry": "Retried the failed stage (#{n})",
        "agCode": "code",
    },
}

def _fill(tpl: str, e: dict[str, Any]) -> str:
    return re.sub(r"\{(\w+)\}", lambda m: str(e.get(m.group(1), "")), tpl)


def agent_lines(session: dict[str, Any], lang: str) -> list[str]:
    """The agent log ("What the AI did") as plain lines, same wording and rules as web/app.js agentLine()."""
    A, L = AGENT.get(lang, AGENT["id"]), LABELS.get(lang, LABELS["id"])
    out: list[str] = []
    for e in session.get("agent_log") or []:
        if not isinstance(e, dict):
            continue
        k = str(e.get("kind") or "")
        if k == "gate":
            line = A["ag_gate_ok"] if e.get("ok") else _fill(A["ag_gate_stop"], e)
        elif k == "plan_guard":
            line = _fill(A["ag_guard_ok"], {"level": L.get(str(e.get("level")), str(e.get("level") or ""))}) if e.get("ok") else A["ag_guard_stop"]
        elif k == "illustrate":
            line = _fill(A["ag_illustrate"], e) + (_fill(A["ag_redrawn"], e) if e.get("redrawn") else "")
        elif k == "check":
            line = _fill(A["ag_check_ok" if e.get("passed") else "ag_check_fail"], e) + (A["ag_check_esc"] if e.get("escalate") else "")
        elif k == "escalate":
            line = A["ag_esc_exhausted" if e.get("reason") == "exhausted" else "ag_esc_red"]
        elif k == "outcome":
            line = A["ag_outcome_fixed" if e.get("result") == "fixed" else "ag_outcome_pro"]
        elif "ag_" + k in A:
            line = _fill(A["ag_" + k], e)
        else:
            line = k
        tool = str(e.get("model") or (A["agCode"] if k in ("gate", "plan_guard", "input_guard") else ""))
        secs = f" {int(e['ms']) / 1000:.1f}s" if isinstance(e.get("ms"), (int, float)) and e["ms"] >= 100 else ""
        t = e.get("t")
        stamp = f"{float(t):.0f}s  " if isinstance(t, (int, float)) else ""
        out.append(f"{stamp}{line}" + (f"  [{tool}]" if tool else "") + secs)
    return out


def brief_lines(session: dict[str, Any], lang: str) -> list[tuple[str, str]]:
    """The mechanic brief as (kind, text) rows: kind is h (heading), t (text), m (muted). Pure, so it is testable."""
    B = BRIEF.get(lang, BRIEF["id"])
    rep, dx = session.get("object_report") or {}, session.get("diagnosis") or {}
    why = handoff.reason(session)
    # the status says what the owner chose: "It works now", "Took it to a mechanic", or nothing yet
    result = (session.get("outcome") or {}).get("result")
    status = why if why != "requested" else {"fixed": "fixed", "pro": "requested"}.get(str(result), "open")
    rows: list[tuple[str, str]] = [("m", B["sub"]), ("h", B["status"]), ("t", B[status])]
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
    done, now = handoff.progress(session, why)
    rows += [("t", f"- {x}") for x in done]
    if now:
        rows.append(("t", f"- {B['now']}: {now}"))
    if not done and not now:
        rows.append(("t", B["nothing"]))
    for a in handoff.attempt_lines(session, lang):
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
    doc.band(B["title"])
    for kind, txt in brief_lines(session, lang):
        if kind == "h":
            doc.heading(txt, 30)
        elif kind == "m":
            doc.text(txt, 21, color=MUTED, indent=10)
        else:
            doc.text(txt, 24, indent=10)
    pics = brief_photos(session, session_dir, lang)
    if not pics:
        return
    doc.heading(B["photos"], 30, keep=380)
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
            doc.paste_round(pic, x, doc.y, 12)
            brand.draw(doc.d, (x, doc.y + pic.height + 6), cap, "semi", 20, MUTED)
        doc.y += cell_h + 40


def _font(size: int, bold: bool = False) -> Any:
    return brand.font("semi" if bold else "body", size)


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
    """A4 pages drawn as images: Barlow type, the app's safety colours, a thin orange strip on top of every page."""

    def __init__(self, footer: str, page_word: str) -> None:
        self.pages: list[Image.Image] = []
        self.footer, self.page_word = footer, page_word
        self.f_body, self.f_small = _font(26), _font(21)
        self._new_page()

    def _new_page(self) -> None:
        self.im = Image.new("RGB", (W, H), "white")
        self.d = ImageDraw.Draw(self.im)
        self.d.rectangle([0, 0, W, 12], fill=ORANGE)
        self.pages.append(self.im)
        self.y = M

    def need(self, h: int) -> None:
        if self.y + h > H - M - 40:
            self._new_page()

    def text(self, s: str, size: int = 26, bold: bool = False, color: tuple[int, int, int] = INK, indent: int = 0, gap: int = 8,
             kind: str = "") -> None:
        k = kind or ("semi" if bold else "body")
        for line in brand.wrap(self.d, s, k, size, W - 2 * M - indent):
            self.need(size + gap)
            brand.draw(self.d, (M + indent, self.y), line, k, size, color)
            self.y += size + gap

    def heading(self, s: str, size: int = 34, keep: int = 110, color: tuple[int, int, int] = INK) -> None:
        """A section title in Barlow Condensed, never left alone at the foot of a page."""
        self.space(14)
        self.need(size + keep)
        self.text(s, size, color=color, kind="display", gap=10)

    def band(self, title: str, sub: str = "") -> None:
        """Dark header plate across the top of a page: the app icon, the name, and what this page is."""
        h = 190 if sub else 170
        self.d.rectangle([0, 0, W, h], fill=brand.DARK)
        self.d.rectangle([0, h, W, h + 10], fill=ORANGE)
        brand.wrench_plate(self.im, M, 44, 64)
        brand.draw(self.d, (M + 84, 38), "Tukang Copilot", "display", 54, brand.WHITE)
        brand.draw(self.d, (M + 84, 98), title, "cond", 34, ORANGE)
        if sub:
            brand.draw(self.d, (M + 84, 142), sub, "body", 22, (190, 196, 204))
        self.y = h + 44

    def space(self, h: int = 18) -> None:
        self.y += h

    def rule(self) -> None:
        self.need(20)
        self.d.line([M, self.y + 6, W - M, self.y + 6], fill=brand.LINE, width=2)
        self.y += 22

    def paste_round(self, pic: Image.Image, x: int, y: int, radius: int = 18) -> None:
        mask = Image.new("L", pic.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, pic.width - 1, pic.height - 1], radius=radius, fill=255)
        self.im.paste(pic, (x, y), mask)

    def image(self, path: Path, max_h: int = 620) -> None:
        try:
            with Image.open(path) as src:
                pic = src.convert("RGB")
        except OSError:
            return
        pic.thumbnail((W - 2 * M, max_h))
        self.need(pic.height + 10)
        self.paste_round(pic, M + (W - 2 * M - pic.width) // 2, self.y)
        self.y += pic.height + 16

    def box(self, x: int, y: int, size: int = 30, ticked: bool = False) -> None:
        """A drawn tick box (green with a white tick when done), instead of "[ ]" text."""
        if ticked:
            self.d.rounded_rectangle([x, y, x + size, y + size], radius=7, fill=brand.GREEN)
            self.d.line([x + size * .22, y + size * .52, x + size * .43, y + size * .72, x + size * .8, y + size * .3],
                        fill=brand.WHITE, width=max(3, size // 8), joint="curve")
        else:
            self.d.rounded_rectangle([x, y, x + size, y + size], radius=7, outline=INK, width=3)

    def finish(self) -> list[Image.Image]:
        n = len(self.pages)
        for i, page in enumerate(self.pages, 1):
            d = ImageDraw.Draw(page)
            d.line([M, H - M - 10, W - M, H - M - 10], fill=brand.LINE, width=2)
            brand.draw(d, (M, H - M), self.footer, "body", 21, MUTED)
            tag = f"{self.page_word} {i}/{n}"
            brand.draw(d, (W - M - brand.length(d, tag, "semi", 21), H - M), tag, "semi", 21, MUTED)
        return self.pages


def _safety_plate(doc: _Doc, level: str, L: dict[str, str], reason: str) -> None:
    """Full-width plate in the safety colour (black on yellow, white on red and green, as on the phone)."""
    fill, on = brand.LEVEL.get(level, (brand.PLATE_2, INK))
    word = L.get(level, level.upper())
    lines = brand.wrap(doc.d, reason, "body", 24, W - 2 * M - 60)[:4] if reason else []
    h = 92 + len(lines) * 32
    doc.need(h + 10)
    doc.d.rounded_rectangle([M, doc.y, W - M, doc.y + h], radius=18, fill=fill)
    tw = brand.draw(doc.d, (M + 30, doc.y + 18), word, "display", 48, on)
    brand.draw(doc.d, (M + 30 + tw + 18, doc.y + 34), L["safety"], "semi", 24, on)
    yy = doc.y + 80
    for ln in lines:
        brand.draw(doc.d, (M + 30, yy), ln, "body", 24, on)
        yy += 32
    doc.y += h + 18


def _causes(doc: _Doc, session: dict[str, Any], L: dict[str, str]) -> None:
    dx = session.get("diagnosis") or {}
    causes = [c for c in dx.get("causes") or [] if isinstance(c, dict) and c.get("title")][:3]
    if not causes:
        return
    doc.heading(L["causes"], 30)
    cur = int(session.get("cause_index") or 0)
    for i, c in enumerate(causes):
        conf = max(0, min(100, int(c.get("confidence") or 0)))
        doc.need(76)
        y = doc.y
        col = brand.ORANGE_TEXT if i == cur else MUTED
        brand.draw(doc.d, (M, y - 4), f"{conf}%", "display", 44, col)
        x = M + 120
        if i < cur:  # tried and failed before this plan: struck through with a red "tried", as on the phone
            tag = L["tried_mark"]
            tag_w = brand.length(doc.d, tag, "semi", 21) + 16
            title = brand.wrap(doc.d, str(c["title"]), "semi", 25, W - M - x - tag_w, 1)[0]
            tw = brand.draw(doc.d, (x, y), title, "semi", 25, MUTED)
            doc.d.line([x, y + 16, x + tw, y + 16], fill=MUTED, width=2)
            brand.draw(doc.d, (x + tw + 16, y + 3), tag, "semi", 21, brand.RED)
        else:
            brand.draw(doc.d, (x, y), brand.wrap(doc.d, str(c["title"]), "semi", 25, W - M - x, 1)[0], "semi", 25, INK)
        doc.d.rounded_rectangle([x, y + 40, W - M, y + 50], radius=5, fill=brand.PLATE_2)
        if conf:
            doc.d.rounded_rectangle([x, y + 40, x + int((W - M - x) * conf / 100), y + 50], radius=5,
                                    fill=brand.ORANGE if i == cur else brand.LINE)
        doc.y = y + 72


def build(rep: dict[str, Any], session: dict[str, Any], session_dir: Path, out: Path) -> Path:
    """Draw the report for one session. `rep` is engine.report(); `session` the full session dict."""
    lang = str(rep.get("lang") or "id")
    if lang not in LABELS:
        lang = "id"
    L = LABELS[lang]
    doc = _Doc(L["made"], L["page"])
    doc.band(L["title"], f"#{rep.get('id', '')}" + (f"   ·   {L['demo']}" if session.get("mode") == "mock" else ""))
    if session.get("fallback"):
        doc.text(f"{L['fallback']}: {', '.join(str(x) for x in session['fallback'])}", 22, bold=True, color=brand.ORANGE_TEXT)

    level = rep.get("safety_level") or ""
    if level:
        _safety_plate(doc, str(level), L, str((session.get("safety") or {}).get("reason") or ""))
    if session.get("stop_reason"):
        doc.text(str(session["stop_reason"]), 26, bold=True, color=brand.RED)

    for key, val in (("object", rep.get("object")), ("problem", rep.get("problem")), ("fix", rep.get("fix"))):
        if val:
            doc.space(6)
            doc.text(L[key], 21, bold=True, color=MUTED, gap=2)
            doc.text(str(val), 30 if key == "object" else 27, kind="cond" if key == "object" else "")

    photo = session_dir / (session.get("parts_image") or "")
    if session.get("parts_image") and photo.exists():
        doc.space(12)
        doc.text(L["photo"], 21, bold=True, color=MUTED, gap=6)
        doc.image(photo, 540)

    _causes(doc, session, L)

    pre = [str(x) for x in ((session.get("diagnosis") or {}).get("before_you_start") or []) if x]
    if pre:
        doc.space(14)
        doc.need(60 + 40 * len(pre))
        top = doc.y
        doc.y += 18
        doc.text(L["before"], 24, bold=True, indent=24, gap=10)
        for x in pre:
            doc.box(M + 24, doc.y + 1, 26)
            doc.text(x, 24, indent=66)
        doc.y += 10
        _tint_under(doc, top, brand.YELLOW_TINT)
        doc.d.rounded_rectangle([M, top, W - M, doc.y], radius=16, outline=brand.YELLOW, width=4)
        doc.y += 8

    steps = (session.get("plan") or {}).get("steps", [])
    if steps:
        doc.heading(f"{L['steps']} ({rep.get('steps_verified', 0)}/{rep.get('steps_total', 0)} {L['verified']})")
        checks = session.get("checks") or {}
        for st in steps:
            ok = bool(checks.get(str(st.get("n")), {}).get("passed"))
            doc.need(70)
            y = doc.y
            # number plate: dark, or green when the camera passed this step (the heading says how many)
            doc.d.rounded_rectangle([M, y, M + 40, y + 40], radius=9, fill=brand.GREEN if ok else brand.DARK)
            n = str(st.get("n"))
            brand.draw(doc.d, (M + 20 - brand.length(doc.d, n, "display", 30) / 2, y + 3), n, "display", 30, brand.WHITE)
            doc.y = y + 4
            doc.text(str(st.get("instruction", "")) + (f"  ({L['verified']})" if ok else ""), 25, indent=62)
            if st.get("expected_state"):
                doc.text(f"-> {st['expected_state']}", 21, color=MUTED, indent=62)
            doc.y = max(doc.y, y + 52) + 8
        done = (session.get("plan") or {}).get("done_check")
        if done:
            doc.space(4)
            doc.text(done, 25, bold=True, color=brand.GREEN)

    items = [(L["tools"], rep.get("tools") or []), (L["parts"], rep.get("parts") or [])]
    if any(v for _, v in items):
        total = 0
        for head, rows in items:
            if not rows:
                continue
            doc.heading(head, 30)
            for r in rows:
                price = int(r.get("est_price_idr") or 0)
                total += price
                doc.need(40)
                y = doc.y
                doc.text(f"- {r.get('name', '')}", 24, indent=10)
                if price:
                    tag = rupiah(price)
                    brand.draw(doc.d, (W - M - brand.length(doc.d, tag, "semi", 24), y), tag, "semi", 24, INK)
                doc.d.line([M + 10, doc.y - 2, W - M, doc.y - 2], fill=brand.PLATE_2, width=2)
        parts_total = sum(int(r.get("est_price_idr") or 0) for r in items[1][1]) if len(items) > 1 else total
        shown = rep.get("cost_estimate_idr") or parts_total
        mins = rep.get("minutes_estimate")
        doc.space(10)
        doc.need(60)
        doc.d.rounded_rectangle([M, doc.y - 6, W - M, doc.y + 44], radius=12, fill=brand.PLATE_2)
        doc.y += 4
        doc.text(f"{L['total']}: {rupiah(shown)}" + (f"   ~{mins} {L['minutes']}" if mins else ""), 26, bold=True, indent=16)
        doc.space(6)
        shop, saving = int(rep.get("shop_cost_estimate_idr") or 0), int(rep.get("diy_saving_idr") or 0)
        if shop:
            doc.text(f"{L['shop']}: {rupiah(shop)}", 24, indent=16)
            if saving:
                doc.text(f"{L['save']}: {rupiah(saving)}", 24, bold=True, color=brand.GREEN, indent=16)

    oc = rep.get("outcome") or {}
    if oc.get("result") in ("fixed", "pro"):
        doc.space(10)
        doc.need(70)
        tint = brand.GREEN_TINT if oc["result"] == "fixed" else brand.PLATE_2
        top = doc.y
        doc.y += 16
        doc.text(f"{L['outcome']}: {L['o_' + oc['result']]}", 28, bold=True, indent=20)
        if oc.get("saved_idr"):
            doc.text(f"{L['save']}: {rupiah(int(oc['saved_idr']))}", 24, indent=20)
        doc.y += 8
        _tint_under(doc, top, tint)

    if rep.get("attempts"):
        doc.heading(L["attempts"], 30)
        for a in rep["attempts"]:
            doc.text(f"- {a}", 23, indent=10)

    ag = agent_lines(session, lang)
    if ag:
        doc.heading(AGENT.get(lang, AGENT["id"])["agentTitle"], 30)
        for line in ag:
            doc.text(f"- {line}", 21, indent=10, gap=5)

    rows = [r for r in build_trace(session) if r["status"] == "done"]
    hood = []
    for r in rows:
        secs = f"  {r['ms'] / 1000:.1f}s" if (r.get("ms") or 0) >= 100 else ""
        tool = L["code_tool"] if r["kind"] == "code" else r["tool"]  # "rules in code" follows the report's language
        hood.append(f"- {L.get('st_' + r['stage'], r['stage'])}: {tool}{secs}")
    _hood_and_disclaimer(doc, L, hood)
    _draw_brief(doc, session, session_dir, lang)
    pages = doc.finish()
    out.parent.mkdir(parents=True, exist_ok=True)
    pages[0].save(out, "PDF", resolution=150.0, save_all=True, append_images=pages[1:])
    return out


def _hood_and_disclaimer(doc: _Doc, L: dict[str, str], hood: list[str]) -> None:
    """The "under the hood" list, then the disclaimer, which never goes alone onto a page of its own.

    When the whole tail does not fit on the page, the list goes in two columns if that makes it fit; otherwise
    the last two list lines move to the next page with the disclaimer."""
    full_w = W - 2 * M
    disc_h = 22 + len(brand.wrap(doc.d, L["disclaimer"], "body", 22, full_w)) * 30
    avail = H - M - 40 - doc.y
    head_h = 14 + 28 + 10

    def col_h(lines: list[str], width: float) -> int:
        return sum(len(brand.wrap(doc.d, t, "body", 20, width)) * 28 for t in lines)

    if hood and head_h + col_h(hood, full_w - 10) + disc_h > avail:
        half = (len(hood) + 1) // 2
        cw = (full_w - 40) // 2
        left, right = hood[:half], hood[half:]
        two_h = max(col_h(left, cw - 10), col_h(right, cw - 10))
        if head_h + two_h + disc_h <= avail:
            doc.heading(L["hood"], 28)
            top = doc.y
            for col, lines in enumerate((left, right)):
                doc.y = top
                for t in lines:
                    for line in brand.wrap(doc.d, t, "body", 20, cw - 10):
                        brand.draw(doc.d, (M + 10 + col * (cw + 40), doc.y), line, "body", 20, MUTED)
                        doc.y += 28
            doc.y = top + two_h
            hood = []
    if hood:
        doc.heading(L["hood"], 28)
        for i, t in enumerate(hood):
            if i == max(0, len(hood) - 2):  # keep the last lines with the disclaimer
                doc.need(col_h(hood[i:], full_w - 10) + disc_h)
            doc.text(t, 20, color=MUTED, indent=10)
    doc.need(disc_h)
    doc.rule()
    doc.text(L["disclaimer"], 22, color=MUTED)


def _tint_under(doc: _Doc, top: int, tint: tuple[int, int, int]) -> None:
    """Put a tinted plate behind lines already drawn between `top` and doc.y (white page, so only white pixels change)."""
    if doc.y <= top or doc.y > H:
        return
    box = (M, top, W - M, doc.y)
    region = doc.im.crop(box)
    plate = Image.new("RGB", region.size, tint)
    mask = Image.new("L", region.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, region.width - 1, region.height - 1], radius=16, fill=255)
    white = region.convert("L").point(lambda v: 255 if v >= 250 else 0)
    from PIL import ImageChops

    doc.im.paste(plate, box[:2], ImageChops.multiply(mask, white))
