"""The test count quoted in the submission docs must be the one the last real run reported.

Nobody trusts "620 automated tests" in the README next to "550" in the testing guide. docs/TEST_REPORT.md is rewritten by scripts/make_test_report.py from
a real run; every doc that quotes a number must match it.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUOTES = ["README.md", "docs/SUBMISSION.md", "docs/WRITEUP.md", "docs/TESTING.md", "docs/launch/COMMUNITY_VOTE_KIT.md",
          "docs/launch/ONE_PAGER.md", "docs/launch/JUDGE_FAQ.md", "docs/JUDGING_MAP.md"]
# \d{3,5}: the count passed 999 in 1.29, and a \d{3} pattern never matched "1005 tests" (no word boundary inside a
# number), so this check had quietly stopped checking anything.
PHRASE = re.compile(r"\b\*{0,2}(\d{3,5})\*{0,2}\s+(?:automated\s+)?tests\b|\ball\s+(\d{3,5})\s+tests\b")


def _reported() -> int:
    m = re.search(r"(\d+) passed, 0 failed", (ROOT / "docs/TEST_REPORT.md").read_text(encoding="utf-8"))
    assert m, "TEST_REPORT.md has no 'N passed, 0 failed' line"
    return int(m.group(1))


def test_quoted_test_counts_match_the_last_real_run() -> None:
    n = _reported()
    bad = []
    for rel in QUOTES:
        f = ROOT / rel
        if not f.exists():
            continue
        for m in PHRASE.finditer(f.read_text(encoding="utf-8")):
            quoted = int(m.group(1) or m.group(2))
            if quoted != n:
                bad.append(f"{rel}: {quoted} (report says {n})")
    assert not bad, "stale test counts: " + "; ".join(bad)


def test_the_report_itself_is_a_green_run() -> None:
    text = (ROOT / "docs/TEST_REPORT.md").read_text(encoding="utf-8")
    assert "ALL PASSED" in text


def test_the_pattern_reads_four_digit_counts() -> None:
    assert [int(m.group(1) or m.group(2)) for m in PHRASE.finditer("**1005** automated tests, all 1234 tests, 987 tests")] == [1005, 1234, 987]
