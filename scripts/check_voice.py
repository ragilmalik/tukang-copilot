"""Checks that the repo's own writing reads like my notes and not like generated filler.

    python scripts/check_voice.py            # scan the whole repo, exit 1 on any hit
    python scripts/check_voice.py README.md  # scan only these files
    python scripts/check_voice.py --rules    # print every rule and every allowlist entry

I wrote this after a cleanup pass on the docs, so the same words don't creep back in. What it reads:

- prose: every Markdown, .txt and .srt file I wrote (README, HANDOFF, CHANGELOG, TODO, docs/, the launch kit);
- code: comments and docstrings only, in Python, JavaScript, CSS, HTML, shell, batch, YAML, TOML, INI, the
  Dockerfile and the ignore files (string literals are product text or test data and are left alone);
- prompts/*.md: those are instructions to the model by design, so only the "who wrote this" rules apply there
  (tool names, chat-session talk, notes about a style guide), never the word list or the imperative-voice rules.

Third-party files (web/vendor/, the font licences, LICENSE), JSON (recorded model answers and fixtures) and
binaries are skipped. A real technical use of a listed word goes in ALLOW below with the reason, so every
exception is written down in one place. api/tests/test_check_voice.py runs this on every test run and in CI.
"""
from __future__ import annotations

import argparse
import ast
import fnmatch
import io
import re
import subprocess
import sys
import tokenize
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Rule:
    id: str
    pattern: re.Pattern[str]
    why: str
    unless: re.Pattern[str] | None = None  # a line that also matches this is a real, literal use
    in_prompts: bool = False  # True: also applies inside prompts/*.md


def _r(p: str, flags: int = re.IGNORECASE) -> re.Pattern[str]:
    return re.compile(p, flags)


# Who-wrote-this rules: the repo is mine, so nothing in it should read like a note to or from a tool.
AUTHOR_RULES = [
    Rule("tool-name", _r(r"\bhark\b"), "names a tool instead of the author", in_prompts=True),
    Rule("coding-agent", _r(r"\bcoding[ -](agent|assistant|session)s?\b|\bsub-?agents?\b|\b(future|next|another) agents?\b"
                            r"|\bthe agent (wrote|committed|pushed|edited|generated|created)\b"
                            r"|\baudit \d+\b|\bskeptical judge\b|\bthe builder\b"),
         "talks about a code-writing agent (the app's own agent loop is fine)", in_prompts=True),
    Rule("chat-session", _r(r"\b(agent|chat|coding|AI) sessions?\b|\bscheduled run\b|\bprevious helper\b"),
         "refers to a chat or tool session", in_prompts=True),
    Rule("ai-author", _r(r"\bthe AI (wrote|writes|coded|committed|authored)\b|\bAI[- ](written|authored)\b"
                         r"|\b(written|authored|drafted) by (an? |the )?(AI|LLM|assistant|agent|ChatGPT|Claude)\b"),
         "an AI as the one writing the code or docs", in_prompts=True),
    Rule("user-asked", _r(r"\bthe user (asked|requested|instructed|told)\b|\bas instructed\b"),
         "reads like a reply to an order", in_prompts=True),
    Rule("style-guide", _r(r"\bper the guide\b|\bcoding guide\b|\bMalik's\b|\bas per (my|the) (rules|guide)\b"),
         "mentions a private writing or coding guide", in_prompts=True),
    Rule("numbered-rule", _r(r"\brule #?\d+\b"), "points at a numbered rule from a private guide"),
    Rule("assistant", _r(r"\bassistant\b"), "assistant talk (the chat API role name is allowlisted)"),
    Rule("reader-order", _r(r"\byou must\b|\b(do not|don't) forget\b|\bIMPORTANT:|\bCRITICAL:|\bnote to (the )?(agent|ai|model)\b"),
         "an order aimed at a reader-agent; say what happens instead"),
    Rule("shouting", re.compile(r"\b(NEVER|ALWAYS|MUST)\b"), "all-caps orders read like a prompt"),
]

