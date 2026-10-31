from fastapi.testclient import TestClient

from api.main import app

c = TestClient(app)


def test_security_headers_on_page_and_error() -> None:
    for path in ("/", "/api/does-not-exist"):
        h = c.get(path).headers
        assert h["x-content-type-options"] == "nosniff"
        assert h["x-frame-options"] == "SAMEORIGIN"
        assert h["referrer-policy"] == "no-referrer"
        assert "camera=(self)" in h["permissions-policy"]
