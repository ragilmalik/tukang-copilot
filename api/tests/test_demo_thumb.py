from pathlib import Path


def test_landing_has_demo_thumb() -> None:
    html = (Path(__file__).resolve().parents[2] / "web" / "index.html").read_text()
    assert 'data-testid="demo-thumb"' in html
