"""Smoothness and feedback from 1.31.0, in real Chromium: screen transitions, reduced motion, taps during a
transition, busy buttons, skeletons without layout shift, step position after a reload, no pull-to-refresh mid-repair."""
import pytest

pytest.importorskip("playwright.sync_api")
import playwright.sync_api as pw  # noqa: E402

from api.tests.test_playwright_smoke import _chromium_path, server  # noqa: E402,F401  (pytest fixtures)

# Counts calls to document.startViewTransition (and keeps the real one working).
COUNT_VT = """() => { const real = document.startViewTransition && document.startViewTransition.bind(document);
  window.__vtCalls = 0;
  if (real) document.startViewTransition = (cb) => { window.__vtCalls++; return real(cb); }; }"""


@pytest.fixture()
def browser():
    with pw.sync_playwright() as p:
        try:
            b = p.chromium.launch(executable_path=_chromium_path(), args=["--no-proxy-server"])
        except Exception as e:
            pytest.skip(f"Chromium not available: {str(e).splitlines()[0]}")
        yield b
        b.close()


def _page(browser, reduced="no-preference"):
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, locale="en-US",
                              reduced_motion=reduced)
    pg = ctx.new_page()
    pg.errors = []
    pg.on("pageerror", lambda e: pg.errors.append(str(e)))
    return pg


def _to_steps(pg, base):
    pg.goto(base + "/?lang=en")
    pg.wait_for_selector("#demoBtn")
    pg.evaluate(COUNT_VT)
    pg.click("#demoBtn")
    pg.wait_for_selector("#question:not(.hidden)", timeout=20000)
    pg.click('#quickAns button[data-q="qNo"]')
    pg.wait_for_selector("#result:not(.hidden)", timeout=20000)
    if pg.is_visible("#tourClose"):
        pg.click("#tourClose")
    for box in pg.locator("#preList input").all():
        box.check()


def test_screens_change_through_a_view_transition(browser, server):  # noqa: F811
    pg = _page(browser)
    pg.goto(server + "/?lang=en")
    pg.wait_for_selector("#demoBtn")
    pg.evaluate(COUNT_VT)
    pg.click("#demoBtn")
    pg.wait_for_selector("#question:not(.hidden)", timeout=20000)
    assert pg.evaluate("typeof document.startViewTransition") == "function"
    assert pg.evaluate("window.__vtCalls") == 1  # home -> progress
    pg.click('#quickAns button[data-q="qNo"]')
    pg.wait_for_selector("#result:not(.hidden)", timeout=20000)
    assert pg.evaluate("window.__vtCalls") == 2  # progress -> result
    # the new screen starts at its top with focus on its heading, for keyboard and screen-reader users
    pg.wait_for_function("() => document.activeElement && document.activeElement.id === 'dxObject'", timeout=5000)
    assert pg.evaluate("scrollY") == 0
    assert not pg.errors, pg.errors


def test_reduced_motion_turns_transitions_and_step_slides_off(browser, server):  # noqa: F811
    pg = _page(browser, reduced="reduce")
    _to_steps(pg, server)
    assert pg.evaluate("window.__vtCalls") == 0
    pg.click("#nextBtn")
    assert pg.inner_text("#stepTitle").startswith("2 /")
    assert pg.evaluate("document.getAnimations().filter((a) => a.playState === 'running').length") == 0
    assert pg.evaluate("getComputedStyle(document.querySelector('.stages li') || document.body).animationName") in ("none", "")
    assert not pg.errors, pg.errors


def test_next_slides_the_step_in_and_announces_it(browser, server):  # noqa: F811
    pg = _page(browser)
    _to_steps(pg, server)
    pg.click("#nextBtn")
    assert pg.inner_text("#stepTitle").startswith("2 /")  # the DOM changes at once, the slide is only paint
    assert pg.evaluate("document.getAnimations().length") >= 1
    status = pg.inner_text("#stepStatus")
    assert status.startswith("Step 2 of") and len(status) > 15, status
    pg.wait_for_function("() => document.getAnimations().every((a) => a.playState !== 'running')", timeout=3000)


def test_a_tap_during_a_screen_transition_still_reaches_its_button(browser, server):  # noqa: F811
    pg = _page(browser)
    pg.goto(server + "/?lang=en")
    pg.wait_for_selector("#demoBtn")
    pg.evaluate("() => document.getElementById('cats').scrollIntoView({block: 'center'})")
    chip = '#cats .chip[data-cat="pump"]'
    box = pg.locator(chip).bounding_box()
    pg.evaluate("() => swapView(() => {}, 'forward')")
    pg.wait_for_timeout(40)
    assert pg.evaluate("() => document.documentElement.matches(':active-view-transition')")
    pg.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    pg.wait_for_function(f"() => document.querySelector('{chip}').getAttribute('aria-pressed') === 'true'", timeout=3000)


