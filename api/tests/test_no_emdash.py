"""Guard: user-facing prompts and UI files must not contain em dashes."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_no_em_dash_in_user_facing_files() -> None:
    files = list((ROOT / "prompts").glob("*.md")) + list((ROOT / "web").glob("*.js")) + list((ROOT / "web").glob("*.html"))
    assert files
    bad = [f.name for f in files if "\u2014" in f.read_text(encoding="utf-8")]
    assert not bad, bad


def test_no_em_dash_in_setup_and_main_docs() -> None:
    files = [ROOT / "docs" / "SETUP.md", ROOT / "TODO.md", ROOT / "README.md", ROOT / "HANDOFF.md", ROOT / "docs" / "TESTING.md",
             ROOT / "docs" / "archive" / "hackathon" / "SUBMISSION.md"]
    bad = [f.name for f in files if "\u2014" in f.read_text(encoding="utf-8")]
    assert not bad, bad
