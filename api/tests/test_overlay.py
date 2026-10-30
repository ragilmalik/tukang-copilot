import numpy as np
from PIL import Image

from api.pipeline import mock
from api.render import overlay


def test_full_mask_places_box_local_mask():
    seg = {"left": 10, "top": 20, "right": 30, "bottom": 40, "mw": 2, "mh": 2, "mask": np.array([1, 0, 0, 1], dtype=np.uint8)}
    m = overlay.full_mask(seg, 100, 100)
    assert m.shape == (100, 100)
    assert m[25, 15] and m[35, 25] and not m[25, 25] and not m[5, 5]


def test_full_mask_clips_out_of_bounds():
    seg = {"left": -50, "top": -50, "right": 500, "bottom": 500, "mw": 1, "mh": 1, "mask": np.array([1], dtype=np.uint8)}
    assert overlay.full_mask(seg, 64, 48).all()


def test_draw_parts_tints_only_masked_area(samples, tmp_path):
    photo = samples["faucet"]
    segs = mock.segment(photo, "faucet spout")
    out = overlay.draw_parts(photo, [{"id": "c2", "label": 1, "name": "spout", "segs": segs}], tmp_path / "o.jpg")
    a, b = np.asarray(Image.open(photo).convert("RGB"), dtype=int), np.asarray(Image.open(out), dtype=int)
    s = segs[0]
    cy, cx = (s["top"] + s["bottom"]) // 2, (s["left"] + s["right"]) // 2
    assert np.abs(a[cy, cx] - b[cy, cx]).sum() > 30      # inside the mask: tinted
    assert np.abs(a[5, 5] - b[5, 5]).sum() < 20           # far corner: untouched


def test_draw_parts_with_no_masks_keeps_photo(samples, tmp_path):
    out = overlay.draw_parts(samples["motor"], [{"id": "x", "label": 1, "name": "x", "segs": []}], tmp_path / "o.jpg")
    assert Image.open(out).size == Image.open(samples["motor"]).size


def test_normalize_caps_size_and_applies_exif(tmp_path):
    img = Image.new("RGB", (4000, 2000), (120, 10, 10))
    exif = img.getexif(); exif[0x0112] = 6  # rotate 90
    img.save(tmp_path / "big.jpg", exif=exif)
    out = overlay.normalize_photo(tmp_path / "big.jpg", tmp_path / "n.jpg", 1536)
    w, h = Image.open(out).size
    assert max(w, h) == 1536 and h > w  # rotated to portrait
