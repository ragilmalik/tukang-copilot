"""Steps with a real waiting time (wait_minutes): schema, mock, coerce, workshop sheet, web wiring."""
from pathlib import Path

import pytest

from api.pipeline import mock
from api.render import workshop_pdf
from api.schemas import RepairPlan


WEB = Path(__file__).resolve().parents[2] / "web"


def test_default_is_no_wait():
    plan = RepairPlan.model_validate(mock.plan("pump", "en"))
    assert all(s.wait_minutes == 0 for s in plan.steps)


@pytest.mark.parametrize("lang", ["id", "jv", "en"])
def test_motor_cooldown_step_has_wait(lang):
    plan = RepairPlan.model_validate(mock.plan("motor", lang))
    assert plan.steps[0].wait_minutes == 10
    assert sum(1 for s in plan.steps if s.wait_minutes) == 1


def test_wait_bounds():
    d = mock.plan("motor", "en")
    d["steps"][0]["wait_minutes"] = 999
    with pytest.raises(ValueError):
        RepairPlan.model_validate(d)


@pytest.mark.parametrize(("lang", "word"), [("id", "Tunggu 10 menit"), ("jv", "Enteni 10 menit"), ("en", "Wait 10 minutes")])
def test_workshop_sheet_mentions_wait(monkeypatch, tmp_path, lang, word):
    from api.render.report_pdf import _Doc

    seen: list[str] = []
    orig = _Doc.text

    def spy(self, txt, *a, **k):
        seen.append(str(txt))
        return orig(self, txt, *a, **k)

    monkeypatch.setattr(_Doc, "text", spy)
    plan = mock.plan("motor", lang)
    doc = _Doc("f", "p")
    workshop_pdf._step_page(doc, plan["steps"][0], len(plan["steps"]), {"plan": plan}, tmp_path, workshop_pdf.TXT[lang])
    assert any(word in t for t in seen), seen
    seen.clear()
    workshop_pdf._step_page(doc, plan["steps"][1], len(plan["steps"]), {"plan": plan}, tmp_path, workshop_pdf.TXT[lang])
    assert not any(word.split()[0] in t and "[ ]" in t for t in seen)


def test_all_languages_have_timer_strings():
    js = (WEB / "app.js").read_text()
    for k in ("waitFor", "timerStart", "timerStop", "timerDone"):
        assert js.count(f"{k}:") == 3, k
    for page in ("index.html", "guide.html"):
        h = (WEB / page).read_text()
        assert 'id="stepTimer"' in h and 'id="timerBtn"' in h and 'id="timerClock"' in h
