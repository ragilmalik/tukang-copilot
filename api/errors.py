"""Friendly, language-aware messages for pipeline failures.

The raw exception text (URLs, HTTP bodies) goes to the log and to `error_detail`; the person holding the phone
only sees one calm sentence in their own language plus a "Try again" button. Nothing here ever includes a key.
"""
from __future__ import annotations

import re

from . import cost

MESSAGES: dict[str, dict[str, str]] = {
    "busy": {
        "id": "Layanan AI sedang sibuk. Tunggu sebentar lalu coba lagi.",
        "jv": "Layanan AI lagi sibuk. Enteni sedhela terus jajal maneh.",
        "en": "The AI service is busy right now. Wait a moment and try again.",
    },
    "network": {
        "id": "Koneksi ke layanan AI terputus. Periksa sinyal internetmu lalu coba lagi.",
        "jv": "Sambungan menyang layanan AI putus. Priksa sinyal internetmu terus jajal maneh.",
        "en": "The connection to the AI service dropped. Check your signal and try again.",
    },
    "auth": {
        "id": "Kunci layanan AI belum benar di server ini. Beri tahu pemilik aplikasi.",
        "jv": "Kunci layanan AI durung bener ing server iki. Kandhanana sing duwe aplikasi.",
        "en": "The AI service key is not set up correctly on this server. Tell the app owner.",
    },
    "budget": {
        "id": "Batas biaya untuk perbaikan ini sudah tercapai. Mulai perbaikan baru dengan foto yang lebih sedikit.",
        "jv": "Wates biaya kanggo ndandani iki wis kecandhak. Wiwiti anyar nganggo foto sing luwih sithik.",
        "en": "The cost limit for this repair was reached. Start a new one with fewer photos.",
    },
    "invalid": {
        "id": "AI memberi jawaban yang tidak bisa dipakai. Coba lagi, atau ambil foto yang lebih jelas.",
        "jv": "AI menehi wangsulan sing ora bisa dienggo. Jajal maneh, utawa jupuk foto sing luwih cetha.",
        "en": "The AI gave an answer that could not be used. Try again, or take a clearer photo.",
    },
    "generic": {
        "id": "Ada masalah saat memeriksa. Coba lagi sebentar lagi.",
        "jv": "Ana masalah nalika mriksa. Jajal maneh sedhela maneh.",
        "en": "Something went wrong while checking. Please try again in a moment.",
    },
}


def classify(exc: BaseException) -> str:
    """Map an exception to a MESSAGES key."""
    if isinstance(exc, cost.BudgetExceeded):
        return "budget"
    text = str(exc).lower()
    m = re.match(r"\s*(\d{3}) from ", text)
    if m:
        code = int(m.group(1))
        if code in (401, 403):
            return "auth"
        if code in (408, 425, 429, 500, 502, 503, 504):
            return "busy"
    if "returned invalid" in text or "failed validation" in text:
        return "invalid"
    if "request to" in text and "failed" in text:
        return "network"
    return "generic"


def friendly(exc: BaseException, lang: str) -> str:
    return MESSAGES[classify(exc)].get(lang) or MESSAGES[classify(exc)]["en"]


def detail(exc: BaseException) -> str:
    """Technical detail for logs and the session file: one line, secrets scrubbed, bounded."""
    t = re.sub(r"(?i)bearer\s+[\w.\-]+", "Bearer ***", str(exc))
    t = re.sub(r"(?i)(api[_-]?key[\"']?\s*[:=]\s*[\"']?)[\w.\-]{6,}", r"\1***", t)
    return " ".join(t.split())[:400]
