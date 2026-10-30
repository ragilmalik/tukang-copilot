"""Per-job cost meter. Prices from https://dev.meta.ai/docs/pricing-rate-limits (read 2026-10-30, Standard mode)."""
from __future__ import annotations

import threading
from typing import Any

PRICES_PER_M = {  # USD per 1M tokens (input, output)
    "muse-wonder-1.0": (4.00, 20.00),
    "muse-spark-1.3": (1.25, 4.25),
    "muse-spark-1.2": (1.25, 4.25),
    "muse-spark-1.1": (1.25, 4.25),
}
IMAGE_USD = 0.01            # Muse Image, per image
SAM_IMAGE_USD = 2.50 / 1000  # SAM 3.1, per image segmented
ASR_USD_PER_HOUR = 0.18      # Muse Voice Transcribe


class BudgetExceeded(RuntimeError):
    pass


class Meter:
    def __init__(self, budget: float):
        self.budget = budget
        self.spent = 0.0
        self.items: dict[str, float] = {}
        self._lock = threading.Lock()

    def charge(self, what: str, usd: float) -> None:
        with self._lock:
            self.spent += usd
            self.items[what] = self.items.get(what, 0.0) + usd

    def check(self, upcoming: float = 0.0) -> None:
        if self.spent + upcoming > self.budget + 1e-9:
            raise BudgetExceeded(f"Job budget ${self.budget:.2f} reached (spent ${self.spent:.3f}).")

    def summary(self) -> dict[str, Any]:
        return {"spent_usd": round(self.spent, 4), "budget_usd": self.budget,
                "by_model": {k: round(v, 4) for k, v in self.items.items()}}


_local = threading.local()


def use(meter: Meter | None) -> None:
    _local.meter = meter


def current() -> Meter | None:
    return getattr(_local, "meter", None)


def charge(what: str, usd: float) -> None:
    m = current()
    if m:
        m.charge(what, usd)


def check(upcoming: float = 0.0) -> None:
    m = current()
    if m:
        m.check(upcoming)


def tokens_usd(model: str | None, usage: dict[str, Any] | None) -> float:
    if not usage or model not in PRICES_PER_M:
        return 0.0
    pin, pout = PRICES_PER_M[model]
    tin = usage.get("prompt_tokens") or usage.get("input_tokens") or 0
    tout = usage.get("completion_tokens") or usage.get("output_tokens") or 0
    return tin / 1e6 * pin + tout / 1e6 * pout


def charge_tokens(model: str | None, usage: dict[str, Any] | None) -> None:
    usd = tokens_usd(model, usage)
    if usd:
        charge(model or "unknown", usd)
