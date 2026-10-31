"""'Before you start' tick list (Diagnosis.before_you_start): schema, mock, coerce, PDF, web wiring."""
from pathlib import Path

import pytest

from api import coerce
from api.pipeline import mock
from api.render import report_pdf
from api.schemas import Diagnosis

WEB = Path(__file__).resolve().parents[2] / "web"


@pytest.mark.parametrize("sc", ["motor", "pump", "tire", "faucet"])
@pytest.mark.parametrize("lang", ["id", "jv", "en"])
def test_mock_scenarios_have_preflight(sc, lang):
    dx = Diagnosis.model_validate(mock.diagnosis(sc, lang))
    assert 1 <= len(dx.before_you_start) <= 4
    assert all(x.strip() and len(x) < 140 for x in dx.before_you_start)


def test_red_stop_has_no_preflight():
    assert Diagnosis.model_validate(mock.diagnosis("rice", "en")).before_you_start == []


def test_pump_mentions_unplug():
    assert any("unplug" in x.lower() for x in Diagnosis.model_validate(mock.diagnosis("pump", "en")).before_you_start)


def test_schema_caps_at_four():
    d = mock.diagnosis("pump", "en")
    d["before_you_start"] = ["a", "b", "c", "d", "e"]
    with pytest.raises(ValueError):
        Diagnosis.model_validate(d)


def test_coerce_repairs_messy_lists():
    d = mock.diagnosis("pump", "en")
    d["before_you_start"] = ["  Unplug it  ", "", None, 5, "x" * 400, "a", "b", "c"]
    out = coerce._diagnosis(d)
    assert out["before_you_start"][0] == "Unplug it"
    assert len(out["before_you_start"]) <= 4
    assert all(len(x) <= 140 for x in out["before_you_start"])
    Diagnosis.model_validate(out)


def test_coerce_drops_preflight_on_red_and_non_lists():
    d = mock.diagnosis("pump", "en")
    d["safety_level"] = "red"
    assert coerce._diagnosis(d)["before_you_start"] == []
    d2 = mock.diagnosis("pump", "en")
    d2["before_you_start"] = "unplug it"
    Diagnosis.model_validate(coerce._diagnosis(d2))


def test_pdf_lists_preflight(monkeypatch, tmp_path):
    seen: list[str] = []
    orig = report_pdf._Doc.text

    def spy(self, txt, *a, **k):
        seen.append(str(txt))
        return orig(self, txt, *a, **k)

    monkeypatch.setattr(report_pdf._Doc, "text", spy)
    dx = mock.diagnosis("pump", "en")
    session = {"lang": "en", "diagnosis": dx, "safety": {"level": "amber", "reason": ""}, "plan": mock.plan("pump", "en"),
               "checks": {}, "status": "ready", "demo": True}
    rep = {"object": "Pump", "problem": "p", "fix": "f", "steps_total": 4, "steps_verified": 0, "tools": [], "parts": [],
           "safety_level": "amber", "attempts": [], "lang": "en", "status": "ready"}
    report_pdf.build(rep, session, tmp_path, tmp_path / "r.pdf")
    assert any("Before you start" in t for t in seen)
    assert any("The pump is unplugged" in t for t in seen)


def test_web_wiring():
    js = (WEB / "app.js").read_text()
    for page in ("index.html", "guide.html"):
        html = (WEB / page).read_text()
        assert 'id="preflight"' in html and 'id="preList"' in html and 'id="preState"' in html
    assert "renderPreflight" in js and js.count("preTitle:") == 3 and js.count("preLocked:") == 3 and js.count("preReady:") == 3
    assert "#stepCard.locked" in (WEB / "style.css").read_text()
    assert "before_you_start" in Path(WEB.parent / "prompts" / "diagnose.md").read_text()
