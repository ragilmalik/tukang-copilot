"""1.29.10: /static files carry a Cache-Control header. Fonts (and anything asked for with ?v=) are cached for a
year, pictures for a day, and the app code is revalidated every time so a new release shows up at once."""
import pytest
from fastapi.testclient import TestClient

from api.main import DAY_CACHE, LONG_CACHE, REVALIDATE, app, static_cache_control

client = TestClient(app)


@pytest.mark.parametrize("path,want", [
    ("/static/fonts/barlow-400.woff2", LONG_CACHE),
    ("/static/fonts/barlow-condensed-800.woff2", LONG_CACHE),
    ("/static/icons/icon-192.png", DAY_CACHE),
    ("/static/demo-thumb.jpg", DAY_CACHE),
    ("/static/replay/files/photo1.jpg", DAY_CACHE),
    ("/static/vendor/qrcode.js", DAY_CACHE),
    ("/static/app.js", REVALIDATE),
    ("/static/style.css", REVALIDATE),
    ("/static/replay.js", REVALIDATE),
    ("/static/replay/demo.json", REVALIDATE),
])
def test_static_files_get_the_right_cache_header(path, want):
    r = client.get(path)
    assert r.status_code == 200
    assert r.headers["cache-control"] == want


def test_versioned_url_is_immutable():
    assert static_cache_control("/static/app.js", "v=1.29.10") == LONG_CACHE
    r = client.get("/static/app.js?v=1.29.10")
    assert r.headers["cache-control"] == LONG_CACHE


def test_revalidation_still_answers_304():
    first = client.get("/static/app.js")
    etag = first.headers["etag"]
    again = client.get("/static/app.js", headers={"If-None-Match": etag})
    assert again.status_code == 304
    assert again.headers["cache-control"] == REVALIDATE


def test_service_worker_and_missing_files_keep_their_own_rules():
    assert client.get("/sw.js").headers["cache-control"] == "no-cache"
    assert "max-age=31536000" not in client.get("/static/nope.js").headers.get("cache-control", "")
    assert "cache-control" not in client.get("/api/health").headers or "immutable" not in client.get("/api/health").headers["cache-control"]
