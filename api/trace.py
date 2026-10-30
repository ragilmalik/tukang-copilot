"""Pipeline trace: which tool did each stage use, and how long did it take.

Shown on the phone ("Under the hood") and printed in the PDF report so judges and users can see exactly
where Meta models are used and where plain code (safety gates) or other tools (edge-tts) take over.
Pure function of the session dict, no I/O.
"""
from __future__ import annotations

from typing import Any

# stage -> (model key in session["models"], kind). kind: meta | open | tts | code
_STAGE_SOURCE: list[tuple[str, str | None, str]] = [
    ("listen", "listen", "meta"),
    ("gate", None, "code"),
    ("look", "look", "meta"),
    ("segment", "segment", "meta"),
    ("diagnose", "diagnose", "meta"),
    ("plan", "plan", "meta"),
    ("safety", None, "code"),
    ("illustrate", "illustrate", "meta"),
    ("narrate", None, "tts"),
]
CODE_LABEL = "rules in code"
TTS_LABEL = "edge-tts (Meta has no TTS)"


def build_trace(s: dict[str, Any]) -> list[dict[str, Any]]:
    """One row per pipeline stage: {stage, tool, kind, status, ms}. Stage order is fixed."""
    models: dict[str, str] = s.get("models") or {}
    stages: dict[str, Any] = s.get("stages") or {}
    open_weights = "open weights" in (models.get("diagnose") or "")
    rows: list[dict[str, Any]] = []
    for stage, key, kind in _STAGE_SOURCE:
        st = stages.get(stage) or {}
        if key is None:
            tool = CODE_LABEL if kind == "code" else TTS_LABEL
        else:
            tool = models.get(key) or ""
            if stage == "listen" and s.get("lang") == "jv" and models.get("listen_javanese"):
                tool = models["listen_javanese"]
            if open_weights and stage in {"diagnose", "plan"}:
                kind = "open"
        rows.append({"stage": stage, "tool": tool, "kind": kind, "status": st.get("status", "waiting"), "ms": st.get("ms")})
    return rows


def meta_stage_count(rows: list[dict[str, Any]]) -> int:
    """How many stages really ran on a Meta model (done, not skipped)."""
    return sum(1 for r in rows if r["kind"] in {"meta", "open"} and r["status"] == "done")
