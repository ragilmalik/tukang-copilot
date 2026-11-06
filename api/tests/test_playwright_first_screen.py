"""Real Chromium: what a first-time visitor on a phone and on a laptop sees.

- 390x844: the Go bar does not cover the 1-tap demo button; it floats once the owner starts their own repair.
- A 500 or a gateway's HTML error page gives a friendly line in the chosen language, never a JS parser message.
- My garage counts a camera-checked step as soon as it passes.
- 1280x800: the side panel links the WhatsApp simulator and the language chips are fully on screen.
"""
import pytest

pytest.importorskip("playwright.sync_api")
from api.tests.test_playwright_smoke import FIX  # noqa: E402
from api.tests.test_playwright_smoke import page, server  # noqa: E402,F401  (pytest fixtures)

pytestmark = pytest.mark.slow


def _top_element_at_demo_button(page):
    return page.evaluate("""() => { const b = document.querySelector('#demoBtn').getBoundingClientRect();
      const el = document.elementFromPoint(b.left + b.width / 2, b.top + b.height / 2); return el ? (el.closest('#demoBtn') ? 'demo' : el.className || el.tagName) : 'none'; }""")


def test_demo_button_is_not_covered_until_the_owner_starts(page):
    page.goto(page.base + "/?lang=en")
    page.wait_for_selector("#demoBtn")
    box = page.locator("#demoBtn").bounding_box()
    assert box and box["y"] + box["height"] <= 844, box  # above the fold
    assert _top_element_at_demo_button(page) == "demo"
    assert page.evaluate("getComputedStyle(document.querySelector('.actionBar')).position") != "sticky"
    page.click('#cats [data-cat="pump"]')
    page.wait_for_function("() => document.querySelector('#capture').classList.contains('armed')")
    assert page.evaluate("getComputedStyle(document.querySelector('.actionBar')).position") == "sticky"
    page.click('#cats [data-cat="pump"]')  # nothing chosen any more: the bar settles again
    page.wait_for_function("() => !document.querySelector('#capture').classList.contains('armed')")
    page.fill("#text", "my pump hums")
    page.wait_for_function("() => document.querySelector('#capture').classList.contains('armed')")


@pytest.mark.parametrize("lang,text", [("id", "Server sedang bermasalah"), ("jv", "Server lagi ana masalah"), ("en", "The server had a problem")])
def test_a_non_json_server_error_reads_as_a_sentence(page, lang, text):
    page.goto(page.base + f"/?lang={lang}")
    page.route("**/api/sessions", lambda r: r.fulfill(status=500, body="Internal Server Error", content_type="text/plain"))
    page.set_input_files("#photo", str(FIX / "sample_faucet_drip.jpg"))
    page.fill("#text", "kran netes")
    page.click("#goBtn")
    page.wait_for_function("() => document.querySelector('#formErr').textContent.length > 3", timeout=10000)
    msg = page.inner_text("#formErr")
    assert text in msg and "JSON" not in msg and "token" not in msg


def test_garage_counts_a_passed_step_at_once(page):
    page.goto(page.base + "/?lang=en")
    page.click('button.sample[data-sample="faucet"]')
    page.wait_for_selector("#result:not(.hidden)", timeout=20000)
    for x in page.locator("#preList input").all():
        x.check()
    page.set_input_files("#stepPhoto", str(FIX / "sample_faucet_hose_clamp.jpg"))
    page.wait_for_function("() => (document.querySelector('#checkResult').className || '').includes('isPass')", timeout=20000)
    got = page.evaluate("JSON.parse(localStorage.getItem('tc_garage'))[0]")
    assert got["verified"] == 1 and got["total"] >= 2, got


def test_laptop_side_panel_links_whatsapp_and_fits(page):
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(page.base + "/?lang=en")
    page.wait_for_selector("#sideWa:not(.hidden)", timeout=10000)
    assert "WhatsApp" in page.inner_text("#sideWa") and page.get_attribute("#sideWa", "href") == "/wa"
    last = page.locator(".sideLang .chip").last.bounding_box()
    assert last and last["y"] + last["height"] <= 800, last
