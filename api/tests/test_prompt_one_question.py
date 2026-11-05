"""Live, the motorbike follow-up was three questions in one ("is it wet, black-sooty, and is there a blue spark?")
under Yes / No / Not sure buttons. The diagnose prompt now asks for one yes/no question about one thing."""
from __future__ import annotations

from pathlib import Path

PROMPT = Path(__file__).resolve().parents[2] / "prompts" / "diagnose.md"


def test_follow_up_is_one_yes_no_question() -> None:
    text = " ".join(PROMPT.read_text(encoding="utf-8").split())
    assert "ONE short `follow_up_question`" in text
    assert "yes, no or not sure" in text and "never two or three things" in text
