"""Render web/og.png, the front page link preview (1200x630), and web/demo-thumb.jpg, the picture on the 1-tap demo
button, from a SAM-marked photo of the labelled AI-generated motorbike sample. The card says it is an AI-generated
sample photo.

Usage:
    python scripts/make_og.py --parts PATH   # a parts photo from a live run (the SAM 3.1 masks the real model drew),
                                             # e.g. the parts.jpg of a live motorbike session or the one
                                             # `make_demo_assets.py capture motor` saves as clips/parts_photo.jpg
    python scripts/make_og.py                # offline sample answers (free, no key): the demo-mode outlines
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def offline_parts() -> Path:
    """The parts photo of an offline-mode motorbike session (no model calls)."""
    os.environ.update({"OFFLINE": "1", "MOCK_PACE": "0", "NARRATION_VOICE": "0", "DATA_DIR": tempfile.mkdtemp(prefix="tc-og-")})
    from api.pipeline import engine

    s = engine.create([ROOT / "samples" / "motor.jpg"], "id", text="motor mogok", sample="motor")
    engine.run(s["id"])
    parts = engine.session_dir(s["id"]) / "parts.jpg"
    for _ in range(50):
        if parts.exists():
            break
        time.sleep(0.1)
    return parts


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--parts", type=Path, help="SAM-marked parts photo from a live run (default: an offline sample run)")
    args = ap.parse_args()
    parts = args.parts if args.parts else offline_parts()
    if not parts.is_file():
        raise SystemExit(f"no parts photo at {parts}")

    from PIL import Image

    from api.render import share_card

    out = share_card.build_home(parts, ROOT / "web" / "og.png")
    print("wrote", out.relative_to(ROOT), out.stat().st_size, "bytes")
    im = Image.open(parts).convert("RGB")
    h = min(im.height, im.width // 2)  # 2:1 band from the top: keeps the photo's "Sample photo (AI-generated)" tag
    thumb = im.crop((0, 0, im.width, h)).resize((640, 320), Image.Resampling.LANCZOS)
    out_thumb = ROOT / "web" / "demo-thumb.jpg"
    for q in (84, 78, 72, 66, 60, 55, 50):  # a real-looking photo has more detail than the old drawing: stay under 30 KB
        thumb.save(out_thumb, "JPEG", quality=q, optimize=True, progressive=True)
        if out_thumb.stat().st_size < 29_000:
            break
    print("wrote web/demo-thumb.jpg", out_thumb.stat().st_size, "bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
