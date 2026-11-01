from pathlib import Path

PROMPTS = Path(__file__).resolve().parents[2] / "prompts"


def test_prompts_nonempty_and_dash_free():
    files = sorted(PROMPTS.glob("*.md"))
    assert files
    for f in files:
        text = f.read_text(encoding="utf-8")
        assert len(text.strip()) > 50, f.name
        assert "\u2014" not in text, f.name
