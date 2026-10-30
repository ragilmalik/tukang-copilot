"""Run every labelled stand-in fixture (api/tests/fixtures, made by scripts/make_fixtures.py) through the
HTTP flow in mock mode and check the expected scenario outcome and safety level."""
import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from api.main import app

FIX = Path(__file__).parent / "fixtures"
MANIFEST = json.loads((FIX / "manifest.json").read_text())["fixtures"]
client = TestClient(app)


def _wait(sid, until=("ready", "stopped", "needs_answer", "error", "exhausted")):
    for _ in range(200):
        s = client.get(f"/api/sessions/{sid}").json()
        if s["status"] in until:
            return s
        time.sleep(0.05)
    raise AssertionError("timeout")


def test_ten_fixtures_all_clearly_labelled():
    assert len(MANIFEST) >= 10
    for item in MANIFEST:
        p = FIX / item["file"]
        assert p.name.startswith("standin_")
        im = Image.open(p)
        assert "STAND-IN" in im.getexif().get(0x010E, "")
        assert max(im.size) <= 1536
        px = im.convert("RGB").getpixel((5, 5))  # red banner top-left
        assert isinstance(px, tuple)
        r, g, b = px[:3]
        assert r > 150 and g < 80 and b < 80


@pytest.mark.parametrize("item", [i for i in MANIFEST if "safety" in i], ids=lambda i: i["file"])
def test_fixture_runs_end_to_end(item):
    with open(FIX / item["file"], "rb") as f:
        r = client.post("/api/sessions", data={"text": item["text"], "language": "id", "category": item["category"]},
                        files=[("photos", (item["file"], f, "image/jpeg"))])
    assert r.status_code == 200, r.text
    sid = r.json()["id"]
    s = _wait(sid)
    if s["status"] == "needs_answer":
        assert client.post(f"/api/sessions/{sid}/answer", data={"text": "tidak bau bensin"}).json()["ok"]
        s = _wait(sid, ("ready", "stopped", "error"))
    assert s["safety"]["level"] == item["safety"]
    assert s["status"] == ("stopped" if item["safety"] == "red" else "ready")
    if s["status"] == "ready":
        step_photos = [i for i in MANIFEST if i.get("role") == "step_check" and i["scenario"] == item["scenario"]]
        if step_photos:
            with open(FIX / step_photos[0]["file"], "rb") as f:
                c = client.post(f"/api/sessions/{sid}/steps/1/check", files={"photo": ("c.jpg", f, "image/jpeg")})
            assert c.status_code == 200 and "passed" in c.json()


def test_vague_description_still_handled():
    item = next(i for i in MANIFEST if i.get("role") == "edge_case")
    with open(FIX / item["file"], "rb") as f:
        r = client.post("/api/sessions", data={"text": item["text"], "category": item["category"]},
                        files=[("photos", (item["file"], f, "image/jpeg"))])
    assert r.status_code == 200
    assert _wait(r.json()["id"])["status"] in ("ready", "needs_answer", "stopped")
