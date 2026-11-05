"""DEMO_FALLBACK: in live mode a Meta call that still fails after its retries is replaced by the demo answer for
that stage, labelled in the session (fallback list), the UI and the PDF. Budget stops and the switch off still fail."""
import io
import time
import types
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from api import meta_client
from api.pipeline import engine
from api.settings import settings
from api.tests.doubles import fake_meta

BASE = fake_meta.serve_in_thread()
WEB = Path(__file__).resolve().parents[2] / "web"


WAIT_S = 60  # seconds a repair may take: generous, CI runners are slow and earlier repairs can still hold the worker pool


@pytest.fixture
def live(monkeypatch):
    monkeypatch.setattr(settings, "mock", False)
    monkeypatch.setattr(settings, "meta_api_key", fake_meta.TEST_KEY)
    monkeypatch.setattr(settings, "meta_api_base", BASE)
    monkeypatch.setattr(settings, "demo_fallback", True)
    monkeypatch.setattr(meta_client, "time", types.SimpleNamespace(sleep=lambda s: None, time=time.time))
    fake_meta.CALLS.clear()
    fake_meta.FAULTS.clear()
    from api.main import app

    yield TestClient(app)
    fake_meta.FAULTS.clear()


def _wait(c, sid):
    deadline = time.monotonic() + WAIT_S
    while time.monotonic() < deadline:
        s = c.get(f"/api/sessions/{sid}").json()
        if s["status"] not in ("created", "running"):
            return s
        time.sleep(0.05)
    raise AssertionError("timeout")


def test_chat_outage_falls_back_to_demo_answers(live):
    fake_meta.FAULTS["/chat/completions"] = {"status": 503, "times": None}
    s = _wait(live, live.post("/api/sessions", data={"sample": "faucet", "language": "en"}).json()["id"])
    assert s["status"] == "ready", s.get("error")
    assert s["mode"] == "live" and {"object_report", "diagnosis", "repair_plan"} <= set(s["fallback"])
    pdf = live.get(f"/api/sessions/{s['id']}/report.pdf")
    assert pdf.status_code == 200


def test_one_flaky_stage_only_labels_that_stage(live):
    fake_meta.FAULTS["/chat/completions"] = {"status": 400, "times": 1}  # 400 is not retried: Look fails once
    s = _wait(live, live.post("/api/sessions", data={"sample": "faucet", "language": "id"}).json()["id"])
    assert s["status"] == "ready" and s["fallback"] == ["object_report"]


def test_no_fallback_when_all_is_well(live):
    s = _wait(live, live.post("/api/sessions", data={"sample": "faucet", "language": "id"}).json()["id"])
    assert s["status"] == "ready" and not s.get("fallback")


def test_switch_off_keeps_the_error(live, monkeypatch):
    monkeypatch.setattr(settings, "demo_fallback", False)
    fake_meta.FAULTS["/chat/completions"] = {"status": 503, "times": None}
    s = _wait(live, live.post("/api/sessions", data={"sample": "faucet", "language": "en"}).json()["id"])
    assert s["status"] == "error" and not s.get("fallback")


def test_budget_stop_never_falls_back(live, monkeypatch):
    from api import cost
    from api.schemas import DiagramReview

    def boom(*a, **k):
        raise cost.BudgetExceeded("budget")

    monkeypatch.setattr(engine, "_chat_json_live", boom)
    sess: dict[str, Any] = {}
    with pytest.raises(cost.BudgetExceeded):
        engine._chat_json(DiagramReview, "x", [], "diagram_review", {"ok": True}, fallback_into=sess)
    assert not sess.get("fallback")

    def down(*a, **k):
        raise meta_client.MetaAPIError("503 from api")

    monkeypatch.setattr(engine, "_chat_json_live", down)
    assert engine._chat_json(DiagramReview, "x", [], "diagram_review", {"ok": True}, fallback_into=sess).ok
    assert sess["fallback"] == ["diagram_review"]
    with pytest.raises(meta_client.MetaAPIError):  # no demo answer to fall back on
        engine._chat_json(DiagramReview, "x", [], "diagram_review", {}, fallback_into=sess)


def test_step_check_fallback_is_labelled_and_not_counted(live):
    s = _wait(live, live.post("/api/sessions", data={"sample": "faucet", "language": "en"}).json()["id"])
    fake_meta.FAULTS["/chat/completions"] = {"status": 503, "times": None}
    buf = io.BytesIO()
    Image.open(engine.session_dir(s["id"]) / "photo1.jpg").save(buf, "JPEG")
    r = live.post(f"/api/sessions/{s['id']}/steps/1/check", files={"photo": ("c.jpg", buf.getvalue(), "image/jpeg")})
    assert r.status_code == 200 and r.json()["fallback"] is True
    rec = engine.load(s["id"])["checks"]["1"]
    assert rec["passed"] is False and rec["fails"] == 0 and rec["tries"][0]["fallback"] is True


def test_web_shows_fallback_label():
    js = (WEB / "app.js").read_text(encoding="utf-8")
    for page in ("index.html", "guide.html"):
        assert 'id="fallbackNote"' in (WEB / page).read_text(encoding="utf-8")
    assert "s.fallback" in js and "r.fallback" in js
    assert "Wangsulan conto (API live" in js[js.index("T.jv = Object.assign"):]
