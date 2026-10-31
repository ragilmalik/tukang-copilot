"""Bengkel hand-off: when the owner should stop (red safety level), has tried every safe cause, or simply
wants a mechanic, give them a ready-made message and the places to send it.

Pure functions, no network: a short WhatsApp text (what it is, what was found, what was tried, links to the
read-only guide and the PDF report with its "mechanic brief" page) and a Google Maps search for the right
kind of workshop near them. Maps queries stay in Bahasa Indonesia in every UI language, because the
workshops that answer them are Indonesian ("bengkel motor terdekat").
"""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote, quote_plus

REASONS = ("red", "exhausted", "requested")

# (pattern on the object / description, maps query). First match wins; category defaults below.
_SPECIFIC: list[tuple[str, str]] = [
    (r"\b(gas|elpiji|lpg|kompor|stove)\b", "service kompor gas terdekat"),
    (r"\b(listrik rumah|instalasi listrik|kabel rumah|wiring|mcb|sekring rumah|stop ?kontak)\b", "jasa tukang listrik terdekat"),
    (r"\b(ban|tyre|tire|tubeless|kempes|tambal)\b", "tambal ban terdekat"),
    (r"\b(rice ?cooker\w*|magic ?com\w*|penanak nasi)\b", "service center rice cooker terdekat"),
    (r"\b(kipas|fan)\b", "servis kipas angin terdekat"),
    (r"\b(kulkas|fridge|refrigerator|lemari es)\b", "service kulkas terdekat"),
    (r"\b(mesin cuci|washing machine)\b", "service mesin cuci terdekat"),
    (r"\b(ac|air ?con|freon)\b", "service ac terdekat"),
    (r"\b(tv|televisi|television)\b", "service tv terdekat"),
    (r"\b(setrika|iron)\b", "service center elektronik terdekat"),
    (r"\b(mobil|car)\b", "bengkel mobil terdekat"),
]
_BY_CATEGORY = {"motor": "bengkel motor terdekat", "pump": "servis pompa air terdekat",
                "appliance": "service center elektronik terdekat", "plumbing": "tukang ledeng terdekat",
                "other": "tukang servis terdekat"}

L: dict[str, dict[str, str]] = {
    "id": {"hello": "Halo, saya butuh bantuan bengkel/servis.", "item": "Barang", "problem": "Masalah",
           "stop": "Dihentikan demi keselamatan", "found": "Kemungkinan penyebab", "tried": "Sudah dicoba",
           "nothing": "belum ada (dihentikan sebelum mulai)",
           "verified": "Langkah dicek kamera", "guide": "Panduan & foto", "pdf": "Laporan PDF (ada ringkasan untuk mekanik)", "by": "Dikirim dari Tukang Copilot",
           "title_red": "Ini pekerjaan untuk ahli", "title_exhausted": "Saatnya ke bengkel/servis", "title_requested": "Serahkan ke bengkel"},
    "jv": {"hello": "Halo, aku butuh bantuan bengkel/servis.", "item": "Barang", "problem": "Masalah",
           "stop": "Dimandhegake kanggo keslametan", "found": "Sebab sing mungkin", "tried": "Wis dijajal",
           "nothing": "durung ana (dimandhegake sadurunge miwiti)",
           "verified": "Langkah dicek kamera", "guide": "Pandhuan & foto", "pdf": "Laporan PDF (ana ringkesan kanggo mekanik)", "by": "Dikirim saka Tukang Copilot",
           "title_red": "Iki gaweane ahli", "title_exhausted": "Wayahe menyang bengkel/servis", "title_requested": "Pasrahna menyang bengkel"},
    "en": {"hello": "Hi, I need help from a repair shop.", "item": "Item", "problem": "Problem",
           "stop": "Stopped for safety", "found": "Likely causes", "tried": "Already tried",
           "nothing": "nothing yet (stopped before starting)",
           "verified": "Steps checked by camera", "guide": "Guide & photos", "pdf": "PDF report (with a mechanic brief)", "by": "Sent from Tukang Copilot",
           "title_red": "This is a job for a professional", "title_exhausted": "Time for a repair shop", "title_requested": "Hand it to a mechanic"},
}


def _clean(s: Any, n: int = 160) -> str:
    return " ".join(str(s or "").split())[:n]


