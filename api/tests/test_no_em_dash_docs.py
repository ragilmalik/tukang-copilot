from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_submission_docs_have_no_em_dash():
    for name in ("SUBMISSION.md", "WRITEUP.md"):
        text = (ROOT / "docs" / name).read_text(encoding="utf-8")
        assert "\u2014" not in text, name
