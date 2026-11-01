"""Names read by a screen reader (aria-label, alt) follow the chosen language (real Chromium, 390x844)."""
import pytest

pytest.importorskip("playwright.sync_api")
import playwright.sync_api as pw  # noqa: E402

from api.tests.test_playwright_smoke import _chromium_path, server  # noqa: E402,F401  (pytest fixtures)

ENGLISH = ("How it works", "Highlighted parts")
EXPECT = {
    "id": ("Cara kerjanya", "Foto dengan bagian yang ditandai"),
    "jv": ("Carane makarya", "Foto karo perangan sing ditandhani"),
    "en": ("How it works", "Photo with the parts highlighted"),
}


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


@pytest.mark.parametrize("lang", ["id", "jv", "en"])
def test_how_it_works_and_parts_picture_are_named_in_the_chosen_language(phone, lang):
    phone.goto(phone.base + "/")
    phone.select_option("#lang", lang)
    assert phone.get_attribute("ol.how", "aria-label") == EXPECT[lang][0]
    assert phone.get_attribute("#partsImg", "alt") == EXPECT[lang][1]
    phone.click("#demoBtn")
    phone.wait_for_selector("#question:not(.hidden)", timeout=20000)
    phone.click('#quickAns button[data-q="qNo"]')
    phone.wait_for_selector("#result:not(.hidden)", timeout=20000)
    assert phone.get_attribute("#partsImg", "alt") == EXPECT[lang][1]
    if lang != "en":
        assert phone.get_attribute("#partsImg", "alt") not in ENGLISH


def test_qr_box_is_named_in_the_chosen_language(phone):
    phone.goto(phone.base + "/")
    phone.select_option("#lang", "jv")
    jv = phone.get_attribute("#qrBox", "aria-label")
    phone.select_option("#lang", "en")
    en = phone.get_attribute("#qrBox", "aria-label")
    assert jv and en and jv != en and jv != "QR"


@pytest.mark.parametrize("lang,expected", [("id", "Langkah sebelumnya"), ("jv", "Langkah sadurunge"), ("en", "Previous step")])
def test_previous_step_button_has_a_spoken_name(phone, lang, expected):
    phone.goto(phone.base + "/")
    phone.select_option("#lang", lang)
    assert phone.get_attribute("#prevBtn", "aria-label") == expected
