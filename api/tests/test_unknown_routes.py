"""Audit 18: unknown routes and wrong methods never 5xx."""
from fastapi.testclient import TestClient

from api.main import app

c = TestClient(app)


def test_unknown_api_path_is_4xx():
    for p in ["/api/nope", "/nope", "/api/session/zzz", "/api/../etc/passwd"]:
        assert c.get(p).status_code < 500


def test_wrong_method_is_4xx():
    for p in ["/api/session", "/api/health"]:
        assert c.delete(p).status_code < 500
