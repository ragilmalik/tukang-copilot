"""Owner input is data, never instructions (prompt-injection hardening).

Everything the owner types or says (description, voice transcript, follow-up answer, "still broken" report)
reaches the model only through `fence()`: control, zero-width and bidi characters are stripped, angle brackets
are swapped for look-alikes so the text cannot close its own tag, and the result is wrapped in a named tag the
prompts tell the model to treat as data. `signals()` spots instruction-like phrases (id / jv / en) so the
session can record that it saw and ignored them. The code safety gates in api/pipeline/safety.py still run on
the raw text and on the plan, so even a model that obeys an injection cannot lift a hard stop.
Pure functions, no I/O.
"""
from __future__ import annotations

import re
import unicodedata

# C0/C1 controls except tab/newline, zero-width chars, bidi overrides/isolates, BOM, soft hyphen.
_INVISIBLE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\u00ad\u200b-\u200f\u202a-\u202e\u2060-\u2064\u2066-\u2069\ufeff]")
MAX_FIELD = 2000

_PATTERNS = [
    # English
    r"ignore (all |any |the )?(previous|prior|above|earlier|preceding)? ?(instructions|rules|prompts?|messages)",
    r"disregard (all |the )?(previous|above|prior)? ?(instructions|rules)",
    r"(reveal|show|print|repeat) (me )?(your|the) (system )?(prompt|instructions|rules)",
    r"\bsystem prompt\b", r"\byou are now\b", r"\bact as\b", r"\bjailbreak\b", r"\bdeveloper mode\b",
    r"(say|mark|rate|label) (it|this)( is)? (safe|green)", r"safety_level", r"skip (the )?safety",
    r"</?(system|assistant|owner_text|owner_report|instructions?)>",
    # Bahasa Indonesia
    r"abaikan (semua |seluruh )?(aturan|instruksi|perintah|petunjuk)", r"lupakan (semua )?(aturan|instruksi|perintah)",
    r"(bilang|katakan|tulis) (saja )?(ini )?aman", r"(tampilkan|bocorkan|tunjukkan) (prompt|instruksi)",
    r"kamu sekarang (adalah|jadi)", r"lewati (langkah )?keselamatan",
    # Basa Jawa
    r"(ora|aja|ojo) usah (ngrungokake|nggatekake|manut) (aturan|pituduh)", r"lalekna (aturan|pituduh)",
    r"(kandha|ngomong|tulisen) (wae )?(iki )?aman",
]
_SIGNAL_RE = re.compile("|".join(f"(?:{p})" for p in _PATTERNS), re.I)


def clean(text: str | None, limit: int = MAX_FIELD) -> str:
    """NFKC-normalise (folds full-width look-alikes), drop invisible characters, trim, cap the length."""
    t = unicodedata.normalize("NFKC", str(text or ""))
    return _INVISIBLE.sub("", t).strip()[:limit]


def fence(text: str | None, tag: str = "owner_text", limit: int = MAX_FIELD) -> str:
    """Wrap cleaned owner text in <tag>…</tag>. Angle brackets inside become ‹ › so it cannot close the tag."""
    body = clean(text, limit).replace("<", "‹").replace(">", "›")
    return f"<{tag}>\n{body}\n</{tag}>"


def signals(*texts: str | None) -> list[str]:
    """Instruction-like phrases found in owner text (lower-cased, unique, max 5). Empty list = nothing seen."""
    found: list[str] = []
    for t in texts:
        for m in _SIGNAL_RE.finditer(clean(t)):
            hit = m.group(0).lower().strip()
            if hit not in found:
                found.append(hit)
    return found[:5]
