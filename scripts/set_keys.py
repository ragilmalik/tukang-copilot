"""The one step to go live: paste your keys, they are saved to .env, then checked.

    python scripts/set_keys.py

It asks for your Meta Model API key (typing is hidden), optionally your Baseten key, writes them into the
.env file next to app.py (creating it from .env.example), turns demo mode off, and runs
scripts/check_keys.py so you see PASS/FAIL for every Meta model straight away.
On Render/Vercel, put the same names (MODEL_API_KEY, BASETEN_API_KEY, USE_OPEN_WEIGHTS) in the
service's Environment settings instead; nothing else changes.
"""
from __future__ import annotations

import getpass
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV, EXAMPLE = ROOT / ".env", ROOT / ".env.example"


def set_var(text: str, name: str, value: str) -> str:
    line = f"{name}={value}"
    if re.search(rf"^#?\s*{name}=.*$", text, flags=re.M):
        return re.sub(rf"^#?\s*{name}=.*$", line, text, count=1, flags=re.M)
    return text.rstrip("\n") + f"\n{line}\n"


def main() -> int:
    if not ENV.exists():
        shutil.copy(EXAMPLE, ENV) if EXAMPLE.exists() else ENV.write_text("")
    text = ENV.read_text(encoding="utf-8")
    key = getpass.getpass("Paste your Meta Model API key (dev.meta.ai > API keys), then Enter: ").strip()
    if not key:
        print("No key entered; nothing changed.")
        return 1
    text = set_var(text, "MODEL_API_KEY", key)
    text = set_var(text, "MOCK", "0")
    text = set_var(text, "DEMO_MODE", "0")
    bt = getpass.getpass("Optional: Baseten API key for open weights (Enter to skip): ").strip()
    if bt:
        text = set_var(text, "BASETEN_API_KEY", bt)
        text = set_var(text, "USE_OPEN_WEIGHTS", "1")
    ENV.write_text(text, encoding="utf-8")
    print(f"Saved to {ENV.name}. Checking the keys now...\n")
    return subprocess.call([sys.executable, str(ROOT / "scripts" / "check_keys.py")], cwd=ROOT)


if __name__ == "__main__":
    sys.exit(main())