# Words and patterns that mark generated filler. Sources: work notes from the humanizer and stop-slop
# checklists, Wikipedia "Signs of AI writing" (AI vocabulary list), and the corpus studies it cites
# (Juzek and Ward, COLING 2025, on why ChatGPT overuses some words; Matsui 2025, PubMed term frequencies).
_WORDS = (r"delve[sd]?|delving|leverag(e|es|ed|ing)|seamless(ly)?|robust(ly|ness)?|comprehensive(ly)?|cutting[- ]edge"
          r"|state[- ]of[- ]the[- ]art|elevat(e|es|ed|ing)|harness(es|ed|ing)?|tapestry|testament|empower(s|ed|ing|ment)?"
          r"|game[- ]chang(er|ing)|furthermore|moreover|intricate(ly)?|intricac(y|ies)|meticulous(ly)?|showcas(e|es|ed|ing)"
          r"|pivotal|realm|commendable|bolster(s|ed|ing)?|paramount|boast(s|ed|ing)?|foster(s|ed|ing)?|garner(s|ed|ing)?"
          r"|interplay|vibrant|groundbreaking|streamlin(e|es|ed|ing)|holistic|synerg(y|ies)|paradigm|transformative"
          r"|revolutioni[sz](e|es|ed|ing)|embark(s|ed|ing)?|endeavou?r(s)?|ever[- ]evolving|nestled|crucial(ly)?"
          r"|utili[sz](e|es|ed|ing)|unparalleled|indispensable|invaluable|plethora|myriad|underscor(e|es|ed|ing)"
          r"|ecosystem|journey")
SLOP_RULES = [
    Rule("slop-word", _r(rf"\b({_WORDS})\b"), "an overused filler word; say the plain thing",
         unless=_r(r"\bunderscore (character|prefix)\b|`_")),
    Rule("unlock", _r(r"\bunlock(s|ed|ing)?\b"), "metaphorical unlock; literal step locking is fine",
         unless=_r(r"\bstep|\block|lock\b")),
    Rule("landscape", _r(r"\blandscape\b"), "abstract landscape; picture orientation is fine",
         unless=_r(r"landscape (picture|photo|orientation|mode|video|frame|page|scene)|, landscape\b")),
    Rule("filler-phrase", _r(r"\bit'?s worth noting\b|\bworth noting\b|\bit is important to note\b|\bin today'?s\b"
                             r"|\bplays? an? (crucial|key|vital|pivotal|important|significant) role\b|\bnavigat(e|es|ing) the\b"
                             r"|\bhere'?s the thing\b|\blet that sink in\b|\bin summary\b|\bin conclusion\b|\bat its core\b"
                             r"|\bat the end of the day\b|\bwhen it comes to\b|\bin a world where\b|\bthe reality is\b"
                             r"|\bi hope this helps\b|\blet me walk you through\b|\bdive into\b|\bdeep dive\b|\brest assured\b"
                             r"|\bserves as an?\b|\bstands as an?\b|\bevolving landscape\b|\bin the heart of\b"),
         "a filler phrase; cut it and state the point"),
    Rule("additionally-opener", _r(r"(^|[.!?]\s+|^\s*([-*]|\d+\.)\s+)additionally\b"), "'Additionally' opening a sentence"),
    Rule("not-just-but", _r(r"\bnot (just|only|merely|simply)\b[^.;:\n]{1,80}?\bbut\b|\bit'?s not [^.,;\n]{1,40}, it'?s\b"),
         "the 'not just X but Y' frame"),
    Rule("em-dash", re.compile("\u2014"), "em dash; use a comma, colon, brackets or a new sentence"),
    Rule("en-dash", re.compile(r"(?<![0-9])\u2013|\u2013(?![0-9])"), "en dash used as a dash (number ranges like 5\u201310 are fine)"),
]
RULES = AUTHOR_RULES + SLOP_RULES


@dataclass(frozen=True)
class Allow:
    path: str  # fnmatch glob on the repo-relative path
    rule: str
    line: str  # regex the offending line must match
    reason: str


ALLOW = [
    Allow("docs/launch/YOUTUBE.md", "assistant", r"^Tukang Copilot, Meta AI,", "the YouTube tag list: 'repair assistant' is a search term people type"),
]

