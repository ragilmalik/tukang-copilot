"""Abuse guard for a public deployment: per-visitor rate limit and a rolling 24 h spend cap.

Only enforced in live mode (a real Meta key is set and MOCK is off), because offline sample mode costs nothing.
Limits are env-configurable: RATE_LIMIT_PER_HOUR (default 30 new repairs per visitor per hour, 0 = off) and
DAILY_BUDGET_USD (default 10, 0 = off). Messages come in id/jv/en so the phone shows a friendly sentence.
"""
from __future__ import annotations

import json
import threading
import time
from collections import defaultdict, deque
from typing import Any

from .settings import settings

MESSAGES = {
    "rate": {
        "id": "Terlalu banyak permintaan dari perangkat ini. Coba lagi sebentar lagi.",
        "jv": "Kakehan panyuwun saka piranti iki. Coba maneh sedhela.",
        "en": "Too many requests from this device. Please try again in a little while.",
    },
    "budget": {
        "id": "Batas pemakaian harian demo ini sudah tercapai. Coba lagi besok.",
        "jv": "Wates panggunaan saben dina demo iki wis kesel. Coba maneh sesuk.",
        "en": "This demo's daily usage limit has been reached. Please try again tomorrow.",
    },
}
WINDOW_S = 3600.0
SPEND_CACHE_S = 20.0

_hits: dict[str, deque[float]] = defaultdict(deque)
_lock = threading.Lock()
_spend_cache: tuple[float, float] = (0.0, 0.0)  # (computed_at, usd)


class Blocked(Exception):
    """Raised when a request must be refused; carries the HTTP status, a message key and Retry-After seconds."""

    def __init__(self, kind: str, retry_after: int):
        super().__init__(kind)
        self.kind = kind
        self.retry_after = retry_after
        self.status = 429 if kind == "rate" else 503


def active() -> bool:
    """Limits only apply when real money could be spent."""
    return not settings.offline


def reset() -> None:
    global _spend_cache
    with _lock:
        _hits.clear()
        _spend_cache = (0.0, 0.0)


def check_rate(client: str, now: float | None = None, bucket: str = "new", limit: int | None = None) -> None:
    """Sliding one-hour window per visitor. bucket "new" = new repairs (RATE_LIMIT_PER_HOUR); "followup" = model
    calls inside a repair (FOLLOWUP_RATE_PER_HOUR), counted separately so a long repair never blocks a new one."""
    if limit is None:
        limit = settings.rate_limit_per_hour if bucket == "new" else settings.followup_rate_per_hour
    if limit <= 0:
        return
    t = time.time() if now is None else now
    with _lock:
        q = _hits[client if bucket == "new" else f"{bucket}:{client}"]
        while q and q[0] <= t - WINDOW_S:
            q.popleft()
        if len(q) >= limit:
            raise Blocked("rate", max(1, int(q[0] + WINDOW_S - t) + 1))
        q.append(t)
        if len(_hits) > 5000:  # keep memory bounded
            for k in [k for k, v in _hits.items() if not v or v[-1] <= t - WINDOW_S]:
                del _hits[k]


def spent_last_24h(now: float | None = None) -> float:
    """Sum of recorded session costs updated in the last 24 h (sessions are kept RETENTION_HOURS on disk)."""
    global _spend_cache
    t = time.time() if now is None else now
    if now is None and t - _spend_cache[0] < SPEND_CACHE_S:
        return _spend_cache[1]
    root = settings.data_dir / "sessions"
    total = 0.0
    if root.exists():
        for f in root.glob("*/session.json"):
            try:
                if f.stat().st_mtime < t - 86400:
                    continue
                cost = json.loads(f.read_text(encoding="utf-8")).get("cost") or {}
                total += float(cost.get("spent_usd") or 0.0)
            except (OSError, ValueError):
                continue
    with _ledger_lock:
        total += sum(r["usd"] for r in _ledger_lines() if t - 86400 <= r["t"] <= t)
    _spend_cache = (t, total)
    return total


def check_budget(now: float | None = None) -> None:
    cap = settings.daily_budget_usd
    if cap <= 0:
        return
    if spent_last_24h(now) >= cap:
        raise Blocked("budget", 3600)


def message(kind: str, lang: str) -> str:
    return MESSAGES[kind].get(lang, MESSAGES[kind]["en"])


def client_key(forwarded_for: str | None, peer: str | None, hops: int | None = None) -> str:
    """The visitor's address for the rate limit. Every proxy appends the address it saw to X-Forwarded-For, so
    only the right-most FORWARDED_HOPS entries are trustworthy; the left-most one is whatever the visitor sent
    (a random value per request used to skip the limit). With hops=0, or no header, the TCP peer is used."""
    n = settings.forwarded_hops if hops is None else hops
    if forwarded_for and n > 0:
        hosts = [h.strip() for h in forwarded_for.split(",") if h.strip()]
        if hosts:
            return hosts[-min(n, len(hosts))][:64]
    return (peer or "unknown")[:64]


def request_key(headers: Any, peer: str | None) -> str:
    """client_key for a request: CLIENT_IP_HEADER first (a header the edge proxy overwrites), then X-Forwarded-For."""
    for name in (n.strip() for n in settings.client_ip_header.split(",")):
        v = str(headers.get(name) or "").strip() if name else ""
        if v:
            return v[:64]
    return client_key(headers.get("x-forwarded-for"), peer)


LEDGER = "spend-erased.jsonl"
_ledger_lock = threading.Lock()


def record_erased_spend(usd: float, at: float) -> None:
    """Keep the spend of an erased or expired repair in the 24 h cap. Without it, erasing each repair (or a
    RETENTION_HOURS under 24) removed its cost from spent_last_24h, and DAILY_BUDGET_USD never tripped.
    One line per session: time and dollars, nothing else."""
    global _spend_cache
    if usd <= 0 or at < time.time() - 86400:
        return
    p = settings.data_dir / LEDGER
    with _ledger_lock:
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"t": round(at, 1), "usd": round(usd, 4)}) + "\n")
        _spend_cache = (0.0, 0.0)


def _ledger_lines() -> list[dict[str, float]]:
    p = settings.data_dir / LEDGER
    out: list[dict[str, float]] = []
    try:
        lines = p.read_text(encoding="utf-8").splitlines()
    except OSError:
        return out
    for line in lines:
        try:
            rec = json.loads(line)
            out.append({"t": float(rec["t"]), "usd": float(rec["usd"])})
        except (ValueError, KeyError, TypeError):
            continue
    return out


def prune_spend_ledger(now: float | None = None) -> None:
    """Drop ledger lines older than 24 h (the janitor calls this hourly)."""
    t = time.time() if now is None else now
    p = settings.data_dir / LEDGER
    with _ledger_lock:
        if not p.exists():
            return
        keep = [r for r in _ledger_lines() if r["t"] >= t - 86400]
        tmp = p.with_suffix(".tmp")
        tmp.write_text("".join(json.dumps(r) + "\n" for r in keep), encoding="utf-8")
        tmp.replace(p)
