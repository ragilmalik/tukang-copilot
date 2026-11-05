"""1.30 review fixes: no cross-origin access by default, no Server header, object heading capitalised.

Before 1.30 the default was "*", so any web page could drive the API from a visitor's browser (start repairs that cost
model calls, read a session by id). The uvicorn Server header is also dropped (Dockerfile and app.py)."""
from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app
from api.settings import Settings

ROOT = Path(__file__).resolve().parents[2]


def test_default_has_no_cors_header() -> None:
    c = TestClient(app)
    r = c.get("/api/health", headers={"Origin": "https://evil.example"})
    assert r.status_code == 200 and "access-control-allow-origin" not in r.headers
    pre = c.options("/api/sessions", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in pre.headers


def test_default_setting_is_same_origin(monkeypatch) -> None:
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    assert Settings().cors_origins == ""


def test_server_header_is_off_where_the_app_starts() -> None:
    assert "--no-server-header" in (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "server_header=False" in (ROOT / "app.py").read_text(encoding="utf-8")


def test_object_heading_starts_with_a_capital() -> None:
    """Live Muse Spark object names often start lower case ("rear wheel of blue automatic scooter")."""
    css = (ROOT / "web" / "style.css").read_text(encoding="utf-8")
    assert "#dxObject::first-letter{text-transform:uppercase}" in css
