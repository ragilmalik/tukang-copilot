"""Model-drift tolerance: messy but harmless model output is repaired, real garbage still fails cleanly."""
import json

import pytest

from api import meta_client
from api.coerce import coerce, extract_json
from api.pipeline import engine, mock
from api.schemas import Diagnosis, ObjectReport, RepairPlan, StepCheck
from api.settings import settings


def test_extract_json_handles_think_fences_and_prose():
    assert extract_json('<think>maybe {"a": 2}</think>{"a": 1}') == {"a": 1}
    assert extract_json('Sure! ```json\n{"a": 1, "b": [1, 2]}\n``` hope it helps {x}') == {"a": 1, "b": [1, 2]}
    assert extract_json('Result: {"a": {"b": "}"}} trailing } brace') == {"a": {"b": "}"}}
    assert extract_json("[1, 2]") == [1, 2]
    with pytest.raises(ValueError):
        extract_json("no json at all")
    with pytest.raises(ValueError):
        extract_json("")


def test_meta_client_uses_tolerant_extractor():
    assert meta_client._extract_json("```\n{\"ok\": true}\n```") == {"ok": True}


def test_diagnosis_quirks_are_repaired():
    d = mock.diagnosis("motor", "id")
    d["safety_level"] = "Amber "
    d["difficulty"] = "3"
    d["minutes_estimate"] = 25.0
    d["causes"] = [{"title": f"c{i}", "confidence": c, "evidence": "one string", "component_ids": [1]}
                   for i, c in enumerate(["40%", 0.85, 20, 10, 5, 2])]
    d["parts"] = [{"name": "Busi", "est_price_idr": "Rp 25.000"}, "Kabel"]
    out = Diagnosis.model_validate(coerce(Diagnosis, d))
    assert out.safety_level == "amber" and out.difficulty == 3
    assert [c.confidence for c in out.causes] == [85, 40, 20, 10]   # sorted, capped at 4
    assert out.causes[0].evidence == ["one string"] and out.causes[0].component_ids == ["1"]
    assert out.parts[0].est_price_idr == 25000 and out.parts[1].name == "Kabel"


def test_aliases_and_clamps():
    d = mock.diagnosis("rice", "en")
    d["safety_level"] = "danger"
    d["difficulty"] = 9
    assert Diagnosis.model_validate(coerce(Diagnosis, d)).safety_level == "red"
    assert Diagnosis.model_validate(coerce(Diagnosis, d)).difficulty == 5


def test_object_report_extra_components_and_percent_boxes():
    r = mock.object_report("motor", "en")
    comp = dict(r["components"][0])
    r["category"] = "Motorcycle"
    r["components"] = [dict(comp, id=i, prompt_box=[10, 10, 50, 60] if i == 0 else None) for i in range(7)]
    out = ObjectReport.model_validate(coerce(ObjectReport, r))
    assert out.category == "motor" and len(out.components) == 5
    assert out.components[0].prompt_box == [0.1, 0.1, 0.5, 0.6] and out.components[0].id == "0"


def test_plan_too_many_steps_and_string_warnings():
    p = mock.plan("faucet", "en", 0)
    p["steps"] = [dict(p["steps"][0], warnings="careful", needs_diagram="false") for _ in range(12)]
    out = RepairPlan.model_validate(coerce(RepairPlan, p))
    assert len(out.steps) == 10 and out.steps[0].warnings == ["careful"] and out.steps[0].needs_diagram is False
    assert [s.n for s in out.steps] == list(range(1, 11))


def test_step_check_bool_words_and_no_mutation():
    raw = {"passed": "Yes", "observation": "ok"}
    assert StepCheck.model_validate(coerce(StepCheck, raw)).passed is True
    assert raw["passed"] == "Yes"   # input untouched


def test_unrepairable_stays_invalid_and_unknown_class_passes_through():
    with pytest.raises(Exception):
        Diagnosis.model_validate(coerce(Diagnosis, {"problem_summary": "x"}))
    assert coerce(Diagnosis, ["not", "a", "dict"]) == ["not", "a", "dict"]


@pytest.fixture
def live(monkeypatch):
    monkeypatch.setattr(settings, "mock", False)
    monkeypatch.setattr(settings, "meta_api_key", "test-key")
    return monkeypatch


def test_engine_retries_when_reply_has_no_json(live):
    good = mock.diagnosis("motor", "id")
    replies = [ValueError("no JSON found in model output"), good]
    seen = []

    def fake(messages, schema, name, **kw):
        seen.append(len(messages))
        r = replies.pop(0)
        if isinstance(r, Exception):
            raise r
        return r

    live.setattr(meta_client, "chat_json", fake)
    out = engine._chat_json(Diagnosis, "sys", [{"type": "text", "text": "x"}], "diagnosis", {})
    assert out.safety_level == good["safety_level"] and seen == [2, 3]


def test_engine_gives_friendly_failure_after_two_bad_replies(live):
    def fake(messages, schema, name, **kw):
        raise ValueError("no JSON")

    live.setattr(meta_client, "chat_json", fake)
    with pytest.raises(RuntimeError, match="returned invalid"):
        engine._chat_json(Diagnosis, "sys", [], "diagnosis", {})


def test_engine_accepts_drifty_reply_without_retry(live):
    d = mock.diagnosis("faucet", "id")
    d["safety_level"] = "GREEN"
    d["causes"][0]["confidence"] = 0.9
    calls = []
    def fake(*a, **k):
        calls.append(1)
        return json.loads(json.dumps(d))

    live.setattr(meta_client, "chat_json", fake)
    out = engine._chat_json(Diagnosis, "sys", [], "diagnosis", {})
    assert out.safety_level == "green" and out.causes[0].confidence == 90 and len(calls) == 1


def test_wait_minutes_repair():
    from api.coerce import _wait
    assert _wait(10) == 10 and _wait("about 15 min") == 15 and _wait("7,5") == 8
    assert _wait(0) == 0 and _wait(-3) == 0 and _wait(500) == 0 and _wait(True) == 0 and _wait(None) == 0 and _wait("none") == 0
    assert _wait(float("nan")) == 0
