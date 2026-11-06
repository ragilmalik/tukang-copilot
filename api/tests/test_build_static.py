"""scripts/build_static.py: the static build is self-contained, relative and honest (fast checks)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import build_static  # type: ignore[import-not-found,unused-ignore]  # noqa: E402


def test_build_is_relative_complete_and_flagged(tmp_path):
    out = tmp_path / "site"
    info = build_static.build(out)
    assert build_static.verify(out) == []
    html = (out / "index.html").read_text(encoding="utf-8")
    assert "window.TC_STATIC" in html and 'href="/' not in html and 'src="/' not in html
    assert not (out / "static" / "sw.js").exists() and (out / ".nojekyll").exists()
    rec = (out / "static" / "replay" / "demo.json").read_text(encoding="utf-8")
    assert '"/static/' not in rec and json.loads(rec)["kind"] == "recorded-demo"
    assert "RECORDED" in str(info["note"])


def test_help_explains_build_try_and_host():
    h = build_static.HELP
    for s in ("Recorded demo", "never calls the API", "python -m http.server", "GitHub Pages", "Netlify", "approval"):
        assert s in h, s
    assert "\u2014" not in h


def test_dist_is_gitignored():
    assert "dist-static/" in (ROOT / ".gitignore").read_text(encoding="utf-8").split()


def test_check_mode_exits_zero(capsys):
    assert build_static.main(["--check"]) == 0
    assert "OK" in capsys.readouterr().out
