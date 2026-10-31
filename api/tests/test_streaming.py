"""v1.23: partial results stream on the progress screen (SSE `progress_view`), with demo-mode pacing."""
import json
from typing import Any
import time

from fastapi.testclient import TestClient

from api.main import app, progress_view
from api.pipeline import engine
from api.settings import settings

client = TestClient(app)


def _snaps(sid):
    with client.stream("GET", f"/api/sessions/{sid}/events") as r:
        body = "".join(r.iter_text())
    return [json.loads(line[6:]) for line in body.splitlines() if line.startswith("data: ")]


def test_stage_results_arrive_one_by_one(monkeypatch):
    monkeypatch.setattr(settings, "mock_pace_s", 0.25)
    sid = client.post("/api/sessions", data={"sample": "faucet"}).json()["id"]
    snaps = _snaps(sid)
    assert snaps[-1]["status"] == "ready"
    # the object report is on screen before the diagnosis exists ...
    seen = [s for s in snaps if s.get("object_report") and not s.get("diagnosis")]
    assert seen and seen[0]["object_report"]["object"] and seen[0]["object_report"]["components"]
    # ... the SAM-marked photo before the plan ...
    masks = [s for s in snaps if s.get("parts_image") and not s.get("plan_steps")]
    assert masks and masks[0]["parts_found"] and masks[0]["files_base"] == f"/files/{sid}/"
    assert client.get(masks[0]["files_base"] + masks[0]["parts_image"]).status_code == 200
    # ... and the top cause while the agent is still working
    dx = [s for s in snaps if s.get("diagnosis") and s["status"] == "running"]
    assert dx and dx[0]["diagnosis"]["causes"][0]["title"] and 0 <= dx[0]["diagnosis"]["causes"][0]["confidence"] <= 100
    assert any(s.get("agent_log") for s in snaps if s["status"] == "running")   # the agent log streams too
    assert snaps[-1]["plan_steps"] >= 1
    look = [e for e in snaps[-1]["agent_log"] if e["kind"] == "look"]
    assert look and look[0].get("ms", 0) < 250          # demo pacing is never counted in the logged model time


def test_progress_view_never_carries_private_fields():
    sid = client.post("/api/sessions", data={"sample": "motor"}).json()["id"]
    for _ in range(100):
        s = engine.load(sid)
        if s["status"] not in {"created", "running"}:
            break
        time.sleep(0.05)
    s["text"], s["history"], s["error_detail"] = "owner secret words", ["owner history"], "Traceback secret"
    v = progress_view(s)
    blob = json.dumps(v)
    assert "owner secret" not in blob and "Traceback" not in blob and "owner history" not in blob
    assert "text" not in v and "history" not in v and "plan" not in v   # trimmed: no full plan on the stream
    assert len(blob) < 12000


def test_pacing_is_demo_only_and_not_counted_in_stage_time(monkeypatch):
    saved = []
    monkeypatch.setattr(engine, "save", lambda s: saved.append(1))
    monkeypatch.setattr(settings, "mock_pace_s", 0.4)
    s: dict[str, Any] = {"status": "running", "stages": {"look": {"status": "waiting", "note": ""}}}
    t0 = time.time(); engine._stage(s, "look", "done", "x", 5)
    assert time.time() - t0 >= 0.35 and s["stages"]["look"]["ms"] == 5        # demo: held on screen, real ms kept
    monkeypatch.setattr(settings, "mock", False)
    monkeypatch.setattr(settings, "meta_api_key", "k")
    t0 = time.time(); engine._stage(s, "look", "done", "x", 5)
    assert time.time() - t0 < 0.1                                             # live: never slowed down
    t0 = time.time(); monkeypatch.setattr(settings, "mock", True); engine._stage(s, "look", "running")
    assert time.time() - t0 < 0.1                                             # only finished stages are held
    s["status"] = "ready"
    t0 = time.time(); engine._stage(s, "look", "done", "x", 5)
    assert time.time() - t0 < 0.1                                             # a re-plan on the result page is not slowed
