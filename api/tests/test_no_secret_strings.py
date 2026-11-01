import re
import subprocess
from pathlib import Path

PATTERN = re.compile(r"(sk-[A-Za-z0-9]{24,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}|LLM\|[A-Za-z0-9]{20,})")


def test_no_secret_looking_strings_tracked():
    root = Path(__file__).resolve().parents[2]
    files = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True, text=True).stdout.split()
    for f in files:
        p = root / f
        if p.suffix in {".png", ".jpg", ".gif", ".mp4", ".pdf", ".zip", ".ico", ".webp"} or not p.is_file():
            continue
        assert not PATTERN.search(p.read_text(encoding="utf-8", errors="ignore")), f
