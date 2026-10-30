"""What the person sees when Meta's API misbehaves: friendly sentence, no raw URLs, a working Try again."""
import time
import types

import pytest
from fastapi.testclient import TestClient

from api import errors, meta_client
from api.pipeline import engine
from api.settings import settings
from api.testing import fake_meta

BASE = fake_meta.serve_in_thread()


@pytest.fixture
def live(monkeypatch):
    monkeypatch.setattr(settings, "mock", False)
    monkeypatch.setattr(settings, "meta_api_key", fake_meta.TEST_KEY)
    monkeypatch.setattr(settings, "meta_api_base", BASE)
    # retries back off 2/4/8 s in real life; tests must not wait
    monkeypatch.setattr(meta_client, "time", types.SimpleNamespace(sleep=lambda s: None, time=time.time))
    fake_meta.CALLS.clear()
    fake_meta.FAULTS.clear()
    from api.main import app

    yield TestClient(app)
    fake_meta.FAULTS.clear()


def _wait(c, sid):
    for _ in range(300):
        s = c.get(f"/api/sessions/{sid}").json()
        if s["status"] not in ("created", "running"):
            return s
        time.sleep(0.05)
    raise AssertionError("timeout")


def _new(c, sample="faucet", lang="id"):
    return c.post("/api/sessions", data={"sample": sample, "language": lang}).json()["id"]


def test_classify_and_friendly_messages_in_all_languages():
    cases = {
        "429 from https://api.meta.ai/v1/chat/completions: slow down": "busy",
        "503 from https://x: down": "busy",
        "401 from https://x: bad key": "auth",
        "Request to https://x failed: timed out": "network",
        "model returned invalid diagnosis: x": "invalid",
        "something odd": "generic",
    }
    for text, kind in cases.items():
        assert errors.classify(RuntimeError(text)) == kind
        for lang in ("id", "jv", "en"):
            msg = errors.friendly(RuntimeError(text), lang)
            assert msg and "http" not in msg and "$" not in msg
    from api import cost

    assert errors.classify(cost.BudgetExceeded("Job budget $1.00 reached")) == "budget"


def test_detail_scrubs_keys():
    d = errors.detail(RuntimeError('401 {"api_key": "sk-abcdef123456"} Authorization: Bearer sk-abcdef123456'))
    assert "abcdef123456" not in d


def test_outage_gives_friendly_error_then_retry_recovers(live):
    fake_meta.FAULTS["/chat/completions"] = {"status": 503, "times": None}
    sid = _new(live)
    s = _wait(live, sid)
    assert s["status"] == "error" and s["error_kind"] == "busy"
    assert "sibuk" in s["error"] and "http" not in s["error"] and "503" not in s["error"]
    assert "error_detail" not in s  # technical detail stays on the server
    assert engine.load(sid)["error_detail"]
    # the AI comes back; one tap on Try again resumes
    fake_meta.FAULTS.clear()
    assert live.post(f"/api/sessions/{sid}/retry").json() == {"ok": True}
    s = _wait(live, sid)
    assert s["status"] == "ready", s.get("error")
    assert s["retries"] == 1 and s["error"] is None


def test_retry_refused_when_nothing_failed(live):
    sid = _new(live)
    _wait(live, sid)
    assert live.post(f"/api/sessions/{sid}/retry").status_code == 409
    assert live.post("/api/sessions/nope/retry").status_code == 404


def test_flaky_api_is_absorbed_by_client_retries(live):
    fake_meta.FAULTS["/chat/completions"] = {"status": 429, "times": 2}
    sid = _new(live, lang="en")
    s = _wait(live, sid)
    assert s["status"] == "ready", s.get("error")
    assert sum(1 for c in fake_meta.CALLS if c["endpoint"] == "fault") == 2


def test_bad_key_message_in_javanese(live, monkeypatch):
    monkeypatch.setattr(settings, "meta_api_key", "wrong")
    sid = _new(live, lang="jv")
    s = _wait(live, sid)
    assert s["status"] == "error" and s["error_kind"] == "auth"
    assert "Kunci" in s["error"]


def test_sam_outage_does_not_sink_the_session(live):
    fake_meta.FAULTS["/responses"] = {"status": 500, "times": None}
    sid = _new(live, sample="motor")
    s = _wait(live, sid)
    if s["status"] == "needs_answer":
        live.post(f"/api/sessions/{sid}/answer", data={"text": "Tidak"})
        s = _wait(live, sid)
    assert s["status"] == "ready", s.get("error")
    assert not any(p["found"] for p in s["parts"].values())  # guide still works, on the plain photo


def test_image_edit_outage_falls_back_to_annotated_photo(live):
    fake_meta.FAULTS["/images/edits"] = {"status": 500, "times": None}
    fake_meta.FAULTS["/images/generations"] = {"status": 500, "times": None}
    sid = _new(live, sample="faucet", lang="en")
    s = _wait(live, sid)
    assert s["status"] == "ready", s.get("error")


def test_step_check_outage_is_a_503_with_friendly_text_and_session_survives(live):
    sid = _new(live, sample="faucet", lang="en")
    assert _wait(live, sid)["status"] == "ready"
    fake_meta.FAULTS["/chat/completions"] = {"status": 500, "times": None}
    photo = engine.session_dir(sid) / "photo1.jpg"
    r = live.post(f"/api/sessions/{sid}/steps/1/check", files={"photo": ("a.jpg", photo.read_bytes(), "image/jpeg")})
    assert r.status_code == 503 and "busy" in r.json()["detail"] and r.headers["retry-after"]
    fake_meta.FAULTS.clear()
    r = live.post(f"/api/sessions/{sid}/steps/1/check", files={"photo": ("a.jpg", photo.read_bytes(), "image/jpeg")})
    assert r.status_code == 200


def test_replan_outage_keeps_the_cause_so_pressing_again_works(live):
    sid = _new(live, sample="faucet", lang="en")
    assert _wait(live, sid)["status"] == "ready"
    fake_meta.FAULTS["/chat/completions"] = {"status": 500, "times": None}
    r = live.post(f"/api/sessions/{sid}/replan", data={"report": "still dripping"})
    assert r.status_code == 503
    s = engine.load(sid)
    assert s["cause_index"] == 0 and s["history"] == []
    fake_meta.FAULTS.clear()
    r = live.post(f"/api/sessions/{sid}/replan", data={"report": "still dripping"})
    assert r.status_code == 200 and r.json()["cause_index"] == 1
