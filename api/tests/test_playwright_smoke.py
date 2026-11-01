"""Browser smoke test of the main phone flow (mock backend, mobile viewport).

Skips cleanly when Playwright or a Chromium binary is missing. Chromium is found via
PLAYWRIGHT_CHROMIUM (path), Playwright's own download (`python -m playwright install chromium`),
or a system /usr/bin/chromium. Run alone: python -m pytest api/tests/test_playwright_smoke.py -q
"""
import os
import shutil
import socket
import threading
import time
from pathlib import Path

import pytest

pw = pytest.importorskip("playwright.sync_api")
FIX = Path(__file__).parent / "fixtures"


def _chromium_path():
    for p in (os.environ.get("PLAYWRIGHT_CHROMIUM"), shutil.which("chromium"), shutil.which("chromium-browser"), shutil.which("google-chrome")):
        if p and Path(p).exists():
            return p
    return None  # let Playwright try its own bundled browser


@pytest.fixture
def server():
    import uvicorn

    from api.main import app

    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    srv = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    t = threading.Thread(target=srv.run, daemon=True); t.start()
    for _ in range(100):
        if srv.started:
            break
        time.sleep(0.05)
    os.environ["NO_PROXY"] = "127.0.0.1,localhost"
    yield f"http://127.0.0.1:{port}"
    srv.should_exit = True; t.join(5)


@pytest.fixture
def page(server):
    with pw.sync_playwright() as p:
        try:
            browser = p.chromium.launch(executable_path=_chromium_path(), args=["--no-proxy-server"])
        except Exception as e:  # no browser available in this environment
            pytest.skip(f"Chromium not available: {str(e).splitlines()[0]}")
        ctx = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, locale="id-ID")
        pg = ctx.new_page()
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.base = server
        yield pg
        browser.close()
        assert not errors, errors  # no JavaScript errors anywhere in the flow


def test_main_flow_faucet_check_step(page):
    page.goto(page.base + "/")
    page.wait_for_selector("#modeBadge:not(.hidden)")              # demo mode badge shown
    page.click('button.sample[data-sample="faucet"]')
    page.wait_for_selector("#result:not(.hidden)", timeout=20000)
    assert page.is_visible("#partsImg") and page.is_visible("#stepCard")
    assert page.locator("#dxCauses li, #dxCauses > *").count() >= 1
    assert page.locator("#gMats a.buy, #gTools a.buy").count() >= 1       # marketplace price links
    assert page.is_visible("#waBtn") and page.get_attribute("#waBtn", "href").startswith("https://wa.me/")
    assert page.get_attribute("#workshopBtn", "href").endswith("/workshop.pdf")
    page.click("#hoodTitle")
    assert "sam-3.1" in page.inner_text("#hoodList") and page.locator("#hoodList li").count() >= 5
    page.set_input_files("#stepPhoto", str(FIX / "standin_faucet_hose_clamp.jpg"))
    page.wait_for_selector("#checkResult:not(.hidden)")
    page.wait_for_function("!document.querySelector('#checkResult').textContent.includes('…')", timeout=15000)
    assert page.text_content("#checkResult").strip()


def test_motor_follow_up_question(page):
    page.goto(page.base + "/")
    page.click('button.sample[data-sample="motor"]')
    page.wait_for_selector("#question:not(.hidden)", timeout=20000)
    page.fill("#answerText", "tidak bau bensin")
    page.click("#answerBtn")
    page.wait_for_selector("#result:not(.hidden)", timeout=20000)
    assert page.is_visible("#stepCard")


def test_rice_cooker_red_stop(page):
    page.goto(page.base + "/")
    page.click('button.sample[data-sample="rice"]')
    page.wait_for_selector("#stopBox:not(.hidden)", timeout=20000)
    box = page.text_content("#stopBox")
    assert "⛔" in box and "112" in box                                   # stop title + emergency line
    assert page.locator("#stopBox li").count() == 3                       # what to do right now
    maps = page.get_attribute("#stopBox a[href*='google.com/maps']", "href")
    assert maps and "query=" in maps
    pdf = page.get_attribute("#stopBox a[href$='report.pdf']", "href")
    assert page.request.get(page.base + pdf).ok                           # technician report works for a stopped job


def test_pwa_manifest_linked(page):
    page.goto(page.base + "/")
    href = page.get_attribute('link[rel="manifest"]', "href")
    assert href and page.request.get(page.base + href).ok


def test_open_weights_badge(page, monkeypatch):
    from api.settings import settings

    page.goto(page.base + "/")
    page.wait_for_selector("#modeBadge:not(.hidden)")
    assert not page.is_visible("#owBadge")                      # off by default
    monkeypatch.setattr(settings, "use_open_weights", True)
    monkeypatch.setattr(settings, "baseten_api_key", "test-baseten-key")
    page.goto(page.base + "/")
    page.wait_for_selector("#owBadge:not(.hidden)")
    assert "Muse Spark Open" in page.text_content("#owBadge")
    page.select_option("#lang", "en")
    assert "Reasoning" in page.text_content("#owBadge")       # follows the language switch


