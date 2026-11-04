"""1.29.12: Basa Jawa sticks to ngoko ("kowe", "fotomu"), the register most of the app already used.
A few lines said "sampeyan" or "antosna" (krama-ish), so the same screen switched registers."""
from pathlib import Path

from api.render import report_pdf, workshop_pdf

ROOT = Path(__file__).resolve().parents[2]
KRAMA = ("sampeyan", "panjenengan", "antosna", "antosan", "sampun", "mboten", "nggih", "dereng")


def _jv_parts() -> list[str]:
    js = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
    parts = [js.split("T.jv = Object.assign({}, T.id, {", 1)[1].split("\n});", 1)[0]]
    parts += [chunk.split("\n  en: ", 1)[0] for chunk in js.split("\n  jv: ")[1:]]
    return parts


def test_app_javanese_is_ngoko():
    text = " ".join(_jv_parts()).lower()
    assert not [w for w in KRAMA if w in text]
    assert "kowe irit kira-kira" in text and "fotomu tetep aman" in text


def test_pdf_javanese_is_ngoko():
    vals = list(report_pdf.LABELS["jv"].values()) + list(report_pdf.AGENT["jv"].values())
    vals += [str(v) for v in workshop_pdf.TXT["jv"].values()]
    joined = " ".join(vals).lower()
    assert not [w for w in KRAMA if w in joined]
    assert report_pdf.AGENT["jv"]["ag_outcome_fixed"].startswith("Kowe ")
