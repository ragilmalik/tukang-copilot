"""The phone Back button returns to the first screen instead of leaving the site (real Chromium, 390x844)."""
import json
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")
from api.tests.test_playwright_smoke import page, server  # noqa: E402,F401  (pytest fixtures)

DEMO = Path(__file__).resolve().parents[2] / "web" / "replay" / "demo.json"


def _visible(page, sel):
    return page.evaluate(f"!document.querySelector('{sel}').classList.contains('hidden')")


def test_back_from_progress_goes_to_first_screen_and_forward_resumes(page):
    page.goto(page.base + "/")
    page.select_option("#lang", "en")
    page.click("#demoBtn")
    page.wait_for_selector("#question:not(.hidden)", timeout=20000)
    assert page.evaluate("location.hash.length") > 1
    page.go_back()
    page.wait_for_selector("#capture:not(.hidden)", timeout=5000)
    assert page.evaluate("location.hash") == "" and _visible(page, "#capture") and not _visible(page, "#progress")
    assert page.url.startswith(page.base)                                  # still on our site, not the previous page
    page.go_forward()
    page.wait_for_selector("#progress:not(.hidden)", timeout=5000)
    page.wait_for_selector("#question:not(.hidden)", timeout=20000)        # the same repair picks up where it was


def test_back_from_result_and_forward_returns_to_the_result(page):
    page.goto(page.base + "/")
    page.select_option("#lang", "en")
    page.click("#demoBtn")
    page.wait_for_selector("#question:not(.hidden)", timeout=20000)
    page.click('#quickAns button[data-q="qNo"]')
    page.wait_for_selector("#result:not(.hidden)", timeout=20000)
    page.go_back()
    page.wait_for_selector("#capture:not(.hidden)", timeout=5000)
    assert not _visible(page, "#result")
    page.go_forward()
    page.wait_for_selector("#result:not(.hidden)", timeout=20000)
    assert page.inner_text("#dxObject").strip()


def test_start_again_lands_on_a_clean_first_screen_without_a_hash(page):
    page.goto(page.base + "/")
    page.click('button.sample[data-sample="faucet"]')
    page.wait_for_selector("#result:not(.hidden)", timeout=20000)
    page.click("#againBtn")
    page.wait_for_selector("#capture:not(.hidden)", timeout=10000)
    page.wait_for_function("() => location.hash === ''", timeout=5000)
    assert _visible(page, "#capture") and not _visible(page, "#result")


def test_back_and_forward_also_work_in_the_recorded_demo(page):
    """The recording asks the follow-up question only if the live run asked one (demo.json "asked"; since 1.33.0 the
    model was sure enough on the new photos and asked none), so wait for whichever screen the recording shows."""
    asked = json.loads(DEMO.read_text(encoding="utf-8"))["langs"]["en"]["asked"]
    first = "#question:not(.hidden)" if asked else "#result:not(.hidden)"
    page.goto(page.base + "/?replay=1")
    page.select_option("#lang", "en")
    page.click("#demoBtn")
    page.wait_for_selector(first, timeout=20000)
    page.go_back()
    page.wait_for_selector("#capture:not(.hidden)", timeout=5000)
    assert not _visible(page, "#question") and not _visible(page, "#result")
    page.go_forward()
    page.wait_for_selector("#progress:not(.hidden)", timeout=5000)
    page.wait_for_selector(first, timeout=20000)
