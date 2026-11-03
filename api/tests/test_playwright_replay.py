"""Recorded demo in real Chromium: with the server unreachable, the 1-tap demo still runs end to end from
web/replay/demo.json, clearly labelled, and never fakes an answer for the visitor's own photo."""
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")
from api.tests.test_playwright_smoke import page, server  # noqa: E402,F401  (pytest fixtures)

FIX = Path(__file__).parent / "fixtures"


def _api_down(page):
    """The server sleeps: every /api call hangs past the wake timeout, then fails (static files still load)."""
    hits = []

    def handler(route):
        hits.append(route.request.url)
        page.wait_for_timeout(5000)
        try:
            route.abort()
        except Exception:
            pass
    page.route("**/api/**", handler)
    return hits


def _run_demo(page, lang):
    page.select_option("#lang", lang)
    page.click("#demoBtn")
    page.wait_for_selector("#question:not(.hidden)", timeout=20000)
    page.click('#quickAns button[data-q="qNo"]')
    page.wait_for_selector("#result:not(.hidden)", timeout=20000)
    for b in page.locator("#preList input").all():
        b.check()


def test_demo_plays_the_recording_when_the_server_sleeps(page):
    _api_down(page)
    page.goto(page.base + "/")
    page.wait_for_selector("#wakeNote:not(.hidden)", timeout=8000)        # honest note while the server wakes
    assert "recorded" in page.inner_text("#wakeNote").lower() or "rekaman" in page.inner_text("#wakeNote").lower()
    _run_demo(page, "en")
    assert "Recorded demo" in page.inner_text("#modeBadge")               # labelled on every screen
    assert page.is_visible("#partsImg")
    assert page.evaluate("document.querySelector('#partsImg').naturalWidth") > 0   # recorded SAM-marked photo loads
    page.click("#sampleBad")
    page.wait_for_function("() => document.querySelector('#checkResult').textContent.includes('⚠')", timeout=15000)
    page.click("#sampleGood")
    page.wait_for_function("() => document.querySelector('#checkResult').textContent.includes('✅')", timeout=15000)
    assert "1/4" in page.inner_text("#verifiedCount")
    assert page.get_attribute("#pdfBtn", "href") == "/static/replay/report-en.pdf"
    assert not page.is_visible("#workshopBtn")                            # not recorded: hidden, not faked
    page.fill("#stuckText", "tried it, still dead")
    page.click("#stuckBtn")
    page.wait_for_function("() => document.querySelector('#stuckMsg').textContent.length > 3 && !document.querySelector('#stuckBtn').disabled", timeout=15000)
    log = page.inner_text("#agent")
    for bit in ("muse-spark-1.3", "sam-3.1", "not yet", "correct", "Still broken: new"):
        assert bit in log, bit
    assert "Fouled spark plug" in page.inner_text("#result")


def test_own_photo_is_never_faked_in_the_recording(page):
    page.goto(page.base + "/?replay=1")
    _run_demo(page, "id")
    assert "rekaman" in page.inner_text("#modeBadge").lower()
    page.set_input_files("#stepPhoto", str(FIX / "sample_faucet_hose_clamp.jpg"))
    page.wait_for_function("() => document.querySelector('#checkResult').textContent.includes('server live')", timeout=10000)
    assert "✅" not in page.inner_text("#checkResult")


def test_forced_replay_sends_nothing_to_the_server(page):
    sent = []
    page.on("request", lambda r: sent.append(r.url) if "/api/" in r.url else None)
    page.goto(page.base + "/?replay=1")
    _run_demo(page, "jv")
    page.click("#sampleGood")
    page.wait_for_function("() => document.querySelector('#checkResult').textContent.includes('✅')", timeout=15000)
    assert not sent, sent
    assert "rekaman" in page.inner_text("#modeBadge").lower()
