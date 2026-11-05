"""1.31.0 UI pass, fast file checks: motion is optional, touch is instant, first paint is light.

The behaviour itself is tested in real Chromium (test_playwright_motion.py, test_playwright_layout.py); these checks
keep the rules from quietly slipping out of the CSS, the HTML and the script.
"""
import re
from pathlib import Path

WEB = Path(__file__).resolve().parents[2] / "web"
CSS = (WEB / "style.css").read_text(encoding="utf-8")
JS = (WEB / "app.js").read_text(encoding="utf-8")
HTML = (WEB / "index.html").read_text(encoding="utf-8")
GUIDE = (WEB / "guide.html").read_text(encoding="utf-8")
SW = (WEB / "sw.js").read_text(encoding="utf-8")


def _ui_block() -> dict[str, dict[str, str]]:
    block = JS.split("/* I18N_UI:start", 1)[1].split("/* I18N_UI:end */", 1)[0]
    out: dict[str, dict[str, str]] = {}
    for lang in ("id", "jv", "en"):
        body = re.search(rf"^\s*{lang}: \{{(.*)\}},?\s*$", block, re.M)  # one line per language
        assert body, lang
        out[lang] = dict(re.findall(r'(\w+): "([^"]*)"', body.group(1)))
    return out


def test_new_strings_exist_in_all_three_languages() -> None:
    ui = _ui_block()
    assert set(ui["id"]) == set(ui["jv"]) == set(ui["en"]) == {"liveUsual", "stepSay"}
    for lang in ui:
        assert all(v.strip() for v in ui[lang].values()), lang
        assert "{n}" in ui[lang]["stepSay"] and "{m}" in ui[lang]["stepSay"] and "{text}" in ui[lang]["stepSay"]
    assert ui["jv"]["liveUsual"] != ui["id"]["liveUsual"]  # Basa Jawa, not a copy of the Indonesian line


def test_reduced_motion_switches_off_transitions_in_css_and_js() -> None:
    reduce = CSS.split("@media (prefers-reduced-motion:reduce){", 1)[1].split("\n.deskNote", 1)[0]
    assert "animation:none!important" in reduce and "transition:none!important" in reduce
    assert "::view-transition-group(*)" in reduce and "::view-transition-new(*)" in reduce
    swap = JS.split("function swapView(", 1)[1].split("\nfunction ", 1)[0]
    assert "reduceMotion()" in swap and "startViewTransition" in swap
    go = JS.split("function goStep(", 1)[1].split("\nfunction ", 1)[0]
    assert "!reduceMotion()" in go and ".animate(" in go


def test_screens_change_through_swapview_and_the_view_state_is_set_at_once() -> None:
    show = JS.split("function show(which) {", 1)[1].split("\n}\n", 1)[0]
    assert "view = which" in show.split("const update", 1)[0]  # before the (delayed) DOM update
    assert "swapView(update" in show
    # nothing decides "is this screen up?" from the .hidden class any more (it changes a frame later)
    assert not re.search(r'\$\("(capture|progress|result)"\)\.classList\.contains\("hidden"\)', JS)


def test_a_tap_during_a_transition_is_handed_to_the_control_under_it() -> None:
    assert 'document.addEventListener("pointerdown"' in JS and "lostTap" in JS and "elementFromPoint" in JS


def test_touch_rules_hands_free_nav_and_ios_zoom() -> None:
    assert "touch-action:manipulation" in CSS
    assert "grid-template-columns:58px 58px minmax(0,1fr)" in CSS
    assert "body.handsfree .nav{grid-template-columns:68px 68px minmax(0,1fr)}" in CSS
    assert ".top select{appearance:none;-webkit-appearance:none;font:600 16px" in CSS  # 16 px: no iOS zoom on focus
    assert "html.inRepair{overscroll-behavior-y:contain}" in CSS
    assert "scroll-padding-top" in CSS
    assert "env(safe-area-inset-bottom)" in CSS.split("footer{", 1)[1].split("}", 1)[0]


def test_step_picture_has_a_fixed_box() -> None:
    rule = CSS.split(".stepImg{", 1)[1].split("}", 1)[0]
    assert "aspect-ratio:4/3" in rule and "object-fit:contain" in rule


def test_first_paint_is_light() -> None:
    for page in (HTML, GUIDE):
        assert '<script src="/static/app.js" defer></script>' in page
    assert HTML.index('src="/static/replay.js" defer') < HTML.index('src="/static/app.js" defer')  # order kept
    for font in ("barlow-400", "barlow-600", "barlow-condensed-800"):
        assert f'<link rel="preload" href="/static/fonts/{font}.woff2" as="font" type="font/woff2" crossorigin>' in HTML
    faces = re.findall(r"@font-face\{[^}]*\}", CSS)
    assert faces and all("font-display:swap" in f for f in faces)
    assert 'class="demoThumb" src="/static/demo-thumb.jpg" alt="" width="640" height="320" fetchpriority="high"' in HTML
    assert 'qrcode.js' not in HTML  # the laptop QR library is fetched only on wide screens


def test_language_picker_has_a_short_form_for_narrow_headers() -> None:
    for page in (HTML, GUIDE):
        assert '<label class="langPick">' in page and 'id="langCode"' in page and '<select id="lang" aria-label="Language">' in page
    assert "@container tctop (max-width:367px)" in CSS
    assert '$("langCode").textContent = lang.toUpperCase()' in JS


def test_offline_cache_was_bumped_for_this_release() -> None:
    m = re.search(r'const CACHE = "tukang-shell-v(\d+)"', SW)
    assert m and int(m.group(1)) >= 24
