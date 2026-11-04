"""What I fixed after playing the re-plan and the red stop again in Basa Jawa (Chromium, 390x844).

- After "Still broken" focus stayed on the page body; it now lands on the "Plan 2 of 3" banner.
- The agent log's last line in the red stop ("hand off") picked up the white hand-off card style by accident:
  no padding, and its pale time "3s" was white on white.
- The red stop offered "nearest service" twice (stop card and hand-off card); the message preview label had
  no sign you could open it.
- My garage showed "0/4 ✓" after a re-plan, which reads as done, and did not say it was the second plan.
"""
import pytest

pytest.importorskip("playwright.sync_api")
from api.tests.test_playwright_smoke import page, server  # noqa: E402,F401  (pytest fixtures)


def _motor_replanned(page, lang):
    page.goto(page.base + f"/?lang={lang}")
    page.select_option("#lang", lang)
    page.click('button.sample[data-sample="motor"]')
    page.wait_for_function("() => !document.querySelector('#question').classList.contains('hidden')"
                           " || !document.querySelector('#result').classList.contains('hidden')", timeout=20000)
    if page.is_visible("#question"):
        page.click('#quickAns [data-q="qYes"]')
    page.wait_for_function("() => !document.querySelector('#result').classList.contains('hidden')", timeout=20000)
    page.fill("#stuckText", "isih mati")
    page.click("#stuckBtn")
    page.wait_for_function("() => !document.querySelector('#planBanner').classList.contains('hidden')", timeout=20000)


def test_focus_lands_on_the_plan_banner_after_still_broken(page):
    _motor_replanned(page, "jv")
    page.wait_for_function("() => document.activeElement && document.activeElement.id === 'planBanner'", timeout=5000)
    assert page.inner_text("#planBanner").startswith("🔁 Rencana 2 saka")
    assert page.evaluate("() => scrollY") < 200


def test_garage_says_camera_checked_and_plan_number(page):
    _motor_replanned(page, "jv")
    page.click("#againBtn")
    page.wait_for_function("() => !document.querySelector('#garage').classList.contains('hidden')", timeout=10000)
    line = page.inner_text("#garageList li")
    assert "0/4 wis dicek kamera" in line and "rencana 2: " in line
    assert "/4 ✓" not in line


def _rice_stop(page, lang="jv"):
    page.goto(page.base + f"/?lang={lang}")
    page.select_option("#lang", lang)
    page.click('button.sample[data-sample="rice"]')
    page.wait_for_function("() => !document.querySelector('#stopBox').classList.contains('hidden')", timeout=20000)
    page.wait_for_function("() => !document.querySelector('#stopHandoff').classList.contains('hidden')", timeout=10000)


def test_stop_agent_log_hand_off_line_is_a_plain_log_line(page):
    _rice_stop(page)
    page.wait_for_selector("#agentLive .agList li.handoff", timeout=10000)
    style = page.evaluate("""() => { const li = document.querySelector('#agentLive .agList li.handoff');
        const cs = getComputedStyle(li), t = getComputedStyle(li.querySelector('.agT'));
        return [cs.backgroundColor, cs.boxShadow, cs.paddingLeft, t.color]; }""")
    bg, shadow, pad, time_color = style
    assert bg in ("rgba(0, 0, 0, 0)", "transparent") and shadow == "none"
    assert pad == "0px"  # same as every other log line
    # icons on the red card are white, not blue on red
    icons = page.evaluate("() => [...document.querySelectorAll('#agentLive .agList .ic')].map(i => getComputedStyle(i).color)")
    assert icons and set(icons) == {"rgb(255, 255, 255)"}
    assert time_color != "rgb(255, 255, 255)" or bg != "rgb(255, 255, 255)"


def test_red_stop_has_one_nearest_service_button_and_an_openable_message(page):
    _rice_stop(page)
    maps = page.locator("#stopBox a[href*='google.com/maps']")
    assert maps.count() == 1
    href = maps.get_attribute("href")
    ho = page.evaluate("async () => { const id = JSON.parse(localStorage.getItem('tc_garage'))[0].id;"
                       " return (await (await fetch('/api/sessions/' + id + '/handoff')).json()).maps_url; }")
    assert href == ho                                          # the hand-off's search for the right kind of workshop
    assert page.locator("#stopHandoff a.wa").count() == 1
    summary = page.locator("#stopHandoff details summary")
    assert summary.inner_text().strip() == "Deleng pesen sing bakal dikirim"
    chevron = page.evaluate("() => getComputedStyle(document.querySelector('#stopHandoff details summary'), '::after').content")
    assert chevron not in ("none", "normal")
    summary.click()
    assert page.is_visible("#stopHandoff pre.hoText")


def test_result_hand_off_still_has_its_maps_button(page):
    page.goto(page.base + "/?lang=en")
    page.click('button.sample[data-sample="faucet"]')
    page.wait_for_selector("#result:not(.hidden)", timeout=20000)
    page.click("#mechBtn")
    page.wait_for_function("() => !document.querySelector('#handoff').classList.contains('hidden')", timeout=10000)
    assert page.locator("#handoff a[href*='google.com/maps']").count() == 1
    assert page.locator("#handoff details summary").inner_text().strip() == "See the message it sends"
