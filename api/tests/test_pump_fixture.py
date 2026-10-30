"""Water-pump scenario (SPEC §8 case 2) end to end over HTTP with the labelled stand-in fixtures:
overview photo -> amber diagnosis (lost prime) -> camera check with the priming-plug photo -> re-plan to the
foot valve -> PDF report. Mock mode, no Meta calls."""
import json
import time
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from api.main import app

FIX = Path(__file__).parent / "fixtures"
MANIFEST = json.loads((FIX / "manifest.json").read_text())["fixtures"]
client = TestClient(app)


def _wait(sid: str, until: tuple[str, ...] = ("ready", "stopped", "needs_answer", "error", "exhausted")) -> dict[str, Any]:
    for _ in range(200):
        s: dict[str, Any] = client.get(f"/api/sessions/{sid}").json()
        if s["status"] in until:
            return s
        time.sleep(0.05)
    raise AssertionError("timeout")


def _fixture(role: str | None) -> dict[str, Any]:
    return next(i for i in MANIFEST if i["scenario"] == "pump" and i.get("role") == role)


def test_pump_fixtures_are_labelled_stand_ins():
    for item in (_fixture(None), _fixture("step_check")):
        assert item["file"].startswith("standin_pump_") and (FIX / item["file"]).exists()


def test_pump_fixture_full_flow():
    item = _fixture(None)
    with open(FIX / item["file"], "rb") as f:
        r = client.post("/api/sessions", data={"text": item["text"], "language": "id", "category": item["category"]},
                        files=[("photos", (item["file"], f, "image/jpeg"))])
    assert r.status_code == 200, r.text
    sid = r.json()["id"]
    s = _wait(sid)
    assert s["status"] == "ready" and s["safety"]["level"] == "amber"
    assert "pancingan" in s["plan"]["cause_title"].lower()
    assert s["plan"]["steps"][0]["component_id"] == "c3"  # unplug first

    check = _fixture("step_check")
    with open(FIX / check["file"], "rb") as f:
        c = client.post(f"/api/sessions/{sid}/steps/2/check", files={"photo": ("c.jpg", f, "image/jpeg")})
    assert c.status_code == 200 and "passed" in c.json()

    rp = client.post(f"/api/sessions/{sid}/replan", data={"report": "sudah dipancing, airnya habis lagi"})
    assert rp.status_code == 200
    s = _wait(sid, ("ready", "exhausted", "error"))
    assert s["status"] == "ready" and "foot valve" in s["plan"]["cause_title"].lower()

    pdf = client.get(f"/api/sessions/{sid}/report.pdf")
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
