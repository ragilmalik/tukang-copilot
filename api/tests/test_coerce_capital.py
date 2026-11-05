"""Names and sentences from the live model start with a capital everywhere, not only where CSS fixes the heading."""
from __future__ import annotations

from api.coerce import coerce
from api.schemas import Diagnosis, ObjectReport, RepairPlan


def test_object_name_gets_a_capital() -> None:
    o = ObjectReport.model_validate(coerce(ObjectReport, {"object": "underbone motorcycle engine cylinder head area", "category": "motor"}))
    assert o.object == "Underbone motorcycle engine cylinder head area"


def test_diagnosis_and_plan_text_get_a_capital() -> None:
    d = Diagnosis.model_validate(coerce(Diagnosis, {
        "problem_summary": "scooter will not crank", "causes": [{"title": "faulty starter relay", "confidence": 60}],
        "safety_level": "amber", "difficulty": 2, "minutes_estimate": 30}))
    assert d.problem_summary == "Scooter will not crank" and d.causes[0].title == "Faulty starter relay"
    p = RepairPlan.model_validate(coerce(RepairPlan, {"cause_title": "faulty starter relay",
                                                      "steps": [{"instruction": "turn the key off", "expected_state": "key out"}]}))
    assert p.cause_title == "Faulty starter relay" and p.steps[0].instruction == "Turn the key off"


def test_text_that_starts_with_a_number_or_capital_is_left_alone() -> None:
    o = ObjectReport.model_validate(coerce(ObjectReport, {"object": "12V aki motor", "category": "motor"}))
    assert o.object == "12V aki motor"


def test_missing_tools_and_parts_are_empty_lists_not_a_validation_error() -> None:
    """coerce used to turn a left-out "tools" into None, which failed validation and cost a retry call."""
    d = Diagnosis.model_validate(coerce(Diagnosis, {"problem_summary": "X", "causes": [{"title": "Y", "confidence": 50}],
                                                    "safety_level": "green", "difficulty": 1, "minutes_estimate": 5}))
    assert d.tools == [] and d.parts == []


def test_null_components_mean_none_found() -> None:
    o = ObjectReport.model_validate(coerce(ObjectReport, {"object": "Pompa", "category": "pump", "components": None}))
    assert o.components == []
