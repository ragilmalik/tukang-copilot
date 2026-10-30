"""Tolerance for real-model drift.

Muse Spark with `response_format` is usually exact, but a live demo must not die on a capitalised enum, a
confidence given as 0.85 or "85%", a price written "Rp 25.000", or a sixth cause. `coerce(cls, raw)` repairs
these harmless quirks before pydantic validates; anything it cannot repair still fails validation and goes
through the one retry-with-error loop in the engine. It never invents content: it only reshapes what is there.
"""
from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel

from .schemas import Diagnosis, ObjectReport, RepairPlan, StepCheck

_THINK = re.compile(r"<think(?:ing)?>.*?</think(?:ing)?>", re.S | re.I)
_FENCE = re.compile(r"```[a-zA-Z0-9_-]*\s*\n?(.*?)```", re.S)


def extract_json(text: str) -> Any:
    """Pull the first complete JSON object/array out of model text (think tags, code fences, prose around it)."""
    text = _THINK.sub("", text or "").strip()
    m = _FENCE.search(text)
    candidates = [m.group(1).strip(), text] if m else [text]
    dec = json.JSONDecoder()
    last: Exception | None = None
    for cand in candidates:
        try:
            return json.loads(cand)
        except ValueError as e:
            last = e
        for i, ch in enumerate(cand):
            if ch in "{[":
                try:
                    obj, _ = dec.raw_decode(cand[i:])
                except ValueError as e:
                    last = e
                    continue
                if isinstance(obj, (dict, list)) and obj:
                    return obj
    raise ValueError(f"no JSON found in model output: {last}")


def _num(v: Any) -> float | None:
    """'85%' -> 85, 'Rp 25.000' -> 25000, '1,5' -> 1.5; None when there is no number."""
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if not isinstance(v, str):
        return None
    s = re.sub(r"(?i)rp\.?|idr|%|\s", "", v)
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", s):        # Indonesian thousands: 25.000
        s = s.replace(".", "")
    elif re.fullmatch(r"\d{1,3}(,\d{3})+", s):       # English thousands: 25,000
        s = s.replace(",", "")
    else:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


_PRICE_UNITS = {"k": 1_000, "rb": 1_000, "ribu": 1_000, "jt": 1_000_000, "juta": 1_000_000}
MAX_PLAUSIBLE_REPAIR_IDR = 15_000_000   # a home repair above this is the model misreading units; treat as unknown


def _price(v: Any) -> int | None:
    """Rupiah from '75k', '75rb', '1,5 juta', 'Rp 75.000' or a plain number; None when unreadable.

    Anything negative or above MAX_PLAUSIBLE_REPAIR_IDR is treated as unknown (0 upstream).
    """
    if isinstance(v, str):
        m = re.fullmatch(r"(?i)\s*(?:rp\.?\s*)?(\d+(?:[.,]\d+)?)\s*(k|rb|ribu|jt|juta)\s*", v)
        if m:
            n: float | None = float(m.group(1).replace(",", ".")) * _PRICE_UNITS[m.group(2).lower()]
        else:
            n = _num(v)
    else:
        n = _num(v)
    if n is None or n < 0 or n > MAX_PLAUSIBLE_REPAIR_IDR:
        return None
    return int(round(n))


def _int(v: Any, lo: int, hi: int) -> Any:
    n = _num(v)
    return v if n is None else max(lo, min(hi, int(round(n))))


def _enum(v: Any, allowed: tuple[str, ...], aliases: dict[str, str] | None = None) -> Any:
    if not isinstance(v, str):
        return v
    k = v.strip().lower()
    k = (aliases or {}).get(k, k)
    return k if k in allowed else v


def _bool(v: Any) -> Any:
    if isinstance(v, str):
        k = v.strip().lower()
        if k in {"true", "yes", "ya", "iya", "ok", "passed", "pass"}:
            return True
        if k in {"false", "no", "tidak", "ora", "failed", "fail"}:
            return False
    return v


def _strs(v: Any) -> Any:
    """A string where a list of strings is expected -> one-item list; None -> []."""
    if v is None:
        return []
    if isinstance(v, str):
        return [v] if v.strip() else []
    if isinstance(v, list):
        return [x if isinstance(x, str) else str(x) for x in v if x is not None]
    return v


