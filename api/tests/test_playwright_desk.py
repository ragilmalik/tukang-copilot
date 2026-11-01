"""Laptop view in real Chromium: phone frame + side panel at 1280x800 and 1440x900, none on a phone."""
import pytest

pw = pytest.importorskip("playwright.sync_api")
from api.tests.test_playwright_smoke import _chromium_path, server  # noqa: E402,F401  (pytest fixture)


@pytest.fixture
def browser():
    with pw.sync_playwright() as p:
        try:
            b = p.chromium.launch(executable_path=_chromium_path(), args=["--no-proxy-server"])
        except Exception as e:  # no browser available in this environment
            pytest.skip(f"Chromium not available: {str(e).splitlines()[0]}")
        yield b
        b.close()


def _open(browser, base, w, h):
    pg = browser.new_page(viewport={"width": w, "height": h})
    errors: list[str] = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(base + "/")
    return pg, errors


@pytest.mark.parametrize("size", [(1280, 800), (1440, 900)])
def test_laptop_shows_phone_frame_side_panel_and_qr(browser, server, size):  # noqa: F811
    pg, errors = _open(browser, server, *size)
    pg.wait_for_selector("#qrBox svg", timeout=5000)                     # QR drawn from the page's own address
    assert "127.0.0.1" in pg.get_attribute("#qrBox", "aria-label")
    assert pg.is_visible("#qrLocal")                                       # honest: localhost only works on this computer
    assert pg.is_visible("#side") and not pg.is_visible("#deskNote")
    ph = pg.evaluate("(() => { const r = document.getElementById('phone').getBoundingClientRect(); return [r.left, r.top, r.width, r.bottom]; })()")
    sd = pg.evaluate("(() => { const r = document.getElementById('side').getBoundingClientRect(); return [r.left, r.bottom]; })()")
    assert 380 <= ph[2] <= 440 and ph[1] >= 0 and ph[3] <= size[1]        # the whole phone fits on screen
    assert sd[0] > ph[0] + ph[2] and sd[1] <= size[1]                      # panel to the right, fully on screen
    pg.click('[data-setlang="en"]')                                        # language switch in the panel
    assert pg.input_value("#lang") == "en" and "Fix it yourself, safely." in pg.inner_text("#side")
    assert pg.get_attribute('[data-setlang="en"]', "aria-pressed") == "true"
    pg.click('[data-setlang="jv"]')
    assert "Basa Jawa" in pg.inner_text(".sideTag") and pg.evaluate("document.documentElement.lang") == "jv"
    pg.click("#sideDemo")                                                  # 1-tap demo from the panel
    pg.wait_for_selector("#question:not(.hidden)", timeout=20000)
    assert pg.evaluate("(() => { const q = document.getElementById('question').getBoundingClientRect(), p = document.getElementById('screen').getBoundingClientRect(); return q.top >= p.top && q.top < p.bottom; })()")
    assert not errors, errors


def test_phone_has_no_side_panel_and_no_qr_download(browser, server):  # noqa: F811
    pg, errors = _open(browser, server, 390, 844)
    pg.wait_for_timeout(500)
    assert not pg.is_visible("#side")
    assert pg.evaluate("!document.getElementById('qrLib') && typeof window.qrcode === 'undefined'")
    assert pg.evaluate("document.getElementById('screen').scrollHeight <= document.getElementById('screen').clientHeight + 1 || getComputedStyle(document.getElementById('screen')).overflowY === 'visible'")
    assert not errors, errors
