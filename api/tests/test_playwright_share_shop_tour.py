"""1.29.11 fixes from playing the result screen on a phone and a laptop (real Chromium).

- Price links: "🛒 Compare prices" did not say which shop, and in the two narrow columns the Tokopedia and Shopee
  links each took their own tall row. Each link is now named by its shop and both sit on one row under the item.
- Share on a laptop (no share sheet) used alert() / prompt(). It now says "Link copied:" with the link in a line
  under the button.
- In the 1-tap demo the tip bar at the bottom covered the "Found so far" findings while they came in.
"""
import pytest

pytest.importorskip("playwright.sync_api")
import playwright.sync_api as pw  # noqa: E402

from api.tests.test_playwright_smoke import _chromium_path, page, server  # noqa: E402,F401  (pytest fixtures)


def _result(pg, sample="pump", lang="en"):
    pg.goto(pg.base + f"/?lang={lang}")
    pg.click(f'button.sample[data-sample="{sample}"]')
    pg.wait_for_function("() => !document.querySelector('#result').classList.contains('hidden')"
                         " || !document.querySelector('#question').classList.contains('hidden')", timeout=20000)
    if pg.is_visible("#question"):
        pg.click('#quickAns [data-q="qYes"]')
        pg.wait_for_function("() => !document.querySelector('#result').classList.contains('hidden')", timeout=20000)


def test_shop_links_name_the_shop_and_share_one_row(page):
    _result(page)
    first = page.locator("#gTools li").first
    links = first.locator("a.buy")
    assert links.count() == 2
    assert links.nth(0).inner_text().strip().endswith("Tokopedia")
    assert links.nth(0).get_attribute("aria-label") == "Compare prices on Tokopedia"
    assert links.nth(1).inner_text().strip() == "Shopee"
    a, b = links.nth(0).bounding_box(), links.nth(1).bounding_box()
    assert abs(a["y"] - b["y"]) < 2, (a, b)                       # same row
    assert b["x"] + b["width"] <= 390                             # and nothing runs off the screen


def test_shop_link_label_in_javanese(page):
    _result(page, "faucet", "jv")
    assert page.locator("#gTools a.buy").first.get_attribute("aria-label") == "Golek rega ing Tokopedia"


@pytest.fixture()
def laptop(server):  # noqa: F811
    with pw.sync_playwright() as p:
        try:
            b = p.chromium.launch(executable_path=_chromium_path(), args=["--no-proxy-server"])
        except Exception as e:
            pytest.skip(f"Chromium not available: {str(e).splitlines()[0]}")
        ctx = b.new_context(viewport={"width": 1280, "height": 800}, locale="en-US")
        ctx.add_init_script("delete Navigator.prototype.share; delete Navigator.prototype.canShare;")
        pg = ctx.new_page()
        pg.base = server  # type: ignore[attr-defined]
        pg.dialogs = []  # type: ignore[attr-defined]
        pg.on("dialog", lambda d: (pg.dialogs.append(d.message), d.dismiss()))
        yield pg
        b.close()


def test_share_on_a_laptop_says_copied_in_a_line_not_an_alert(laptop):
    _result(laptop, "faucet")
    laptop.evaluate("() => { navigator.clipboard.writeText = () => Promise.resolve(); }")
    laptop.click("#shareBtn")
    laptop.wait_for_function("() => !document.querySelector('#shareMsg').classList.contains('hidden')", timeout=5000)
    msg = laptop.inner_text("#shareMsg")
    assert msg.startswith("✅ Link copied:") and "/guide/" in msg
    assert laptop.dialogs == []


def test_share_without_clipboard_shows_the_link_to_copy(laptop):
    _result(laptop, "faucet")
    laptop.evaluate("() => { navigator.clipboard.writeText = () => Promise.reject(new Error('no')); }")
    laptop.click("#shareBtn")
    laptop.wait_for_function("() => !document.querySelector('#shareMsg').classList.contains('hidden')", timeout=5000)
    assert laptop.inner_text("#shareMsg").startswith("Link:") and "/guide/" in laptop.inner_text(".shareUrl")
    assert laptop.dialogs == []


def test_demo_findings_are_never_under_the_tip_bar(page):
    # On a fast server the findings all land before the first frame, so replay the moment by hand: back on the
    # progress screen at the top, drop the newest finding and let the app add it again as it does mid-run.
    page.goto(page.base + "/?lang=en")
    page.wait_for_selector("#modeBadge:not(.hidden)")
    page.click("#demoBtn")
    page.wait_for_selector("#question:not(.hidden)", timeout=20000)
    page.wait_for_selector("#tourBar:not(.hidden)")
    r = page.evaluate("""() => {
        document.querySelector('#question').classList.add('hidden');
        document.querySelector('#progress').classList.remove('hidden');
        window.scrollTo(0, 0);
        const items = document.querySelectorAll('#liveFind li');
        items[items.length - 1].remove();
        const before = scrollY;
        renderPartial(S);
        const li = [...document.querySelectorAll('#liveFind li')].pop();
        return { before, after: scrollY, bottom: li.getBoundingClientRect().bottom,
                 bar: document.querySelector('#tourBar').getBoundingClientRect().top }; }""")
    assert r["after"] > r["before"], r                       # it scrolled for the new finding
    assert r["bottom"] <= r["bar"], r                        # and the finding sits above the tip bar


def test_no_scroll_for_findings_outside_the_demo(page):
    page.goto(page.base + "/?lang=en")
    page.click('button.sample[data-sample="pump"]')
    page.wait_for_selector("#result:not(.hidden)", timeout=20000)
    assert page.evaluate("() => { const y = scrollY; keepAboveTourBar(document.body); return scrollY === y; }")
