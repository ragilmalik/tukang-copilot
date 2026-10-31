"""Health version and CHANGELOG must not drift apart."""
import re
from pathlib import Path

from api import __version__


def test_changelog_has_current_minor() -> None:
    text = (Path(__file__).resolve().parents[2] / "CHANGELOG.md").read_text()
    versions = re.findall(r"^## v(\d+\.\d+)", text, re.M)
    assert versions, "no versions in changelog"
    assert ".".join(__version__.split(".")[:2]) == versions[0]
