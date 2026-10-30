"""Offline stand-ins for every Meta call (MOCK=1 or no MODEL_API_KEY). The app, the tests and the demo
fallback all run on these for free. Three scenarios from SPEC §8, picked by keywords:

  * motor  - Honda Beat won't start: loose / fouled spark plug cap        (green)
  * faucet - dripping kitchen tap: worn washer                               (green)
  * rice   - rice cooker not heating: opening mains internals -> RED stop    (red)
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageStat

TRANSCRIPTS = {
    "id": "Motor saya Honda Beat susah hidup dari pagi, distarter cuma bunyi tapi mesin nggak nyala.",
    "jv": "Motorku Honda Beat angel urip wiwit esuk, distarter mung muni nanging mesine ora urip.",
    "en": "My Honda Beat won't start since this morning, the starter turns but the engine doesn't fire.",
}


def scenario(text: str, category: str = "") -> str:
    t = (text or "").lower() + " " + (category or "")
    if re.search(r"\b(rice cooker|magic ?com|penanak|nasi|appliance)\b", t):
        return "rice"
    if re.search(r"\b(kran|keran|faucet|tap|wastafel|netes|menetes|plumbing|pipa)\b", t):
        return "faucet"
    return "motor"


def _L(lang: str, id_: str, en: str) -> str:
    return en if lang == "en" else id_


# ------------------------------------------------------------------ Look
def object_report(sc: str, lang: str) -> dict[str, Any]:
    rep = _object_report(sc, lang)
    for c in rep["components"]:
        c["prompt_box"] = list(_BOXES[c["sam_phrase"]])
    return rep


def _object_report(sc: str, lang: str) -> dict[str, Any]:
    if sc == "faucet":
        return {"object": _L(lang, "Kran air wastafel dapur", "Kitchen sink faucet"), "brand_model_guess": "", "category": "plumbing",
                "components": [{"id": "c1", "name": _L(lang, "Tuas kran", "Faucet handle"), "sam_phrase": "faucet handle", "condition": ""},
                               {"id": "c2", "name": _L(lang, "Mulut kran", "Faucet spout"), "sam_phrase": "faucet spout", "condition": _L(lang, "basah, menetes", "wet, dripping")},
                               {"id": "c3", "name": _L(lang, "Kran stop", "Shut-off valve"), "sam_phrase": "shut-off valve", "condition": ""}],
                "visible_issues": [_L(lang, "Tetesan air di ujung mulut kran", "Water drop at the spout tip")]}
    if sc == "rice":
        return {"object": _L(lang, "Rice cooker (magic com)", "Rice cooker"), "brand_model_guess": "", "category": "appliance",
                "components": [{"id": "c1", "name": _L(lang, "Tombol cook", "Cook switch"), "sam_phrase": "cook switch", "condition": ""},
                               {"id": "c2", "name": _L(lang, "Kabel power", "Power cord"), "sam_phrase": "power cord", "condition": ""}],
                "visible_issues": [_L(lang, "Lampu indikator mati", "Indicator light off")]}
    return {"object": _L(lang, "Honda Beat, area busi", "Honda Beat, spark plug area"), "brand_model_guess": "Honda Beat", "category": "motor",
            "components": [{"id": "c1", "name": _L(lang, "Cop busi", "Spark plug cap"), "sam_phrase": "spark plug cap", "condition": _L(lang, "terlihat agak longgar", "looks slightly loose")},
                           {"id": "c2", "name": _L(lang, "Kabel busi", "Ignition cable"), "sam_phrase": "ignition cable", "condition": ""},
                           {"id": "c3", "name": _L(lang, "Filter udara", "Air filter box"), "sam_phrase": "air filter box", "condition": ""}],
            "visible_issues": [_L(lang, "Cop busi tidak menempel rapat", "Plug cap not fully seated")]}


# ------------------------------------------------------------------ Diagnose
def diagnosis(sc: str, lang: str) -> dict[str, Any]:
    if sc == "faucet":
        return {"problem_summary": _L(lang, "Kran menetes dari mulut kran saat ditutup.", "The faucet drips from the spout when closed."),
                "causes": [{"title": _L(lang, "Seal karet di dalam kran aus", "Worn rubber washer"), "confidence": 75, "evidence": [_L(lang, "Tetes dari mulut kran saat tertutup", "Drip from spout when closed")], "component_ids": ["c1", "c2"]},
                           {"title": _L(lang, "Dudukan katup tergores", "Scratched valve seat"), "confidence": 20, "evidence": [], "component_ids": ["c1"]}],
                "safety_level": "green", "safety_reason": _L(lang, "Air dan bagian kecil; risiko rendah.", "Water and small parts; low risk."),
                "tools": [{"name": _L(lang, "Kunci inggris", "Adjustable wrench"), "est_price_idr": 45000}, {"name": _L(lang, "Obeng plus", "Phillips screwdriver"), "est_price_idr": 15000}],
                "parts": [{"name": _L(lang, "Seal karet kran 1/2\"", "1/2\" faucet washer"), "est_price_idr": 3000}, {"name": "Seal tape", "est_price_idr": 5000}],
                "difficulty": 2, "minutes_estimate": 30, "follow_up_question": ""}
    if sc == "rice":
        return {"problem_summary": _L(lang, "Rice cooker tidak memanas; lampu indikator mati.", "The rice cooker doesn't heat; indicator is off."),
                "causes": [{"title": _L(lang, "Sekring termal di dalam putus", "Internal thermal fuse blown"), "confidence": 60, "evidence": [], "component_ids": []},
                           {"title": _L(lang, "Kabel power rusak", "Damaged power cord"), "confidence": 25, "evidence": [], "component_ids": ["c2"]}],
                "safety_level": "red", "safety_reason": _L(lang, "Perlu membuka bagian dalam alat 220V.", "Needs opening the 220V internals."),
                "tools": [], "parts": [], "difficulty": 4, "minutes_estimate": 60, "follow_up_question": ""}
    return {"problem_summary": _L(lang, "Starter berputar tapi mesin tidak menyala: kemungkinan tidak ada percikan api.", "Starter turns but the engine won't fire: likely no spark."),
            "causes": [{"title": _L(lang, "Cop busi longgar", "Loose spark plug cap"), "confidence": 55, "evidence": [_L(lang, "Cop terlihat tidak rapat di foto", "Cap looks unseated in the photo")], "component_ids": ["c1"]},
                       {"title": _L(lang, "Busi kotor / berkerak", "Fouled spark plug"), "confidence": 35, "evidence": [_L(lang, "Susah hidup di pagi hari", "Hard start in the morning")], "component_ids": ["c1", "c2"]},
                       {"title": _L(lang, "Filter udara tersumbat", "Clogged air filter"), "confidence": 10, "evidence": [], "component_ids": ["c3"]}],
            "safety_level": "amber", "safety_reason": _L(lang, "Ada bensin dan mesin bisa panas; kerjakan saat mesin dingin, jauh dari api.", "Fuel nearby and the engine gets hot; work cold, away from flames."),
            "tools": [{"name": _L(lang, "Kunci busi 16 mm", "16 mm spark plug socket"), "est_price_idr": 25000}, {"name": _L(lang, "Amplas halus / sikat kawat", "Fine sandpaper / wire brush"), "est_price_idr": 5000}],
            "parts": [{"name": _L(lang, "Busi NGK CPR8EA-9 (cadangan)", "NGK CPR8EA-9 plug (spare)"), "est_price_idr": 25000}],
            "difficulty": 2, "minutes_estimate": 20,
            "follow_up_question": _L(lang, "Apakah tercium bau bensin saat distarter?", "Do you smell fuel when you crank it?")}


# ------------------------------------------------------------------ Plan
def plan(sc: str, lang: str, cause_index: int = 0) -> dict[str, Any]:
    if sc == "faucet" and cause_index >= 1:
        s = [("c3", "Tutup lagi kran stop di bawah wastafel.", "Close the shut-off valve again.", "Air tidak keluar saat kran dibuka.", "No water when the faucet is opened.", False),
             ("c1", "Lepas tuas dan kepala kran seperti sebelumnya.", "Remove the handle and headgear as before.", "Lubang dudukan katup terlihat.", "The valve seat is visible.", True),
             ("c1", "Haluskan dudukan katup dengan alat pengasah dudukan (reseating tool), putar 3-4 kali.", "Smooth the valve seat with a reseating tool, 3-4 turns.", "Permukaan dudukan rata dan mengkilap.", "The seat looks even and shiny.", False),
             ("c2", "Pasang kembali dengan seal baru, buka kran stop, lalu tutup kran.", "Reassemble with a new washer, open the shut-off, close the faucet.", "Mulut kran kering.", "The spout is dry.", False)]
        done, pro, cause = (_L(lang, "Tidak ada tetesan selama 2 menit.", "No drips for 2 minutes."),
                            _L(lang, "Bila masih menetes, ganti kran utuh (sekitar Rp60.000) atau panggil tukang ledeng.", "If it still drips, replace the whole faucet (about Rp60,000) or call a plumber."),
                            _L(lang, "Dudukan katup tergores", "Scratched valve seat"))
    elif sc == "faucet":
        s = [("c3", "Putar kran stop di bawah wastafel searah jarum jam sampai mentok.", "Turn the shut-off valve under the sink clockwise until it stops.", "Air tidak keluar saat kran dibuka.", "No water when the faucet is opened.", False),
             ("c1", "Congkel tutup tuas, buka sekrupnya, lalu angkat tuas kran.", "Pry off the handle cap, undo the screw and lift the handle off.", "Batang kran (spindle) terlihat.", "The spindle is visible.", False),
             ("c1", "Buka kepala kran dengan kunci inggris berlapis kain, ganti seal karetnya.", "Unscrew the headgear with a cloth-wrapped wrench and swap the washer.", "Seal baru duduk rata di ujung kepala kran.", "The new washer sits flat on the headgear.", True),
             ("c2", "Pasang kembali, buka kran stop pelan-pelan, lalu tutup kran wastafel.", "Reassemble, open the shut-off slowly, then close the faucet.", "Mulut kran kering, tidak ada tetesan.", "The spout is dry, no drips.", False)]
        done, pro, cause = (_L(lang, "Tidak ada tetesan selama 2 menit.", "No drips for 2 minutes."),
                            _L(lang, "Berhenti bila badan kran retak atau pipa di tembok ikut bocor.", "Stop if the faucet body is cracked or the wall pipe leaks."),
                            _L(lang, "Seal karet di dalam kran aus", "Worn rubber washer"))
    elif cause_index >= 1:
        s = [("c1", "Pastikan mesin mati dan dingin, lalu cabut cop busi.", "Make sure the engine is off and cold, then pull off the plug cap.", "Cop busi terlepas, busi terlihat.", "The cap is off and the plug is visible.", False),
             ("c1", "Buka busi dengan kunci busi 16 mm, putar berlawanan jarum jam.", "Remove the plug with the 16 mm socket, turning anticlockwise.", "Busi sudah di tangan, ujungnya terlihat.", "The plug is out and its tip is visible.", True),
             ("c1", "Bersihkan kerak di ujung busi dengan amplas halus sampai logamnya terlihat.", "Clean the carbon off the tip with fine sandpaper until metal shows.", "Ujung busi bersih, tidak hitam pekat.", "The tip is clean, not black.", False),
             ("c1", "Pasang busi dengan tangan dulu, kencangkan 1/4 putaran, lalu pasang cop sampai bunyi klik.", "Thread the plug by hand, tighten a quarter turn, then press the cap on until it clicks.", "Cop busi menempel rapat tanpa celah.", "The cap is fully seated, no gap.", False)]
        done, pro, cause = (_L(lang, "Mesin hidup dalam 3 kali starter.", "The engine starts within 3 tries."),
                            _L(lang, "Bawa ke bengkel bila busi basah bensin atau tetap mati.", "See a mechanic if the plug is fuel-soaked or it still won't start."),
                            _L(lang, "Busi kotor / berkerak", "Fouled spark plug"))
    else:
        s = [("", "Matikan kunci kontak dan tunggu mesin dingin 10 menit.", "Switch the ignition off and let the engine cool for 10 minutes.", "Kunci kontak di posisi OFF.", "The key is in the OFF position.", False),
             ("c1", "Buka penutup samping lalu temukan cop busi (bagian yang ditandai nomor 1).", "Open the side cover and find the plug cap (part number 1).", "Cop busi terlihat jelas di foto.", "The plug cap is clearly visible.", False),
             ("c1", "Tekan cop busi lurus ke dalam sampai terasa bunyi klik.", "Push the plug cap straight in until it clicks.", "Cop busi menempel rapat tanpa celah.", "The cap is fully seated, no gap.", False),
             ("", "Pasang penutup, starter sambil tarik rem.", "Refit the cover and press the starter while holding the brake.", "Mesin menyala.", "The engine runs.", False)]
        done, pro, cause = (_L(lang, "Mesin hidup dan stasioner stabil.", "The engine starts and idles steadily."),
                            _L(lang, "Bawa ke bengkel bila tercium bau bensin kuat.", "See a mechanic if there's a strong fuel smell."),
                            _L(lang, "Cop busi longgar", "Loose spark plug cap"))
    steps = []
    for i, (cid, ins_id, ins_en, exp_id, exp_en, diag) in enumerate(s, 1):
        ins = ins_en if lang == "en" else ins_id
        steps.append({"n": i, "component_id": cid, "instruction": ins, "why": "", "expected_state": exp_en if lang == "en" else exp_id,
                      "warnings": [], "voice_text": ins, "needs_diagram": diag,
                      "diagram_prompt": "cutaway of the part being serviced, orange arrow showing the motion" if diag else ""})
    return {"cause_title": cause, "steps": steps, "done_check": done, "when_to_call_pro": pro}


# ------------------------------------------------------------------ SAM, verify, image
_BOXES = {"spark plug cap": (0.40, 0.35, 0.62, 0.58), "ignition cable": (0.55, 0.20, 0.85, 0.40), "air filter box": (0.10, 0.55, 0.40, 0.85),
          "faucet handle": (0.38, 0.12, 0.62, 0.24), "faucet spout": (0.55, 0.30, 0.85, 0.42), "shut-off valve": (0.42, 0.70, 0.58, 0.88),
          "cook switch": (0.40, 0.60, 0.60, 0.72), "power cord": (0.70, 0.70, 0.95, 0.95)}


def segment(image_path: Path, phrase: str) -> list[dict[str, Any]]:
    w, h = Image.open(image_path).size
    box = _BOXES.get(phrase)
    if box is None:
        return []  # SAM returns an empty list when nothing matches; mimic that
    l, t, r, b = int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)
    mh = mw = 32
    yy, xx = np.mgrid[0:mh, 0:mw]
    ellipse = (((xx - mw / 2) / (mw / 2)) ** 2 + ((yy - mh / 2) / (mh / 2)) ** 2) <= 1
    return [{"object_id": 1, "left": l, "top": t, "right": r, "bottom": b, "mask": ellipse.astype(np.uint8),
             "mw": mw, "mh": mh, "confidence": 0.9}]


def step_check(photo: Path, lang: str) -> dict[str, Any]:
    """Deterministic: a dark or nearly blank photo fails (asks for more light), anything else passes."""
    stat = ImageStat.Stat(Image.open(photo).convert("L"))
    if stat.mean[0] < 45:
        return {"passed": False, "observation": _L(lang, "Foto terlalu gelap, bagiannya tidak terlihat.", "The photo is too dark to see the part."),
                "correction": _L(lang, "Nyalakan senter HP dan foto lebih dekat ke bagian yang ditandai.", "Turn on your phone torch and shoot closer to the marked part.")}
    if stat.stddev[0] < 6:
        return {"passed": False, "observation": _L(lang, "Foto kosong atau buram.", "The photo is blank or blurry."),
                "correction": _L(lang, "Arahkan kamera ke bagian yang ditandai dan tahan HP tetap diam.", "Point at the marked part and hold the phone still.")}
    return {"passed": True, "observation": _L(lang, "Terlihat sesuai dengan kondisi yang diharapkan.", "It matches the expected state."), "correction": ""}


def diagram(photo: Path, step_n: int, out: Path) -> Path:
    im = Image.open(photo).convert("RGB").resize((768, 768))
    im = Image.blend(im, Image.new("RGB", im.size, (250, 246, 238)), 0.5)
    d = ImageDraw.Draw(im)
    cx, cy = 260 + (step_n * 97) % 300, 260 + (step_n * 61) % 260
    d.ellipse([cx - 90, cy - 90, cx + 90, cy + 90], outline=(255, 122, 0), width=12)
    d.line([cx + 120, cy + 160, cx + 60, cy + 70], fill=(255, 122, 0), width=14)
    d.polygon([(cx + 45, cy + 50), (cx + 95, cy + 70), (cx + 60, cy + 100)], fill=(255, 122, 0))
    im.save(out, "PNG")
    return out


def make_sample_photos(folder: Path) -> dict[str, Path]:
    """Draws simple stand-in photos for the three scenarios (used by tests and 'Try a sample')."""
    folder.mkdir(parents=True, exist_ok=True)
    out = {}
    # motor
    im = Image.new("RGB", (1200, 900), (60, 64, 70)); d = ImageDraw.Draw(im)
    d.rectangle([150, 250, 1050, 800], fill=(30, 30, 34)); d.rectangle([520, 330, 720, 500], fill=(20, 20, 20), outline=(200, 200, 200), width=6)
    d.line([700, 360, 1000, 220], fill=(15, 15, 15), width=22); d.rectangle([140, 500, 470, 760], fill=(90, 90, 95))
    out["motor"] = folder / "motor.jpg"; im.save(out["motor"], quality=90)
    # faucet
    im = Image.new("RGB", (1024, 1024), (225, 230, 235)); d = ImageDraw.Draw(im)
    d.rectangle([80, 520, 944, 640], fill=(245, 245, 245), outline=(150, 150, 150), width=6); d.rectangle([470, 140, 560, 520], fill=(190, 195, 200))
    d.rectangle([390, 140, 640, 230], fill=(170, 175, 180)); d.rectangle([560, 320, 860, 410], fill=(190, 195, 200)); d.ellipse([820, 420, 850, 460], fill=(80, 150, 230))
    d.rectangle([480, 640, 540, 1000], fill=(160, 160, 160)); d.ellipse([440, 740, 580, 880], fill=(200, 60, 50))
    out["faucet"] = folder / "faucet.jpg"; im.save(out["faucet"], quality=90)
    # rice cooker
    im = Image.new("RGB", (1000, 1000), (238, 232, 220)); d = ImageDraw.Draw(im)
    d.ellipse([200, 200, 800, 420], fill=(250, 250, 250), outline=(160, 160, 160), width=6); d.rectangle([200, 300, 800, 800], fill=(250, 250, 250), outline=(160, 160, 160), width=6)
    d.rectangle([420, 600, 580, 700], fill=(220, 60, 50)); d.line([800, 760, 980, 980], fill=(30, 30, 30), width=14)
    out["rice"] = folder / "rice.jpg"; im.save(out["rice"], quality=90)
    return out
