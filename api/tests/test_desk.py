"""v1.25 laptop view: phone frame + side panel (what it is, QR code, 1-tap demo, language switch). Static checks."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"
JS = (WEB / "app.js").read_text(encoding="utf-8")
HTML = (WEB / "index.html").read_text(encoding="utf-8")
CSS = (WEB / "style.css").read_text(encoding="utf-8")


def _desk_strings():
    block = JS[JS.index("/* I18N_DESK:start"):JS.index("/* I18N_DESK:end */")]
    out = {}
    for k in ("id", "jv", "en"):
        rest = block[block.index(f"  {k}: {{"):]
        out[k] = dict(re.findall(r"(\w+): \"([^\"]*)\"", rest[:rest.index("},\n")]))
    return out


def test_side_panel_strings_in_all_three_languages():
    s = _desk_strings()
    assert set(s["id"]) == set(s["jv"]) == set(s["en"])
    used = set(re.findall(r'data-t="(desk\w+)"', HTML)) - {"deskNote"}
    assert used and used <= set(s["en"]), used - set(s["en"])
    assert s["en"]["deskTag"] == "Fix it yourself, safely. In Javanese."
    assert not [k for k in s["jv"] if s["jv"][k] == s["id"][k]]          # Javanese written out, not copied


def test_markup_has_frame_side_panel_qr_demo_and_language_buttons():
    for needle in ('id="phone"', 'id="screen"', 'id="side"', 'id="qrBox"', 'id="sideDemo"', 'data-setlang="jv"', 'data-setlang="en"', 'data-setlang="id"'):
        assert needle in HTML, needle
    assert HTML.index('id="screen"') < HTML.index('<header class="top">') < HTML.index('id="tourBar"') < HTML.index('id="side"')


def test_side_panel_only_on_wide_screens_and_qr_lib_lazy():
    assert ".side{display:none}" in CSS and "@media (min-width:1024px)" in CSS
    assert "vendor/qrcode.js" not in HTML                                  # phones never download the QR encoder
    assert '"/static/vendor/qrcode.js"' in JS and "(min-width: 1024px)" in JS


def test_vendored_qr_encoder_keeps_its_mit_licence():
    lib = (WEB / "vendor" / "qrcode.js").read_text(encoding="utf-8")
    assert "Licensed under the MIT license" in lib and "Kazuhiko Arase" in lib


def test_scroll_to_top_also_moves_the_phone_screen():
    assert "function toTop()" in JS and 'sc.scrollTop = 0' in JS
    assert JS.count("window.scrollTo(0, 0)") == 1                          # only inside toTop()
