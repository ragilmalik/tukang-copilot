"""Nothing pokes out of its card, and the page never scrolls sideways (real Chromium).

Checked on each main screen at the three phone sizes I design for (360x740, 390x844, 430x932) and in the laptop
phone frame (1280x800). Before 1.31.0 the hands-free "Lanjut" button stuck out of the step card, and at 360 px the
language picker covered the app name.
"""
import pytest

pytest.importorskip("playwright.sync_api")
import playwright.sync_api as pw  # noqa: E402

from api.tests.test_playwright_smoke import _chromium_path, server  # noqa: E402,F401  (pytest fixtures)

# Every visible element is checked against its nearest card-like box and its card.
OVERFLOW_JS = r"""() => {
  const C = '.card,.actions,.demoPlate,.stop,.live,.outcome,.voiceBar,.sampleCheck,#question,.liveFind,.tourBar,.safety,.preflight,.timer,div.handoff,.nav,.actionBar,.photoBox,header.top';
  const vis = (e) => { const r = e.getBoundingClientRect(), s = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && !e.closest('.hidden,.sr-only,.eg,#tcIcons'); };
  const name = (x) => x.tagName.toLowerCase() + (x.id ? '#' + x.id : '');
  const out = [];
  const desk = innerWidth >= 1024, scr = document.getElementById('screen'), root = document.scrollingElement;
  if (!desk && root.scrollWidth > innerWidth + 0.5) out.push('page scrolls sideways: ' + root.scrollWidth);
  if (desk && scr.scrollWidth > scr.clientWidth + 0.5) out.push('phone frame scrolls sideways: ' + scr.scrollWidth);
  for (const e of document.querySelectorAll('body *')) {
    if (!vis(e) || !e.parentElement) continue;
    for (const c of [e.parentElement.closest(C), e.parentElement.closest('.card,.actions,.demoPlate,main')]) {
      if (!c) continue;
      const r = e.getBoundingClientRect(), cr = c.getBoundingClientRect();
      const over = Math.max(r.right - cr.right, cr.left - r.left);
      if (over > 0.5) out.push(name(e) + ' sticks out of ' + name(c) + ' by ' + over.toFixed(1) + 'px');
    }
  }
  return [...new Set(out)];
}"""

HEADER_JS = """() => {
  const b = document.querySelector('header.top .brand b'), p = document.querySelector('header.top .langPick');
  const a = b.getBoundingClientRect(), c = p.getBoundingClientRect();
  return { gap: c.left - a.right, truncated: b.scrollWidth > b.clientWidth + 1 };
}"""


def _browser(p):
    try:
        return p.chromium.launch(executable_path=_chromium_path(), args=["--no-proxy-server"])
    except Exception as e:  # no browser here
        pytest.skip(f"Chromium not available: {str(e).splitlines()[0]}")


def _walk(pg, base, lang):
    """Yields (screen name) after reaching each main screen."""
    pg.goto(f"{base}/?lang={lang}")
    pg.wait_for_selector("#demoBtn")
    yield "home"
    pg.click("#demoBtn")
    pg.wait_for_selector("#question:not(.hidden)", timeout=20000)
    yield "question"
    pg.click('#quickAns button[data-q="qNo"]')
    pg.wait_for_selector("#result:not(.hidden)", timeout=20000)
    if pg.is_visible("#tourClose"):
        pg.click("#tourClose")
    for box in pg.locator("#preList input").all():
        box.check()
    yield "steps"
    pg.check("#handsFree")
    pg.wait_for_function("() => document.body.classList.contains('handsfree')")
    yield "hands-free"
    pg.uncheck("#handsFree")
    pg.click('#againBtn')
    pg.wait_for_selector("#capture:not(.hidden)", timeout=10000)
    pg.click('button.sample[data-sample="rice"]')
    pg.wait_for_selector("#progress.isStop", timeout=20000)
    yield "red stop"


@pytest.mark.parametrize("w,h,lang,scheme", [(360, 740, "id", "light"), (390, 844, "jv", "dark"), (430, 932, "en", "light"),
                                             (1280, 800, "id", "dark")])
def test_no_element_sticks_out_of_its_card(server, w, h, lang, scheme):  # noqa: F811
    with pw.sync_playwright() as p:
        b = _browser(p)
        phone = w < 1024
        ctx = b.new_context(viewport={"width": w, "height": h}, is_mobile=phone, has_touch=phone, color_scheme=scheme)
        pg = ctx.new_page()
        errors: list[str] = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        problems = {}
        for screen in _walk(pg, server, lang):
            pg.wait_for_timeout(250)  # a screen change finishes its 200 ms transition
            found = pg.evaluate(OVERFLOW_JS)
            if found:
                problems[screen] = found
            hd = pg.evaluate(HEADER_JS)
            if hd["gap"] < 4 or hd["truncated"]:
                problems.setdefault(screen, []).append(f"header: app name and language picker collide {hd}")
        b.close()
    assert not problems, problems
    assert not errors, errors


def test_hands_free_next_button_fits_its_card_at_360(server):  # noqa: F811
    """The 1.30 bug: in hands-free mode the enlarged Next ("Lanjut") stuck out past the step card."""
    with pw.sync_playwright() as p:
        b = _browser(p)
        pg = b.new_context(viewport={"width": 360, "height": 740}, is_mobile=True, has_touch=True).new_page()
        pg.goto(server + "/?lang=id")
        pg.click("#demoBtn")
        pg.wait_for_selector("#question:not(.hidden)", timeout=20000)
        pg.click('#quickAns button[data-q="qNo"]')
        pg.wait_for_selector("#result:not(.hidden)", timeout=20000)
        for box in pg.locator("#preList input").all():
            box.check()
        pg.check("#handsFree")
        r = pg.evaluate("""() => { const c = document.getElementById('stepCard').getBoundingClientRect(),
          n = document.getElementById('nextBtn').getBoundingClientRect(), pad = parseFloat(getComputedStyle(document.getElementById('stepCard')).paddingRight);
          return { cardInner: c.right - pad, next: n.right, h: n.height, w: n.width }; }""")
        b.close()
    assert r["next"] <= r["cardInner"] + 0.5, r
    assert r["h"] >= 68 and r["w"] >= 120, r  # still the big hands-free target


def test_language_pill_on_a_narrow_phone_still_switches_language(server):  # noqa: F811
    with pw.sync_playwright() as p:
        b = _browser(p)
        pg = b.new_context(viewport={"width": 360, "height": 740}, is_mobile=True, has_touch=True).new_page()
        pg.goto(server + "/?lang=id")
        pg.wait_for_selector("#demoBtn")
        assert pg.inner_text("#langCode") == "ID"
        assert pg.evaluate("getComputedStyle(document.querySelector('.langShort')).display") != "none"
        size = pg.evaluate("() => { const r = document.getElementById('lang').getBoundingClientRect(); return [r.width, r.height]; }")
        assert size[0] >= 44 and size[1] >= 44, size  # the invisible select covers the whole pill: a full-size target
        pg.select_option("#lang", "jv")
        pg.wait_for_function("() => document.getElementById('langCode').textContent === 'JV'")
        assert pg.inner_text("#capture h1") == "Apa sing rusak?"
        wide = b.new_context(viewport={"width": 430, "height": 932}, is_mobile=True, has_touch=True).new_page()
        wide.goto(server + "/?lang=id")
        wide.wait_for_selector("#demoBtn")
        assert wide.evaluate("getComputedStyle(document.querySelector('.langShort')).display") == "none"
        assert wide.evaluate("getComputedStyle(document.getElementById('lang')).opacity") == "1"
        b.close()
