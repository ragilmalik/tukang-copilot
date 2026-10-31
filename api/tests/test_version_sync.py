"""Health version and CHANGELOG must not drift apart (audit 5: /api/health said 1.23.0 while the repo was 1.23.8)."""
import re
from pathlib import Path

from api import __version__


def test_changelog_has_current_minor() -> None:
    text = (Path(__file__).resolve().parents[2] / "CHANGELOG.md").read_text()
    versions = re.findall(r"^## v?(\d+\.\d+)", text, re.M)
    assert versions, "no versions in changelog"
    assert ".".join(__version__.split(".")[:2]) == versions[0]


def test_top_changelog_entry_is_the_running_version() -> None:
    text = (Path(__file__).resolve().parents[2] / "CHANGELOG.md").read_text()
    top = re.findall(r"^## v?(\d+\.\d+\.\d+)", text, re.M)[0]
    assert top == __version__, (top, __version__)
