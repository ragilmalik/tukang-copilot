"""Agent log ("What the AI did", v1.22): every decision is recorded with the tool that made it, the owner's own
words never appear in it, and the 1-tap demo's stand-in check photos drive a real fail -> pass -> re-plan loop."""
import io
import json
import time
from typing import Any

from fastapi.testclient import TestClient
from PIL import Image

from api.main import app
from api.pipeline import engine
from api.tests.owner_auth import owner

client = TestClient(app)


def _wait(sid, until=("ready", "stopped", "needs_answer", "error", "exhausted")):
    for _ in range(200):
        s = client.get(f"/api/sessions/{sid}").json()
        if s["status"] in until:
            return s
        time.sleep(0.03)
    raise AssertionError("timeout")


def _kinds(s):
    return [e["kind"] for e in s["agent_log"]]


def _jpg(color=(200, 200, 200)):
    b = io.BytesIO(); Image.new("RGB", (800, 600), color).save(b, "JPEG"); b.seek(0)
    return b


def test_full_agent_loop_is_logged_with_tools():
    sid = client.post("/api/sessions", data={"sample": "motor", "language": "en"}).json()["id"]
    s = _wait(sid)
    assert s["status"] == "needs_answer" and s["sample"] == "motor"
    assert _kinds(s)[:5] == ["gate", "look", "segment", "diagnose", "ask"]
    by = {e["kind"]: e for e in s["agent_log"]}
    assert by["look"]["model"] == "muse-spark-1.3" and by["look"]["n"] == 3
    assert by["segment"]["model"] == "sam-3.1" and by["segment"]["found"] == 3
    assert by["ask"] == {**by["ask"], "conf": 55, "threshold": 60}
    assert client.post(f"/api/sessions/{sid}/answer", data={"text": "no"}).status_code == 200
    s = _wait(sid, ("ready",))
    k = _kinds(s)
    assert k.count("gate") == 1  # a resumed run does not log the text gate twice
    assert {"answer", "plan", "plan_guard"} <= set(k)
    assert next(e for e in s["agent_log"] if e["kind"] == "plan_guard")["ok"] is True
    # verify: a dark stand-in fails, the right one passes
    dark = client.get("/api/demo/check-photo/dark?sample=motor")
    assert dark.status_code == 200 and dark.headers["content-type"] == "image/jpeg"
    r = client.post(f"/api/sessions/{sid}/steps/1/check", files={"photo": ("d.jpg", dark.content, "image/jpeg")}).json()
    assert r["passed"] is False
    ok = client.get("/api/demo/check-photo/ok?sample=motor")
    r = client.post(f"/api/sessions/{sid}/steps/1/check", files={"photo": ("o.jpg", ok.content, "image/jpeg")}).json()
    assert r["passed"] is True
    s = client.get(f"/api/sessions/{sid}").json()
    checks = [e for e in s["agent_log"] if e["kind"] == "check"]
    assert [c["passed"] for c in checks] == [False, True] and all(c["step"] == 1 for c in checks)
    # re-plan, then outcome
    s = client.post(f"/api/sessions/{sid}/replan", data={"report": "tried, still dead"}).json()
    rp = [e for e in s["agent_log"] if e["kind"] == "replan"][-1]
    assert rp["tried"] == "Loose spark plug cap" and rp["cause"] == "Fouled spark plug" and rp["steps"] == 4
    s = client.post(f"/api/sessions/{sid}/outcome", data={"result": "fixed"}, headers=owner(sid)).json()
    assert s["agent_log"][-1] == {**s["agent_log"][-1], "kind": "outcome", "result": "fixed"}
    assert all(isinstance(e["t"], float) and e["t"] >= 0 for e in s["agent_log"])


