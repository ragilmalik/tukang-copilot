"""v1.25.3: the capture screen speaks the owner's language when a file is refused (real Chromium, 390x844)."""
import pytest

pytest.importorskip("playwright.sync_api")
import playwright.sync_api as pw  # noqa: E402
from PIL import Image  # noqa: E402

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


NOT_A_PHOTO = {
    "id": "Berkas itu bukan foto",
    "jv": "Berkas iku dudu foto",
    "en": "That file is not a photo",
}
UNREADABLE = {
    "id": "Foto itu tidak bisa dibaca",
    "jv": "Foto iku ora bisa diwaca",
    "en": "That photo could not be read",
}


@pytest.mark.parametrize("lang", ["id", "jv", "en"])
def test_a_non_photo_is_refused_at_once_in_the_owners_language(phone, tmp_path, lang):
    f = tmp_path / "note.txt"
    f.write_text("hello")
    phone.goto(phone.base + f"/?lang={lang}")
    phone.wait_for_selector("#photo", state="attached")
    phone.set_input_files("#photo", str(f))
    phone.wait_for_function("document.querySelector('#formErr').textContent.length > 3")
    assert NOT_A_PHOTO[lang] in phone.inner_text("#formErr")
    # nothing was kept: the preview box stays empty and Go asks for a photo again
    assert phone.evaluate("document.querySelector('#photoPreview').classList.contains('hidden')")
    phone.fill("#text", "motor mati")
    phone.click("#goBtn")
    assert "Unsupported" not in phone.inner_text("#formErr")


@pytest.mark.parametrize("lang", ["id", "jv", "en"])
def test_a_broken_photo_is_refused_by_the_server_in_the_owners_language(phone, tmp_path, lang):
    f = tmp_path / "fake.jpg"
    f.write_bytes(b"not an image")
    phone.goto(phone.base + f"/?lang={lang}")
    phone.wait_for_selector("#photo", state="attached")
    phone.set_input_files("#photo", str(f))
    phone.fill("#text", "motor mati")
    phone.click("#goBtn")
    phone.wait_for_function("document.querySelector('#formErr').textContent.length > 3")
    msg = phone.inner_text("#formErr")
    assert UNREADABLE[lang] in msg
    assert lang == "en" or "Could not read" not in msg


def test_a_good_photo_after_a_bad_one_clears_the_error(phone, tmp_path):
    bad = tmp_path / "note.txt"
    bad.write_text("hello")
    good = tmp_path / "ok.jpg"
    Image.new("RGB", (64, 64), (120, 90, 60)).save(good)
    phone.goto(phone.base + "/?lang=en")
    phone.wait_for_selector("#photo", state="attached")
    phone.set_input_files("#photo", str(bad))
    phone.wait_for_function("document.querySelector('#formErr').textContent.length > 3")
    phone.set_input_files("#photo", str(good))
    phone.wait_for_function("document.querySelector('#formErr').textContent === ''")
    assert not phone.evaluate("document.querySelector('#photoPreview').classList.contains('hidden')")


def test_unit_server_messages_map_to_keys():
    """Every refusal the API can raise for a person's mistake has a translation in all three languages."""
    import re
    from pathlib import Path

    js = (Path(__file__).resolve().parents[2] / "web" / "app.js").read_text(encoding="utf-8")
    for key in ("badFile", "unreadPhoto", "bigFile", "emptyFile", "tooLong"):
        assert len(re.findall(rf"\b{key}:", js)) == 3, key
