"""axe-core on every screen in real Chromium (no serious or critical findings), one h1 on each screen, file pickers
are native inputs in the tab order, and the skipped listening stage says why in the owner's language."""
import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")
import playwright.sync_api as pw  # noqa: E402

from api.tests.test_playwright_smoke import _chromium_path, server  # noqa: E402,F401  (pytest fixtures)

pytestmark = pytest.mark.slow
ROOT = Path(__file__).resolve().parents[2]


def _axe_path() -> Path:
    """axe-core is found where jsdom is found (test_dom_jsdom.py): JSDOM_DIR, the repo's node_modules (CI), /tmp/jd."""
    for d in (os.environ.get("JSDOM_DIR"), str(ROOT), "/tmp/jd"):
        if d and (Path(d) / "node_modules" / "axe-core" / "axe.min.js").is_file():
            return Path(d) / "node_modules" / "axe-core" / "axe.min.js"
    return Path("/tmp/jd/node_modules/axe-core/axe.min.js")  # missing: the test below skips and says how to install


AXE = _axe_path()
RUN = """async () => { const r = await axe.run(document, {runOnly: ['wcag2a', 'wcag2aa', 'wcag21aa', 'best-practice']});
  return r.violations.map(v => ({id: v.id, impact: v.impact, at: v.nodes.slice(0, 3).map(n => n.target.join(' '))})); }"""


@pytest.fixture()
def phone(server):  # noqa: F811
    with pw.sync_playwright() as p:
        try:
            b = p.chromium.launch(executable_path=_chromium_path(), args=["--no-proxy-server"])
        except Exception as e:
            pytest.skip(f"Chromium not available: {str(e).splitlines()[0]}")
        ctx = b.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, locale="en-US")
        pg = ctx.new_page()
        pg.base = server  # type: ignore[attr-defined]
        yield pg
        b.close()


def _visible_h1(pg) -> list[str]:
    found: list[str] = pg.evaluate("() => [...document.querySelectorAll('h1')].filter(h => h.offsetParent !== null).map(h => h.id || h.textContent)")
    return found


def _axe(pg, name: str) -> list[str]:
    pg.evaluate(AXE.read_text(encoding="utf-8"))  # evaluate, not a <script> tag: the page's CSP blocks inline scripts
    return [f"{name}: {v['impact']} {v['id']} {v['at']}" for v in pg.evaluate(RUN) if v["impact"] in ("serious", "critical")]


def test_every_screen_has_one_h1_and_no_serious_axe_findings(phone):
    if not AXE.exists():
        pytest.skip("axe-core not installed (npm install --prefix . --no-save axe-core, or into /tmp/jd)")
    pg, base, bad = phone, phone.base, []
    pg.goto(base + "/?lang=en", wait_until="load")
    pg.wait_for_timeout(500)
    assert len(_visible_h1(pg)) == 1
    bad += _axe(pg, "home")
    pg.click("#demoBtn")
    pg.wait_for_selector("#question:not(.hidden)", timeout=30000)
    assert _visible_h1(pg) == ["progTitle"]
    bad += _axe(pg, "question")
    pg.click('#quickAns button[data-q="qNo"]')
    pg.wait_for_selector("#result:not(.hidden)", timeout=30000)
    pg.wait_for_timeout(800)
    assert _visible_h1(pg) == ["dxObject"]
    bad += _axe(pg, "result")
    pg.goto(base + "/?lang=en")
    pg.click('button.sample[data-sample="rice"]')
    pg.wait_for_selector("#stopBox:not(.hidden)", timeout=30000)
    assert _visible_h1(pg) == ["progTitle"]
    bad += _axe(pg, "stop")
    sid = pg.evaluate("() => JSON.parse(localStorage.getItem('tc_garage') || '[]').map(g => g.id)[0]")
    pg.goto(f"{base}/guide/{sid}")
    pg.wait_for_selector("#stopBox:not(.hidden)", timeout=20000)
    assert _visible_h1(pg) == ["progTitle"]
    bad += _axe(pg, "guide_stop")
    pg.goto(base + "/wa?lang=en")
    pg.wait_for_selector("#chips button")
    bad += _axe(pg, "wa")
    assert bad == []


def test_file_pickers_are_native_inputs_in_the_tab_order(phone):
    phone.goto(phone.base + "/?lang=en")
    info = phone.evaluate("""() => ['photo', 'video'].map(id => { const i = document.getElementById(id);
        return {hidden: i.hidden, role: i.closest('label').getAttribute('role'), tab: i.tabIndex}; })""")
    assert info == [{"hidden": False, "role": None, "tab": 0}] * 2
    phone.focus("#photo")
    ring = phone.evaluate("() => getComputedStyle(document.getElementById('photoBox')).outlineStyle")
    assert ring == "solid"
    inside = phone.evaluate("""() => { const i = document.getElementById('photo').getBoundingClientRect(),
        l = document.getElementById('photoBox').getBoundingClientRect();
        return i.top >= l.top && i.bottom <= l.bottom && i.left >= l.left && i.right <= l.right; }""")
    assert inside  # the 1 px input sits in its picture, so focusing it scrolls to the picture and nowhere else


@pytest.mark.parametrize("lang,stage,note", [
    ("en", "Listening", "skipped: you typed instead"),
    ("id", "Mendengarkan", "dilewati: kamu mengetik"),
    ("jv", "Ngrungokake", "diliwati: kowe ngetik"),
])
def test_typed_repair_says_why_listening_was_skipped(phone, lang, stage, note):
    phone.goto(f"{phone.base}/?lang={lang}")
    phone.click('button.sample[data-sample="faucet"]')
    phone.wait_for_selector("#st-listen .note:not(:empty)", timeout=20000)
    assert phone.inner_text("#st-listen .note") == note
    assert phone.inner_text("#st-listen").startswith(stage)


def test_axe_is_found_where_jsdom_is_found(tmp_path, monkeypatch):
    # CI installs axe-core into the repo's node_modules; a hard-coded /tmp/jd path made the axe test skip there.
    js = tmp_path / "node_modules" / "axe-core" / "axe.min.js"
    js.parent.mkdir(parents=True)
    js.write_text("/* axe */")
    monkeypatch.setenv("JSDOM_DIR", str(tmp_path))
    assert _axe_path() == js
