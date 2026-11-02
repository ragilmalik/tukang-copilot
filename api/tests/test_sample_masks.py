"""The sample photos are AI-generated phone shots; mock SAM answers with outlines drawn by hand on each one,
so the overlay sits on the real part. Any other picture still gets the old fixed demo boxes."""
from pathlib import Path

import numpy as np
from PIL import Image

from api.pipeline import mock, sample_masks
from api.render import overlay

ROOT = Path(__file__).resolve().parents[2]
SAMPLES = ROOT / "samples"


def test_every_sample_photo_is_recognised_after_the_upload_resize(tmp_path):
    for name in ("motor", "pump", "faucet", "rice", "tire", "check_motor", "check_pump", "check_faucet", "check_tire"):
        out = overlay.normalize_photo(SAMPLES / f"{name}.jpg", tmp_path / f"{name}.jpg", 800)  # smaller and re-encoded
        assert sample_masks.lookup(out) is not None, name


def test_main_parts_have_hand_drawn_outlines():
    for sample, phrases in {"motor": ("spark plug cap", "ignition cable", "air filter box"), "pump": ("priming plug", "suction pipe", "power plug"),
                            "faucet": ("faucet handle", "faucet spout", "shut-off valve"), "rice": ("cook switch", "power cord"),
                            "tire": ("tyre tread", "valve stem", "wheel rim")}.items():
        w, h = Image.open(SAMPLES / f"{sample}.jpg").size
        for phrase in phrases:
            segs = mock.segment(SAMPLES / f"{sample}.jpg", phrase)
            assert len(segs) == 1, (sample, phrase)
            s = segs[0]
            m = np.asarray(s["mask"]).astype(bool)
            assert m.shape == (s["mh"], s["mw"]) == (s["bottom"] - s["top"], s["right"] - s["left"])
            assert 0.0005 < m.sum() / (w * h) < 0.25, (sample, phrase)    # a real part, not a blob over half the photo
            assert m.mean() < 0.95 or phrase in ("priming plug", "cook switch", "valve stem", "power plug")  # an outline, not a box


def test_spark_plug_cap_sits_where_it_was_drawn():
    segs = mock.segment(SAMPLES / "motor.jpg", "spark plug cap")
    w, h = Image.open(SAMPLES / "motor.jpg").size
    x1, y1, x2, y2 = sample_masks.box(sample_masks.lookup(SAMPLES / "motor.jpg") or {}, "spark plug cap") or [0, 0, 0, 0]
    s = segs[0]
    assert abs(s["left"] / w - x1) < 0.01 and abs(s["top"] / h - y1) < 0.01 and abs(s["right"] / w - x2) < 0.01 and abs(s["bottom"] / h - y2) < 0.01


def test_part_not_in_the_picture_returns_nothing_like_sam():
    assert mock.segment(SAMPLES / "faucet.jpg", "spark plug cap") == []
    assert mock.segment(ROOT / "api/tests/fixtures/sample_unknown_object.jpg", "spark plug cap") == []


def test_other_pictures_keep_the_fixed_demo_boxes(samples):
    segs = mock.segment(samples["motor"], "spark plug cap")
    w, h = Image.open(samples["motor"]).size
    assert segs and abs(segs[0]["left"] - int(0.40 * w)) <= 1


def test_object_report_box_follows_the_outline():
    rep = mock.object_report("motor", "en", SAMPLES / "motor.jpg")
    cap = next(c for c in rep["components"] if c["sam_phrase"] == "spark plug cap")
    assert cap["prompt_box"] != list(mock._BOXES["spark plug cap"])
    assert mock.object_report("motor", "en")["components"][0]["prompt_box"] == list(mock._BOXES["spark plug cap"])
