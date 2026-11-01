from pathlib import Path

INDEX = Path(__file__).resolve().parents[2] / "web" / "index.html"


def test_index_declares_default_language_and_no_em_dash() -> None:
    html = INDEX.read_text(encoding="utf-8")
    assert '<html lang="id">' in html
    assert "\u2014" not in html
