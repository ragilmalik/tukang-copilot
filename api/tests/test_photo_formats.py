"""Photos from real phones: HEIC, EXIF-rotated JPEG, odd extensions, fake files."""
import io
import time
from typing import Any

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from api.main import app
from api.pipeline import photos

client = TestClient(app)


WAIT_S = 60  # seconds a repair may take: generous, CI runners are slow and earlier repairs can still hold the worker pool


def _wait(sid: str) -> dict[str, Any]:
    t0 = time.time()
    while time.time() - t0 < WAIT_S:
        s: dict[str, Any] = client.get(f"/api/sessions/{sid}").json()
        if s["status"] in ("ready", "stopped", "needs_answer", "error"):
            return s
        time.sleep(0.05)
    raise AssertionError("timeout")


def _img(fmt: str, size: tuple[int, int] = (320, 240), **kw: Any) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, (120, 90, 60)).save(buf, fmt, **kw)
    return buf.getvalue()


def _post(name: str, data: bytes, ctype: str = "image/jpeg") -> Any:
    return client.post("/api/sessions", data={"text": "motor mati", "language": "id"}, files=[("photos", (name, data, ctype))])


def test_jfif_and_uppercase_extensions_are_accepted():
    for name in ("IMG_0001.JPG", "photo.jfif", "x.JPEG"):
        r = _post(name, _img("JPEG"))
        assert r.status_code == 200, (name, r.text)
        assert _wait(r.json()["id"])["status"] != "error"


def test_exif_rotated_photo_is_straightened():
    buf = io.BytesIO()
    im = Image.new("RGB", (400, 200), (10, 200, 10))
    exif = Image.Exif()
    exif[0x0112] = 6  # rotate 90 degrees clockwise when displayed
    im.save(buf, "JPEG", exif=exif)
    r = _post("rot.jpg", buf.getvalue())
    assert r.status_code == 200
    s = _wait(r.json()["id"])
    assert s["status"] != "error"


def test_corrupt_image_gets_friendly_400_not_500():
    r = _post("broken.jpg", b"this is not a picture at all")
    assert r.status_code in (400, 422)


def test_unsupported_type_is_400():
    assert _post("doc.pdf", b"%PDF-1.4", "application/pdf").status_code == 400
    assert _post("pic.gif", _img("GIF"), "image/gif").status_code == 400


@pytest.mark.skipif(not photos.HEIF_OK, reason="pillow-heif not installed")
def test_heic_photo_is_converted_and_runs():
    buf = io.BytesIO()
    Image.new("RGB", (320, 240), (50, 80, 200)).save(buf, "HEIF")
    r = _post("IMG_1234.HEIC", buf.getvalue(), "image/heic")
    assert r.status_code == 200, r.text
    s = _wait(r.json()["id"])
    assert s["status"] != "error"
    assert s["photos"], "converted photo should be stored as a normal image"


def test_heic_without_decoder_is_refused_with_clear_message(monkeypatch):
    monkeypatch.setattr(photos, "HEIF_OK", False)
    r = _post("IMG_1.heic", b"\x00\x00\x00\x18ftypheic" + b"\x00" * 64, "image/heic")
    assert r.status_code == 400
    assert "HEIC" in r.json()["detail"] and "JPG" in r.json()["detail"]


def test_heic_check_photo_path_also_converts():
    if not photos.HEIF_OK:
        pytest.skip("pillow-heif not installed")
    sid = client.post("/api/sessions", data={"sample": "faucet", "language": "en"}).json()["id"]
    s = _wait(sid)
    assert s["status"] == "ready"
    buf = io.BytesIO()
    Image.new("RGB", (320, 240), (50, 80, 200)).save(buf, "HEIF")
    r = client.post(f"/api/sessions/{sid}/steps/1/check", files={"photo": ("c.heic", buf.getvalue(), "image/heic")})
    assert r.status_code == 200, r.text
