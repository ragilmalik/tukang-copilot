"""Cost guards inside a repair: step checks are capped per repair and their spend counts toward the
session cost (so DAILY_BUDGET_USD sees it); follow-up model calls are rate limited per visitor in live mode."""
import time

import pytest
from fastapi.testclient import TestClient

from api import guard
from api.main import app
from api.pipeline import engine
from api.settings import settings
from api.tests.doubles import fake_meta

client = TestClient(app)


WAIT_S = 60  # seconds a repair may take: generous, CI runners are slow and earlier repairs can still hold the worker pool


@pytest.fixture(autouse=True)
def _reset_guard():
    guard.reset()
    yield
    guard.reset()


def _ready(c, sample="faucet", lang="en"):
    sid = c.post("/api/sessions", data={"sample": sample, "language": lang}).json()["id"]
    deadline = time.monotonic() + WAIT_S
    while time.monotonic() < deadline:
        s = c.get(f"/api/sessions/{sid}").json()
        if s["status"] not in ("created", "running"):
            return sid, s
        time.sleep(0.03)
    raise AssertionError("timeout")


def _photo(sid):
    return {"photo": ("a.jpg", (engine.session_dir(sid) / "photo1.jpg").read_bytes(), "image/jpeg")}


def test_step_checks_are_capped_per_repair_even_across_a_replan(monkeypatch):
    monkeypatch.setattr(settings, "max_step_checks", 2)
    sid, _ = _ready(client)
    assert client.post(f"/api/sessions/{sid}/steps/1/check", files=_photo(sid)).status_code == 200
    client.post(f"/api/sessions/{sid}/replan", data={"report": "still dripping"})
    assert client.post(f"/api/sessions/{sid}/steps/1/check", files=_photo(sid)).status_code == 200
    r = client.post(f"/api/sessions/{sid}/steps/1/check", files=_photo(sid))
    assert r.status_code == 429 and "photo checks" in r.json()["detail"]
    assert engine.load(sid)["checks_used"] == 2


def test_step_check_spend_is_added_to_the_session_cost(monkeypatch):
    base = fake_meta.serve_in_thread()
    monkeypatch.setattr(settings, "mock", False)
    monkeypatch.setattr(settings, "meta_api_key", fake_meta.TEST_KEY)
    monkeypatch.setattr(settings, "meta_api_base", base)
    sid, s = _ready(client, "faucet", "en")
    assert s["status"] == "ready"
    before = s["cost"]["spent_usd"]
    assert client.post(f"/api/sessions/{sid}/steps/1/check", files=_photo(sid)).status_code == 200
    after = client.get(f"/api/sessions/{sid}").json()["cost"]["spent_usd"]
    assert after > before


def test_followup_calls_are_rate_limited_per_visitor_in_live_mode(monkeypatch):
    sid, _ = _ready(client)
    monkeypatch.setattr(guard, "active", lambda: True)
    monkeypatch.setattr(settings, "followup_rate_per_hour", 2)
    h = {"x-forwarded-for": "9.9.9.9"}
    for _ in range(2):
        assert client.post(f"/api/sessions/{sid}/steps/1/check", files=_photo(sid), headers=h).status_code == 200
    r = client.post(f"/api/sessions/{sid}/replan", data={"report": "x"}, headers=h)
    assert r.status_code == 429 and r.headers["retry-after"].isdigit() and r.json()["detail"] == guard.MESSAGES["rate"]["en"]
    # the follow-up bucket never eats the new-repair allowance, and another visitor is unaffected
    assert client.post("/api/sessions", data={"sample": "faucet", "language": "en"}, headers=h).status_code == 200
    assert client.post(f"/api/sessions/{sid}/steps/1/check", files=_photo(sid), headers={"x-forwarded-for": "1.2.3.4"}).status_code == 200


def test_followup_calls_are_free_of_limits_in_demo_mode(monkeypatch):
    monkeypatch.setattr(settings, "followup_rate_per_hour", 1)
    sid, _ = _ready(client)
    for _ in range(3):
        assert client.post(f"/api/sessions/{sid}/steps/1/check", files=_photo(sid)).status_code == 200


def test_oversized_answer_and_report_are_refused():
    sid, _ = _ready(client)
    assert client.post(f"/api/sessions/{sid}/replan", data={"report": "x" * 2001}).status_code == 400
    assert client.post(f"/api/sessions/{sid}/answer", data={"text": "x" * 2001}).status_code == 400
