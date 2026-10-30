"""Every UI string exists in Basa Jawa and English, not only Bahasa Indonesia."""
import re
from pathlib import Path

JS = (Path(__file__).resolve().parents[2] / "web" / "app.js").read_text(encoding="utf-8")


def _keys(block: str) -> set[str]:
    return set(re.findall(r"(\w+): [\"{]", block))


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
