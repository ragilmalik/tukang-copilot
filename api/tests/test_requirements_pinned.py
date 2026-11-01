from pathlib import Path


def test_requirements_nonempty_and_no_secrets():
    root = Path(__file__).resolve().parents[2]
    text = (root / "requirements.txt").read_text()
    lines = [x for x in text.splitlines() if x.strip() and not x.startswith("#")]
    assert lines
    assert "sk-" not in text