def test_video_capture_flow(page, tmp_path):
    from api.tests.test_video import _clip

    clip = _clip(tmp_path / "pump.mp4")
    page.goto(page.base + "/")
    page.set_input_files("#video", str(clip))
    assert page.text_content("#videoHint").strip()               # "Video siap ✓ ..."
    page.click('#cats [data-cat="pump"]')
    page.click("#goBtn")                                          # no photo, no text: the clip is enough
    page.wait_for_selector("#result:not(.hidden), #question:not(.hidden)", timeout=30000)


def test_tip_bar_is_compact_and_collapses_after_first_check(page):
    """v1.22.0: the demo tip bar is a corner pill (not a full-width sheet), folds to a 💡 chip after the first step
    check, can be reopened and closed, and never blocks the buttons the tips point at (clicks would fail if it did)."""
    page.goto(page.base + "/")
    page.select_option("#lang", "en")
    page.click("#demoBtn")
    page.wait_for_selector("#tourBar:not(.hidden):not(.collapsed)")
    box = page.locator("#tourBar").bounding_box()
    assert box and box["width"] <= 370 and box["height"] <= 120, box
    page.wait_for_selector("#question:not(.hidden)", timeout=20000)
    page.click('#quickAns button[data-q="qNo"]')
    page.wait_for_selector("#result:not(.hidden)", timeout=20000)
    for b in page.locator("#preList input").all():
        b.check()
    assert "collapsed" not in (page.get_attribute("#tourBar", "class") or "")
    page.click("#sampleBad")
    page.wait_for_selector("#tourBar.collapsed:not(.hidden)", timeout=15000)
    chip = page.locator("#tourBar").bounding_box()
    assert chip and chip["width"] <= 60 and chip["height"] <= 60, chip
    assert page.get_attribute("#tourToggle", "aria-expanded") == "false"
    assert page.get_attribute("#tourToggle", "aria-label") == "Show tip"
    page.click("#sampleGood")                                   # not covered by the chip
    page.wait_for_function("document.querySelector('#checkResult').textContent.includes('✅')", timeout=15000)
    page.click("#tourToggle")
    page.wait_for_selector("#tourBar:not(.collapsed)")
    assert page.get_attribute("#tourToggle", "aria-expanded") == "true" and "Still broken" in page.inner_text("#tourText")
    page.click("#tourToggle")
    page.wait_for_selector("#tourBar.collapsed")
    page.click("#tourToggle")
    page.click("#tourClose")
    page.wait_for_selector("#tourBar.hidden", state="attached")


def test_one_tap_demo_runs_the_whole_agent_loop(page):
    """v1.22 judge path: one tap, a quick answer, stand-in check photos (fail then pass), re-plan, agent log."""
    page.goto(page.base + "/")
    page.select_option("#lang", "en")
    box = page.locator("#demoBtn").bounding_box()
    assert box and box["y"] + box["height"] < 844 and box["height"] >= 44   # above the fold on a 390x844 phone, big tap target
    page.click("#demoBtn")
    page.wait_for_selector("#tourBar:not(.hidden)")
    page.wait_for_selector("#question:not(.hidden)", timeout=20000)
    assert "60%" in page.inner_text("#agentLive")                         # the log says why it asks
    page.click('#quickAns button[data-q="qNo"]')
    page.wait_for_selector("#result:not(.hidden)", timeout=20000)
    for b in page.locator("#preList input").all():
        b.check()
    page.click("#sampleBad")
    page.wait_for_function("document.querySelector('#checkResult').textContent.includes('⚠')", timeout=15000)
    page.click("#sampleGood")
    page.wait_for_function("document.querySelector('#checkResult').textContent.includes('✅')", timeout=15000)
    page.fill("#stuckText", "tried it, still dead")
    page.click("#stuckBtn")
    page.wait_for_function("document.querySelector('#stuckMsg').textContent.length > 3 && !document.querySelector('#stuckBtn').disabled", timeout=15000)
    log = page.inner_text("#agent")
    for bit in ("muse-spark-1.3", "sam-3.1", "Only 55% sure", "not yet", "correct", "Still broken: new"):
        assert bit in log, bit
    assert page.locator("#agent .agLoop .lp.on").count() >= 7