def test_double_tap_on_the_demo_starts_one_repair_and_shows_it_is_working(browser, server):  # noqa: F811
    pg = _page(browser)
    posts: list[str] = []
    pg.on("request", lambda r: posts.append(r.url) if r.method == "POST" and r.url.endswith("/api/sessions") else None)
    pg.goto(server + "/?lang=en")
    pg.wait_for_selector("#demoBtn")
    pg.evaluate("() => { const b = document.getElementById('demoBtn'); b.click(); window.__busy = b.classList.contains('isBusy'); b.click(); }")
    pg.wait_for_selector("#question:not(.hidden)", timeout=20000)
    assert pg.evaluate("window.__busy") is True
    assert len(posts) == 1, posts
    assert pg.evaluate("document.getElementById('demoBtn').classList.contains('isBusy')") is False


def test_reload_mid_repair_returns_to_the_same_step(browser, server):  # noqa: F811
    pg = _page(browser)
    _to_steps(pg, server)
    pg.click("#nextBtn")
    pg.click("#nextBtn")
    assert pg.inner_text("#stepTitle").startswith("3 /")
    pg.reload()
    pg.wait_for_selector("#result:not(.hidden)", timeout=20000)
    assert pg.inner_text("#stepTitle").startswith("3 /")


def test_pull_to_refresh_is_off_only_during_a_repair(browser, server):  # noqa: F811
    pg = _page(browser)
    pg.goto(server + "/?lang=en")
    pg.wait_for_selector("#demoBtn")
    over = "() => getComputedStyle(document.documentElement).overscrollBehaviorY"
    assert pg.evaluate(over) == "auto"
    _to_steps(pg, server)
    assert pg.evaluate(over) == "contain"


def test_skeletons_hold_the_place_of_slow_results_without_layout_shift(browser, server, monkeypatch):  # noqa: F811
    from api.settings import settings

    monkeypatch.setattr(settings, "mock_pace_s", 0.7)  # each stage takes a moment, like a slow network
    pg = _page(browser)
    pg.goto(server + "/?lang=en")
    pg.wait_for_selector("#demoBtn")
    pg.evaluate("""() => { window.__cls = 0; window.__sk = 0;
      new PerformanceObserver((l) => l.getEntries().forEach((e) => { if (!e.hadRecentInput) window.__cls += e.value; })).observe({ type: 'layout-shift', buffered: false });
      setInterval(() => { if (document.querySelector('#liveFind li[data-sk]')) window.__sk++; }, 50); }""")
    pg.click("#demoBtn")
    pg.wait_for_selector('#liveFind li[data-sk]', state="attached", timeout=15000)
    pg.wait_for_selector('#liveFind li[data-k="segment"] img.lfImg', timeout=20000)
    pg.wait_for_selector("#question:not(.hidden)", timeout=20000)
    assert pg.evaluate("window.__sk") > 0
    # skeleton rows are aria-hidden and never carry text a screen reader would read
    assert pg.evaluate("[...document.querySelectorAll('#liveFind li[data-sk]')].every((li) => li.getAttribute('aria-hidden') === 'true')")
    cls = pg.evaluate("window.__cls")
    assert cls < 0.1, cls  # "good" CLS by the Web Vitals line


def test_running_stage_shows_its_own_seconds_and_the_model(browser, server, monkeypatch):  # noqa: F811
    from api.settings import settings

    monkeypatch.setattr(settings, "mock_pace_s", 1.2)
    pg = _page(browser)
    pg.goto(server + "/?lang=en")
    pg.wait_for_selector("#demoBtn")
    pg.click("#demoBtn")
    pg.wait_for_function("() => /\\d+ s · .+\\(.+\\)/.test(document.getElementById('elapsed').textContent)", timeout=15000)
    pg.wait_for_function("() => { const x = document.querySelector('#stageList li.running .stT'); return x && /\\d+ s/.test(x.textContent); }", timeout=15000)
    assert "a live repair usually" not in pg.inner_text("#elapsed")  # that hint is for the live server only


def test_tapping_next_does_little_work_on_the_main_thread(browser, server):  # noqa: F811
    """Interaction to Next Paint starts with the handler's own time: keep Next well under the 200 ms INP line."""
    pg = _page(browser)
    _to_steps(pg, server)
    pg.evaluate("""() => { window.__ev = [];
      new PerformanceObserver((l) => l.getEntries().forEach((e) => window.__ev.push(e.processingEnd - e.processingStart)))
        .observe({ type: 'event', durationThreshold: 16, buffered: false }); }""")
    for _ in range(3):
        pg.click("#nextBtn")
    pg.click("#prevBtn")
    pg.wait_for_timeout(300)
    worst = max(pg.evaluate("window.__ev") or [0])
    assert worst < 100, worst
