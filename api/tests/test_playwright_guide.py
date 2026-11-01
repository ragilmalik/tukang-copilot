"""The shared guide page leads with the repair, the "What the AI did" log sits after the steps (real Chromium, 390x844)."""
import time

import httpx
import pytest

pytest.importorskip("playwright.sync_api")
import playwright.sync_api as pw  # noqa: E402

from api.tests.test_playwright_smoke import _chromium_path, server  # noqa: E402,F401  (pytest fixtures)


@pytest.fixture()
def phone(server):  # noqa: F811
    with pw.sync_playwright() as p:
        try:
            b = p.chromium.launch(executable_path=_chromium_path(), args=["--no-proxy-server"])
        except Exception as e:
            pytest.skip(f"Chromium not available: {str(e).splitlines()[0]}")
        ctx = b.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, locale="en-US")
        pg = ctx.new_page()
        pg.base = server  # type: ignore[attr-defined]
        yield pg
        b.close()


def _ready_session(base: str, lang: str) -> str:
    with httpx.Client(trust_env=False, timeout=30) as c:
        sid = c.post(base + "/api/sessions", data={"sample": "faucet", "language": lang}).json()["id"]
        end = time.time() + 40
        while time.time() < end:
            s = c.get(f"{base}/api/sessions/{sid}").json()
            if s.get("status") == "ready":
                return str(sid)
            time.sleep(0.1)
    raise AssertionError("session never became ready")


@pytest.mark.parametrize("lang", ["id", "jv", "en"])
def test_guide_page_shows_the_steps_before_the_ai_log(phone, lang):
    sid = _ready_session(phone.base, lang)
    errs: list[str] = []
    phone.on("pageerror", lambda e: errs.append(str(e)))
    phone.goto(f"{phone.base}/guide/{sid}")
    phone.wait_for_selector("#result:not(.hidden)", timeout=20000)
    phone.wait_for_selector("#agent:not(.hidden)", timeout=20000)
    top = phone.evaluate("""() => ({
        step: document.querySelector('#stepCard').getBoundingClientRect().top + scrollY,
        agent: document.querySelector('#agent').getBoundingClientRect().top + scrollY,
        outcome: document.querySelector('#outcome').getBoundingClientRect().top + scrollY})""")
    assert top["step"] < top["agent"], top
    assert top["outcome"] < top["agent"], top
    # the log is still complete and its lines still work
    assert phone.locator("#agent .agList li").count() >= 5
    phone.locator("#agent .agList li").first.scroll_into_view_if_needed()
    assert errs == []


def test_main_screen_order_is_unchanged(phone):
    phone.goto(phone.base + "/")
    order = phone.evaluate("""() => { const ids = ['dxObject','agent','stepCard'];
        return ids.map(i => [...document.querySelectorAll('#result > *')].findIndex(e => e.contains(document.getElementById(i)))); }""")
    assert order == sorted(order), order
