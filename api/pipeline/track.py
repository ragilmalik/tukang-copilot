"""Live guide: SAM 3.1 on live camera frames, so the phone can draw "this part" over the moving picture.

The phone sends a small JPEG (about 640 px) roughly once a second while the owner points the camera.
For the current step we know the target part (step.component_id -> Component.sam_phrase from Look),
so each frame is ONE SAM 3.1 concept-prompt call. We return normalised boxes plus a rough outline
polygon (from SAM's mask) for the browser to draw. Frames are never stored (privacy).

Cost guards: a per-session minimum interval (TRACK_MIN_INTERVAL_S, too fast -> TooFast) and a per-session
frame cap (MAX_TRACK_FRAMES); once the cap is reached the answer says so and the phone falls back to the
still-photo check. Mock mode jitters the demo outlines (hand-drawn on the sample photos, fixed boxes on any
other picture) so the overlay visibly "tracks".
"""
from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from .. import cost
from ..settings import settings
from . import engine, mock

log = logging.getLogger("tukang.track")
_last: dict[str, float] = {}
_lock = threading.Lock()
MAX_POLY = 24


class TooFast(Exception):
    """The phone sent frames faster than TRACK_MIN_INTERVAL_S."""


def target(s: dict[str, Any], n: int) -> dict[str, Any] | None:
    """The part to highlight for step n: {id, name, phrase, label}, or None when the step names no visible part."""
    steps = (s.get("plan") or {}).get("steps") or []
    step = next((st for st in steps if st.get("n") == n), None)
    if step is None:
        raise ValueError("no such step")
    comps = {c.get("id"): c for c in (s.get("object_report") or {}).get("components") or []}
    cid = step.get("component_id") or ""
    if cid not in comps:  # fall back to the first part of the cause being fixed
        causes = (s.get("diagnosis") or {}).get("causes") or []
        idx = min(int(s.get("cause_index") or 0), max(0, len(causes) - 1))
        ids = (causes[idx].get("component_ids") if causes else None) or []
        cid = next((i for i in ids if i in comps), "")
    if not cid:
        return None
    c = comps[cid]
    return {"id": cid, "name": c.get("name", ""), "phrase": c.get("sam_phrase") or c.get("name", ""),
            "label": (s.get("parts") or {}).get(cid, {}).get("label")}


def mask_polygon(rec: dict[str, Any], w: int, h: int, max_points: int = MAX_POLY) -> list[list[float]]:
    """Rough outline of one SAM mask as normalised [x, y] points (left edge down, right edge up).
    Masks are box-local rasters (mh x mw); an empty or missing mask gives the box corners."""
    l, t, r, b = (float(rec[k]) for k in ("left", "top", "right", "bottom"))
    box = [[l / w, t / h], [r / w, t / h], [r / w, b / h], [l / w, b / h]]
    m = rec.get("mask")
    if m is None:
        return _round(box)
    arr = np.asarray(m).astype(bool)
    if arr.ndim != 2 or not arr.any():
        return _round(box)
    mh, mw = arr.shape
    rows = [y for y in range(mh) if arr[y].any()]
    pick = rows if len(rows) <= max_points // 2 else [rows[int(i * (len(rows) - 1) / (max_points // 2 - 1))] for i in range(max_points // 2)]
    left, right = [], []
    for y in pick:
        xs = np.flatnonzero(arr[y])
        py = t + (y + 0.5) / mh * (b - t)
        left.append([(l + xs[0] / mw * (r - l)) / w, py / h])
        right.append([(l + (xs[-1] + 1) / mw * (r - l)) / w, py / h])
    return _round(left + right[::-1])


def _round(pts: list[list[float]]) -> list[list[float]]:
    return [[round(min(1.0, max(0.0, x)), 4), round(min(1.0, max(0.0, y)), 4)] for x, y in pts]


def _segment(frame: Path, phrase: str, seed: int) -> list[dict[str, Any]]:
    if settings.offline:
        return mock.track(frame, phrase, seed)
    from .. import meta_client

    return meta_client.segment(frame, phrase)


def track_step(sid: str, n: int, frame: Path) -> dict[str, Any]:
    """Run SAM 3.1 on one live frame for step n's target part. Raises ValueError (no plan / no step) or TooFast."""
    s = engine.load(sid)
    if not s.get("plan"):
        raise ValueError("no plan yet")
    tgt = target(s, n)
    tr = s.setdefault("track", {"frames": 0})
    used = int(tr.get("frames", 0))
    out: dict[str, Any] = {"step": n, "component_id": (tgt or {}).get("id"), "name": (tgt or {}).get("name", ""),
                           "label": (tgt or {}).get("label"), "found": False, "boxes": [], "polygon": [],
                           "frames_used": used, "frames_left": max(0, settings.max_track_frames - used),
                           "limit_reached": used >= settings.max_track_frames, "mode": settings.mode}
    if tgt is None or out["limit_reached"]:
        return out
    now = time.monotonic()
    with _lock:
        if now - _last.get(sid, 0.0) < settings.track_min_interval_s:
            raise TooFast()
        _last[sid] = now
    tr["frames"] = used + 1  # reserve the frame before the (slow) call, so the cap holds under parallel requests
    engine.save(s)
    with Image.open(frame) as im:
        w, h = im.size
    meter = cost.Meter(settings.max_cost_usd)
    cost.use(meter)
    try:
        recs = _segment(frame, str(tgt["phrase"]), seed=used)
    finally:
        cost.use(None)
    recs = sorted(recs, key=lambda x: -(x.get("confidence") or 0))[:3]
    out["boxes"] = [{"x1": round(r["left"] / w, 4), "y1": round(r["top"] / h, 4), "x2": round(r["right"] / w, 4),
                     "y2": round(r["bottom"] / h, 4), "confidence": round(float(r.get("confidence") or 0), 3)} for r in recs]
    out["polygon"] = mask_polygon(recs[0], w, h) if recs else []
    out["found"] = bool(recs)
    out["frames_used"] = used + 1
    out["frames_left"] = max(0, settings.max_track_frames - used - 1)
    out["limit_reached"] = out["frames_left"] == 0
    if meter.spent:
        s = engine.load(sid)  # reload: a step check may have written meanwhile
        c = s.get("cost") or {"spent_usd": 0.0, "budget_usd": settings.max_cost_usd, "by_model": {}}
        c["spent_usd"] = round(float(c.get("spent_usd", 0)) + meter.spent, 4)
        bm = dict(c.get("by_model") or {})
        for k, v in meter.items.items():
            bm[k] = round(bm.get(k, 0) + v, 4)
        c["by_model"] = bm
        s["cost"] = c
        s.setdefault("track", {})["frames"] = max(int(s.get("track", {}).get("frames", 0)), used + 1)
        engine.save(s)
    return out


def forget(sid: str) -> None:
    with _lock:
        _last.pop(sid, None)
