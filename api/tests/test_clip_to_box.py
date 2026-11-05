"""Live SAM once returned a "spark plug cable" mask that spread over the wall behind the bike. Masks are kept near
the box Muse Spark located the part in."""
from __future__ import annotations

import numpy as np

from api.pipeline.engine import clip_to_box


def _seg(l: int, t: int, r: int, b: int) -> dict:  # type: ignore[type-arg]
    return {"left": l, "top": t, "right": r, "bottom": b, "mask": np.ones((b - t, r - l), dtype=np.uint8), "mw": r - l, "mh": b - t}


def test_a_mask_far_outside_its_box_is_cut_back() -> None:
    # part boxed at 40-50 % of a 1000x800 photo, mask covers the whole top half
    out = clip_to_box([_seg(0, 0, 1000, 400)], [0.4, 0.4, 0.5, 0.5], (1000, 800))
    assert len(out) == 1 and out[0]["clipped"]
    assert out[0]["left"] >= 300 and out[0]["right"] <= 600 and out[0]["top"] >= 250


def test_a_mask_inside_the_margin_is_untouched() -> None:
    seg = _seg(380, 300, 520, 420)
    assert clip_to_box([seg], [0.4, 0.4, 0.5, 0.5], (1000, 800)) == [seg]


def test_a_mask_with_nothing_near_the_box_is_dropped_and_no_box_keeps_all() -> None:
    assert clip_to_box([_seg(900, 700, 1000, 800)], [0.0, 0.0, 0.1, 0.1], (1000, 800)) == []
    seg = _seg(0, 0, 1000, 800)
    assert clip_to_box([seg], None, (1000, 800)) == [seg]