def _ids(v: Any) -> Any:
    return [str(x) for x in v] if isinstance(v, list) else v


def _object_report(d: dict[str, Any]) -> dict[str, Any]:
    d["category"] = _enum(d.get("category"), ("motor", "pump", "appliance", "plumbing", "other"),
                          {"motorcycle": "motor", "motorbike": "motor", "water pump": "pump", "electrical": "appliance"})
    d["visible_issues"] = _strs(d.get("visible_issues"))
    comps = d.get("components")
    if isinstance(comps, list):
        comps = [c for c in comps if isinstance(c, dict)][:5]
        for i, c in enumerate(comps, 1):
            c["id"] = str(c["id"]) if c.get("id") not in (None, "") else str(i)
            if c.get("prompt_box") is not None and not (isinstance(c["prompt_box"], list) and len(c["prompt_box"]) == 4):
                c["prompt_box"] = None
            elif isinstance(c.get("prompt_box"), list):
                nums = [_num(x) for x in c["prompt_box"]]
                c["prompt_box"] = None if any(n is None for n in nums) else [
                    n / 100 if n is not None and n > 1.5 else n for n in nums]   # percent -> fraction
        d["components"] = comps
    return d


def _items(v: Any) -> Any:
    if not isinstance(v, list):
        return v
    out = []
    for it in v:
        if isinstance(it, str):
            out.append({"name": it, "est_price_idr": 0})
        elif isinstance(it, dict):
            p = _price(it.get("est_price_idr"))
            it["est_price_idr"] = 0 if p is None else p
            out.append(it)
    return out


def _diagnosis(d: dict[str, Any]) -> dict[str, Any]:
    d["safety_level"] = _enum(d.get("safety_level"), ("green", "amber", "red"),
                              {"yellow": "amber", "orange": "amber", "safe": "green", "danger": "red", "stop": "red"})
    d["difficulty"] = _int(d.get("difficulty"), 1, 5)
    d["minutes_estimate"] = _int(d.get("minutes_estimate"), 1, 600)
    shop = _price(d.get("shop_cost_estimate_idr"))
    d["shop_cost_estimate_idr"] = 0 if shop is None or d["safety_level"] == "red" else shop
    d["tools"], d["parts"] = _items(d.get("tools")), _items(d.get("parts"))
    causes = d.get("causes")
    if isinstance(causes, list):
        causes = [c for c in causes if isinstance(c, dict)]
        for c in causes:
            n = _num(c.get("confidence"))
            if n is not None:
                c["confidence"] = int(round(max(0.0, min(100.0, n * 100 if 0 < n <= 1 else n))))
            c["evidence"] = _strs(c.get("evidence"))
            c["component_ids"] = _ids(c.get("component_ids", []))
        causes.sort(key=lambda c: -(c["confidence"] if isinstance(c.get("confidence"), int) else 0))
        d["causes"] = causes[:4]
    return d


def _plan(d: dict[str, Any]) -> dict[str, Any]:
    steps = d.get("steps")
    if isinstance(steps, list):
        steps = [s for s in steps if isinstance(s, dict)][:10]
        for i, s in enumerate(steps, 1):
            s["n"] = i
            s["warnings"] = _strs(s.get("warnings"))
            s["needs_diagram"] = _bool(s.get("needs_diagram", False))
            if s.get("component_id") is not None:
                s["component_id"] = str(s["component_id"])
        d["steps"] = steps
    return d


def _step_check(d: dict[str, Any]) -> dict[str, Any]:
    d["passed"] = _bool(d.get("passed"))
    return d


_FIX = {ObjectReport: _object_report, Diagnosis: _diagnosis, RepairPlan: _plan, StepCheck: _step_check}


def coerce(cls: type[BaseModel], raw: Any) -> Any:
    """Return `raw` reshaped for `cls`; non-dicts and unknown classes pass through untouched."""
    fix = _FIX.get(cls)
    if fix is None or not isinstance(raw, dict):
        return raw
    return fix(json.loads(json.dumps(raw)))   # deep copy: never mutate the caller's object
