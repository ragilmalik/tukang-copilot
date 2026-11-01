"""v1.25 demo video: under the 3:00 limit, opens on the hook title card with the hackathon line, shows the Muse Image
diagram step, and the scene timestamps are written for the docs."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DEMO = ROOT / "docs" / "demo"
sys.path.insert(0, str(ROOT / "scripts"))
import make_demo_assets as mda  # type: ignore[import-not-found]  # noqa: E402


def _dur(p: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(p)], capture_output=True, text=True)
    return float(json.loads(r.stdout)["format"]["duration"])


def test_title_card_first_with_hackathon_line_and_diagram_scene():
    first = mda.SCENES[0]
    assert first.key == "title" and first.min_s == 3 and "Fix it yourself, safely. In Javanese." in first.image
    assert "Built during the Meta AI Developer Hackathon, Oct 26 to Nov 4, 2026" in first.image
    keys = [s.key for s in mda.SCENES]
    assert "diagram" in keys and next(s for s in mda.SCENES if s.key == "diagram").image == "28_diagram_step"
    assert (DEMO / "screenshots" / "28_diagram_step.png").exists() and (DEMO / "screenshots" / "29_laptop.png").exists()
    assert all("image analy" not in (s.caption + s.say).lower() for s in mda.SCENES)


def test_captions_split_into_short_sentences():
    for s in mda.SCENES:
        for sent in mda._sentences(s.say):
            assert len(sent) <= 140, sent


@pytest.mark.skipif(not shutil.which("ffprobe"), reason="ffprobe not installed")
def test_videos_fit_the_limits_and_timestamps_match():
    main = _dur(DEMO / "tukang-copilot-demo.mp4")
    assert 150 < main < 180                                                 # hackathon limit is 3:00
    assert 35 < _dur(DEMO / "tukang-copilot-x-vertical.mp4") <= 46
    ts = (DEMO / "TIMESTAMPS.txt").read_text(encoding="utf-8")
    assert "0:00  title" in ts and "diagram" in ts and f"{main:.1f} s" in ts
    srt = (DEMO / "tukang-copilot-demo.en.srt").read_text(encoding="utf-8")
    assert "Muse Image draws a diagram" in srt
