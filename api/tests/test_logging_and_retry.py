"""Logs carry no secrets and no owner text; every request gets an id; Meta retries back off and respect Retry-After."""
from __future__ import annotations

import io
import time
import json
import logging
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from api import logs, meta_client
from api.main import app
from api.settings import settings

c = TestClient(app)


def _capture(fmt: str = "") -> tuple[logging.Logger, io.StringIO]:
    buf = io.StringIO()
    h = logging.StreamHandler(buf)
    h.addFilter(logs.RedactFilter())
    h.setFormatter(logs.JsonFormatter() if fmt == "json" else logging.Formatter("%(message)s"))
    lg = logging.getLogger(f"tukang.test.{fmt or 'text'}")
    lg.handlers[:] = [h]
    lg.propagate = False
    lg.setLevel(logging.INFO)
    return lg, buf


@pytest.mark.parametrize("raw", [
    "Authorization: Bearer abc.DEF-123_xyz",
    'error {"api_key": "abcdef123456"}',
    "token sk-EXAMPLE-TOKEN",
    "graph EAABBBBBBBBBBBBBBBBBBBBBBBBBBB",
    "google AIzaSyA1234567890abcdefghijk",
    "gh ghp_EXAMPLE",
])
def test_known_secret_shapes_are_scrubbed(raw: str) -> None:
    out = logs.redact(raw)
    assert out != raw and "***" in out


def test_the_configured_key_itself_is_scrubbed_even_without_a_pattern(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "meta_api_key", "plainkeylookslikeaword")
    lg, buf = _capture()
    lg.warning("call failed with %s", "plainkeylookslikeaword")
    assert "plainkeylookslikeaword" not in buf.getvalue() and "***" in buf.getvalue()


def test_exception_tracebacks_are_scrubbed_too(monkeypatch: pytest.MonkeyPatch) -> None:
    lg, buf = _capture()
    try:
        raise RuntimeError("401 from server, sent Bearer zzzsecretzzz")
    except RuntimeError:
        lg.exception("boom")
    assert "zzzsecretzzz" not in buf.getvalue() and "Bearer ***" in buf.getvalue()


def test_json_format_is_one_parseable_object_per_line() -> None:
    lg, buf = _capture("json")
    lg.info("GET /api/health 200", extra={"request_id": "abc12345", "status": 200, "ms": 3})
    rec = json.loads(buf.getvalue().strip())
    assert rec["msg"] == "GET /api/health 200" and rec["request_id"] == "abc12345" and rec["status"] == 200 and rec["level"] == "INFO"


def test_every_response_has_a_request_id_and_a_sane_one_is_kept() -> None:
    r = c.get("/api/health")
    assert len(r.headers["x-request-id"]) == 16
    assert c.get("/api/health", headers={"X-Request-ID": "proxy-req-12345"}).headers["x-request-id"] == "proxy-req-12345"
    bad = c.get("/api/health", headers={"X-Request-ID": "<script>alert(1)</script>"}).headers["x-request-id"]
    assert "<" not in bad and len(bad) == 16


def test_access_log_has_path_but_no_query_or_owner_text(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO, logger="tukang.http"):
        c.get("/api/health?token=hunter2hunter2")
        c.post("/api/sessions", data={"text": "rumah saya di Jalan Rahasia 7", "language": "id", "sample": "faucet"})
    text = "\n".join(r.getMessage() for r in caplog.records if r.name == "tukang.http")
    assert "GET /api/health 200" in text and "hunter2" not in text
    assert "POST /api/sessions" in text and "Rahasia" not in text


def _resp(status: int, headers: dict[str, str] | None = None) -> httpx.Response:
    return httpx.Response(status, headers=headers or {}, request=httpx.Request("POST", "https://x"))


def test_backoff_doubles_and_honours_retry_after() -> None:
    assert [meta_client.backoff_s(a) for a in range(3)] == [2, 4, 8]
    assert meta_client.backoff_s(0, _resp(429, {"Retry-After": "7"})) == 7
    assert meta_client.backoff_s(0, _resp(429, {"Retry-After": "9999"})) == meta_client.MAX_RETRY_AFTER_S
    assert meta_client.backoff_s(1, _resp(429, {"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"})) == 4
    assert meta_client.backoff_s(0, _resp(504, {"Retry-After": "7"})) == 2  # only 429/503 carry a useful Retry-After


def test_post_retries_429_with_the_servers_wait(monkeypatch: pytest.MonkeyPatch) -> None:
    waits: list[float] = []
    answers = [_resp(429, {"Retry-After": "3"}), _resp(200)]
    monkeypatch.setattr(time, "sleep", waits.append)
    monkeypatch.setattr(httpx, "post", lambda *a, **k: answers.pop(0))
    assert meta_client._post("https://x").status_code == 200 and waits == [3]


def test_post_does_not_retry_auth_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[Any] = []

    def post(*a: Any, **k: Any) -> httpx.Response:
        calls.append(1)
        return _resp(401)

    monkeypatch.setattr(httpx, "post", post)
    with pytest.raises(meta_client.MetaAPIError, match="401"):
        meta_client._post("https://x")
    assert calls == [1]


def test_post_gives_up_on_network_errors_after_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    waits: list[float] = []
    monkeypatch.setattr(time, "sleep", waits.append)

    def post(*a: Any, **k: Any) -> httpx.Response:
        raise httpx.ConnectError("down")

    monkeypatch.setattr(httpx, "post", post)
    with pytest.raises(meta_client.MetaAPIError, match="failed"):
        meta_client._post("https://x", retries=2)
    assert waits == [2, 4]


def test_fallback_to_canned_answers_is_off_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    from api.settings import Settings

    monkeypatch.delenv("DEMO_FALLBACK", raising=False)
    assert Settings().demo_fallback is False
    monkeypatch.setenv("DEMO_FALLBACK", "1")
    assert Settings().demo_fallback is True
