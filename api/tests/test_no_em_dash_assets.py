from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_web_assets_have_no_em_dash():
    bad = [
        p.name
        for p in (ROOT / "web").glob("*")
        if p.suffix in {".js", ".html", ".css", ".webmanifest"}
        and "\u2014" in p.read_text(encoding="utf-8")
    ]
    assert bad == []
