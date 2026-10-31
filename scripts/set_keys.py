"""The one step to go live: paste your keys, they are saved to .env, then checked.

    python scripts/set_keys.py                     # asks for the key (typing hidden)
    python scripts/set_keys.py --check-only        # just re-run the checks on the saved key
    echo "$KEY" | python scripts/set_keys.py --stdin   # non-interactive (CI, scripts); first line = Meta key, optional second = Baseten

It asks for your Meta Model API key (typing is hidden), optionally your Baseten key, writes them into the
.env file next to app.py (creating it from .env.example), turns demo mode off, and runs
scripts/check_keys.py so you see PASS/FAIL for every Meta model straight away.
On Render/Vercel, put the same names (MODEL_API_KEY, BASETEN_API_KEY, USE_OPEN_WEIGHTS) in the
service's Environment settings instead; nothing else changes.
"""
from __future__ import annotations

import getpass
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV, EXAMPLE = Path(os.environ.get("TC_ENV_FILE") or ROOT / ".env"), ROOT / ".env.example"  # TC_ENV_FILE: tests only


def set_var(text: str, name: str, value: str) -> str:
    line = f"{name}={value}"
    if re.search(rf"^#?\s*{name}=.*$", text, flags=re.M):
        return re.sub(rf"^#?\s*{name}=.*$", line, text, count=1, flags=re.M)
    return text.rstrip("\n") + f"\n{line}\n"


def _ask(prompt: str, piped: list[str]) -> str:
    """Hidden prompt on a terminal; next piped line otherwise (never echoes the key)."""
    if piped or not sys.stdin.isatty():
        return piped.pop(0).strip() if piped else ""
    return getpass.getpass(prompt).strip()


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if "-h" in args or "--help" in args:
        print(__doc__)
        return 0
    check = [sys.executable, str(ROOT / "scripts" / "check_keys.py")]
    if "--check-only" in args:
        return subprocess.call(check, cwd=ROOT)
    piped = sys.stdin.read().splitlines() if ("--stdin" in args or not sys.stdin.isatty()) else []
    key = _ask("Paste your Meta Model API key (dev.meta.ai > API keys), then Enter: ", piped)
    if not key:
        print("No key entered; nothing changed.")
        return 1
    if not ENV.exists():
        shutil.copy(EXAMPLE, ENV) if EXAMPLE.exists() else ENV.write_text("")
    text = ENV.read_text(encoding="utf-8")
    text = set_var(text, "MODEL_API_KEY", key)
    text = set_var(text, "MOCK", "0")
    text = set_var(text, "DEMO_MODE", "0")
    bt = _ask("Optional: Baseten API key for open weights (Enter to skip): ", piped)
    if bt:
        text = set_var(text, "BASETEN_API_KEY", bt)
        text = set_var(text, "USE_OPEN_WEIGHTS", "1")
    ENV.write_text(text, encoding="utf-8")
    print(f"Saved to {ENV.name} (demo mode is now off). Checking the keys now...\n", flush=True)
    return subprocess.call(check, cwd=ROOT)


if __name__ == "__main__":
    sys.exit(main())
