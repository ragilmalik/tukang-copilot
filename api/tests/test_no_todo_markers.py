from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_web_has_no_debug_leftovers():
    for p in (ROOT / "web").glob("*.js"):
        t = p.read_text(encoding="utf-8")
        assert "debugger;" not in t, p.name
        assert "console.log(" not in t, p.name
