"""Run every labelled sample fixture (AI-generated photos) (api/tests/fixtures, made by scripts/make_fixtures.py) through the
HTTP flow in mock mode and check the expected scenario outcome and safety level."""
import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from api.main import app
from api.pipeline.sample_masks import LABEL

FIX = Path(__file__).parent / "fixtures"
ROOT = Path(__file__).resolve().parents[2]
MANIFEST = json.loads((FIX / "manifest.json").read_text())["fixtures"]
client = TestClient(app)


def _wait(sid, until=("ready", "stopped", "needs_answer", "error", "exhausted")):
    for _ in range(200):
        s = client.get(f"/api/sessions/{sid}").json()
        if s["status"] in until:
            return s
        time.sleep(0.05)
    raise AssertionError("timeout")


def _tagged(p: Path) -> None:
    """EXIF label plus the dark corner tag that says the same thing on the picture itself."""
    im = Image.open(p)
    assert im.getexif().get(0x010E, "") == LABEL
    assert max(im.size) <= 1536
    m = max(8, im.width // 90)
    px = im.convert("RGB").getpixel((m + 6, m + max(14, im.width // 52) // 2 + 6))
    assert isinstance(px, tuple) and max(px[:3]) < 110


def test_ten_fixtures_all_clearly_labelled():
    assert len(MANIFEST) >= 10
    assert "AI-generated" in LABEL and "demo mode" in LABEL
    for item in MANIFEST:
        p = FIX / item["file"]
        assert p.name.startswith("sample_")
        _tagged(p)


def test_app_sample_photos_are_labelled_too():
    samples = sorted((ROOT / "samples").glob("*.jpg"))
    assert {p.stem for p in samples} >= {"motor", "pump", "faucet", "rice", "tire", "check_motor"}
    for p in samples:
        _tagged(p)


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
