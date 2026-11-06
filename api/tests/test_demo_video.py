"""Demo video: under the 3:00 limit, opens on the hook title card with the hackathon line, shows the Muse Image
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
    # A missing file used to surface as KeyError: 'format' (CI on a commit without the MP4s); say what is wrong instead.
    assert p.is_file(), f"{p.relative_to(ROOT)} is missing: commit the rendered video (scripts/make_demo_assets.py video)"
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(p)], capture_output=True, text=True)
    return float(json.loads(r.stdout)["format"]["duration"])


def test_title_card_first_with_hackathon_line_and_diagram_scene():
    first = mda.SCENES[0]
    assert first.key == "title" and first.min_s == 3 and "Fix it yourself, safely. In Javanese." in first.image
    assert "Built during the Meta AI Developer Hackathon, Oct 26 to Nov 4, 2026" in first.image
    keys = [s.key for s in mda.SCENES]
    assert "diagram" in keys and next(s for s in mda.SCENES if s.key == "diagram").image == "28_diagram_step"
    assert (DEMO / "screenshots" / "28_diagram_step.png").exists() and (DEMO / "screenshots" / "29_laptop.png").exists()
    for rec in (False, True):
        assert all("image analy" not in (s.caption + s.say).lower() for s in mda.scenes(rec))


def test_captions_split_into_short_sentences():
    for rec in (False, True):
        for s in mda.scenes(rec):
            for sent in mda._sentences(s.say):
                assert len(sent) <= 140, sent


def test_intro_says_where_the_answers_come_from():
    """Live filming says the answers are live; played-back answers are called recorded, never live."""
    live = next(s for s in mda.scenes(False) if s.key == "intro").say
    rec = next(s for s in mda.scenes(True) if s.key == "intro").say
    assert "live from Meta's models" in live
    assert "recorded on a live run" in rec and "live from" not in rec
    assert next(s for s in mda.SCENES if s.key == "intro").say == ""  # only scenes() gives the line, so no mode is forgotten


@pytest.mark.skipif(not shutil.which("ffprobe"), reason="ffprobe not installed")
def test_videos_fit_the_limits_and_timestamps_match():
    main = _dur(DEMO / "tukang-copilot-demo.mp4")
    assert 150 < main < 180                                                 # hackathon limit is 3:00
    assert 35 < _dur(DEMO / "tukang-copilot-x-vertical.mp4") <= 46
    ts = (DEMO / "TIMESTAMPS.txt").read_text(encoding="utf-8")
    assert "0:00  title" in ts and "diagram" in ts and f"{main:.1f} s" in ts
    srt = (DEMO / "tukang-copilot-demo.en.srt").read_text(encoding="utf-8")
    assert "Muse Image draws a diagram" in srt


def test_whatsapp_scene_in_javanese_with_its_screenshots():
    """A ~12 s WhatsApp scene (simulator, Basa Jawa): marked photo + diagnosis, step buttons, red stop."""
    sc = next(s for s in mda.SCENES if s.key == "wa")
    names = sc.image[3:].split(",")
    assert sc.image.startswith("wa:") and names == ["30_whatsapp_jv_diagnosis", "30_whatsapp_jv_steps", "30_whatsapp_jv_redstop"]
    for n in mda.WA_SHOTS:
        assert (DEMO / "screenshots" / f"{n}.png").exists(), n
    assert "WhatsApp" in sc.caption and "Basa Jawa" in sc.caption and "red stop" in sc.say
    keys = [s.key for s in mda.SCENES]
    assert keys.index("rice") < keys.index("wa") < keys.index("arch")
    assert "  wa " in (DEMO / "TIMESTAMPS.txt").read_text(encoding="utf-8")
    assert "30_whatsapp_jv_diagnosis" in mda.GIF_SHOTS
