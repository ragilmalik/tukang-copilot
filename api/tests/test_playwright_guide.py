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


def _ready_owned_session(base: str, lang: str) -> tuple[str, str]:
    """A repair on its steps, plus the owner token the create call hands back (the server runs in its own process,
    so the token can't be read from the session file the way OwnerClient does)."""
    with httpx.Client(trust_env=False, timeout=30) as c:
        made = c.post(base + "/api/sessions", data={"sample": "faucet", "language": lang}).json()
        sid, token = str(made["id"]), str(made["owner_token"])
        end = time.time() + 40
        while time.time() < end:
            s = c.get(f"{base}/api/sessions/{sid}").json()
            if s.get("status") == "ready":
                return sid, token
            time.sleep(0.1)
    raise AssertionError("session never became ready")


def _ready_session(base: str, lang: str) -> str:
    return _ready_owned_session(base, lang)[0]


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


def _finished_session(base: str, sample: str, lang: str) -> str:
    with httpx.Client(trust_env=False, timeout=30) as c:
        sid = c.post(base + "/api/sessions", data={"sample": sample, "language": lang}).json()["id"]
        end = time.time() + 40
        while time.time() < end:
            if c.get(f"{base}/api/sessions/{sid}").json().get("status") not in ("created", "running"):
                return str(sid)
            time.sleep(0.1)
    raise AssertionError("session never finished")


@pytest.mark.parametrize("lang", ["id", "jv", "en"])
def test_red_stop_guide_link_shows_the_stop_card(phone, lang):
    """A shared link to a red stop used to open an empty result page (no steps, no warning)."""
    sid = _finished_session(phone.base, "rice", lang)
    errs: list[str] = []
    csp: list[str] = []
    phone.on("pageerror", lambda e: errs.append(str(e)))
    phone.on("console", lambda m: csp.append(m.text) if "Content Security Policy" in m.text else None)
    phone.goto(f"{phone.base}/guide/{sid}")
    phone.wait_for_selector("#stopBox:not(.hidden)", timeout=20000)
    assert phone.locator("#result").is_hidden()
    box = phone.inner_text("#stopBox")
    assert len(box) > 40, box
    assert errs == [] and csp == [], (errs, csp)


@pytest.mark.parametrize("lang,start", [("en", "🔁 Plan 2 of "), ("jv", "🔁 Rencana 2 saka "), ("id", "🔁 Rencana 2 dari ")])
def test_shared_guide_after_a_replan_says_which_plan(phone, lang, start):
    # 1.29.10: the shared link showed the second plan's steps with no sign the first cause had been tried
    sid, token = _ready_owned_session(phone.base, lang)
    with httpx.Client(trust_env=False, timeout=30) as c:  # "Still broken" from the owner's phone (1.32.0: owner only)
        r = c.post(f"{phone.base}/api/sessions/{sid}/replan", data={"report": "still dripping"}, headers={"X-Owner-Token": token})
        assert r.status_code == 200, r.text
    phone.goto(f"{phone.base}/guide/{sid}")
    phone.wait_for_selector("#result:not(.hidden)", timeout=20000)
    phone.wait_for_function("() => !document.querySelector('#planBanner').classList.contains('hidden')", timeout=10000)
    assert phone.inner_text("#planBanner").startswith(start)
    assert phone.locator("#dxCauses li.tried").count() == 1


def test_shared_guide_on_the_first_plan_has_no_banner(phone):
    sid = _ready_session(phone.base, "en")
    phone.goto(f"{phone.base}/guide/{sid}")
    phone.wait_for_selector("#result:not(.hidden)", timeout=20000)
    assert phone.is_hidden("#planBanner")
