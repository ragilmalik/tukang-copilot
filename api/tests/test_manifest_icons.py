import json
from pathlib import Path

WEB = Path(__file__).resolve().parents[2] / "web"


def test_manifest_icons_exist():
    m = json.loads((WEB / "manifest.webmanifest").read_text())
    for icon in m["icons"]:
        assert (WEB / icon["src"].lstrip("/").removeprefix("static/")).exists() or (
            WEB / Path(icon["src"]).name
        ).exists() or (WEB / "icons" / Path(icon["src"]).name).exists()