def test_tip_bar_moves_to_top_while_typing(page):
    """ffc24d8: while a text field has focus (phone keyboard open) the tip bar sits at the top, never by Send;
    it goes back to the bottom corner when the field loses focus. Checkboxes and file inputs do not move it."""
    page.goto(page.base + "/")
    page.select_option("#lang", "en")
    page.click("#demoBtn")
    page.wait_for_selector("#question:not(.hidden)", timeout=20000)
    page.wait_for_selector("#tourBar:not(.hidden)")
    low = page.locator("#tourBar").bounding_box()
    assert low and low["y"] > 844 / 2, low                     # bottom corner by default
    page.focus("#answerText")
    page.wait_for_function("document.body.classList.contains('typing')")
    top = page.locator("#tourBar").bounding_box()
    assert top and top["y"] < 60, top                          # moved to the top while typing
    ans = page.locator("#answerText").bounding_box()
    assert ans and not (top["y"] < ans["y"] + ans["height"] and ans["y"] < top["y"] + top["height"] and
                        top["x"] < ans["x"] + ans["width"] and ans["x"] < top["x"] + top["width"]) or ans["y"] > 120
    page.locator("#answerText").blur()
    page.wait_for_function("!document.body.classList.contains('typing')")
    back = page.locator("#tourBar").bounding_box()
    assert back and back["y"] > 844 / 2, back


def test_progress_screen_streams_partial_results(page, monkeypatch):
    """v1.23: while the agent works, what it saw, the SAM-outlined photo and the top cause appear one by one."""
    from api.settings import settings
    monkeypatch.setattr(settings, "mock_pace_s", 0.6)
    page.goto(page.base + "/")
    page.select_option("#lang", "en")
    page.click('button.sample[data-sample="faucet"]')
    page.wait_for_selector("#lf-look", timeout=15000)
    assert "Seen:" in page.inner_text("#lf-look") and page.locator("#progress:not(.hidden)").count() == 1
    assert page.locator("#lf-diagnose").count() == 0                       # diagnosis not there yet
    page.wait_for_selector("#lf-segment img", timeout=15000)
    page.wait_for_function("document.querySelector('#lf-segment img').naturalWidth > 0", timeout=10000)
    assert "outlined" in page.inner_text("#lf-segment")
    page.wait_for_selector("#lf-diagnose", timeout=15000)
    assert "Most likely:" in page.inner_text("#lf-diagnose") and page.locator("#progress:not(.hidden)").count() == 1
    order = page.eval_on_selector_all("#liveFind li", "els => els.map(e => e.dataset.k)")
    assert order[:3] == ["look", "segment", "diagnose"], order
    page.wait_for_selector("#result:not(.hidden)", timeout=20000)


def _in_view(page, sel, timeout=20000):
    """Waits (on the condition, not a fixed sleep) for a smooth scroll to bring the element into the viewport.
    20 s: under a loaded test run Chromium can take well over 5 s to finish a smooth scroll."""
    page.wait_for_function("(sel) => { const el = document.querySelector(sel); if (!el) return false;"
                           " const r = el.getBoundingClientRect();"
                           " return r.top >= -2 && r.top < innerHeight - 40; }", arg=sel, timeout=timeout)
    return True


def test_agent_log_lines_jump_to_what_they_describe(page):
    """v1.23: tap a line of the agent log and the stage, photo or checked step it is about scrolls into view and
    lights up. On the result page a step-check line brings that exact step back on the step card."""
    page.goto(page.base + "/")
    page.select_option("#lang", "en")
    page.click("#demoBtn")
    page.wait_for_selector("#question:not(.hidden)", timeout=20000)
    page.locator("#agentLive .agGo", has_text="Looked at the photo").click()          # progress screen
    page.wait_for_selector("#lf-look.flash, #st-look.flash", timeout=15000)
    page.click('#quickAns button[data-q="qNo"]')
    page.wait_for_selector("#result:not(.hidden)", timeout=20000)
    page.click("#tourClose")
    for b in page.locator("#preList input").all():
        b.check()
    page.click("#sampleBad")
    page.wait_for_function("document.querySelector('#checkResult').textContent.includes('⚠')", timeout=15000)
    page.click("#sampleGood")
    page.wait_for_function("document.querySelector('#stepNo').textContent.trim() === '2'", timeout=15000)  # auto-advance
    page.locator("#agent .agGo", has_text="Outlined").click()
    page.wait_for_selector("#partsWrap.flash", timeout=15000)
    assert _in_view(page, "#partsWrap")
    page.locator("#agent .agGo", has_text="Step 1 checked").first.click()
    page.wait_for_selector("#stepCard.flash", timeout=15000)
    page.wait_for_function("document.querySelector('#stepNo').textContent.trim() === '1'", timeout=15000)
    assert _in_view(page, "#stepCard")
    assert page.get_attribute("#agent .agGo", "title") == "Show it on screen"
    page.wait_for_function("document.activeElement && document.activeElement.id === 'stepCard'",
                           timeout=15000)                                              # focus follows for keyboards


def test_follow_up_question_is_brought_on_screen(page, monkeypatch):
    """v1.23 audit fix: the stage list plus streamed results push the question below the fold on a 390x844 phone,
    so the page scrolls it into view when it appears (the owner must not have to hunt for it)."""
    from api.settings import settings
    monkeypatch.setattr(settings, "mock_pace_s", 0.3)
    page.goto(page.base + "/")
    page.select_option("#lang", "en")
    page.click('button.sample[data-sample="motor"]')
    page.wait_for_selector("#question:not(.hidden)", timeout=20000)
    assert _in_view(page, "#quickAns")
