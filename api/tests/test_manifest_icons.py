import json
from pathlib import Path

WEB = Path(__file__).resolve().parents[2] / "web"


def test_manifest_icons_exist() -> None:
    m = json.loads((WEB / "manifest.webmanifest").read_text())
    for icon in m["icons"]:
        assert (WEB / icon["src"].lstrip("/")).exists(), icon["src"]
