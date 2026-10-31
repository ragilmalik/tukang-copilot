import re
from pathlib import Path

WEB = Path(__file__).resolve().parents[2] / "web"


def test_index_local_assets_exist() -> None:
    html = (WEB / "index.html").read_text()
    refs = re.findall(r'(?:src|href)="/?([\w./-]+\.(?:js|css|png|svg|webmanifest))"', html)
    assert refs
    for ref in refs:
        assert (WEB / ref.removeprefix("static/")).exists() or ref in ("sw.js", "manifest.webmanifest"), ref
