"""docs/launch/make_launch_assets.py: the asset picker and the one-page rule for the one-pager PDF.

The PDF itself needs pandoc and WeasyPrint, which CI does not install, so these tests cover the parts that decide
what gets built and when the build must refuse, plus the source text the PDF is made from.
"""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "docs" / "launch" / "make_launch_assets.py"


def _load():
    spec = importlib.util.spec_from_file_location("make_launch_assets", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_one_pager_must_be_exactly_one_page() -> None:
    mod = _load()
    mod.check_one_page(1)
    for pages in (0, 2, 3):
        with pytest.raises(SystemExit, match=f"{pages} pages"):
            mod.check_one_page(pages)


def test_unknown_asset_name_is_refused_before_anything_is_built(capsys: pytest.CaptureFixture[str]) -> None:
    mod = _load()
    assert mod.main(["onepagr"]) == 2
    assert "unknown asset(s): onepagr" in capsys.readouterr().err
    assert set(mod.BUILDERS) == {"thumbnail", "architecture", "onepager"}


def test_one_pager_source_has_no_placeholders_and_its_pdf_is_in_the_repo() -> None:
    text = (ROOT / "docs" / "launch" / "ONE_PAGER.md").read_text(encoding="utf-8")
    assert "{{" not in text
    pdf = ROOT / "docs" / "launch" / "one-pager.pdf"
    assert pdf.read_bytes()[:5] == b"%PDF-"