def test_red_stop_and_exhausted_are_handoffs():
    sid = client.post("/api/sessions", data={"sample": "rice", "language": "en"}).json()["id"]
    s = _wait(sid)
    assert s["status"] == "stopped" and _kinds(s)[-1] == "escalate" and s["agent_log"][-1]["reason"] == "red"
    sid = client.post("/api/sessions", data={"sample": "faucet", "language": "id"}).json()["id"]
    _wait(sid)
    client.post(f"/api/sessions/{sid}/replan", data={"report": "masih netes"})
    s = client.post(f"/api/sessions/{sid}/replan", data={"report": "masih netes"}).json()
    assert s["status"] == "exhausted" and s["agent_log"][-1] == {**s["agent_log"][-1], "kind": "escalate", "reason": "exhausted"}


def test_code_gate_stop_is_logged_before_any_model_call():
    r = client.post("/api/sessions", data={"text": "ada bau gas dari kompor, regulator bocor", "language": "id"},
                    files=[("photos", ("a.jpg", _jpg(), "image/jpeg"))])
    s = _wait(r.json()["id"])
    assert s["status"] == "stopped"
    assert [e["kind"] for e in s["agent_log"]] == ["gate", "escalate"]
    assert s["agent_log"][0]["ok"] is False and s["agent_log"][0]["category"] == "gas"


def test_owner_words_never_reach_the_agent_log():
    marker = "Zyxqv-owner-secret-91"
    r = client.post("/api/sessions", data={"text": f"motor mogok {marker}", "language": "id"},
                    files=[("photos", ("a.jpg", _jpg(), "image/jpeg"))])
    sid = r.json()["id"]
    _wait(sid)
    client.post(f"/api/sessions/{sid}/answer", data={"text": f"tidak {marker}"})
    s = _wait(sid, ("ready",))
    client.post(f"/api/sessions/{sid}/replan", data={"report": f"masih mati {marker}"})
    s = client.get(f"/api/sessions/{sid}").json()
    assert marker not in json.dumps(s["agent_log"])


def test_demo_check_photo_route_rejects_unknown_input():
    assert client.get("/api/demo/check-photo/ok?sample=../../etc/passwd").status_code == 404
    assert client.get("/api/demo/check-photo/evil?sample=motor").status_code == 404
    assert client.get("/api/demo/check-photo/ok?sample=pump").status_code == 200  # falls back to the sample photo


def test_short_cuts_at_a_word_boundary():
    assert engine.short("short") == "short"
    out = engine.short("Needs opening the 220V internals. This repair is high-risk. For your safety, take it to a service centre", 90)
    assert out.endswith("…") and len(out) <= 90
    assert out == "Needs opening the 220V internals. This repair is high-risk. For your safety, take it to…"  # whole words only
    assert engine.short("x" * 200, 10) == "x" * 9 + "…"  # one long word: hard cut


def test_agent_log_is_capped():
    s: dict[str, Any] = {"created": time.time(), "agent_log": []}
    for _ in range(engine.AGENT_LOG_MAX + 20):
        engine._event(s, "check", step=1, passed=False)
    assert len(s["agent_log"]) == engine.AGENT_LOG_MAX


def test_check_event_records_which_plan_it_belonged_to():
    """v1.23: the UI links a step-check log line to the step card only while that plan is current."""
    from fastapi.testclient import TestClient

    from api.main import app
    import io
    import time
    from PIL import Image

    c = TestClient(app)
    sid = c.post("/api/sessions", data={"sample": "faucet"}).json()["id"]
    for _ in range(100):
        if c.get(f"/api/sessions/{sid}").json()["status"] == "ready":
            break
        time.sleep(0.05)
    b = io.BytesIO(); Image.new("RGB", (400, 300), (5, 5, 5)).save(b, "JPEG"); b.seek(0)
    c.post(f"/api/sessions/{sid}/steps/1/check", files={"photo": ("c.jpg", b, "image/jpeg")})
    c.post(f"/api/sessions/{sid}/replan", data={"report": "still dripping"})
    log = c.get(f"/api/sessions/{sid}").json()["agent_log"]
    checks = [e for e in log if e["kind"] == "check"]
    assert checks and checks[0]["cause"] == 0
