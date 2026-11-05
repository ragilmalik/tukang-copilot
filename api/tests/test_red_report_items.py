"""A red stop's report carries no shopping list. Live, Muse Spark filled tools and parts for the rice cooker stop
(a thermal fuse at Rp15.000), and the owner's PDF printed them under the STOP card."""
from __future__ import annotations

from typing import Any

import pytest

from api.pipeline import engine


def _session(level: str) -> dict[str, Any]:
    return {"id": "abc", "lang": "jv", "status": "stopped", "created": 0, "checks": {}, "safety": {"level": level},
            "object_report": {"object": "penanak sega elektrik"}, "plan": None,
            "diagnosis": {"problem_summary": "Rice cooker ora panas", "tools": [{"name": "Avo meter", "est_price_idr": 85000}],
                          "parts": [{"name": "Sekring termal", "est_price_idr": 15000}], "cost_estimate_idr": 15000,
                          "shop_cost_estimate_idr": 0, "diy_saving_idr": 0, "minutes_estimate": 30}}


@pytest.mark.parametrize("level,items", [("red", 0), ("amber", 1)])
def test_red_stop_report_has_no_tools_or_parts(monkeypatch: pytest.MonkeyPatch, level: str, items: int) -> None:
    monkeypatch.setattr(engine, "load", lambda sid: _session(level))
    r = engine.report("abc")
    assert len(r["tools"]) == items and len(r["parts"]) == items
    if level == "red":
        assert r["cost_estimate_idr"] == 0 and r["shop_cost_estimate_idr"] == 0
