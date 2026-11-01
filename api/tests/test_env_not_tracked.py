import subprocess
from pathlib import Path


def test_env_files_not_tracked() -> None:
    root = Path(__file__).resolve().parents[2]
    out = subprocess.run(
        ["git", "ls-files"], cwd=root, capture_output=True, text=True, check=False
    ).stdout.split()
    bad = [f for f in out if Path(f).name == ".env" or f.endswith(".pem")]
    assert bad == []
