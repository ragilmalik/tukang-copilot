from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_writeup_and_archived_submission_have_no_em_dash():
    for name in ("WRITEUP.md", "archive/hackathon/SUBMISSION.md"):
        text = (ROOT / "docs" / name).read_text(encoding="utf-8")
        assert "\u2014" not in text, name
