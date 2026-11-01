from pathlib import Path

WEB = Path(__file__).resolve().parents[2] / "web"


def test_sw_exists_and_has_cache_name():
    text = (WEB / "sw.js").read_text()
    assert "caches" in text
    assert "fetch" in text
