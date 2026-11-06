"""docs/launch/make_launch_assets.py: the asset picker and the one-page rule for the one-pager PDF.

The PDF itself needs pandoc and WeasyPrint, which CI does not install, so these tests cover the parts that decide
what gets built and when the build must refuse, plus the source text the PDF is made from.
"""
import importlib.util
import sys
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
    assert set(mod.BUILDERS) == {"thumbnail", "thumbnail-drawn", "architecture", "onepager"}


def test_one_pager_source_has_no_placeholders_and_its_pdf_is_in_the_repo() -> None:
    text = (ROOT / "docs" / "launch" / "ONE_PAGER.md").read_text(encoding="utf-8")
    assert "{{" not in text
    pdf = ROOT / "docs" / "launch" / "one-pager.pdf"
    assert pdf.read_bytes()[:5] == b"%PDF-"


def test_marketing_images_are_labelled_real_screens_at_their_sizes() -> None:
    """docs/launch/make_marketing_images.py: each image uses a real screenshot that exists, a scene that exists, a
    screen quad shaped like the screenshot it takes (so the warp does not stretch the UI), and the files in the repo
    have the sizes the platforms want. The labels are drawn by the script (checked by reading its source)."""
    from PIL import Image

    spec = importlib.util.spec_from_file_location("make_marketing_images", ROOT / "docs" / "launch" / "make_marketing_images.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # dataclasses look the module up while the class is made
    spec.loader.exec_module(mod)
    want = {"thumbnail": (1280, 720), "cover": (1920, 1080), "square": (1080, 1080), "poster-vertical": (1080, 1920)}
    assert {k: s.size for k, s in mod.SPECS.items()} == want
    for name, s in mod.SPECS.items():
        assert (mod.SCENES / s.scene).is_file() and (mod.SHOTS / s.shot).is_file()
        (x0, y0), (x1, y1), (x2, y2), (x3, y3) = s.screen
        top, bottom = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5, ((x2 - x3) ** 2 + (y2 - y3) ** 2) ** 0.5
        left, right = ((x3 - x0) ** 2 + (y3 - y0) ** 2) ** 0.5, ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        with Image.open(mod.SHOTS / s.shot) as shot:
            aspect = s.shot_crop_h / shot.width
        assert abs((left + right) / (top + bottom) - aspect) / aspect < 0.08, name
        with Image.open(ROOT / "docs" / "launch" / f"{name}.png") as im:
            assert im.size == want[name]
    src = (ROOT / "docs" / "launch" / "make_marketing_images.py").read_text(encoding="utf-8")
    assert '"AI-generated scene"' in src and '"Real app screen"' in src
    assert (ROOT / "docs" / "launch" / "thumbnail.png").stat().st_size < 2_000_000
