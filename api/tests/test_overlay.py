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


def _reference_full_image(photo, found, out):
    """The pre-1.22 renderer: edge filters over the whole photo (slow). The cropped version must match it."""
    from PIL import ImageDraw, ImageFilter

    base = Image.open(photo).convert("RGB")
    w, h = base.size
    tint = Image.new("RGBA", base.size, (0, 0, 0, 0))
    edges = Image.new("RGBA", base.size, (0, 0, 0, 0))
    badges = []
    for i, part in enumerate(found):
        color = overlay.PALETTE[i % len(overlay.PALETTE)]
        union = np.zeros((h, w), dtype=bool)
        for seg in part.get("segs", [])[:3]:
            union |= overlay.full_mask(seg, w, h)
        if not union.any():
            continue
        m = Image.fromarray((union * 255).astype(np.uint8), "L")
        tint.paste(Image.new("RGBA", base.size, color + (90,)), (0, 0), m)
        edge = m.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(5))
        edges.paste(Image.new("RGBA", base.size, color + (255,)), (0, 0), edge)
        ys, xs = np.nonzero(union)
        k = int(np.argmin((xs - xs.min()) ** 2 + (ys - ys.min()) ** 2))  # the part pixel nearest its box corner
        badges.append((part["label"], int(xs[k]), int(ys[k]), color))
    img = Image.alpha_composite(Image.alpha_composite(base.convert("RGBA"), tint), edges)
    d = ImageDraw.Draw(img)
    r = max(14, w // 40)
    f = overlay._font(int(r * 1.2))
    for label, x, y, color in badges:
        cx, cy = min(max(x - r * 3 // 4, r), w - r), min(max(y - r * 3 // 4, r), h - r)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color + (255,), outline=(255, 255, 255, 255), width=3)
        d.text((cx, cy), str(label), fill=(255, 255, 255, 255), font=f, anchor="mm")
    img.convert("RGB").save(out, "JPEG", quality=90)


def test_cropped_outline_is_pixel_identical_to_full_image_filtering(samples, tmp_path):
    """The speed-up (edge filters on the part's box, not the whole photo) must not change a single pixel,
    including a part that touches the photo border."""
    photo = samples["motor"]
    w, h = Image.open(photo).size
    found = [{"id": "c1", "label": 1, "name": "a", "segs": mock.segment(photo, "spark plug cap")},
             {"id": "c2", "label": 2, "name": "b", "segs": [{"left": w - 120, "top": h - 90, "right": w, "bottom": h}]},
             {"id": "c3", "label": 3, "name": "c", "segs": [{"left": 0, "top": 0, "right": 60, "bottom": 40}]}]
    new = tmp_path / "new.jpg"
    overlay.draw_parts(photo, found, new)
    _reference_full_image(photo, found, tmp_path / "ref.jpg")
    a = np.asarray(Image.open(new).convert("RGB"), dtype=int)
    b = np.asarray(Image.open(tmp_path / "ref.jpg").convert("RGB"), dtype=int)
    assert a.shape == b.shape
    assert (a == b).all()  # same pixels in, same JPEG out


def test_draw_parts_is_fast_on_a_full_size_photo(tmp_path):
    import time

    p = tmp_path / "big.jpg"
    Image.new("RGB", (1536, 1152), (120, 130, 140)).save(p)
    found = [{"id": f"c{i}", "label": i, "name": "x", "segs": [{"left": 100 * i, "top": 80 * i, "right": 100 * i + 200, "bottom": 80 * i + 150}]}
             for i in range(1, 4)]
    t0 = time.time()
    overlay.draw_parts(p, found, tmp_path / "o.jpg")
    assert time.time() - t0 < 1.0  # was ~0.25 s per part on the whole photo; the box crop is ~10x faster
