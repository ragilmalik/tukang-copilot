"""Draw ~10 clearly labelled STAND-IN photos for tests (spec §8): synthetic drawings, NOT real photos.
Every image carries a visible red "STAND-IN" banner and an EXIF ImageDescription, so nobody mistakes
them for evidence. I will swap in my own Semarang photos (same file names) when I have them.
Run: python scripts/make_fixtures.py   -> api/tests/fixtures/*.jpg + manifest.json"""
from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "api" / "tests" / "fixtures"
LABEL = "STAND-IN - synthetic test image, not a real photo"
D = ImageDraw.ImageDraw


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
    except OSError:
        return ImageFont.load_default()


def _canvas(bg: tuple[int, int, int], w: int = 1024, h: int = 768) -> tuple[Image.Image, D]:
    im = Image.new("RGB", (w, h), bg)
    return im, ImageDraw.Draw(im)


def motor_plug_area(d: D) -> None:
    d.rectangle([120, 220, 900, 700], fill=(32, 32, 36)); d.rectangle([430, 300, 620, 470], fill=(18, 18, 18), outline=(200, 200, 200), width=6)
    d.line([600, 330, 900, 200], fill=(12, 12, 12), width=22); d.ellipse([560, 300, 640, 360], fill=(150, 30, 30))


def motor_plug_closeup(d: D) -> None:
    d.rectangle([380, 120, 640, 260], fill=(200, 200, 205)); d.rectangle([450, 260, 570, 560], fill=(235, 235, 235))
    d.rectangle([470, 560, 550, 650], fill=(40, 30, 25)); d.line([510, 650, 510, 700], fill=(30, 30, 30), width=10)


def motor_step_cap_on(d: D) -> None:
    motor_plug_area(d); d.ellipse([555, 295, 645, 365], outline=(46, 204, 113), width=8)


def pump_overview(d: D) -> None:
    d.rectangle([0, 600, 1024, 768], fill=(120, 115, 105)); d.rounded_rectangle([280, 260, 700, 560], radius=36, fill=(30, 90, 170))
    d.ellipse([420, 130, 600, 280], fill=(200, 200, 205)); d.rectangle([20, 400, 290, 480], fill=(235, 235, 235)); d.rectangle([700, 340, 1000, 410], fill=(235, 235, 235))


def pump_prime_plug(d: D) -> None:
    d.ellipse([300, 180, 720, 600], fill=(200, 200, 205), outline=(90, 90, 95), width=8); d.rectangle([440, 300, 580, 440], fill=(110, 110, 115))
    d.line([440, 370, 580, 370], fill=(60, 60, 60), width=10)


def faucet_drip(d: D) -> None:
    d.rectangle([60, 470, 964, 580], fill=(245, 245, 245)); d.rectangle([460, 120, 540, 470], fill=(190, 195, 200))
    d.rectangle([540, 290, 820, 370], fill=(190, 195, 200)); d.ellipse([790, 390, 820, 430], fill=(80, 150, 230))


def faucet_hose_clamp(d: D) -> None:
    d.rectangle([100, 330, 924, 430], fill=(160, 160, 160)); d.rectangle([440, 300, 560, 460], fill=(200, 60, 50))
    d.ellipse([600, 440, 630, 480], fill=(80, 150, 230))


def rice_cooker_front(d: D) -> None:
    d.ellipse([220, 160, 800, 360], fill=(250, 250, 250), outline=(160, 160, 160), width=6); d.rectangle([220, 260, 800, 680], fill=(250, 250, 250), outline=(160, 160, 160), width=6)
    d.rectangle([440, 520, 580, 600], fill=(60, 60, 60))


def rice_cooker_base_open(d: D) -> None:
    d.ellipse([200, 200, 820, 640], fill=(70, 70, 75)); d.ellipse([360, 330, 660, 510], fill=(180, 120, 60))
    for x in (300, 720):
        d.line([x, 420, 512, 420], fill=(220, 40, 40), width=8)


def tire_flat(d: D) -> None:
    d.rectangle([0, 600, 1024, 768], fill=(95, 92, 88)); d.ellipse([250, 190, 790, 640], fill=(25, 25, 27)); d.ellipse([380, 320, 660, 520], fill=(170, 172, 178))
    d.ellipse([500, 400, 540, 440], fill=(60, 60, 64)); d.line([512, 215, 512, 262], fill=(190, 190, 195), width=9); d.ellipse([505, 205, 520, 220], fill=(210, 210, 215))


def tire_valve_check(d: D) -> None:
    d.rectangle([0, 600, 1024, 768], fill=(95, 92, 88)); d.ellipse([200, 140, 820, 700], fill=(30, 30, 33)); d.ellipse([360, 300, 660, 540], fill=(170, 172, 178))
    d.rectangle([700, 330, 740, 400], fill=(190, 190, 195)); d.ellipse([690, 322, 750, 345], fill=(60, 60, 64))


