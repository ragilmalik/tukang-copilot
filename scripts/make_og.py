"""Render web/og.png, the front page link preview (1200x630), from a demo-mode motorbike session so the card shows
real SAM-style outlines. Demo data: the photo is a labelled stand-in and the card says so.
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

from api.pipeline import engine, mock  # noqa: E402
from api.render import share_card  # noqa: E402


def main() -> int:
    photos = mock.make_sample_photos(Path(os.environ["DATA_DIR"]) / "samples")
    s = engine.create([photos["motor"]], "id", text="motor mogok", sample="motor")
    engine.run(s["id"])
    for _ in range(50):
        if (engine.session_dir(s["id"]) / "parts.jpg").exists():
            break
        time.sleep(0.1)
    out = share_card.build_home(engine.session_dir(s["id"]) / "parts.jpg", ROOT / "web" / "og.png")
    print("wrote", out.relative_to(ROOT), out.stat().st_size, "bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
