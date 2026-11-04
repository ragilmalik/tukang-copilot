"""1.29.9: the PDF strikes through causes already tried, and Basa Jawa says "keslametan" for safety everywhere."""
import re
from pathlib import Path

from api.render import brand, report_pdf

ROOT = Path(__file__).resolve().parents[2]


def _rep(lang):
    return {"id": "x", "lang": lang, "object": "Pompa", "problem": "Ora metu banyu", "fix": "Foot valve", "steps_total": 0,
            "steps_verified": 0, "tools": [], "parts": [], "attempts": [], "safety_level": "amber"}


def _session(cur):
    causes = [{"title": "Pancingan kosong", "confidence": 60}, {"title": "Foot valve bocor", "confidence": 30},
              {"title": "Kapasitor", "confidence": 10}]
    return {"mode": "mock", "safety": {"reason": "ok"}, "diagnosis": {"causes": causes}, "cause_index": cur}


def _drawn(monkeypatch, tmp_path, lang, cur):
    seen: list[tuple[str, object]] = []
    real = brand.draw

    def spy(d, xy, text, kind, size, fill):
        seen.append((text, fill))
        return real(d, xy, text, kind, size, fill)

    monkeypatch.setattr(brand, "draw", spy)
    report_pdf.build(_rep(lang), _session(cur), tmp_path, tmp_path / "r.pdf")
    return seen


def test_tried_cause_is_greyed_with_a_red_tried_label(monkeypatch, tmp_path):
    seen = _drawn(monkeypatch, tmp_path, "jv", 1)
    assert ("wis dijajal", brand.RED) in seen
    assert ("Pancingan kosong", report_pdf.MUTED) in seen      # the tried one, struck through
    assert ("Foot valve bocor", report_pdf.INK) in seen         # the one being worked on


def test_no_tried_label_on_the_first_plan(monkeypatch, tmp_path):
    seen = _drawn(monkeypatch, tmp_path, "en", 0)
    assert not [t for t, _ in seen if t == "tried"]


def test_tried_label_in_every_language():
    assert {k: report_pdf.LABELS[k]["tried_mark"] for k in ("id", "jv", "en")} == {"id": "sudah dicoba", "jv": "wis dijajal", "en": "tried"}


def _jv_parts(js: str) -> list[str]:
    parts = [js.split("T.jv = Object.assign({}, T.id, {", 1)[1].split("\n});", 1)[0]]
    parts += [chunk.split("\n  en: ", 1)[0] for chunk in js.split("\n  jv: ")[1:]]       # T_EXTRA style tables
    parts += [ln for ln in js.splitlines() if re.search(r"\bjv: \[", ln)]                 # SAFETY_BASE / SAFETY_BY_KIND
    return parts


def test_javanese_never_says_keamanan():
    js = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
    parts = _jv_parts(js)
    assert len(parts) >= 5
    assert not [p[:80] for p in parts if "keamanan" in p.lower()]
    for table in (report_pdf.LABELS["jv"], report_pdf.AGENT["jv"]):
        assert not [v for v in table.values() if "keamanan" in v.lower()]
    assert "keslametan" in report_pdf.AGENT["jv"]["ag_guard_ok"]


def test_safety_by_kind_has_every_language_for_every_kind():
    js = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
    block = js.split("window.SAFETY_BY_KIND = {", 1)[1].split("\n};", 1)[0]
    for kind in ("motor", "plumbing", "pump", "appliance"):
        entry = block.split(f"{kind}: {{", 1)[1].split("] },", 1)[0]
        assert all(f"{lang}: [" in entry for lang in ("id", "jv", "en")), kind