def tire_sticker_closeup(d: D) -> None:
    d.rectangle([180, 160, 840, 620], fill=(235, 235, 225), outline=(60, 60, 60), width=6)
    for i in range(5):
        d.line([240, 230 + i * 70, 780, 230 + i * 70], fill=(70, 70, 70), width=10)
    d.ellipse([700, 450, 800, 550], fill=(220, 190, 40))


def unknown_object(d: D) -> None:
    d.rectangle([300, 200, 724, 600], fill=(120, 140, 110)); d.ellipse([440, 330, 584, 470], fill=(40, 40, 40))


FIXTURES: list[dict[str, object]] = [
    {"file": "standin_motor_plug_area.jpg", "draw": motor_plug_area, "bg": (60, 64, 70), "scenario": "motor", "safety": "amber",
     "text": "Motor Honda Beat saya susah hidup, distarter cuma bunyi.", "category": "motor"},
    {"file": "standin_motor_plug_closeup.jpg", "draw": motor_plug_closeup, "bg": (70, 70, 74), "scenario": "motor", "safety": "amber",
     "text": "Busi motor kelihatan hitam, mesin nggak nyala.", "category": "motor"},
    {"file": "standin_motor_step_cap_on.jpg", "draw": motor_step_cap_on, "bg": (60, 64, 70), "scenario": "motor", "role": "step_check"},
    {"file": "standin_pump_overview.jpg", "draw": pump_overview, "bg": (180, 175, 165), "scenario": "pump", "safety": "amber",
     "text": "Pompa air Shimizu bunyi dan muter tapi air nggak keluar.", "category": "pump"},
    {"file": "standin_pump_prime_plug.jpg", "draw": pump_prime_plug, "bg": (175, 170, 160), "scenario": "pump", "role": "step_check"},
    {"file": "standin_faucet_drip.jpg", "draw": faucet_drip, "bg": (225, 230, 235), "scenario": "faucet", "safety": "green",
     "text": "Kran wastafel dapur netes terus walau sudah ditutup.", "category": "plumbing"},
    {"file": "standin_faucet_hose_clamp.jpg", "draw": faucet_hose_clamp, "bg": (215, 220, 225), "scenario": "faucet", "safety": "green",
     "text": "The tap hose under the sink is dripping at the clamp.", "category": "plumbing"},
    {"file": "standin_rice_cooker_front.jpg", "draw": rice_cooker_front, "bg": (238, 232, 220), "scenario": "rice", "safety": "red",
     "text": "Rice cooker saya nggak panas, lampunya mati.", "category": "appliance"},
    {"file": "standin_rice_cooker_base_open.jpg", "draw": rice_cooker_base_open, "bg": (230, 225, 215), "scenario": "rice", "safety": "red",
     "text": "Rice cooker not heating, I opened the bottom cover.", "category": "appliance"},
    {"file": "standin_tire_flat_nail.jpg", "draw": tire_flat, "bg": (150, 148, 142), "scenario": "tire", "safety": "amber",
     "text": "Ban belakang motor skutik kempes pelan-pelan, kayaknya kena paku.", "category": "motor"},
    {"file": "standin_tire_flat_nail_en.jpg", "draw": tire_flat, "bg": (140, 140, 138), "scenario": "tire", "safety": "amber",
     "text": "My scooter rear tyre keeps going flat, I see a nail in the tread.", "category": "motor"},
    {"file": "standin_tire_valve_check.jpg", "draw": tire_valve_check, "bg": (150, 148, 142), "scenario": "tire", "role": "step_check"},
    {"file": "standin_tire_pressure_sticker.jpg", "draw": tire_sticker_closeup, "bg": (120, 120, 118), "scenario": "tire", "role": "reference"},
    {"file": "standin_unknown_object.jpg", "draw": unknown_object, "bg": (200, 200, 200), "scenario": "motor", "role": "edge_case",
     "text": "Ini rusak.", "category": "other"},
]


def make(item: dict[str, object]) -> Path:
    bg = item["bg"]; draw = item["draw"]
    assert isinstance(bg, tuple) and callable(draw)
    im, d = _canvas(bg)
    fn: Callable[[D], None] = draw
    fn(d)
    d.rectangle([0, 0, im.width, 56], fill=(200, 20, 20))
    d.text((16, 12), LABEL, fill=(255, 255, 255), font=_font(28))
    exif = Image.Exif(); exif[0x010E] = LABEL  # ImageDescription
    p = OUT / str(item["file"])
    im.save(p, "JPEG", quality=82, exif=exif)
    return p


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = []
    for item in FIXTURES:
        make(item)
        manifest.append({k: v for k, v in item.items() if k not in ("draw", "bg")})
    (OUT / "manifest.json").write_text(json.dumps({"note": LABEL, "fixtures": manifest}, indent=2, ensure_ascii=False) + "\n")
    print(f"{len(FIXTURES)} stand-in fixtures -> {OUT}")


if __name__ == "__main__":
    main()
