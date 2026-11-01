"""v1.25.1: the first-visit language follows ?lang= and the phone's language list (real Chromium)."""
import pytest

pytest.importorskip("playwright.sync_api")
import playwright.sync_api as pw  # noqa: E402

from api.tests.test_playwright_smoke import _chromium_path, server  # noqa: E402,F401  (pytest fixtures)


def _first_screen(server, langs, query="", saved=None):
    with pw.sync_playwright() as p:
        try:
            b = p.chromium.launch(executable_path=_chromium_path(), args=["--no-proxy-server"])
        except Exception as e:
            pytest.skip(f"Chromium not available: {str(e).splitlines()[0]}")
        ctx = b.new_context(viewport={"width": 390, "height": 844}, locale=langs[0])
        ctx.add_init_script(f"Object.defineProperty(navigator, 'languages', {{get: () => {langs!r}}});")
        if saved:
            ctx.add_init_script(f"try {{ localStorage.setItem('tc_lang', '{saved}') }} catch (e) {{}}")
        pg = ctx.new_page()
        pg.goto(server + "/" + query)
        pg.wait_for_selector("#demoBtn")
        out = (pg.input_value("#lang"), pg.inner_text("#demoBtn"), pg.evaluate("document.documentElement.lang"))
        b.close()
        return out


def test_english_phone_opens_in_english(server):
    v, btn, html_lang = _first_screen(server, ["en-US", "en"])
    assert v == "en" and "demo" in btn.lower() and "Jajal" not in btn and html_lang == "en"


def test_indonesian_phone_opens_in_bahasa(server):
    v, btn, _ = _first_screen(server, ["id-ID", "id"])
    assert v == "id" and "Coba" in btn


def test_indonesian_listed_after_english_still_means_bahasa(server):
    assert _first_screen(server, ["en-US", "id"])[0] == "id"


def test_javanese_phone_and_other_languages(server):
    assert _first_screen(server, ["jv-ID", "id"])[0] == "jv"
    assert _first_screen(server, ["de-DE", "de"])[0] == "en"


def test_query_param_and_saved_choice(server):
    assert _first_screen(server, ["en-US"], query="?lang=jv")[0] == "jv"
    assert _first_screen(server, ["id-ID"], query="?lang=en")[0] == "en"
    assert _first_screen(server, ["en-US"], saved="id")[0] == "id"          # an earlier choice always wins
    assert _first_screen(server, ["en-US"], query="?lang=zz")[0] == "en"    # unknown value ignored
