"""Judge QA 2026-11-02 (v1.26.0), real Chromium at 390x844: what a judge saw on screen.

- A red safety stop was a dead end: no way back to try another repair except the browser's Back button.
- The stop card's "do this now" list was one generic line for every hazard ("unplug it / close the gas / stop the
  engine", "don't open the casing" for a gas leak). Gas, house wiring and brakes now get their own list.
- "💰 est. Rp25.000" sat next to items adding up to Rp55.000 (the estimate counts parts only, tools are reusable):
  the chip now says "parts".
- "Great, repair done. save Rp35.000." and "Total saved Rp35.000 from 1 repairs" read as broken English.
- The 1-tap demo left a judge on "No connection" when the page had loaded but the server then stopped answering;
  it now plays the recorded demo.
"""
from pathlib import Path

import pytest

FIX = Path(__file__).parent / "fixtures"
pytest.importorskip("playwright.sync_api")
from api.tests.test_playwright_smoke import page, server  # noqa: E402,F401  (pytest fixtures)


def _red_stop(page, text, lang="en"):
    page.goto(page.base + f"/?lang={lang}")
    page.set_input_files("#photo", str(FIX / "standin_unknown_object.jpg"))
    page.fill("#text", text)
    page.click("#goBtn")
    page.wait_for_selector("#stopAgain:not(.hidden)", timeout=20000)


def test_red_stop_has_a_way_back_to_the_first_screen(page):
    _red_stop(page, "rem motorku blong", "jv")
    btn = page.locator("#stopAgainBtn")
    assert btn.is_visible() and "Ndandani barang liya" in btn.inner_text()      # in the chosen language
    btn.click()
    page.wait_for_selector("#capture:not(.hidden)", timeout=10000)
    assert page.is_hidden("#progress")


@pytest.mark.parametrize("text,must,must_not", [
    ("My LPG gas stove hose smells of gas", "Close the regulator", "Don't open the casing"),
    ("I want to rewire my wall socket", "breaker (MCB)", "close the gas"),
    ("my brakes don't work at all", "Don't ride or drive it", "unplug it"),
])
def test_stop_card_says_what_to_do_for_that_hazard(page, text, must, must_not):
    _red_stop(page, text, "en")
    box = page.inner_text("#stopBox")
    assert must in box and must_not not in box


def test_rice_cooker_red_stop_keeps_the_general_list(page):
    page.goto(page.base + "/?lang=en")
    page.click('button.sample[data-sample="rice"]')
    page.wait_for_selector("#stopAgain:not(.hidden)", timeout=20000)
    assert "Don't open the casing" in page.inner_text("#stopBox")


def test_cost_chip_says_parts_and_outcome_reads_as_a_sentence(page):
    page.goto(page.base + "/?lang=en")
    page.click('button.sample[data-sample="faucet"]')
    page.wait_for_selector("#result:not(.hidden)", timeout=20000)
    assert page.inner_text("#gCost").startswith("💰 parts Rp")
    page.click("#fixedBtn")
    page.wait_for_function("document.querySelector('#outcomeMsg').textContent.includes('Rp')", timeout=10000)
    msg = page.inner_text("#outcomeMsg")
    assert "You saved about Rp67.000 compared with a workshop." in msg and " save Rp" not in msg
    page.click("#againBtn")
    page.wait_for_selector("#garage:not(.hidden)", timeout=10000)
    assert "from 1 repair" in page.inner_text("#garageSaved") and "1 repairs" not in page.inner_text("#garageSaved")


def test_indonesian_outcome_and_parts_chip(page):
    page.goto(page.base + "/?lang=id")
    page.click('button.sample[data-sample="faucet"]')
    page.wait_for_selector("#result:not(.hidden)", timeout=20000)
    assert page.inner_text("#gCost").startswith("💰 sparepart Rp")
    page.click("#fixedBtn")
    page.wait_for_function("document.querySelector('#outcomeMsg').textContent.includes('Rp')", timeout=10000)
    assert "Kamu hemat sekitar Rp67.000 dibanding ke bengkel." in page.inner_text("#outcomeMsg")


def test_demo_plays_the_recording_when_the_server_stops_answering(page):
    page.goto(page.base + "/?lang=en")
    page.wait_for_selector("#modeBadge:not(.hidden)")      # the page and /api/health loaded fine
    page.route("**/api/**", lambda r: r.abort())           # then the server went away
    page.click("#demoBtn")
    page.wait_for_selector("#question:not(.hidden)", timeout=30000)
    assert "Recorded demo" in page.inner_text("#modeBadge")
    assert page.inner_text("#formErr").strip() == ""
    page.click('#quickAns button[data-q="qYes"]')
    page.wait_for_selector("#result:not(.hidden)", timeout=30000)
    assert "70%" in page.inner_text("#dxCauses")           # the recording has the answer-aware demo diagnosis


def test_shared_guide_shows_the_outcome_read_only(page):
    """A viewer of someone else's /guide/<id> sees the owner's answer but has no buttons to change it."""
    page.goto(page.base + "/?lang=en")
    page.click('button.sample[data-sample="faucet"]')
    page.wait_for_selector("#result:not(.hidden)", timeout=20000)
    sid = page.evaluate("S.id")
    page.goto(page.base + f"/guide/{sid}")
    page.wait_for_selector("#stepCard", timeout=20000)
    page.wait_for_timeout(500)
    assert page.is_hidden("#fixedBtn") and page.is_hidden("#proBtn")
    assert page.is_hidden("#outcome")                      # no answer yet: nothing to show
    page.evaluate(f"fetch('/api/sessions/{sid}/outcome', {{method: 'POST', body: (() => {{ const f = new FormData(); f.append('result', 'fixed'); return f; }})()}})")
    page.wait_for_timeout(300)
    page.reload()
    page.wait_for_selector("#outcome:not(.hidden)", timeout=20000)
    assert page.is_hidden("#fixedBtn") and page.is_hidden("#proBtn")
    assert "the owner says it works again" in page.inner_text("#outcomeMsg")
    page.evaluate("sendOutcome('pro')")                    # even a direct call does nothing here
    page.wait_for_timeout(300)
    s = page.evaluate(f"fetch('/api/sessions/{sid}').then(r => r.json())")
    assert s["outcome"]["result"] == "fixed"
