"""scripts/eval_fixtures.py scores the labelled stand-in fixtures; run it in-process against the mock app."""
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from api.main import app

ROOT = Path(__file__).resolve().parents[2]


def _load() -> Any:
    spec = importlib.util.spec_from_file_location("eval_fixtures", ROOT / "scripts" / "eval_fixtures.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["eval_fixtures"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_eval_scores_every_fixture_in_mock_mode() -> None:
    ev = _load()
    manifest = json.loads((ev.DEFAULT_DIR / "manifest.json").read_text())["fixtures"]
    client = TestClient(app)
    rows: list[dict[str, Any]] = []
    sessions: dict[str, str] = {}
    for item in manifest:
        if item.get("role") in ("step_check", "reference") or not item.get("text"):
            continue
        row = ev.run_item(client, ev.DEFAULT_DIR, item)
        rows.append(row)
        if row["status"] == "ready" and not item.get("role"):
            sessions.setdefault(item["scenario"], row["sid"])
    assert len(rows) >= 9
    assert all(r["pass"] for r in rows), [r for r in rows if not r["pass"]]
    steps = ev.run_step_checks(client, ev.DEFAULT_DIR, manifest, sessions)
    assert len(steps) >= 3 and all(s["pass"] for s in steps)
    md = ev.markdown(rows, steps, "http://test")
    assert "photos met every expectation" in md and "| standin_rice_cooker_front.jpg | stopped | red" in md


def test_red_fixture_is_not_counted_as_met_when_it_gets_a_plan() -> None:
    ev = _load()
    # A fixture that expects a red stop but is routed to the motorbike text (amber) must FAIL.
    client = TestClient(app)
    item = {"file": "standin_motor_plug_area.jpg", "scenario": "motor", "safety": "red",
            "text": "Motor Honda Beat saya susah hidup, distarter cuma bunyi.", "category": "motor"}
    row = ev.run_item(client, ev.DEFAULT_DIR, item)
    assert row["pass"] is False and row["checks"]["safety level"] is False
