"""v1.24 skeptical-judge audit fixes that do not need a browser (the browser ones are in test_playwright_audit5.py)."""
import re
from pathlib import Path

from api.pipeline import mock
from api.render.report_pdf import LABELS

WEB = Path(__file__).resolve().parents[2] / "web"


def test_a_passing_check_names_what_it_confirmed(tmp_path):
    from PIL import Image, ImageDraw

    p = tmp_path / "ok.jpg"
    im = Image.new("RGB", (200, 200), (180, 170, 160))
    ImageDraw.Draw(im).rectangle([40, 40, 160, 160], fill=(30, 30, 30))
    im.save(p)
    for lang, prefix in (("id", "Terlihat benar: "), ("jv", "Katon bener: "), ("en", "Looks right: ")):
        r = mock.step_check(p, lang, "The cap is off and the plug is visible.")
        assert r["passed"] and r["observation"] == prefix + "The cap is off and the plug is visible."
    assert mock.step_check(p, "en")["observation"] == "It matches the expected state."   # no expected state: old text


def test_pdf_never_calls_an_unfixed_cause_fixed():
    assert LABELS["en"]["fix"] == "Cause worked on"
    assert "diperbaiki" not in LABELS["id"]["fix"] and LABELS["jv"]["fix"] != LABELS["id"]["fix"]


def test_landing_thumbnail_is_a_small_language_neutral_photo_with_a_translated_caption():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    assert 'src="/static/demo-thumb.jpg"' in html and 'src="/og.png"' not in html   # og.png has Indonesian text baked in
    assert 'data-t="thumbCap"' in html
    assert (WEB / "demo-thumb.jpg").stat().st_size < 30_000


def test_new_strings_exist_in_all_three_languages():
    js = (WEB / "app.js").read_text(encoding="utf-8")
    block = js[js.index("/* I18N_REPLAY:start"):js.index("/* I18N_REPLAY:end */")]
    for key in ("planOf", "triedMark", "stopHead", "deskNote", "thumbCap"):
        assert len(re.findall(rf"\b{key}: \"", block)) == 3, key
    assert block.count("{n}") == block.count("{m}") == block.count("{cause}") == 3


def test_stop_box_sits_under_the_progress_heading():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    prog = html[html.index('<section id="progress"'):html.index("<!-- 3. Result -->")]
    assert prog.index('id="progTitle"') < prog.index('id="stopBox"') < prog.index('id="stageList"')
