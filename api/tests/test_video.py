"""Video capture: a short clip becomes the 3 sharpest frames (one per third) and can carry the voice."""
import subprocess
import time

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.pipeline import media

client = TestClient(app)


def _clip(path, seconds=6, audio=True):
    args = [media.ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", f"testsrc=size=640x480:rate=15:duration={seconds}"]
    if audio:
        args += ["-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}", "-c:a", "aac"]
    subprocess.run(args + ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-shortest", str(path)], check=True)
    return path


def _wait(sid):
    for _ in range(200):
        s = client.get(f"/api/sessions/{sid}").json()
        if s["status"] in ("ready", "stopped", "needs_answer", "error"):
            return s
        time.sleep(0.05)
    raise AssertionError("timeout")


def test_extract_three_frames_spread_over_clip(tmp_path):
    frames = media.extract_frames(_clip(tmp_path / "c.mp4"), tmp_path / "out")
    assert [f.name for f in frames] == ["video_frame1.jpg", "video_frame2.jpg", "video_frame3.jpg"]
    assert len({f.read_bytes() for f in frames}) == 3          # different moments of the clip


def test_sharpest_frame_wins():
    from PIL import Image, ImageFilter
    sharp = Image.effect_mandelbrot((256, 256), (-2, -1.5, 1, 1.5), 50).convert("RGB")
    assert media.sharpness(sharp) > media.sharpness(sharp.filter(ImageFilter.GaussianBlur(4)))


def test_too_long_video_rejected(tmp_path):
    with pytest.raises(RuntimeError, match="too long"):
        media.extract_frames(_clip(tmp_path / "long.mp4", seconds=32, audio=False), tmp_path / "o")


def test_video_only_session_uses_frames_and_clip_sound(tmp_path):
    clip = _clip(tmp_path / "pump.mp4")
    with open(clip, "rb") as f:
        r = client.post("/api/sessions", data={"language": "id", "category": "pump"}, files={"video": ("pump.mp4", f, "video/mp4")})
    assert r.status_code == 200, r.text
    s = _wait(r.json()["id"])
    assert s["status"] in ("ready", "needs_answer", "stopped")
    assert len(s["photos"]) == 3


def test_photo_plus_video_capped_at_three(tmp_path):
    clip = _clip(tmp_path / "v.mp4", audio=False)
    from api.tests.test_api import _jpg
    with open(clip, "rb") as f:
        r = client.post("/api/sessions", data={"text": "kran menetes", "category": "plumbing"},
                        files=[("photos", ("a.jpg", _jpg(), "image/jpeg")), ("video", ("v.mp4", f, "video/mp4"))])
    assert r.status_code == 200, r.text
    assert len(_wait(r.json()["id"])["photos"]) == 3


def test_bad_video_is_a_clean_400(tmp_path):
    r = client.post("/api/sessions", data={"text": "x"}, files={"video": ("v.mp4", b"not a video", "video/mp4")})
    assert r.status_code == 400
