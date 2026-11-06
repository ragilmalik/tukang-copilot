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


def test_private_repair_data_is_never_cached():
    # photos and the repair JSON are the owner's: no shared cache (a proxy, a café Wi-Fi box) may keep them
    import time

    from api.pipeline import engine

    sid = c.post("/api/sessions", data={"sample": "faucet", "language": "en"}).json()["id"]
    deadline = time.monotonic() + 60
    while engine.load(sid)["status"] in ("created", "running") and time.monotonic() < deadline:
        time.sleep(0.02)
    assert c.get(f"/api/sessions/{sid}").headers["cache-control"] == "no-store"
    assert c.get(f"/files/{sid}/photo1.jpg").headers["cache-control"] == "no-store"
    assert c.get(f"/api/sessions/{sid}/report.pdf").headers["cache-control"] == "no-store"
    assert c.get(f"/api/sessions/{sid}/card.png").headers["cache-control"] == "public, max-age=60"  # the link preview is public