SKIP_GLOBS = ["web/vendor/*", "*/OFL.txt", "LICENSE", "*.json", "*.jsonl", "*.webmanifest",
              "dist-static/*", "data/*", "samples/*"]
TEXT_EXT = {".md": "prose", ".txt": "prose", ".srt": "prose", ".py": "python", ".js": "js", ".mjs": "js", ".css": "css",
            ".html": "html", ".sh": "hash", ".yml": "hash", ".yaml": "hash", ".toml": "hash", ".ini": "hash", ".bat": "bat"}
CODE_FENCES = {"bash", "sh", "shell", "console", "json", "python", "py", "js", "javascript", "mermaid", "yaml", "toml", "ini", "html", "css"}
HASH_NAMES = {"Dockerfile", ".gitignore", ".dockerignore", ".env.example"}


def mode_for(rel: str) -> str | None:
    if any(fnmatch.fnmatch(rel, g) for g in SKIP_GLOBS):
        return None
    name = Path(rel).name
    if name in HASH_NAMES or fnmatch.fnmatch(name, "requirements*.txt"):
        return "hash"
    if rel.startswith("prompts/") and rel.endswith(".md"):
        return "prompt"
    return TEXT_EXT.get(Path(rel).suffix.lower())


# ---- text extraction: (line number, text) pairs that a person reads as writing ----

def lines_prose(src: str) -> list[tuple[int, str]]:
    out, fence, code = [], False, False
    for i, line in enumerate(src.splitlines(), 1):
        if line.lstrip().startswith("```"):
            fence = not fence
            # a block tagged with a language holds code or a diagram; an untagged one is usually copy-paste text
            # (the YouTube description, the X thread, form answers), which is my writing and gets checked
            code = fence and line.strip().strip("`").strip().lower() in CODE_FENCES
            continue
        if not code:
            out.append((i, re.sub(r"`[^`]*`", "``", line)))  # inline code is a name, not a word I chose
    return out


def lines_python(src: str) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.COMMENT:
                out.append((tok.start[0], tok.string))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return out
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                raw = ast.get_source_segment(src, first.value) or ""
                for k, text in enumerate(raw.splitlines()):
                    out.append((first.value.lineno + k, re.sub(r"`[^`]*`", "``", text)))
    return out


def lines_c_like(src: str, line_comments: bool) -> list[tuple[int, str]]:
    """Comments in JavaScript (// and /* */) or CSS (/* */), skipping strings, template literals and regex literals."""
    out: list[tuple[int, str]] = []
    i, n, line = 0, len(src), 1
    prev = ""  # last non-space character outside comments, to tell a regex literal from a division
    while i < n:
        c = src[i]
        if c == "\n":
            line += 1
            i += 1
            continue
        if src.startswith("/*", i):
            j = src.find("*/", i + 2)
            j = n if j < 0 else j
            for k, text in enumerate(src[i + 2:j].split("\n")):
                out.append((line + k, text))
            line += src.count("\n", i, j)
            i = j + 2
            continue
        if line_comments and src.startswith("//", i):
            j = src.find("\n", i)
            j = n if j < 0 else j
            out.append((line, src[i + 2:j]))
            i = j
            continue
        if c in "'\"`":
            j = i + 1
            while j < n and src[j] != c:
                if src[j] == "\\":
                    j += 1
                elif src[j] == "\n" and c != "`":
                    break
                j += 1
            line += src.count("\n", i, j)
            i, prev = j + 1, c
            continue
        if line_comments and c == "/" and (prev == "" or prev in "(,=:[!&|?{};+-*%<>~^"):
            j, in_class = i + 1, False
            while j < n and src[j] != "\n":
                if src[j] == "\\":
                    j += 2
                    continue
                if src[j] == "[":
                    in_class = True
                elif src[j] == "]":
                    in_class = False
                elif src[j] == "/" and not in_class:
                    break
                j += 1
            i, prev = j + 1, "/"
            continue
        if not c.isspace():
            prev = c
        i += 1
    return out


def lines_html(src: str) -> list[tuple[int, str]]:
    out = []
    for m in re.finditer(r"<!--(.*?)-->", src, re.S):
        start = src.count("\n", 0, m.start()) + 1
        for k, text in enumerate(m.group(1).split("\n")):
            out.append((start + k, text))
    return out


