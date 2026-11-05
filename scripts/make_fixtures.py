"""Label the sample photos for offline sample mode and the tests: samples/*.jpg (what "Try a sample" and the 1-tap demo
send) and api/tests/fixtures/sample_*.jpg (spec §8 cases) plus manifest.json.

The photos are AI-generated (an image model, prompted for a phone shot of each broken thing in an Indonesian
home), NOT real repairs. Each copy gets a small "Sample photo (AI-generated)" tag in the corner
and the same text in EXIF ImageDescription, so nobody takes them for evidence. My own Semarang photos go in
api/tests/fixtures/real/ later and are never tagged like this.

The part outlines that mock SAM returns for these photos are drawn by hand in api/pipeline/sample_masks.json
(percent of width and height). This script only fills in each photo's dHash there, which is how mock mode
recognises a sample after it was resized or re-encoded.

Run: python scripts/make_fixtures.py --src DIR    (DIR holds the untagged originals: motor.jpg, pump.jpg, ...)
     python scripts/make_fixtures.py              (re-tag nothing, only refresh manifest.json and the dHashes)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from api.pipeline.sample_masks import LABEL, MASKS_FILE, dhash  # noqa: E402

SAMPLES = ROOT / "samples"
OUT = ROOT / "api" / "tests" / "fixtures"
FONT = ROOT / "web" / "fonts" / "barlow-600.woff2"

# source photo -> sample file name (served by the app), or None
SAMPLE_FILES = {"motor": "motor", "check_motor": "check_motor", "pump": "pump", "check_pump": "check_pump", "faucet": "faucet",
                "check_faucet": "check_faucet", "rice": "rice", "tire": "tire", "check_tire": "check_tire"}

FIXTURES: list[dict[str, str]] = [
    {"file": "sample_motor_plug_area.jpg", "src": "motor", "scenario": "motor", "safety": "amber",
     "text": "Motor Honda Beat saya susah hidup, distarter cuma bunyi.", "category": "motor"},
    {"file": "sample_motor_plug_closeup.jpg", "src": "motor_closeup", "scenario": "motor", "safety": "amber",
     "text": "Busi motor kelihatan hitam, mesin nggak nyala.", "category": "motor"},
    {"file": "sample_motor_step_cap_on.jpg", "src": "check_motor", "scenario": "motor", "role": "step_check"},
    {"file": "sample_pump_overview.jpg", "src": "pump", "scenario": "pump", "safety": "amber",
     "text": "Pompa air Shimizu bunyi dan muter tapi air nggak keluar.", "category": "pump"},
    {"file": "sample_pump_prime_plug.jpg", "src": "check_pump", "scenario": "pump", "role": "step_check"},
    {"file": "sample_faucet_drip.jpg", "src": "faucet", "scenario": "faucet", "safety": "green",
     "text": "Kran wastafel dapur netes terus walau sudah ditutup.", "category": "plumbing"},
    {"file": "sample_faucet_step_dry.jpg", "src": "check_faucet", "scenario": "faucet", "role": "step_check"},
    {"file": "sample_faucet_hose_clamp.jpg", "src": "faucet_hose", "scenario": "faucet", "safety": "green",
     "text": "The tap hose under the sink is dripping at the clamp.", "category": "plumbing",
     "parts_in_photo": 1},  # only the shut-off valve is in this under-sink picture, not the tap handle or spout
    {"file": "sample_rice_cooker_front.jpg", "src": "rice", "scenario": "rice", "safety": "red",
     "text": "Rice cooker saya nggak panas, lampunya mati.", "category": "appliance"},
    {"file": "sample_rice_cooker_base_open.jpg", "src": "rice_base_open", "scenario": "rice", "safety": "red",
     "text": "Rice cooker not heating, I opened the bottom cover.", "category": "appliance"},
    {"file": "sample_tire_flat_nail.jpg", "src": "tire", "scenario": "tire", "safety": "amber",
     "text": "Ban belakang motor skutik kempes pelan-pelan, kayaknya kena paku.", "category": "motor"},
    {"file": "sample_tire_flat_nail_en.jpg", "src": "tire_wheel", "scenario": "tire", "safety": "amber",
     "text": "My scooter rear tyre keeps going flat, I see a nail in the tread.", "category": "motor"},
    {"file": "sample_tire_valve_check.jpg", "src": "tire_valve", "scenario": "tire", "role": "step_check"},
    {"file": "sample_tire_nail_out.jpg", "src": "check_tire", "scenario": "tire", "role": "step_check"},
    {"file": "sample_tire_pressure_gauge.jpg", "src": "tire_gauge", "scenario": "tire", "role": "reference"},
    {"file": "sample_unknown_object.jpg", "src": "unknown", "scenario": "motor", "role": "edge_case",
     "text": "Ini rusak.", "category": "other"},
]


def phone_look(im: Image.Image, long_side: int, seed: int) -> Image.Image:
    """Make a generated picture sit closer to a phone camera file: phone resolution, a little sensor grain,
    slight corner fall-off and the light sharpening phones apply. Same seed, same file."""
    w, h = im.size
    k = long_side / max(w, h)
    im = im.resize((round(w * k), round(h * k)), Image.Resampling.LANCZOS)
    im = im.filter(ImageFilter.UnsharpMask(radius=1.4, percent=70, threshold=2))
    a = np.asarray(im).astype(np.float32)
    rng = np.random.default_rng(seed)
    luma = rng.normal(0.0, 2.4, a.shape[:2]).astype(np.float32)
    chroma = rng.normal(0.0, 1.2, a.shape).astype(np.float32)
    a += luma[..., None] + chroma
    yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]].astype(np.float32)
    r = np.hypot((xx - a.shape[1] / 2) / (a.shape[1] / 2), (yy - a.shape[0] / 2) / (a.shape[0] / 2)) / np.sqrt(2)
    a *= (1.0 - 0.10 * r ** 2.2)[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def tag(src: Path, dst: Path, max_side: int, look: bool = False) -> None:
    """Copy one original with the corner tag and the EXIF label. Only ImageDescription is written (no camera or
    generator fields), and it says the photo is AI-generated."""
    im = Image.open(src).convert("RGB")
    if look:
        im = phone_look(im, max_side, seed=sum(src.stem.encode()))
    else:
        im.thumbnail((max_side, max_side))
    w = im.width
    size = max(14, w // 52)
    font = ImageFont.truetype(str(FONT), size) if FONT.exists() else ImageFont.load_default()
    pad, m = size // 2, max(8, w // 90)
    x0, y0, x1, y1 = ImageDraw.Draw(im).textbbox((0, 0), LABEL, font=font)
    box = (m, m, m + (x1 - x0) + 2 * pad, m + (y1 - y0) + 2 * pad)
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle(box, radius=(box[3] - box[1]) // 2, fill=(20, 22, 26, 170))
    d.text((box[0] + pad - x0, box[1] + pad - y0), LABEL, fill=(255, 255, 255, 235), font=font)
    out = Image.alpha_composite(im.convert("RGBA"), layer).convert("RGB")
    exif = Image.Exif()
    exif[0x010E] = LABEL  # ImageDescription
    if look:
        out.save(dst, "JPEG", quality=90, subsampling=2, exif=exif, optimize=True)
    else:
        out.save(dst, "JPEG", quality=84, exif=exif, optimize=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--src", type=Path, help="folder with the untagged originals (<name>.jpg)")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if a.src:
        for name, sample in SAMPLE_FILES.items():
            tag(a.src / f"{name}.jpg", SAMPLES / f"{sample}.jpg", 1600, look=True)
        for item in FIXTURES:
            tag(a.src / f"{item['src']}.jpg", OUT / item["file"], 1024)
    masks = json.loads(MASKS_FILE.read_text())
    for name, entry in masks["photos"].items():
        p = SAMPLES / f"{SAMPLE_FILES[name]}.jpg" if name in SAMPLE_FILES else OUT / next(i["file"] for i in FIXTURES if i["src"] == name)
        entry["dhash"] = dhash(Image.open(p))
    MASKS_FILE.write_text(json.dumps(masks, indent=1, ensure_ascii=False) + "\n")
    manifest = [{k: v for k, v in item.items() if k != "src"} for item in FIXTURES]
    (OUT / "manifest.json").write_text(json.dumps({"note": LABEL, "fixtures": manifest}, indent=2, ensure_ascii=False) + "\n")
    print(f"{len(SAMPLE_FILES)} sample photos, {len(FIXTURES)} fixtures, {len(masks['photos'])} outlined photos")


if __name__ == "__main__":
    main()
