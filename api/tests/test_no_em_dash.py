from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_docs_and_web_have_no_em_dash():
    bad = []
    for sub in ("docs", "web", "prompts"):
        for p in (ROOT / sub).rglob("*"):
            if p.suffix in {".md", ".js", ".html", ".css"} and "\u2014" in p.read_text("utf-8", "ignore"):
                bad.append(str(p.relative_to(ROOT)))
    assert not bad, bad
