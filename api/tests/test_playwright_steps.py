"""v1.25.7: the 1.5 s auto-advance after a passed camera check never skips a step the owner chose, and never runs
past the last step (real Chromium, 390x844)."""
import pytest

pytest.importorskip("playwright.sync_api")
from api.tests.test_playwright_smoke import page, server  # noqa: E402,F401  (pytest fixtures)


def _open_steps(page):
    page.goto(page.base + "/")
    page.select_option("#lang", "en")
    page.click("#demoBtn")
    page.wait_for_selector("#question:not(.hidden)", timeout=20000)
    page.click('#quickAns button[data-q="qNo"]')
    page.wait_for_selector("#result:not(.hidden)", timeout=20000)
    for box in page.locator("#preList input").all():
        box.check()


def _pass_current_step(page):
    page.click("#sampleGood")
    page.wait_for_function("document.querySelector('#checkResult').textContent.includes('✅')", timeout=15000)


def test_tapping_next_right_after_a_pass_does_not_skip_a_step(page):
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    _open_steps(page)
    _pass_current_step(page)                       # step 1 passed, auto-advance is 1.5 s away
    page.click("#nextBtn")                         # the owner is faster than the timer
    assert page.inner_text("#stepTitle").startswith("2 /")
    page.wait_for_timeout(2600)
    assert page.inner_text("#stepTitle").startswith("2 /"), "the old timer moved the owner on to step 3"
    assert not errors, errors


def test_going_back_right_after_a_pass_stays_put(page):
    _open_steps(page)
    page.click("#nextBtn")                         # step 2
    _pass_current_step(page)
    page.click("#prevBtn")                         # back to step 1 before the timer fires
    page.wait_for_timeout(2600)
    assert page.inner_text("#stepTitle").startswith("1 /")


def test_auto_advance_still_happens_when_the_owner_does_nothing(page):
    _open_steps(page)
    _pass_current_step(page)
    page.wait_for_function("document.querySelector('#stepTitle').textContent.startsWith('2 /')", timeout=5000)


def test_next_on_the_last_step_after_a_pass_does_not_crash(page):
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    _open_steps(page)
    total = int(page.inner_text("#stepTitle").split("/")[1])
    for _ in range(total - 2):
        page.click("#nextBtn")                     # up to the step before the last
    _pass_current_step(page)
    page.click("#nextBtn")                         # last step, then the old timer would step past it
    page.wait_for_timeout(2600)
    assert page.inner_text("#stepTitle").startswith(f"{total} /")
    assert not errors, errors


def test_last_verified_step_brings_the_outcome_question_on_screen(page):
    _open_steps(page)
    total = int(page.inner_text("#stepTitle").split("/")[1])
    for i in range(total):
        _pass_current_step(page)
        if i < total - 1:
            page.wait_for_function(f"document.querySelector('#stepTitle').textContent.startsWith('{i + 2} /')", timeout=5000)
    page.wait_for_function("document.activeElement && document.activeElement.id === 'fixedBtn'", timeout=5000)
    assert "camera" in page.inner_text("#outcomeMsg")
    # the smooth scroll takes a moment: wait until the whole question is in view
    page.wait_for_function("(() => { const r = document.getElementById('outcome').getBoundingClientRect(); return r.top >= 0 && r.bottom <= innerHeight + 2; })()", timeout=6000)


def test_outcome_question_is_not_forced_when_steps_are_unverified_or_answered(page):
    _open_steps(page)
    total = int(page.inner_text("#stepTitle").split("/")[1])
    for _ in range(total - 1):
        page.click("#nextBtn")                     # jump to the last step without verifying the others
    _pass_current_step(page)
    page.wait_for_timeout(2400)
    assert page.inner_text("#outcomeMsg").strip() == ""


@pytest.mark.parametrize("lang,word", [("id", "Semua langkah"), ("jv", "Kabeh langkah")])
def test_outcome_prompt_is_in_the_owner_language(page, lang, word):
    page.goto(page.base + f"/?lang={lang}")
    page.click("#demoBtn")
    page.wait_for_selector("#question:not(.hidden)", timeout=20000)
    page.click('#quickAns button[data-q="qNo"]')
    page.wait_for_selector("#result:not(.hidden)", timeout=20000)
    for box in page.locator("#preList input").all():
        box.check()
    total = int(page.inner_text("#stepTitle").split("/")[1])
    for i in range(total):
        _pass_current_step(page)
        if i < total - 1:
            page.wait_for_function(f"document.querySelector('#stepTitle').textContent.startsWith('{i + 2} /')", timeout=5000)
    page.wait_for_function("document.activeElement && document.activeElement.id === 'fixedBtn'", timeout=5000)
    assert word in page.inner_text("#outcomeMsg")
