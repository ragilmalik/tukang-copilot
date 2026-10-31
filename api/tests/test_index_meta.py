from pathlib import Path

HTML = (Path(__file__).resolve().parents[2] / "web" / "index.html").read_text()


def test_viewport_and_manifest_present():
    assert 'name="viewport"' in HTML
    assert 'rel="manifest"' in HTML
    assert "<title>" in HTML
