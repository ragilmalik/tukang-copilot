"""v1.24 skeptical-judge audit fixes in real Chromium (390x844 phone, and a 1280x800 laptop)."""
import pytest

pytest.importorskip("playwright.sync_api")
from api.tests.test_playwright_smoke import page, server  # noqa: E402,F401  (pytest fixtures)

VIEW_H = 844


def _in_view(page, sel):
    return page.evaluate(f"(() => {{ const r = document.querySelector('{sel}').getBoundingClientRect(); return r.top >= 0 && r.top < innerHeight; }})()")


def test_result_opens_at_the_top_and_question_gets_focus(page):
    page.goto(page.base + "/")
    page.select_option("#lang", "en")
    page.click("#demoBtn")
    page.wait_for_selector("#question:not(.hidden)", timeout=20000)
    page.wait_for_function("document.activeElement && document.activeElement.closest('#quickAns')", timeout=5000)
    page.keyboard.press("Enter")                                           # keyboard only: answers "Yes"
    page.wait_for_selector("#result:not(.hidden)", timeout=20000)
    page.wait_for_timeout(300)
    assert page.evaluate("scrollY") == 0 and _in_view(page, "#dxObject") and _in_view(page, "#safetyBadge")


def test_red_stop_is_on_screen_with_a_stop_heading(page):
    page.goto(page.base + "/")
    page.select_option("#lang", "en")
    page.click('button.sample[data-sample="rice"]')
    page.wait_for_selector("#stopBox:not(.hidden)", timeout=20000)
    page.wait_for_timeout(300)
    assert "Stopped for your safety" in page.inner_text("#progTitle") and "Checking" not in page.inner_text("#progTitle")
    assert _in_view(page, "#stopBox") and _in_view(page, "#progTitle") and page.evaluate("scrollY") == 0
    page.wait_for_selector("#stopHandoff:not(.hidden)")
    assert page.locator("#stopBox a[href$='report.pdf']").count() == 1      # one PDF button, not two


def test_replan_says_so_at_the_top(page):
    page.goto(page.base + "/")
    page.select_option("#lang", "en")
    page.click('button.sample[data-sample="faucet"]')
    page.wait_for_selector("#result:not(.hidden)", timeout=20000)
    assert not page.is_visible("#planBanner")
    for b in page.locator("#preList input").all():
        b.check()
    page.fill("#stuckText", "still drips")
    page.click("#stuckBtn")
    page.wait_for_selector("#planBanner:not(.hidden)", timeout=15000)
    assert page.inner_text("#planBanner").startswith("🔁 Plan 2 of")
    assert _in_view(page, "#planBanner")
    first = page.locator("#dxCauses li").first
    assert "tried" in (first.get_attribute("class") or "") and "tried" in first.inner_text()


def test_landing_thumbnail_and_desktop_note(page):
    page.goto(page.base + "/")
    page.select_option("#lang", "en")
    assert page.evaluate("document.querySelector('.demoThumb').naturalWidth") > 0
    assert "Stand-in sample photo" in page.inner_text(".demoFig figcaption")
    assert not page.is_visible("#deskNote")                                # a phone needs no "use a phone" note
    page.set_viewport_size({"width": 1280, "height": 800})
    assert page.is_visible("#deskNote") and "Made for phones" in page.inner_text("#deskNote")
