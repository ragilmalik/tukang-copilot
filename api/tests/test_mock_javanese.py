"""Demo answers in Basa Jawa, so the jv demo never shows Indonesian content under Javanese buttons."""
import time

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.pipeline import mock
from api.pipeline.mock_jv import JV

client = TestClient(app)
SCENARIOS = ["motor", "pump", "faucet", "rice", "tire"]


def _texts(sc, lang):
    rep, dx = mock._object_report(sc, lang), mock.diagnosis(sc, lang)
    out = [rep["object"], *rep["visible_issues"], *[c["name"] for c in rep["components"]], dx["problem_summary"], dx["safety_reason"],
           *[c["title"] for c in dx["causes"]], *[e for c in dx["causes"] for e in c["evidence"]], *dx.get("before_you_start", []),
           dx.get("follow_up_question") or ""]
    for ci in (0, 1):
        p = mock.plan(sc, lang, ci)
        out += [p["done_check"], p["when_to_call_pro"], p["cause_title"], *[s["instruction"] for s in p["steps"]],
                *[s["expected_state"] for s in p["steps"]]]
    return [t for t in out if t]


def test_every_indonesian_demo_string_has_a_javanese_entry(monkeypatch):
    seen = []
    real = mock._L

    def spy(lang, i, e):
        seen.append(i)
        return real(lang, i, e)

    monkeypatch.setattr(mock, "_L", spy)
    for sc in SCENARIOS:
        _texts(sc, "id")
    missing = sorted({s for s in seen if s not in JV})
    assert not missing, missing


@pytest.mark.parametrize("sc", SCENARIOS)
def test_javanese_demo_content_is_mostly_not_indonesian(sc):
    ids, jvs = _texts(sc, "id"), _texts(sc, "jv")
    assert len(ids) == len(jvs)
    changed = sum(1 for a, b in zip(ids, jvs) if a != b)
    assert changed / len(ids) >= 0.75, (sc, changed, len(ids))  # short part names (Cop busi, Tang, Pelek) stay


def test_step_check_answers_are_javanese(tmp_path):
    from PIL import Image

    p = tmp_path / "d.jpg"
    Image.new("RGB", (100, 100), (5, 5, 5)).save(p)
    r = mock.step_check(p, "jv")
    assert r["observation"].startswith("Fotone kepetengen") and "senter" in r["correction"]


@pytest.mark.parametrize("sample,status", [("pump", "ready"), ("tire", "ready"), ("faucet", "ready"), ("rice", "stopped"), ("motor", "needs_answer")])
def test_javanese_samples_still_pass_the_safety_gates(sample, status):
    sid = client.post("/api/sessions", data={"sample": sample, "language": "jv"}).json()["id"]
    for _ in range(200):
        s = client.get(f"/api/sessions/{sid}").json()
        if s["status"] not in ("created", "running"):
            break
        time.sleep(0.03)
    assert s["status"] == status
    if status == "ready":
        assert s["plan"]["steps"][0]["instruction"] != mock.plan(sample, "id")["steps"][0]["instruction"]
