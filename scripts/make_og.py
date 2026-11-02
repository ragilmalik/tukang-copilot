"""Render web/og.png, the front page link preview (1200x630), and web/demo-thumb.jpg, the picture on the 1-tap demo
button, from a demo-mode motorbike session so both show the SAM-style outlines. Demo data: the photo is a labelled AI-generated sample and the card says so.
Usage: python scripts/make_og.py"""
from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.update({"MOCK": "1", "MOCK_PACE": "0", "NARRATION_VOICE": "0", "DATA_DIR": tempfile.mkdtemp(prefix="tc-og-")})

from PIL import Image  # noqa: E402

from api.pipeline import engine  # noqa: E402
from api.render import share_card  # noqa: E402


def main() -> int:
    s = engine.create([ROOT / "samples" / "motor.jpg"], "id", text="motor mogok", sample="motor")
    engine.run(s["id"])
    parts = engine.session_dir(s["id"]) / "parts.jpg"
    for _ in range(50):
        if parts.exists():
            break
        time.sleep(0.1)
    out = share_card.build_home(parts, ROOT / "web" / "og.png")
    print("wrote", out.relative_to(ROOT), out.stat().st_size, "bytes")
    im = Image.open(parts).convert("RGB")
    h = im.width // 2  # 2:1 band from just above the plug cap down into the air filter box
    top = min(max(0, int(im.height * 0.14)), im.height - h)
    thumb = im.crop((0, top, im.width, top + h)).resize((640, 320), Image.Resampling.LANCZOS)
    out_thumb = ROOT / "web" / "demo-thumb.jpg"
    for q in (84, 78, 72, 66, 60, 55, 50):  # a real-looking photo has more detail than the old drawing: stay under 30 KB
        thumb.save(out_thumb, "JPEG", quality=q, optimize=True, progressive=True)
        if out_thumb.stat().st_size < 29_000:
            break
    print("wrote web/demo-thumb.jpg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
