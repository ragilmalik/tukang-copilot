"""Impact trial log: every outcome the owner reports ("it works now" / "took it to a mechanic") is appended as
one JSON line to DATA_DIR/impact/outcomes.jsonl (append-only; data/ is gitignored and never leaves the server).

scripts/impact_report.py turns the file into docs/IMPACT.md and the impact slide. No photos, no voice, no free
text from the owner is written here: only the numbers the report needs plus the object's short name.
"""
from __future__ import annotations

import json
import re
import threading
import time
from pathlib import Path
from typing import Any

from .settings import settings

_lock = threading.Lock()
MAX_MINUTES = 600
TESTER_RE = re.compile(r"^[A-Za-z0-9 _.-]{1,40}$")


def log_path() -> Path:
    return settings.data_dir / "impact" / "outcomes.jsonl"


def clean_tester(tester: str) -> str:
    """Optional trial label like "T1" or "Pak Budi": short, plain characters only, else rejected."""
    t = " ".join((tester or "").split())
    if t and not TESTER_RE.match(t):
        raise ValueError("tester label: up to 40 letters, digits, spaces, . _ -")
    return t


def record(s: dict[str, Any], minutes: int | None = None, tester: str = "") -> dict[str, Any]:
    """Build and append one outcome row. `minutes` is what the owner says the fix took; default is the time from
    starting the repair to reporting the outcome (capped)."""
    oc = s.get("outcome") or {}
    dx, rep = s.get("diagnosis") or {}, s.get("object_report") or {}
    steps = (s.get("plan") or {}).get("steps") or []
    elapsed = (float(oc.get("at") or time.time()) - float(s.get("created") or time.time())) / 60
    mins = minutes if minutes is not None else round(elapsed)
    row = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(float(oc.get("at") or time.time()))),
        "session": s.get("id"), "tester": clean_tester(tester), "mode": s.get("mode"), "lang": s.get("lang"),
        "scenario": rep.get("category") or s.get("category") or "other", "object": str(rep.get("object") or "")[:80],
        "result": oc.get("result"), "fixed": oc.get("result") == "fixed",
        "minutes": max(0, min(MAX_MINUTES, int(mins))), "minutes_source": "owner" if minutes is not None else "elapsed",
        "saved_idr": int(oc.get("saved_idr") or 0), "shop_cost_idr": int(dx.get("shop_cost_estimate_idr") or 0),
        "parts_cost_idr": int(dx.get("cost_estimate_idr") or 0), "replans": int(s.get("cause_index") or 0),
        "steps_total": len(steps),
        "steps_verified": sum(1 for st in steps if (s.get("checks") or {}).get(str(st.get("n")), {}).get("passed")),
        "fallback": bool(s.get("fallback")),
    }
    p = log_path()
    with _lock:
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def read(path: Path | None = None) -> list[dict[str, Any]]:
    """All rows; a broken line (power cut mid-write) is skipped, not fatal."""
    p = path or log_path()
    if not p.exists():
        return []
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if isinstance(r, dict):
            rows.append(r)
    return rows