def lines_hash(src: str) -> list[tuple[int, str]]:
    out = []
    for i, line in enumerate(src.splitlines(), 1):
        m = re.search(r"(^|\s)#(?!!)(.*)$", line)
        if m and line.count('"', 0, m.start()) % 2 == 0 and line.count("'", 0, m.start()) % 2 == 0:
            out.append((i, m.group(2)))
    return out


def lines_bat(src: str) -> list[tuple[int, str]]:
    return [(i, m.group(2)) for i, line in enumerate(src.splitlines(), 1)
            if (m := re.match(r"\s*(rem\b|::)(.*)$", line, re.I))]


def extract(mode: str, src: str) -> list[tuple[int, str]]:
    if mode in ("prose", "prompt"):
        return lines_prose(src)
    if mode == "python":
        return lines_python(src)
    if mode == "js":
        return lines_c_like(src, True)
    if mode == "css":
        return lines_c_like(src, False)
    if mode == "html":
        return lines_html(src)
    if mode == "bat":
        return lines_bat(src)
    return lines_hash(src)


@dataclass(frozen=True)
class Hit:
    path: str
    line: int
    rule: str
    text: str


ALLOW_USED: dict[int, int] = {}  # allowlist index -> how many hits it let through on the last scan


def allowed(rel: str, rule: str, text: str) -> bool:
    for k, a in enumerate(ALLOW):
        if fnmatch.fnmatch(rel, a.path) and a.rule in ("*", rule) and re.search(a.line, text):
            ALLOW_USED[k] = ALLOW_USED.get(k, 0) + 1
            return True
    return False


def unused_allows() -> list[Allow]:
    """Allowlist entries the last full scan never needed: a stale exception hides nothing, so it should go."""
    return [a for k, a in enumerate(ALLOW) if not ALLOW_USED.get(k)]


def scan_text(rel: str, mode: str, src: str) -> list[Hit]:
    hits = []
    for no, text in extract(mode, src):
        for rule in RULES:
            if mode == "prompt" and not rule.in_prompts:
                continue
            if rule.pattern.search(text) and not (rule.unless and rule.unless.search(text)) and not allowed(rel, rule.id, text):
                hits.append(Hit(rel, no, rule.id, text.strip()[:160]))
    return hits


def repo_files() -> list[str]:
    try:
        out = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
        return sorted({f for f in out.splitlines() if (ROOT / f).is_file()})
    except (OSError, subprocess.CalledProcessError):  # not a git checkout (zip download)
        skip = {".git", "node_modules", ".venv", "__pycache__", ".mypy_cache", ".ruff_cache", ".pytest_cache"}
        return sorted(str(p.relative_to(ROOT)) for p in ROOT.rglob("*") if p.is_file() and not skip & set(p.parts))


def scan(paths: list[str] | None = None) -> list[Hit]:
    ALLOW_USED.clear()
    hits: list[Hit] = []
    for rel in paths or repo_files():
        mode = mode_for(rel)
        if mode is None:
            continue
        try:
            src = (ROOT / rel).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        hits += scan_text(rel, mode, src)
    return hits


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("paths", nargs="*", help="repo-relative files (default: the whole repo)")
    ap.add_argument("--rules", action="store_true", help="print the rules and the allowlist")
    args = ap.parse_args(argv)
    if args.rules:
        for r in RULES:
            print(f"{r.id:20} {'prompts too' if r.in_prompts else '':12} {r.why}")
        print("\nallowlist:")
        for a in ALLOW:
            print(f"  {a.path} [{a.rule}] {a.reason}")
        return 0
    hits = scan(args.paths or None)
    for h in hits:
        print(f"{h.path}:{h.line}: [{h.rule}] {h.text}")
    stale = [] if args.paths else unused_allows()
    for a in stale:
        print(f"unused allowlist entry: {a.path} [{a.rule}] {a.reason}")
    print(f"check_voice: {len(hits)} hit(s), {len(stale)} unused allowlist entr{'y' if len(stale) == 1 else 'ies'}")
    return 1 if hits or stale else 0


if __name__ == "__main__":
    sys.exit(main())
