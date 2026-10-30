"""Abuse guard for a public deployment: per-visitor rate limit and a rolling 24 h spend cap.

Only enforced in live mode (a real Meta key is set and MOCK is off), because demo mode costs nothing.
Limits are env-configurable: RATE_LIMIT_PER_HOUR (default 30 new repairs per visitor per hour, 0 = off) and
DAILY_BUDGET_USD (default 10, 0 = off). Messages come in id/jv/en so the phone shows a friendly sentence.
"""
from __future__ import annotations

import json
import threading
import time
from collections import defaultdict, deque

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


def check_rate(client: str, now: float | None = None) -> None:
    limit = settings.rate_limit_per_hour
    if limit <= 0:
        return
    t = time.time() if now is None else now
    with _lock:
        q = _hits[client]
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


def client_key(forwarded_for: str | None, peer: str | None) -> str:
    """Render and most hosts put the real visitor first in X-Forwarded-For."""
    if forwarded_for:
        first = forwarded_for.split(",")[0].strip()
        if first:
            return first[:64]
    return (peer or "unknown")[:64]
