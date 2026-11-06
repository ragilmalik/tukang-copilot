"""Every relative link in the repo's Markdown files points at a file or folder that exists.

Added in 1.33.0, when the hackathon papers moved to docs/archive/hackathon/: a moved file leaves links behind in
README, HANDOFF and the docs, and nothing else would notice. Web links (http, https, mailto) and in-page anchors are
not checked here; a link's #anchor part is dropped before the path is looked up.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# [text](target) and [text](target "title"); images too. Skips links inside inline code.
LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
CODE = re.compile(r"`[^`]*`")
FENCE = re.compile(r"^\s*```")


def _md_files() -> list[Path]:
    try:
        out = subprocess.run(["git", "ls-files", "*.md"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
        files = [ROOT / p for p in out.splitlines() if p]
    except (OSError, subprocess.CalledProcessError):  # not a git checkout (a zip): read the folder
        files = [p for p in ROOT.rglob("*.md") if "node_modules" not in p.parts and ".git" not in p.parts]
    return [f for f in files if f.exists()]


def broken_links(path: Path) -> list[str]:
    bad = []
    in_fence = False
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for m in LINK.finditer(CODE.sub("", line)):
            target = m.group(1)
            if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I) or target.startswith("#"):
                continue
            rel = target.split("#", 1)[0].split("?", 1)[0]
            if not rel:
                continue
            if not (path.parent / rel).exists():
                bad.append(f"{path.relative_to(ROOT)}:{n}: {target}")
    return bad


def test_every_relative_markdown_link_resolves() -> None:
    files = _md_files()
    assert len(files) > 20
    bad = [b for f in files for b in broken_links(f)]
    assert not bad, "broken links:\n" + "\n".join(bad)


def test_the_checker_finds_a_broken_link(tmp_path: Path) -> None:
    (tmp_path / "there.md").write_text("x", encoding="utf-8")
    doc = tmp_path / "a.md"
    doc.write_text("[ok](there.md#top) [web](https://example.com) `[code](nope.md)`\n[gone](missing.md)\n",
                   encoding="utf-8")
    global ROOT
    old, ROOT = ROOT, tmp_path
    try:
        assert broken_links(doc) == ["a.md:2: missing.md"]
    finally:
        ROOT = old
