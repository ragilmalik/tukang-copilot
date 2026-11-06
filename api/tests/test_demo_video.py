"""Demo film: opens on a real problem (a labelled AI-generated scene), shows the app on recorded screens, ends on the
measured numbers and the repo link; the vertical clip has voice and music; captions, timestamps and the music credit
are written for the docs."""
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


def _probe(p: Path) -> dict:
    # A missing file used to surface as KeyError: 'format' (CI on a commit without the MP4s); say what is wrong instead.
    assert p.is_file(), f"{p.relative_to(ROOT)} is missing: commit the rendered video (scripts/make_demo_assets.py video)"
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_name,width,height,r_frame_rate",
                        "-of", "json", str(p)], capture_output=True, text=True)
    return json.loads(r.stdout)


def test_film_opens_on_the_problem_and_ends_on_the_repo():
    keys = [s.key for s in mda.SCENES]
    first = mda.SCENES[0]
    assert first.key == "hook" and first.image.startswith("broll:") and first.pre[1] and first.pre_en
    assert keys[-2:] == ["proof", "close"] and mda.REPO_URL == "github.com/ragilmalik/tukang-copilot"
    # one workflow end to end, in this order
    flow = ["home", "capture", "progress", "diagnosis", "parts", "preflight", "steps", "check_fail", "check_pass",
            "replan", "handoff", "diagram", "rice", "tyre"]
    assert [k for k in keys if k in flow] == flow
    # no hackathon framing, no screens from the previous photo set
    text = " ".join(s.caption + s.say + s.image + s.head for s in mda.SCENES + mda.VSCENES).lower()
    assert "hackathon" not in text
    for old in ("03_question", "16_live_guide", "30_whatsapp"):
        assert old not in text
    assert "question" not in keys and "live" not in keys


def test_ai_scenes_are_labelled_and_exist():
    import demo_video as dv

    assert dv.SCENE_TAG == "AI-generated scene"
    for s in mda.SCENES + mda.VSCENES:
        kind, _, ref = s.image.partition(":")
        if kind == "broll":
            assert (ROOT / ref).is_file(), ref
        if kind == "still":
            assert ref in ("cover", "poster-vertical", "thumbnail", "square"), ref
    # the intro says plainly that the screens are recorded Meta API output
    home = next(s for s in mda.SCENES if s.key == "home")
    assert "real output from Meta's models, recorded on a live run" in home.say


def test_proof_numbers_match_the_reports():
    """Every number on the proof card is in the report it names."""
    ev = (ROOT / "docs" / "EVAL.md").read_text(encoding="utf-8")
    tr = (ROOT / "docs" / "TEST_REPORT.md").read_text(encoding="utf-8")
    assert "83492.4" in ev and "$0.0437" in ev                     # median latency and cost, live column
    assert "23/23 (100%)" in ev and "10/10 (100%)" in ev           # 23 + 10 = 33 dangerous cases stopped
    assert "0 of 17 safe cases stopped" in ev
    assert "1096 passed, 0 failed, 0 skipped" in tr
    nums = [n for n, _ in mda.PROOF]
    assert nums == ["83 s", "$0.044", "33 / 33", "0 / 17", "1,096"]
    assert "earlier set" in mda.PROOF_NOTE and "earlier sample photos" in next(s for s in mda.SCENES if s.key == "proof").say


def test_captions_split_into_short_sentences():
    for s in mda.SCENES + mda.VSCENES:
        for sent in mda._sentences(s.say):
            assert len(sent) <= 140, sent


def test_spoken_forms_only_change_the_voice():
    assert mda._spoken("about $0.044") == "about four point four cents"
    assert "one thousand" in mda._spoken("1,096 automated tests")


def test_music_credit_everywhere():
    credit = mda.MUSIC_CREDIT
    assert "Lucky Acoustic" in credit and "Jesse Keller" in credit and "CC BY 3.0" in credit
    for doc in (DEMO / "README.md", ROOT / "docs" / "ATTRIBUTIONS.md", ROOT / "docs" / "launch" / "YOUTUBE.md"):
        body = doc.read_text(encoding="utf-8")
        assert "Lucky Acoustic" in body and "1540859" in body and "creativecommons.org/licenses/by/3.0" in body, doc.name
    assert "Lucky Acoustic" in (DEMO / "TIMESTAMPS.txt").read_text(encoding="utf-8")


@pytest.mark.skipif(not shutil.which("ffprobe"), reason="ffprobe not installed")
def test_videos_fit_the_limits_and_timestamps_match():
    main = _probe(DEMO / "tukang-copilot-demo.mp4")
    dur = float(main["format"]["duration"])
    assert 90 <= dur <= 150                                                  # 1:30 to 2:30
    v = next(s for s in main["streams"] if s["codec_name"] == "h264")
    assert (v["width"], v["height"]) == (1920, 1080)
    assert any(s["codec_name"] == "aac" for s in main["streams"])
    vert = _probe(DEMO / "tukang-copilot-x-vertical.mp4")
    vd = float(vert["format"]["duration"])
    assert 30 <= vd <= 45
    vv = next(s for s in vert["streams"] if s["codec_name"] == "h264")
    assert (vv["width"], vv["height"]) == (1080, 1920)
    assert any(s["codec_name"] == "aac" for s in vert["streams"])           # voice and music this time
    ts = (DEMO / "TIMESTAMPS.txt").read_text(encoding="utf-8")
    assert "0:00  hook" in ts and "  proof " in ts and f"{dur:.1f} s" in ts
    srt = (DEMO / "tukang-copilot-demo.en.srt").read_text(encoding="utf-8")
    assert "Muse Image draws a diagram" in srt and "recorded on a live run" in srt
    for f in DEMO.glob("*.mp4"):
        assert f.stat().st_size < 100 * 1024 * 1024, f.name                # GitHub refuses files over 100 MB
    gif = DEMO / "hero.gif"
    assert gif.stat().st_size < 3 * 1024 * 1024


def test_open_recorded_uses_the_sessions_owner_token(tmp_path, monkeypatch):
    """Since 1.32.0 the live guide, step checks and "Still broken" answer 403 without the owner token, so the
    screenshot scripts must read the token stored with a recorded session and put it in the page's store under the
    same key web/app.js uses (OWNER_KEY)."""
    from api.settings import settings

    sid = "abc123def456"
    (tmp_path / "sessions" / sid).mkdir(parents=True)
    (tmp_path / "sessions" / sid / "session.json").write_text(json.dumps({"id": sid, "owner_token": "tok-1"}), encoding="utf-8")
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    assert mda.owner_token(sid) == "tok-1"
    (tmp_path / "sessions" / sid / "session.json").write_text(json.dumps({"id": sid}), encoding="utf-8")
    assert mda.owner_token(sid) == ""  # an old session without a token: the page simply gets no header
    import inspect
    src = inspect.getsource(mda.open_recorded)
    app = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
    assert 'const OWNER_KEY = "tc_owner";' in app and "'tc_owner'" in src


def test_screenshot_index_lists_every_png():
    """docs/demo/screenshots/INDEX.md (scripts/make_screenshot_index.py) names every screenshot on disk."""
    shots = DEMO / "screenshots"
    index = (shots / "INDEX.md").read_text(encoding="utf-8")
    missing = [p.relative_to(shots).as_posix() for p in shots.rglob("*.png") if f"`{p.relative_to(shots).as_posix()}`" not in index]
    assert not missing, f"not in INDEX.md (run scripts/make_screenshot_index.py): {missing}"
