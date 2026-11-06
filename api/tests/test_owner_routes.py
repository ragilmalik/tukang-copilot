"""A shared guide link is read-only at the API too (1.32.0). Before, only "It works now" and erase checked the
owner token; anyone holding the link could answer the question, re-plan the owner's repair, use up its photo
checks and live-guide frames, and spend on it. Also: the rate-limit key, session ids and bad pictures."""
import io
import time
from typing import Any

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from api import guard
from api.main import app
from api.pipeline import engine
from api.settings import settings
from api.tests.owner_auth import owner

viewer = TestClient(app)  # someone with the guide link: never sends the owner token
WAIT_S = 60


def _settle(sid: str) -> dict[str, Any]:
    deadline = time.monotonic() + WAIT_S
    while time.monotonic() < deadline:
        s: dict[str, Any] = engine.load(sid)
        if s["status"] not in ("created", "running"):
            return s
        time.sleep(0.02)
    raise AssertionError("timeout")


def _jpg() -> io.BytesIO:
    b = io.BytesIO()
    Image.new("RGB", (320, 240), (180, 180, 180)).save(b, "JPEG")
    b.seek(0)
    return b


def _post(sid: str, route: str, headers: dict[str, str] | None = None) -> Any:
    if route.endswith(("check", "track")):
        field = "photo" if route.endswith("check") else "frame"
        return viewer.post(f"/api/sessions/{sid}/{route}", files={field: ("a.jpg", _jpg(), "image/jpeg")}, headers=headers or {})
    data = {"answer": {"text": "no"}, "replan": {"report": "x"}, "command": {"text": "next"}}.get(route, {})
    return viewer.post(f"/api/sessions/{sid}/{route}", data=data, headers=headers or {})


ROUTES = ["answer", "retry", "replan", "command", "steps/1/check", "steps/1/track"]


@pytest.mark.parametrize("route", ROUTES)
def test_every_route_that_changes_a_repair_needs_the_owner_token(route: str) -> None:
    sid = viewer.post("/api/sessions", data={"sample": "faucet", "language": "en"}).json()["id"]
    before = _settle(sid)
    r = _post(sid, route)
    assert r.status_code == 403, (route, r.status_code, r.text)
    r = _post(sid, route, {"X-Owner-Token": "not-the-token"})
    assert r.status_code == 403
    after = engine.load(sid)
    for k in ("cause_index", "checks", "checks_used", "track", "answer", "status", "plan"):
        assert after.get(k) == before.get(k), k


def test_the_owner_still_does_all_of_it() -> None:
    sid = viewer.post("/api/sessions", data={"sample": "faucet", "language": "en"}).json()["id"]
    _settle(sid)
    own = owner(sid)
    settings_interval = settings.track_min_interval_s
    try:
        settings.track_min_interval_s = 0.0
        assert _post(sid, "steps/1/check", own).status_code == 200
        assert _post(sid, "steps/1/track", own).status_code == 200
        assert _post(sid, "command", own).status_code == 200
        assert _post(sid, "replan", own).json()["cause_index"] == 1
    finally:
        settings.track_min_interval_s = settings_interval


def test_the_app_sends_the_owner_token_on_each_of_those_routes() -> None:
    from pathlib import Path

    js = (Path(__file__).resolve().parents[2] / "web" / "app.js").read_text(encoding="utf-8")
    for route in ("retry", "answer", "steps/${st.n}/check", "steps/${st.n}/track", "replan", "command"):
        i = js.index(f"/api/sessions/${{S.id}}/{route}`")
        assert "headers: ownerHeaders(S.id)" in js[i: i + 160], route


def test_a_session_from_before_owner_tokens_stays_open() -> None:
    sid = viewer.post("/api/sessions", data={"sample": "faucet", "language": "en"}).json()["id"]
    _settle(sid)
    s = engine.load(sid)
    s["owner_token"] = ""
    engine.save(s)
    assert _post(sid, "replan").status_code == 200


# --- B2: the rate-limit key
def test_rate_limit_key_is_the_address_our_proxy_wrote() -> None:
    assert guard.client_key("6.6.6.6, 203.0.113.7", "10.0.0.1", hops=1) == "203.0.113.7"
    assert guard.client_key("6.6.6.6, 203.0.113.7, 10.1.1.1", "10.0.0.1", hops=2) == "203.0.113.7"
    assert guard.client_key("203.0.113.7", "10.0.0.1", hops=3) == "203.0.113.7"  # fewer entries than hops
    assert guard.client_key("6.6.6.6", "192.0.2.5", hops=0) == "192.0.2.5"  # no proxy: the header is ignored
    assert guard.client_key("", "192.0.2.5") == "192.0.2.5"
    assert guard.client_key(None, None) == "unknown"


def test_a_spoofed_header_no_longer_skips_the_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "forwarded_hops", 1)
    guard.reset()
    for i in range(3):
        guard.check_rate(guard.client_key(f"10.9.9.{i}, 203.0.113.7", "10.0.0.1"), limit=3)
    with pytest.raises(guard.Blocked):
        guard.check_rate(guard.client_key("10.9.9.99, 203.0.113.7", "10.0.0.1"), limit=3)
    guard.reset()


# --- B3: session ids are ASCII
@pytest.mark.parametrize("sid", ["１２３", "٣٣٣", "abcé", "a" * 33, "", "ab/cd", "ab cd"])
def test_session_ids_are_ascii_letters_and_digits(sid: str) -> None:
    with pytest.raises(ValueError):
        engine.session_dir(sid)


def test_ascii_ids_still_work() -> None:
    assert engine.session_dir("abc123DEF").name == "abc123DEF"


# --- B4: a decompression bomb is a bad picture, not a busy AI
def test_a_bomb_on_the_step_check_is_400_not_503(monkeypatch: pytest.MonkeyPatch) -> None:
    sid = viewer.post("/api/sessions", data={"sample": "faucet", "language": "en"}).json()["id"]
    _settle(sid)
    b = io.BytesIO()
    Image.new("RGB", (400, 400), (120, 120, 120)).save(b, "JPEG")
    b.seek(0)
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 10_000)  # 400x400 is over twice the limit: DecompressionBombError
    r = viewer.post(f"/api/sessions/{sid}/steps/1/check", files={"photo": ("a.jpg", b, "image/jpeg")}, headers=owner(sid))
    assert r.status_code == 400, r.text
    assert int(engine.load(sid).get("checks_used", 0)) == 0


def test_a_header_the_edge_proxy_overwrites_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "client_ip_header", "cf-connecting-ip,true-client-ip")
    h = {"x-forwarded-for": "6.6.6.6, 172.16.0.1", "true-client-ip": "198.51.100.4"}
    assert guard.request_key(h, "10.0.0.1") == "198.51.100.4"
    h["cf-connecting-ip"] = "198.51.100.9"
    assert guard.request_key(h, "10.0.0.1") == "198.51.100.9"
    monkeypatch.setattr(settings, "client_ip_header", "")
    assert guard.request_key(h, "10.0.0.1") == "172.16.0.1"  # not configured: never trusted


def test_render_blueprint_names_the_cloudflare_header() -> None:
    from pathlib import Path

    import yaml

    env = yaml.safe_load((Path(__file__).resolve().parents[2] / "render.yaml").read_text(encoding="utf-8"))["services"][0]["envVars"]
    assert {e["key"]: e.get("value") for e in env}["CLIENT_IP_HEADER"] == "cf-connecting-ip"
