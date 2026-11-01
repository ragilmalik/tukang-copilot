"""1.27.0 in real Chromium at 390x844: the owner token (backlog Q14) and the WhatsApp simulator link.

- The phone that started a repair can still answer "Does it work again?" and erase it; a second phone that only has
  the guide link gets 403 from the server even when it calls the API directly.
- The first screen links the WhatsApp simulator in the chosen language, thumb-sized, and it opens /wa.
"""
import pytest

pytest.importorskip("playwright.sync_api")
from api.tests.test_playwright_smoke import page, server  # noqa: E402,F401  (pytest fixtures)

pytestmark = pytest.mark.slow

POST_FIXED = ("(sid) => fetch(`/api/sessions/${sid}/outcome`, {method: 'POST', body: (() => { const f = new FormData();"
              " f.append('result', 'fixed'); return f; })()}).then((r) => r.status)")


def test_owner_answers_but_another_phone_with_the_link_cannot(page):
    page.goto(page.base + "/?lang=en")
    page.click('button.sample[data-sample="faucet"]')
    page.wait_for_selector("#result:not(.hidden)", timeout=20000)
    sid = page.evaluate("S.id")
    assert page.evaluate(f"!!JSON.parse(localStorage.getItem('tc_owner'))['{sid}']")
    # a second phone: fresh browser context, same server, only the guide link
    other = page.context.browser.new_context(viewport={"width": 390, "height": 844})
    op = other.new_page()
    op.goto(page.base + f"/guide/{sid}")
    op.wait_for_selector("#stepCard", timeout=20000)
    assert op.evaluate(POST_FIXED, sid) == 403
    assert op.evaluate(f"fetch('/api/sessions/{sid}', {{method: 'DELETE'}}).then((r) => r.status)") == 403
    other.close()
    # the owner's own button still works
    page.click("#fixedBtn")
    page.wait_for_function("document.querySelector('#outcomeMsg').textContent.includes('Rp')", timeout=10000)
    assert "You saved about" in page.inner_text("#outcomeMsg")


@pytest.mark.parametrize("lang,text", [("id", "Coba juga lewat WhatsApp"), ("jv", "Jajal uga lewat WhatsApp"),
                                       ("en", "Also works in WhatsApp")])
def test_first_screen_links_the_whatsapp_simulator(page, lang, text):
    page.goto(page.base + f"/?lang={lang}")
    page.wait_for_selector("#waSim:not(.hidden)", timeout=10000)
    link = page.locator("#waSimLink")
    assert text in link.inner_text()
    box = link.bounding_box()
    assert box and box["height"] >= 44
    link.click()
    page.wait_for_url("**/wa", timeout=10000)
