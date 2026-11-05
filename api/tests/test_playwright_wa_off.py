"""With a live key and no WA_SIM=1 the simulator API is off (404), but /wa still opens if someone types the address.
It used to let a visitor type and then answered "Not Found" in the chat. Now it says the simulator is off, in the
visitor's language, and the composer is disabled."""
import pytest

pytest.importorskip("playwright.sync_api")
import playwright.sync_api as pw  # noqa: E402

from api.settings import settings  # noqa: E402
from api.tests.test_playwright_smoke import _chromium_path  # noqa: E402
from api.tests.test_playwright_wa import server  # noqa: E402,F401  (fixture)

pytestmark = pytest.mark.slow


@pytest.mark.parametrize("lang,word", [("id", "mati"), ("jv", "dipateni"), ("en", "switched off")])
def test_simulator_page_says_it_is_off(server, monkeypatch, lang, word):  # noqa: F811
    monkeypatch.setattr(settings, "mock", False)
    monkeypatch.setattr(settings, "meta_api_key", "x" * 12)  # never used: the simulator refuses before any call
    monkeypatch.setattr(settings, "wa_sim", False)
    with pw.sync_playwright() as p:
        try:
            b = p.chromium.launch(executable_path=_chromium_path(), args=["--no-proxy-server"])
        except Exception as e:
            pytest.skip(f"Chromium not available: {str(e).splitlines()[0]}")
        pg = b.new_page(viewport={"width": 390, "height": 844})
        errs: list[str] = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(f"{server}/wa?lang={lang}")
        pg.wait_for_function("() => document.querySelector('#text').disabled", timeout=8000)
        assert word in pg.inner_text("#simLabel")
        assert pg.eval_on_selector_all("#chips button", "bs => bs.length > 0 && bs.every(b => b.disabled)")
        assert "Not Found" not in pg.inner_text("#log")
        assert not errs
        b.close()
