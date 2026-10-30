"""HTTP API tests with FastAPI's TestClient (MOCK mode)."""
import io
import time

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from api.main import app

client = TestClient(app)


def _wait(sid, until=("ready", "stopped", "needs_answer", "error", "exhausted")):
    for _ in range(100):
        s = client.get(f"/api/sessions/{sid}").json()
        if s["status"] in until:
            return s
        time.sleep(0.05)
    raise AssertionError("timeout")


def _jpg(color=(200, 200, 200)):
    b = io.BytesIO(); Image.new("RGB", (800, 600), color).save(b, "JPEG"); b.seek(0)
    return b


def test_health():
    j = client.get("/health").json()
    assert j["ok"] and j["mode"] == "mock" and j["models"]["segment"] == "sam-3.1"


def test_pages_served():
    assert "Tukang Copilot" in client.get("/").text
    assert client.get("/static/app.js").status_code == 200


def test_upload_flow_and_files():
    r = client.post("/api/sessions", data={"text": "kran wastafel menetes", "language": "id", "category": "plumbing"},
                    files=[("photos", ("a.jpg", _jpg(), "image/jpeg")), ("photos", ("b.jpg", _jpg((90, 90, 90)), "image/jpeg"))])
    assert r.status_code == 200, r.text
    s = _wait(r.json()["id"])
    assert s["status"] == "ready" and s["photos"] == ["photo1.jpg", "photo2.jpg"]
    assert "text" not in s  # the raw description is not echoed back
    assert client.get(s["files_base"] + "parts.jpg").status_code == 200
    assert client.get(f"/guide/{s['id']}").status_code == 200
    rep = client.get(f"/api/sessions/{s['id']}/report").json()
    assert rep["steps_total"] == 4


def test_sample_motor_answer_check_replan():
    sid = client.post("/api/sessions", data={"sample": "motor", "language": "en"}).json()["id"]
    s = _wait(sid)
    assert s["status"] == "needs_answer"
    assert client.post(f"/api/sessions/{sid}/answer", data={"text": "no fuel smell"}).json()["ok"]
    s = _wait(sid, ("ready",))
    r = client.post(f"/api/sessions/{sid}/steps/3/check", files={"photo": ("c.jpg", _jpg((5, 5, 5)), "image/jpeg")}).json()
    assert r["passed"] is False and r["correction"]
    s2 = client.post(f"/api/sessions/{sid}/replan", data={"report": "still dead"}).json()
    assert s2["cause_index"] == 1 and s2["status"] == "ready"


def test_sse_events_stream():
    sid = client.post("/api/sessions", data={"sample": "faucet"}).json()["id"]
    with client.stream("GET", f"/api/sessions/{sid}/events") as r:
        body = "".join(r.iter_text())
    assert body.startswith("data: ") and '"status": "ready"' in body


def test_rice_red_stop_over_http():
    sid = client.post("/api/sessions", data={"sample": "rice"}).json()["id"]
    s = _wait(sid)
    assert s["status"] == "stopped" and s["safety"]["level"] == "red"


@pytest.mark.parametrize("data,files,code", [
    ({"text": "x"}, None, 400),                                                      # no photo
    ({"text": ""}, [("photos", ("a.jpg", _jpg(), "image/jpeg"))], 400),               # no description
    ({"text": "x", "language": "fr"}, [("photos", ("a.jpg", _jpg(), "image/jpeg"))], 400),
    ({"text": "x", "category": "rocket"}, [("photos", ("a.jpg", _jpg(), "image/jpeg"))], 400),
    ({"text": "x"}, [("photos", ("a.exe", io.BytesIO(b"MZ"), "application/octet-stream"))], 400),
    ({"text": "x"}, [("photos", ("a.jpg", io.BytesIO(b"not an image"), "image/jpeg"))], 400),
    ({"sample": "spaceship"}, None, 400),
])
def test_bad_requests(data, files, code):
    assert client.post("/api/sessions", data=data, files=files).status_code == code


def test_not_found_and_path_traversal():
    assert client.get("/api/sessions/nope123").status_code == 404
    assert client.get("/api/sessions/..%2F..%2Fetc").status_code == 404
    sid = client.post("/api/sessions", data={"sample": "faucet"}).json()["id"]
    _wait(sid)
    for name in ["session.json", "..%2Fsession.json", "voice.wav", "x.py"]:
        assert client.get(f"/files/{sid}/{name}").status_code == 404
    assert client.post(f"/api/sessions/{sid}/answer", data={"text": "x"}).status_code == 409
