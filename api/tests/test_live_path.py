"""The REAL meta_client HTTP path (multipart ASR, structured chat, SAM SSE stream + mask decoding, image
edits, Baseten open weights) end to end against the fake Meta server in api/tests/doubles/fake_meta.py."""
import time

import pytest
from fastapi.testclient import TestClient

from api.pipeline import engine
from api.settings import settings
from api.tests.doubles import fake_meta

BASE = fake_meta.serve_in_thread()


WAIT_S = 60  # seconds a repair may take: generous, CI runners are slow and earlier repairs can still hold the worker pool


@pytest.fixture
def live(monkeypatch):
    monkeypatch.setattr(settings, "mock", False)
    monkeypatch.setattr(settings, "meta_api_key", fake_meta.TEST_KEY)
    monkeypatch.setattr(settings, "meta_api_base", BASE)
    fake_meta.CALLS.clear()
    from api.main import app

    return TestClient(app)


def _wait(c, sid):
    deadline = time.monotonic() + WAIT_S
    while time.monotonic() < deadline:
        s = c.get(f"/api/sessions/{sid}").json()
        if s["status"] not in ("created", "running"):
            return s
        time.sleep(0.05)
    raise AssertionError("timeout")


def test_live_motor_full_flow(live):
    sid = live.post("/api/sessions", data={"sample": "motor", "language": "id"}).json()["id"]
    s = _wait(live, sid)
    assert s["mode"] == "live" and s["status"] == "needs_answer"  # top cause 55% -> agent asks first
    live.post(f"/api/sessions/{sid}/answer", data={"text": "Tidak"})
    s = _wait(live, sid)
    assert s["status"] == "ready", s["error"]
    assert all(p["found"] for p in s["parts"].values())
    sam = [c for c in fake_meta.CALLS if c["endpoint"] == "sam"]
    assert sam and sam[0]["prompt"].startswith("<0f>1<|box;")  # one box-prompt call for all located parts
    schemas = [c["schema"] for c in fake_meta.CALLS if c["endpoint"] == "chat"]
    assert {"object_report", "diagnosis", "repair_plan"} <= set(schemas)
    r = live.post(f"/api/sessions/{sid}/steps/1/check", files={"photo": ("a.jpg", open(engine.session_dir(sid) / "photo1.jpg", "rb"), "image/jpeg")})
    assert r.status_code == 200 and r.json()["passed"] is True
    r = live.post(f"/api/sessions/{sid}/replan", data={"report": "masih mati"}).json()
    assert r["cause_index"] == 1 and r["status"] == "ready"
    assert r["cost"]["spent_usd"] > 0


def test_live_faucet_draws_and_reviews_diagram(live):
    sid = live.post("/api/sessions", data={"sample": "faucet", "language": "en"}).json()["id"]
    s = _wait(live, sid)
    assert s["status"] == "ready"
    assert any(v.get("file") for v in s["diagrams"].values())
    assert any(c["endpoint"] == "images" and c["path"].endswith("edits") for c in fake_meta.CALLS)
    assert "diagram_review" in [c.get("schema") for c in fake_meta.CALLS]


def test_live_rice_cooker_red_stop(live):
    sid = live.post("/api/sessions", data={"sample": "rice", "language": "id"}).json()["id"]
    s = _wait(live, sid)
    assert s["status"] == "stopped" and s["safety"]["level"] == "red"
    assert s["plan"] is None  # no repair steps are ever produced for a red job


def test_live_voice_note_is_transcribed(live, tmp_path):
    import wave

    wav = tmp_path / "v.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\x00\x00" * 8000)
    from api.main import SAMPLES

    files = [("photos", ("p.jpg", open(SAMPLES / "motor.jpg", "rb"), "image/jpeg")),
             ("audio", ("v.wav", open(wav, "rb"), "audio/wav"))]
    sid = live.post("/api/sessions", data={"language": "id"}, files=files).json()["id"]
    s = _wait(live, sid)
    assert s["transcript"].startswith("Motor saya")
    assert any(c["endpoint"] == "asr" and c["request"]["languageBias"] == ["Indonesian"] for c in fake_meta.CALLS)
    assert not (engine.session_dir(sid) / "voice.wav").exists()  # recording deleted after transcription


def test_live_open_weights_path(live, monkeypatch):
    monkeypatch.setattr(settings, "use_open_weights", True)
    monkeypatch.setattr(settings, "baseten_api_key", "test-baseten-key")
    monkeypatch.setattr(settings, "open_api_base", BASE.replace("/v1", "/baseten/v1"))
    sid = live.post("/api/sessions", data={"sample": "faucet", "language": "id"}).json()["id"]
    s = _wait(live, sid)
    assert s["status"] == "ready", s["error"]
    assert [c for c in fake_meta.CALLS if c["endpoint"] == "baseten"]


def test_wrong_key_fails_cleanly(live, monkeypatch):
    monkeypatch.setattr(settings, "meta_api_key", "wrong")
    sid = live.post("/api/sessions", data={"sample": "faucet", "language": "id"}).json()["id"]
    s = _wait(live, sid)
    assert s["status"] == "error" and s["error_kind"] == "auth"
    assert "401" not in s["error"] and "401" in engine.load(sid)["error_detail"]  # friendly outside, detail kept on the server
