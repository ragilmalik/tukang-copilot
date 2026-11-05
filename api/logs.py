"""Logging setup: one line per event, secrets scrubbed, no owner text.

LOG_FORMAT=json gives one JSON object per line (for a log service); anything else gives plain text. Every record
goes through RedactFilter first, so a Bearer token, an api_key=..., a key-shaped string or the configured Meta /
Baseten / WhatsApp secrets never reach the log, even if an exception message carries them.

What the app logs on purpose: stage names, model ids, latency, HTTP status, masked phone numbers, request ids.
What it never logs: the owner's description, transcripts, photos, answers from the model.
"""
from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

from .settings import settings

_PATTERNS = [
    (re.compile(r"(?i)bearer\s+[\w.~+/=-]+"), "Bearer ***"),
    (re.compile(r"(?i)(api[_-]?key[\"']?\s*[:=]\s*[\"']?)[\w.~+/=-]{6,}"), r"\1***"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{12,}"), "sk-***"),
    (re.compile(r"\bEAA[A-Za-z0-9]{20,}"), "EAA***"),
    (re.compile(r"\bAIza[0-9A-Za-z_-]{20,}"), "AIza***"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"), "gh*_***"),
]


def _secrets() -> list[str]:
    vals = [settings.meta_api_key, settings.baseten_api_key, settings.wa_token, settings.wa_app_secret,
            settings.wa_verify_token, settings.impact_token]
    return [v for v in vals if v and len(v) >= 6]


def redact(text: str) -> str:
    for s in _secrets():
        text = text.replace(s, "***")
    for pat, rep in _PATTERNS:
        text = pat.sub(rep, text)
    return text


class RedactFilter(logging.Filter):
    """Formats the message once, scrubs it, and stores the clean text (args cleared), so no handler sees a secret."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = record.getMessage()
        except Exception:  # noqa: BLE001  (a bad format string must not kill logging)
            msg = str(record.msg)
        record.msg, record.args = redact(msg), None
        if record.exc_info and not record.exc_text:
            record.exc_text = redact(logging.Formatter().formatException(record.exc_info))
            record.exc_info = None
        elif record.exc_text:
            record.exc_text = redact(record.exc_text)
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        out: dict[str, Any] = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)) + "Z",
                               "level": record.levelname, "logger": record.name, "msg": record.getMessage()}
        for k in ("request_id", "stage", "model", "status", "ms", "method", "path"):
            if hasattr(record, k):
                out[k] = getattr(record, k)
        if record.exc_text:
            out["exc"] = record.exc_text
        return json.dumps(out, ensure_ascii=False)


def setup(fmt: str = "", level: int = logging.INFO) -> None:
    """Install the filter and formatter on the root handler (idempotent)."""
    root = logging.getLogger()
    if not root.handlers:
        root.addHandler(logging.StreamHandler())
    root.setLevel(level)
    for h in root.handlers:
        if not any(isinstance(f, RedactFilter) for f in h.filters):
            h.addFilter(RedactFilter())
        h.setFormatter(JsonFormatter() if fmt == "json" else logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
