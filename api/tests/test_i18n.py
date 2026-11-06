"""Every UI string exists in Basa Jawa and English, not only Bahasa Indonesia."""
import re
from pathlib import Path

JS = (Path(__file__).resolve().parents[2] / "web" / "app.js").read_text(encoding="utf-8")


def _keys(block: str) -> set[str]:
    return set(re.findall(r"(\w+): [\"{\[]", block))


def test_javanese_and_english_cover_every_indonesian_string():
    id_block = JS[JS.index("  id: {"):JS.index("  en: {")]
    en_block = JS[JS.index("  en: {"):JS.index("T.jv")]
    jv_block = JS[JS.index("T.jv = Object.assign"):]
    jv_block = jv_block[:jv_block.index("});")]
    ids = _keys(id_block) - {"id"}
    assert not ids - _keys(jv_block), sorted(ids - _keys(jv_block))
    assert not ids - _keys(en_block), sorted(ids - _keys(en_block))


def test_javanese_is_not_just_indonesian():
    jv_block = JS[JS.index("T.jv = Object.assign"):]
    for word in ("Priksa saiki", "Garasiku", "MANDHEG", "Rungokna"):
        assert word in jv_block


def test_extra_strings_exist_in_all_three_languages_and_differ():
    block = JS[JS.index("/* I18N_EXTRA:start"):JS.index("/* I18N_EXTRA:end */")]
    parts = {k: block[block.index(f"  {k}: {{"):] for k in ("id", "jv", "en")}
    keys = {}
    for k, rest in parts.items():
        body = rest[:rest.index("},\n")]
        keys[k] = dict(re.findall(r"(\w+): \"([^\"]*)\"", body))
    assert set(keys["id"]) == set(keys["jv"]) == set(keys["en"]), set(keys["id"]) ^ set(keys["jv"]) ^ set(keys["en"])
    assert len(keys["id"]) >= 40
    same_as_id = [k for k in keys["jv"] if keys["jv"][k] == keys["id"][k] and k not in {"agCode", "elapsed", "agentLive", "tourClose", "note_steps"}]
    assert not same_as_id, same_as_id  # Javanese is written out, not copied from Indonesian
    # every {placeholder} used in a template is the same in all three languages
    for k in keys["id"]:
        ph = {lg: sorted(re.findall(r"\{(\w+)\}", keys[lg][k])) for lg in keys}
        assert ph["id"] == ph["jv"] == ph["en"], (k, ph)


def _pairs(block: str) -> dict[str, str]:
    return dict(re.findall(r'(\w+): "((?:[^"\\]|\\.)*)"', block))


def test_no_english_string_shows_in_bahasa_or_basa_jawa():
    # Every label has its own Bahasa Indonesia and Basa Jawa text; none is the English one copied over
    # (Basa Jawa falls back to Bahasa Indonesia for a missing key, never to English).
    en = _pairs(JS[JS.index("  en: {"):JS.index("T.jv")])
    idb = _pairs(JS[JS.index("  id: {"):JS.index("  en: {")])
    jv_block = JS[JS.index("T.jv = Object.assign"):]
    jv = _pairs(jv_block[:jv_block.index("});")])
    same_word = {"red"}  # "STOP" on the red card is the same word in all three on purpose
    leaks = [(lang, k) for lang, table in (("id", idb), ("jv", jv)) for k, v in table.items()
             if k in en and v == en[k] and re.search(r"[A-Za-z]{4,}", v) and k not in same_word]
    assert not leaks, leaks
    only_en = set(en) - set(idb) - {"savedUnit1"}  # savedUnit1: English singular ("1 repair"); Bahasa has no plural
    assert not only_en, only_en
