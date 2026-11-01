import json
import subprocess
from pathlib import Path


def test_tracked_json_files_parse():
    root = Path(__file__).resolve().parents[2]
    files = subprocess.run(["git", "ls-files", "*.json", "*.webmanifest"], cwd=root, capture_output=True, text=True).stdout.split()
    for f in files:
        json.loads((root / f).read_text(encoding="utf-8"))
