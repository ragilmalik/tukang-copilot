from pathlib import Path


def test_prompts_nonempty():
    files = list((Path(__file__).resolve().parents[2] / "prompts").glob("*.md"))
    assert files
    for f in files:
        assert len(f.read_text().strip()) > 50, f.name
