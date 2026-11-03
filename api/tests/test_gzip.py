"""Text files are gzipped for slow phones; fonts and pictures are already packed, so they go out as they are."""
import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)
GZ = {"accept-encoding": "gzip, deflate, br"}


@pytest.mark.parametrize("path", ["/static/app.js", "/static/style.css", "/"])
def test_text_is_gzipped(path: str):
    r = client.get(path, headers=GZ)
    assert r.status_code == 200 and r.headers.get("content-encoding") == "gzip", path


@pytest.mark.parametrize("path", ["/static/fonts/barlow-600.woff2", "/static/demo-thumb.jpg", "/static/og.png",
                                  "/static/icons/icon-512.png"])
def test_packed_files_are_not_gzipped(path: str):
    r = client.get(path, headers=GZ)
    assert r.status_code == 200, path
    assert "content-encoding" not in r.headers, path
    assert int(r.headers["content-length"]) == len(r.content)
