"""Flat scooter tyre scenario end to end over HTTP with the labelled sample fixtures (id and en text),
camera check with the valve photo, re-plan to the leaking valve stem, PDF report. Mock mode, no Meta calls."""
import json
import time
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from api.main import app

FIX = Path(__file__).parent / "fixtures"
MANIFEST = json.loads((FIX / "manifest.json").read_text())["fixtures"]
TIRE = [i for i in MANIFEST if i["scenario"] == "tire"]
client = TestClient(app)


def _wait(sid: str, until: tuple[str, ...] = ("ready", "stopped", "needs_answer", "error", "exhausted")) -> dict[str, Any]:
    for _ in range(200):
        s: dict[str, Any] = client.get(f"/api/sessions/{sid}").json()
        if s["status"] in until:
            return s
        time.sleep(0.05)
    raise AssertionError("timeout")


def test_tire_fixtures_are_labelled_stand_ins():
    assert len(TIRE) >= 4
    for item in TIRE:
        assert item["file"].startswith("sample_tire_") and (FIX / item["file"]).exists()


@pytest.mark.parametrize("item", [i for i in TIRE if "safety" in i], ids=lambda i: i["file"])
def test_tire_fixture_flow(item: dict[str, Any]) -> None:
    lang = "en" if item["file"].endswith("_en.jpg") else "id"
    with open(FIX / item["file"], "rb") as f:
        r = client.post("/api/sessions", data={"text": item["text"], "language": lang, "category": item["category"]},
                        files=[("photos", (item["file"], f, "image/jpeg"))])
    assert r.status_code == 200, r.text
    sid = r.json()["id"]
    s = _wait(sid)
    if s["status"] == "needs_answer":
        assert client.post(f"/api/sessions/{sid}/answer", data={"text": "paku masih menancap"}).json()["ok"]
        s = _wait(sid, ("ready", "stopped", "error"))
    assert s["status"] == "ready" and s["safety"]["level"] == "amber"
    blob = json.dumps(s).lower()
    assert "tyre" in blob or "ban" in blob
    check = next(i for i in TIRE if i.get("role") == "step_check")
    with open(FIX / check["file"], "rb") as f:
        c = client.post(f"/api/sessions/{sid}/steps/1/check", files={"photo": ("c.jpg", f, "image/jpeg")})
    assert c.status_code == 200 and "passed" in c.json()
    pdf = client.get(f"/api/sessions/{sid}/report.pdf")
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
