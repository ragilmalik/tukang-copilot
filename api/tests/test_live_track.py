"""Live guide: SAM 3.1 on live camera frames (POST /api/sessions/{id}/steps/{n}/track), throttle, frame cap,
mask -> outline polygon, mock jitter, the real meta_client path, and the web wiring."""
import io
import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from api.main import app
from api.pipeline import engine, mock, track
from api.settings import settings
from api.tests.owner_auth import owner

client = TestClient(app)
WEB = Path(__file__).resolve().parents[2] / "web"


@pytest.fixture(autouse=True)
def _fast(monkeypatch):
    monkeypatch.setattr(settings, "track_min_interval_s", 0.0)
    track._last.clear()


def _ready(sample: str = "pump", lang: str = "en") -> dict[str, Any]:
    sid = client.post("/api/sessions", data={"sample": sample, "language": lang}).json()["id"]
    for _ in range(400):
        s: dict[str, Any] = client.get(f"/api/sessions/{sid}").json()
        if s["status"] not in ("created", "running"):
            return s
        time.sleep(0.05)
    raise AssertionError("timeout")


def _frame(w: int = 640, h: int = 480) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (w, h), (90, 100, 110)).save(buf, "JPEG")
    return buf.getvalue()


def _track(sid: str, n: int = 1) -> Any:
    return client.post(f"/api/sessions/{sid}/steps/{n}/track", files={"frame": ("f.jpg", _frame(), "image/jpeg")})


def test_track_returns_normalised_box_and_outline():
    s = _ready("pump")
    r = _track(s["id"], 1)
    assert r.status_code == 200, r.text
    j = r.json()
    step1 = s["plan"]["steps"][0]
    assert j["found"] and j["component_id"] == step1["component_id"] and j["name"]
    b = j["boxes"][0]
    assert 0 <= b["x1"] < b["x2"] <= 1 and 0 <= b["y1"] < b["y2"] <= 1 and b["confidence"] > 0.5
    phrase = next(c["sam_phrase"] for c in s["object_report"]["components"] if c["id"] == j["component_id"])
    ref = mock._BOXES[phrase]
    assert abs(b["x1"] - ref[0]) < 0.03 and abs(b["y1"] - ref[1]) < 0.03  # jitter stays small
    assert len(j["polygon"]) > 4 and all(0 <= x <= 1 and 0 <= y <= 1 for x, y in j["polygon"])
    assert j["frames_used"] == 1 and j["frames_left"] == settings.max_track_frames - 1 and j["mode"] == "mock"


def test_mock_boxes_jitter_between_frames():
    s = _ready("pump")
    a, b = _track(s["id"]).json(), _track(s["id"]).json()
    assert a["boxes"][0] != b["boxes"][0]
    assert b["frames_used"] == 2


def test_frames_are_not_stored():
    s = _ready("faucet")
    before = sorted(p.name for p in engine.session_dir(s["id"]).iterdir())
    _track(s["id"])
    after = sorted(p.name for p in engine.session_dir(s["id"]).iterdir())
    assert before == after


def test_throttle_gives_429(monkeypatch):
    monkeypatch.setattr(settings, "track_min_interval_s", 30.0)
    s = _ready("pump")
    assert _track(s["id"]).status_code == 200
    r = _track(s["id"])
    assert r.status_code == 429 and r.headers["retry-after"] == "1"


def test_frame_cap_stops_calls(monkeypatch):
    monkeypatch.setattr(settings, "max_track_frames", 2)
    s = _ready("pump")
    assert _track(s["id"]).json()["limit_reached"] is False
    last = _track(s["id"]).json()
    assert last["found"] and last["limit_reached"] is True and last["frames_left"] == 0
    calls: list[Any] = []

    def spy(*a: Any, **k: Any) -> list[Any]:
        calls.append(a)
        return []

    monkeypatch.setattr(mock, "track", spy)
    capped = _track(s["id"]).json()
    assert capped["limit_reached"] and not capped["found"] and capped["frames_used"] == 2 and calls == []
    assert engine.load(s["id"])["track"]["frames"] == 2


