import pytest
from pydantic import ValidationError

from api.pipeline import mock
from api.schemas import Diagnosis, ObjectReport, RepairPlan, StepCheck, json_schema


@pytest.mark.parametrize("sc", ["motor", "faucet", "rice"])
@pytest.mark.parametrize("lang", ["id", "jv", "en"])
def test_mock_fixtures_validate(sc, lang):
    ObjectReport.model_validate(mock.object_report(sc, lang))
    Diagnosis.model_validate(mock.diagnosis(sc, lang))
    RepairPlan.model_validate(mock.plan(sc, lang))


def test_causes_sorted_by_confidence():
    d = mock.diagnosis("motor", "id")
    d["causes"] = list(reversed(d["causes"]))
    dx = Diagnosis.model_validate(d)
    assert [c.confidence for c in dx.causes] == sorted([c.confidence for c in dx.causes], reverse=True)


def test_steps_renumbered():
    p = mock.plan("faucet", "en")
    for st in p["steps"]:
        st["n"] = 99
    assert [s.n for s in RepairPlan.model_validate(p).steps] == [1, 2, 3, 4]


def test_cost_estimate_sums_parts():
    dx = Diagnosis.model_validate(mock.diagnosis("faucet", "id"))
    assert dx.cost_estimate_idr == 8000


def test_rejects_bad_values():
    d = mock.diagnosis("motor", "id")
    d["safety_level"] = "purple"
    with pytest.raises(ValidationError):
        Diagnosis.model_validate(d)
    d = mock.diagnosis("motor", "id")
    d["causes"][0]["confidence"] = 140
    with pytest.raises(ValidationError):
        Diagnosis.model_validate(d)
    with pytest.raises(ValidationError):
        RepairPlan.model_validate({"cause_title": "x", "steps": []})


@pytest.mark.parametrize("cls", [ObjectReport, Diagnosis, RepairPlan, StepCheck])
def test_json_schema_has_no_refs(cls):
    s = json_schema(cls)
    assert "$ref" not in str(s) and "$defs" not in s
    assert s["type"] == "object"
