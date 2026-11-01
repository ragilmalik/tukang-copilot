import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_env_file_not_tracked():
    out = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True
    ).stdout.split()
    assert not [f for f in out if Path(f).name == ".env"]
