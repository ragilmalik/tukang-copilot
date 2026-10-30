"""PWA: manifest + service worker are served from the root with the right types, and icons exist."""
import json

from fastapi.testclient import TestClient

from api.main import app

c = TestClient(app)


def test_manifest_served_and_valid():
    r = c.get("/manifest.webmanifest")
    assert r.status_code == 200 and "manifest+json" in r.headers["content-type"]
    m = json.loads(r.text)
    assert m["display"] == "standalone" and m["start_url"].startswith("/")
    sizes = {i["sizes"] for i in m["icons"]}
    assert {"192x192", "512x512"} <= sizes
    assert any(i.get("purpose") == "maskable" for i in m["icons"])
    for icon in m["icons"]:
        assert c.get(icon["src"]).status_code == 200, icon["src"]


def test_service_worker_served_and_never_caches_api():
    r = c.get("/sw.js")
    assert r.status_code == 200 and "javascript" in r.headers["content-type"]
    assert "/api/" not in r.text.split("const SHELL")[1].split(";")[0]
