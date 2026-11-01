"""Small text links and summaries are still thumb-sized targets (real Chromium, 390x844)."""
import pytest

pytest.importorskip("playwright.sync_api")
import playwright.sync_api as pw  # noqa: E402

from api.tests.test_playwright_smoke import _chromium_path, server  # noqa: E402,F401  (pytest fixtures)

MIN_H = 36  # comfortable minimum for a text link; WCAG 2.2 AA asks 24, our buttons use 44

JS = """(sel) => [...document.querySelectorAll(sel)].filter((e) => {
  const r = e.getBoundingClientRect(); const s = getComputedStyle(e);
  return r.width > 0 && r.height > 0 && s.visibility !== 'hidden';
}).map((e) => [e.textContent.trim().slice(0, 30), Math.round(e.getBoundingClientRect().height)])"""


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


def _too_small(page, sel, minimum=MIN_H):
    rows = page.evaluate(JS, sel)
    assert rows, f"no visible element for {sel}"
    return [r for r in rows if r[1] < minimum]


def test_landing_links_are_thumb_sized(phone):
    phone.goto(phone.base + "/")
    phone.wait_for_selector("#demoBtn")
    assert _too_small(phone, "button.sample") == []
    assert _too_small(phone, "#videoBox", 44) == []


def test_shop_links_and_summaries_are_thumb_sized_on_the_result(phone):
    phone.goto(phone.base + "/")
    phone.click("#demoBtn")
    phone.wait_for_selector("#question:not(.hidden)", timeout=20000)
    phone.click('#quickAns button[data-q="qNo"]')
    phone.wait_for_selector("#result:not(.hidden)", timeout=20000)
    assert _too_small(phone, "a.buy") == []
    assert _too_small(phone, "#hoodTitle", 32) == []


def test_garage_entry_link_is_thumb_sized_and_themed(phone):
    phone.goto(phone.base + "/")
    phone.click('button.sample[data-sample="faucet"]')
    phone.wait_for_selector("#result:not(.hidden)", timeout=20000)
    phone.goto(phone.base + "/")
    phone.wait_for_selector("#garageList a", timeout=10000)
    assert _too_small(phone, "#garageList a") == []
    color = phone.evaluate("getComputedStyle(document.querySelector('#garageList a')).color")
    assert color != "rgb(0, 0, 238)", "garage link must not be the browser default blue"