def maps_query(s: dict[str, Any]) -> str:
    """The Google Maps search for the right kind of workshop, from what the object is."""
    rep = s.get("object_report") or {}
    hay = " ".join(str(x) for x in (rep.get("object"), rep.get("brand_model_guess"), s.get("text"), s.get("transcript"))).lower()
    cat = rep.get("category") or s.get("category") or "other"
    for pat, q in _SPECIFIC:
        if cat == "motor" and "ban" not in pat:  # on a motorbike "gas" is the throttle: only the tyre rule applies
            continue
        if re.search(pat, hay):
            return q
    return _BY_CATEGORY.get(str(cat), _BY_CATEGORY["other"])


def maps_url(query: str) -> str:
    return "https://www.google.com/maps/search/?api=1&query=" + quote_plus(query)


def reason(s: dict[str, Any]) -> str:
    if s.get("status") == "stopped" or (s.get("safety") or {}).get("level") == "red":
        return "red"
    if s.get("status") == "exhausted":
        return "exhausted"
    return "requested"


def tried(s: dict[str, Any], why: str) -> list[str]:
    """Causes the owner worked through: every cause before the current one, plus the current one unless it was a red stop."""
    if why == "red" or not s.get("plan"):
        return []
    causes = (s.get("diagnosis") or {}).get("causes") or []
    upto = min(len(causes), int(s.get("cause_index") or 0) + 1)
    return [_clean(c.get("title"), 90) for c in causes[:upto] if c.get("title")]


def message(s: dict[str, Any], lang: str, guide_url: str, pdf_url: str | None) -> str:
    """Short plain-text summary for WhatsApp (fits one phone screen)."""
    t = L.get(lang, L["id"])
    why = reason(s)
    rep, dx = s.get("object_report") or {}, s.get("diagnosis") or {}
    lines = [t["hello"]]
    obj, brand = _clean(rep.get("object"), 100), _clean(rep.get("brand_model_guess"), 40)
    if brand and brand.lower().split()[0] not in obj.lower():
        obj = f"{obj} ({brand})".strip()
    if obj:
        lines.append(f"{t['item']}: {obj}")
    prob = _clean(dx.get("problem_summary") or s.get("text") or s.get("transcript"), 200)
    if prob:
        lines.append(f"{t['problem']}: {prob}")
    if why == "red" and s.get("stop_reason"):
        lines.append(f"⚠️ {t['stop']}: {_clean(s['stop_reason'], 200)}")
    causes = [f"{_clean(c.get('title'), 70)} ({int(c.get('confidence') or 0)}%)" for c in (dx.get("causes") or [])[:3] if c.get("title")]
    if causes:
        lines.append(f"{t['found']}: " + "; ".join(causes))
    done = tried(s, why)
    lines.append(f"{t['tried']}: " + ("; ".join(done) if done else t["nothing"]))
    steps = (s.get("plan") or {}).get("steps") or []
    if steps:
        ok = sum(1 for st in steps if (s.get("checks") or {}).get(str(st.get("n")), {}).get("passed"))
        lines.append(f"{t['verified']}: {ok}/{len(steps)}")
    lines.append(f"{t['guide']}: {guide_url}")
    if pdf_url:
        lines.append(f"{t['pdf']}: {pdf_url}")
    lines.append(t["by"])
    return "\n".join(lines)


def build(s: dict[str, Any], base_url: str) -> dict[str, Any]:
    """Everything the hand-off card needs. base_url is the public origin (https://app.example)."""
    lang = s.get("lang") if s.get("lang") in L else "id"
    base = base_url.rstrip("/")
    sid = s["id"]
    guide_url = f"{base}/guide/{sid}"
    pdf_url = f"{base}/api/sessions/{sid}/report.pdf" if s.get("diagnosis") or s.get("status") == "stopped" else None
    why = reason(s)
    text = message(s, str(lang), guide_url, pdf_url)
    q = maps_query(s)
    return {"id": sid, "reason": why, "title": L[str(lang)]["title_" + why], "text": text,
            "whatsapp_url": "https://wa.me/?text=" + quote(text), "maps_query": q, "maps_url": maps_url(q),
            "guide_url": guide_url, "pdf_url": pdf_url, "emergency": "112" if why == "red" else None}