def test_step_without_part_makes_no_sam_call(monkeypatch):
    s = _ready("pump")
    sess = engine.load(s["id"])
    sess["plan"]["steps"][0]["component_id"] = ""
    for c in sess["diagnosis"]["causes"]:
        c["component_ids"] = []
    engine.save(sess)
    calls: list[Any] = []

    def spy(*a: Any, **k: Any) -> list[Any]:
        calls.append(a)
        return []

    monkeypatch.setattr(mock, "track", spy)
    j = _track(s["id"]).json()
    assert j["component_id"] is None and not j["found"] and calls == [] and j["frames_used"] == 0


def test_step_without_part_falls_back_to_cause_part():
    s = _ready("pump")
    sess = engine.load(s["id"])
    sess["plan"]["steps"][0]["component_id"] = "nope"
    engine.save(sess)
    j = _track(s["id"]).json()
    assert j["component_id"] == sess["diagnosis"]["causes"][0]["component_ids"][0] and j["found"]


def test_errors():
    assert _track("nope").status_code == 404
    rice = _ready("rice")  # red stop: no plan, nothing to guide
    assert _track(rice["id"]).status_code == 409
    s = _ready("pump")
    assert _track(s["id"], 99).status_code == 409
    r = client.post(f"/api/sessions/{s['id']}/steps/1/track", files={"frame": ("f.jpg", b"not an image", "image/jpeg")})
    assert r.status_code == 400
    r = client.post(f"/api/sessions/{s['id']}/steps/1/track", files={"frame": ("f.exe", _frame(), "application/octet-stream")})
    assert r.status_code == 400


def test_mask_polygon_shapes():
    yy, xx = np.mgrid[0:32, 0:32]
    ell = ((((xx - 16) / 16) ** 2 + ((yy - 16) / 16) ** 2) <= 1).astype(np.uint8)
    rec = {"left": 100, "top": 50, "right": 300, "bottom": 250, "mask": ell}
    poly = track.mask_polygon(rec, 400, 400)
    assert 4 < len(poly) <= track.MAX_POLY
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    assert min(xs) >= 0.25 - 1e-6 and max(xs) <= 0.75 + 1e-6 and min(ys) >= 0.125 - 0.01 and max(ys) <= 0.625 + 0.01
    empty = track.mask_polygon({**rec, "mask": np.zeros((8, 8), np.uint8)}, 400, 400)
    assert empty == [[0.25, 0.125], [0.75, 0.125], [0.75, 0.625], [0.25, 0.625]]
    assert len(track.mask_polygon({**rec, "mask": None}, 400, 400)) == 4


def test_track_cost_is_added_in_live_mode(monkeypatch):
    from api.testing import fake_meta

    base = fake_meta.serve_in_thread()
    s = _ready("faucet")  # made in mock mode, then tracked through the real HTTP client
    monkeypatch.setattr(settings, "mock", False)
    monkeypatch.setattr(settings, "meta_api_key", fake_meta.TEST_KEY)
    monkeypatch.setattr(settings, "meta_api_base", base)
    fake_meta.CALLS.clear()
    before = float((engine.load(s["id"]).get("cost") or {}).get("spent_usd", 0))
    r = _track(s["id"])
    assert r.status_code == 200, r.text
    sam = [c for c in fake_meta.CALLS if c["endpoint"] == "sam"]
    assert len(sam) == 1 and not sam[0]["prompt"].startswith("<")  # one noun-phrase SAM 3.1 call
    after = engine.load(s["id"])["cost"]
    assert after["spent_usd"] > before and any("sam" in k for k in after["by_model"])
    assert r.json()["mode"] == "live"


def test_delete_forgets_throttle():
    s = _ready("pump")
    _track(s["id"])
    assert s["id"] in track._last
    client.delete(f"/api/sessions/{s['id']}", headers=owner(s['id']))
    assert s["id"] not in track._last


def test_web_has_live_guide():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    js = (WEB / "app.js").read_text(encoding="utf-8")
    for el in ('id="liveBtn"', 'id="liveVideo"', 'id="liveCanvas"', 'id="liveCheck"', "playsinline"):
        assert el in html
    assert "/track`" in js and "getUserMedia" in js and 'facingMode: { ideal: "environment" }' in js
    assert "liveFallback" in js and "r.status === 429" in js
    jv = js[js.index("T.jv = Object.assign"):]
    assert "Pandhuan kamera langsung" in jv
    assert json.dumps("liveNoCam")[1:-1] in jv
