"""Two parts that share a top-left corner used to get their number badges on the same spot (live tap photo: badge 2,
the tap body, was hidden under badge 4, the wall flange)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from typing import Any

import pytest
from PIL import Image, ImageDraw

from api.render import overlay


def _part(label: int, box: tuple[int, int, int, int]) -> dict[str, Any]:
    l, t, r, b = box
    return {"id": f"c{label}", "label": label, "name": str(label),
            "segs": [{"left": l, "top": t, "right": r, "bottom": b, "mask": np.ones((b - t, r - l), dtype=np.uint8), "mw": r - l, "mh": b - t}]}


def test_badges_never_sit_on_top_of_each_other(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    src = tmp_path / "p.jpg"
    Image.new("RGB", (800, 600), (200, 200, 200)).save(src)
    drawn: list[tuple[float, float]] = []
    real = ImageDraw.ImageDraw.ellipse

    def spy(self: Any, xy: Any, *a: Any, **k: Any) -> Any:
        drawn.append(((xy[0] + xy[2]) / 2, (xy[1] + xy[3]) / 2))
        return real(self, xy, *a, **k)

    monkeypatch.setattr(ImageDraw.ImageDraw, "ellipse", spy)
    parts = [_part(1, (100, 100, 400, 300)), _part(2, (100, 100, 300, 200)), _part(3, (102, 98, 200, 400))]
    overlay.draw_parts(src, parts, tmp_path / "o.jpg")
    r = max(14, 800 // 40)
    assert len(drawn) == 3
    for i in range(3):
        for j in range(i + 1, 3):
            (x1, y1), (x2, y2) = drawn[i], drawn[j]
            assert (x1 - x2) ** 2 + (y1 - y2) ** 2 >= (2 * r) ** 2, drawn
