"""Robustness of the public endpoints against bad input (no crash, no leftovers, friendly 4xx)."""
import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from api.main import MAX_PHOTO, app
from api.settings import settings

client = TestClient(app, raise_server_exceptions=False)


_IGNORE: set[str] = set()


@pytest.fixture(autouse=True)
def _baseline(_tmp_data):
    """A worker thread leaked by an earlier test may still write its own stale folder; ignore ids present at start."""
    _IGNORE.clear()
    _IGNORE.update(_ids())
    yield


def _ids() -> set[str]:
    d = settings.data_dir / "sessions"
    return {p.name for p in d.iterdir()} if d.exists() else set()


def _sessions_on_disk() -> int:
    return len(_ids() - _IGNORE)


def _post(files, **data):
    return client.post("/api/sessions", data={"text": "kran menetes", "language": "id", **data}, files=files)


def test_garbage_bytes_named_jpg_is_a_400_and_leaves_no_session():
    r = _post([("photos", ("x.jpg", io.BytesIO(b"this is not an image"), "image/jpeg"))])
    assert r.status_code == 400, r.text
    assert _sessions_on_disk() == 0


def test_html_disguised_as_png_is_rejected():
    r = _post([("photos", ("x.png", io.BytesIO(b"<html><script>alert(1)</script></html>"), "image/png"))])
    assert r.status_code == 400
    assert _sessions_on_disk() == 0


def test_unsupported_extension_and_empty_file():
    assert _post([("photos", ("x.exe", io.BytesIO(b"MZ"), "application/octet-stream"))]).status_code == 400
    assert _post([("photos", ("x.jpg", io.BytesIO(b""), "image/jpeg"))]).status_code == 400


def test_oversize_photo_is_413(monkeypatch):
    monkeypatch.setattr("api.main.MAX_PHOTO", 1000)
    r = _post([("photos", ("x.jpg", io.BytesIO(b"\xff\xd8" + b"0" * 5000), "image/jpeg"))])
    assert r.status_code == 413
    assert MAX_PHOTO > 1000


def test_decompression_bomb_is_a_400(monkeypatch):
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 10_000)
    b = io.BytesIO()
    Image.new("RGB", (400, 400), (1, 2, 3)).save(b, "PNG")
    b.seek(0)
    r = _post([("photos", ("big.png", b, "image/png"))])
    assert r.status_code == 400, r.text
    assert _sessions_on_disk() == 0


def test_garbage_audio_does_not_crash_session_creation():
    b = io.BytesIO()
    Image.new("RGB", (200, 200), (9, 9, 9)).save(b, "JPEG")
    b.seek(0)
    r = client.post("/api/sessions", data={"language": "id"},
                    files=[("photos", ("a.jpg", b, "image/jpeg")), ("audio", ("v.webm", io.BytesIO(b"not audio"), "audio/webm"))])
    assert r.status_code in (200, 400), r.text
    assert r.status_code != 500


def test_bad_ids_and_names_are_404_not_500():
    for url in ("/api/sessions/..%2f..%2fetc", "/api/sessions/zzzz", "/guide/nope", "/api/sessions/nope/report",
                "/api/sessions/nope/report.pdf", "/files/nope/photo1.jpg", "/files/../photo1.jpg", "/api/sessions/nope/events"):
        assert client.get(url).status_code in (404, 422), url


def test_check_and_replan_on_unknown_session():
    b = io.BytesIO()
    Image.new("RGB", (50, 50)).save(b, "JPEG")
    b.seek(0)
    assert client.post("/api/sessions/nope/steps/1/check", files={"photo": ("a.jpg", b, "image/jpeg")}).status_code == 404
    assert client.post("/api/sessions/nope/replan", data={"report": "x"}).status_code == 404
    assert client.post("/api/sessions/nope/answer", data={"text": "x"}).status_code == 404
