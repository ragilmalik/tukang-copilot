"""scripts/check_voice.py keeps the repo's writing plain: zero hits on the whole repo, and the checker really catches
what it says it catches (so a broken extractor can't pass by reading nothing)."""
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("check_voice", ROOT / "scripts" / "check_voice.py")
assert _spec and _spec.loader
cv = importlib.util.module_from_spec(_spec)
sys.modules["check_voice"] = cv
_spec.loader.exec_module(cv)


def rules_hit(rel: str, mode: str, text: str) -> set[str]:
    return {h.rule for h in cv.scan_text(rel, mode, text)}


def test_the_repo_has_no_hits_and_no_stale_exceptions() -> None:
    hits = cv.scan()
    assert not hits, "\n".join(f"{h.path}:{h.line}: [{h.rule}] {h.text}" for h in hits[:40])
    assert not cv.unused_allows(), cv.unused_allows()


def test_it_reads_a_real_share_of_the_repo() -> None:
    modes = [cv.mode_for(f) for f in cv.repo_files()]
    for mode, at_least in (("prose", 30), ("python", 150), ("js", 4), ("prompt", 7), ("html", 3), ("hash", 8)):
        assert modes.count(mode) >= at_least, (mode, modes.count(mode))


@pytest.mark.parametrize("text, rule", [
    ("We delve into the code.", "slop-word"),
    ("A robust, seamless pipeline.", "slop-word"),
    ("Furthermore, it works.", "slop-word"),
    ("Additionally, it works.", "additionally-opener"),
    ("- Additionally the cache is cleared.", "additionally-opener"),
    ("It's worth noting that the cache clears.", "filler-phrase"),
    ("This plays a crucial role here.", "filler-phrase"),
    ("It is not just a scanner but a guide.", "not-just-but"),
    ("Fast \u2014 and cheap.", "em-dash"),
    ("Fast \u2013 and cheap.", "en-dash"),
    ("Built by Hark.", "tool-name"),
    ("The coding agent wrote this file.", "coding-agent"),
    ("Notes from the previous helper.", "chat-session"),
    ("The user asked for a table.", "user-asked"),
    ("Done per the guide.", "style-guide"),
    ("Kept short (Rule 3).", "numbered-rule"),
    ("You must run the tests first.", "reader-order"),
    ("NEVER commit the key.", "shouting"),
    ("This unlocks real value.", "unlock"),
])
def test_each_rule_catches_its_example(text: str, rule: str) -> None:
    assert rule in rules_hit("docs/x.md", "prose", text)


@pytest.mark.parametrize("text", [
    "A 5\u201310 s video, 0:00\u20130:12 in the script.",  # number ranges keep their en dash
    "The tick list unlocks the steps.",  # the app really locks and unlocks steps
    "The share card is a landscape picture.",
    "The agent loop plans, acts, verifies and re-plans.",  # the product's own agent
    "The same agent runs in WhatsApp.",
])
def test_real_uses_are_not_flagged(text: str) -> None:
    assert not rules_hit("docs/x.md", "prose", text)


def test_prompts_keep_their_orders_but_not_tool_talk() -> None:
    assert not rules_hit("prompts/x.md", "prompt", "You MUST answer in JSON. Be robust to blur.")
    assert "tool-name" in rules_hit("prompts/x.md", "prompt", "Written for Hark.")


def test_code_strings_are_left_alone_comments_and_docstrings_are_read() -> None:
    py = 'x = "robust \u2014 seamless"\n# a seamless fix\ndef f() -> None:\n    """We delve."""\n'
    assert {(h.line, h.rule) for h in cv.scan_text("a.py", "python", py)} == {(2, "slop-word"), (4, "slop-word")}
    js = "const u = 'http://x.test/robust'; // seamless\nconst r = /\\/\\//g; /* robust */\n"
    assert [h.line for h in cv.scan_text("a.js", "js", js)] == [1, 2]
    assert rules_hit("a.html", "html", '<p>robust</p><!-- a seamless page -->') == {"slop-word"}
    assert [h.line for h in cv.scan_text("a.sh", "hash", 'echo "#robust"\n# robust\n')] == [2]


def test_copy_paste_blocks_are_read_but_code_blocks_are_not() -> None:
    md = "```\nA seamless repair app.\n```\n```bash\necho robust\n```\n"
    assert [h.line for h in cv.scan_text("docs/x.md", "prose", md)] == [2]
