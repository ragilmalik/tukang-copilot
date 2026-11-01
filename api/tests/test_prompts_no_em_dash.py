from pathlib import Path


def test_prompts_have_no_em_dash():
    root = Path(__file__).resolve().parents[2] / "prompts"
    for p in root.glob("*.md"):
        assert "\u2014" not in p.read_text(encoding="utf-8"), p.name
