"""Abuse guard: per-visitor rate limit and rolling 24 h spend cap (live mode only)."""
import json
import time

import pytest
from fastapi.testclient import TestClient

from api import guard
from api.main import app
from api.settings import settings

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clean():
    guard.reset()
    yield
    guard.reset()


def test_inactive_in_mock_mode():
    assert settings.offline and not guard.active()
    for _ in range(3):
        assert client.post("/api/sessions", data={"sample": "faucet", "language": "en"}).status_code == 200


def test_rate_limit_blocks_then_recovers(monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_per_hour", 3)
    for i in range(3):
        guard.check_rate("1.2.3.4", now=1000.0 + i)
    with pytest.raises(guard.Blocked) as e:
        guard.check_rate("1.2.3.4", now=1010.0)
    assert e.value.status == 429 and 3500 < e.value.retry_after <= 3601
    guard.check_rate("9.9.9.9", now=1010.0)  # another visitor is unaffected
    guard.check_rate("1.2.3.4", now=1000.0 + 3601)  # window slid past the first hits


def test_rate_limit_zero_disables(monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_per_hour", 0)
    for i in range(50):
        guard.check_rate("x", now=1.0 + i)


def test_spend_cap_sums_recent_sessions(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "daily_budget_usd", 0.10)
    now = time.time()
    for name, usd in (("aaa", 0.04), ("bbb", 0.05)):
        d = tmp_path / "sessions" / name
        d.mkdir(parents=True)
        (d / "session.json").write_text(json.dumps({"cost": {"spent_usd": usd}}))
    assert guard.spent_last_24h(now=now) == pytest.approx(0.09)
    guard.check_budget(now=now)  # 0.09 < 0.10
    d = tmp_path / "sessions" / "ccc"
    d.mkdir()
    (d / "session.json").write_text(json.dumps({"cost": {"spent_usd": 0.02}}))
    with pytest.raises(guard.Blocked) as e:
        guard.check_budget(now=now)
    assert e.value.status == 503
    # sessions older than 24 h no longer count
    assert guard.spent_last_24h(now=now + 90000) == 0.0


def test_client_key_prefers_forwarded_for():
    assert guard.client_key("5.6.7.8, 10.0.0.1", "10.0.0.1") == "5.6.7.8"
    assert guard.client_key(None, "10.0.0.1") == "10.0.0.1"
    assert guard.client_key(None, None) == "unknown"


def test_messages_in_all_languages():
    for kind in ("rate", "budget"):
        texts = {guard.message(kind, lang) for lang in ("id", "jv", "en")}
        assert len(texts) == 3
        assert guard.message(kind, "zz") == guard.message(kind, "en")


def test_endpoint_returns_429_with_retry_after_in_live_mode(monkeypatch):
    monkeypatch.setattr(guard, "active", lambda: True)
    monkeypatch.setattr(settings, "rate_limit_per_hour", 2)
    h = {"x-forwarded-for": "7.7.7.7"}
    for _ in range(2):
        assert client.post("/api/sessions", data={"sample": "faucet", "language": "id"}, headers=h).status_code == 200
    r = client.post("/api/sessions", data={"sample": "faucet", "language": "jv"}, headers=h)
    assert r.status_code == 429
    assert r.headers["retry-after"].isdigit()
    assert r.json()["detail"] == guard.MESSAGES["rate"]["jv"]
    # a different visitor still gets through
    assert client.post("/api/sessions", data={"sample": "faucet", "language": "id"}, headers={"x-forwarded-for": "8.8.8.8"}).status_code == 200


def test_endpoint_returns_503_when_daily_budget_spent(monkeypatch, tmp_path):
    monkeypatch.setattr(guard, "active", lambda: True)
    monkeypatch.setattr(settings, "daily_budget_usd", 0.01)
    d = tmp_path / "sessions" / "zzz"
    d.mkdir(parents=True)
    (d / "session.json").write_text(json.dumps({"cost": {"spent_usd": 0.5}}))
    r = client.post("/api/sessions", data={"sample": "faucet", "language": "en"})
    assert r.status_code == 503 and "daily" in r.json()["detail"]


def test_security_headers_on_api_and_pages():
    for path in ("/api/health", "/", "/manifest.webmanifest"):
        r = client.get(path)
        assert r.headers["x-content-type-options"] == "nosniff"
        assert r.headers["x-frame-options"] == "SAMEORIGIN"
        assert r.headers["referrer-policy"] == "no-referrer"
        assert "camera=(self)" in r.headers["permissions-policy"]
