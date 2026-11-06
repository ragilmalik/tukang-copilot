"""Impact trial kit: outcomes go to an append-only JSONL, scripts/impact_report.py aggregates them into
docs/IMPACT.md + a 1920x1080 slide, the --mock run is stamped MOCK DATA, the download endpoint is token-gated."""
import json
import sys
import time
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from api import impact
from api.main import app
from api.pipeline import engine
from api.settings import settings
from api.tests.owner_auth import owner

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import impact_report  # type: ignore[import-not-found,unused-ignore]  # noqa: E402

client = TestClient(app)


WAIT_S = 60  # seconds a repair may take: generous, CI runners are slow and earlier repairs can still hold the worker pool


def _ready(sample: str = "pump", lang: str = "en") -> dict[str, Any]:
    sid = client.post("/api/sessions", data={"sample": sample, "language": lang}).json()["id"]
    deadline = time.monotonic() + WAIT_S
    while time.monotonic() < deadline:
        s: dict[str, Any] = client.get(f"/api/sessions/{sid}").json()
        if s["status"] not in ("created", "running"):
            return s
        time.sleep(0.05)
    raise AssertionError("timeout")


def test_outcome_appends_a_row():
    s = _ready("pump")
    client.post(f"/api/sessions/{s['id']}/outcome", data={"result": "fixed", "minutes": "35", "tester": "T1"}, headers=owner(s['id']))
    client.post(f"/api/sessions/{s['id']}/outcome", data={"result": "pro"}, headers=owner(s['id']))
    rows = impact.read()
    assert len(rows) == 2  # append-only: both taps are kept
    r = rows[0]
    assert r["session"] == s["id"] and r["fixed"] is True and r["minutes"] == 35 and r["minutes_source"] == "owner"
    assert r["tester"] == "T1" and r["scenario"] == "pump" and r["saved_idr"] == s["diagnosis"]["diy_saving_idr"] > 0
    assert r["shop_cost_idr"] == s["diagnosis"]["shop_cost_estimate_idr"] and r["mode"] == "offline" and r["steps_total"] == 4
    assert rows[1]["fixed"] is False and rows[1]["saved_idr"] == 0 and rows[1]["minutes_source"] == "elapsed"
    assert set(r) >= {"ts", "lang", "object", "replans", "steps_verified", "fallback"}
    assert impact.log_path() == settings.data_dir / "impact" / "outcomes.jsonl"
    assert "minutes" not in engine.load(s["id"])["outcome"]  # last tap wins on the session
    latest = impact_report.latest_per_session(rows)
    assert len(latest) == 1 and latest[0]["result"] == "pro"


@pytest.mark.parametrize("data", [{"minutes": "-1"}, {"minutes": "601"}, {"tester": "<script>"}, {"tester": "x" * 41}])
def test_bad_trial_fields_are_rejected(data):
    s = _ready("faucet")
    assert client.post(f"/api/sessions/{s['id']}/outcome", data={"result": "fixed", **data}, headers=owner(s['id'])).status_code == 422
    assert impact.read() == []


def test_broken_line_is_skipped():
    p = impact.log_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text('{"session": "a", "fixed": true}\n{"session": "b", "fix\n[1,2]\n', encoding="utf-8")
    assert impact.read() == [{"session": "a", "fixed": True}]


def test_summary_math():
    rows = impact_report.mock_rows()
    s = impact_report.summarize(rows)
    fixed = [r for r in rows if r["fixed"]]
    assert s["repairs"] == 10 and s["testers"] == 5 and s["fixed"] == len(fixed)
    assert s["total_saved_idr"] == sum(r["saved_idr"] for r in fixed)
    mins = sorted(r["minutes"] for r in fixed)
    assert s["median_minutes"] == (mins[len(mins) // 2 - 1] + mins[len(mins) // 2]) / 2  # 8 fixed: mean of the middle two
    per = impact_report.by_scenario(rows)
    assert sum(v["repairs"] for v in per.values()) == 10 and per["appliance"]["fixed"] == 0
    assert impact_report.summarize([])["fixed_rate"] == 0.0


def test_mock_report_is_stamped(tmp_path):
    md, png = tmp_path / "IMPACT.md", tmp_path / "impact.png"
    assert impact_report.main(["--mock", "--md", str(md), "--png", str(png)]) == 0
    text = md.read_text(encoding="utf-8")
    assert text.count(impact_report.MOCK_STAMP) >= 2 and "(MOCK DATA)" in text.splitlines()[0]
    assert "| Water pump |" in text and "Rp" in text
    with Image.open(png) as im:
        assert im.size == (1920, 1080)


def test_real_report_uses_live_rows_only(tmp_path):
    data = tmp_path / "o.jsonl"
    rows = [{"session": "a", "mode": "live", "tester": "T1", "scenario": "motor", "fixed": True, "minutes": 20, "saved_idr": 50000},
            {"session": "b", "mode": "mock", "tester": "T2", "scenario": "pump", "fixed": True, "minutes": 30, "saved_idr": 99000}]
    data.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    md, png = tmp_path / "I.md", tmp_path / "i.png"
    impact_report.main(["--data", str(data), "--md", str(md), "--png", str(png)])
    text = md.read_text(encoding="utf-8")
    assert impact_report.MOCK_STAMP not in text and "1 repairs by 1 testers" in text and "Rp50.000" in text
    impact_report.main(["--data", str(data), "--include-demo", "--md", str(md), "--png", str(png)])
    assert "2 repairs" in md.read_text(encoding="utf-8")
    impact_report.main(["--data", str(tmp_path / "none.jsonl"), "--md", str(md), "--png", str(png)])
    assert "No outcomes recorded yet" in md.read_text(encoding="utf-8")


def test_committed_docs_are_the_stamped_mock():
    text = (ROOT / "docs" / "IMPACT.md").read_text(encoding="utf-8")
    first = text.splitlines()[0]
    assert first.startswith("# Impact")
    if "MOCK" in first or impact_report.MOCK_STAMP in text:  # mock output must carry the stamp (top and bottom)
        assert text.count(impact_report.MOCK_STAMP) >= 2 and "(MOCK DATA)" in first
    assert (ROOT / "docs" / "img" / "impact.png").exists()
    kit = (ROOT / "docs" / "USER_TRIAL_KIT.md").read_text(encoding="utf-8")
    assert "?trial=T1" in kit and "Boleh?" in kit and "112" in kit


def test_download_endpoint_is_token_gated(monkeypatch):
    assert client.get("/api/impact/outcomes.jsonl").status_code == 404
    monkeypatch.setattr(settings, "impact_token", "s3cret")
    assert client.get("/api/impact/outcomes.jsonl", headers={"X-Impact-Token": "nope"}).status_code == 404
    s = _ready("faucet")
    client.post(f"/api/sessions/{s['id']}/outcome", data={"result": "fixed"}, headers=owner(s['id']))
    r = client.get("/api/impact/outcomes.jsonl", headers={"X-Impact-Token": "s3cret"})
    assert r.status_code == 200 and json.loads(r.text.splitlines()[0])["session"] == s["id"]


def test_web_trial_mode():
    js = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
    assert 'get("trial")' in js and 'fd.append("tester"' in js and 'fd.append("minutes"' in js
    assert 'id="trialMinutes"' in (ROOT / "web" / "index.html").read_text(encoding="utf-8")
