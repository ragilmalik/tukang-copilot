"""Offline stand-ins for every Meta call (MOCK=1 or no MODEL_API_KEY). The app, the tests and the demo
fallback all run on these for free. Four scenarios from SPEC §8, picked by keywords:

  * motor  - Honda Beat won't start: loose / fouled spark plug cap        (green)
  * pump   - Shimizu water pump runs but no water: lost prime / foot valve   (amber)
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
    if re.search(r"\b(pompa|pump|shimizu|sanyo|panasonic pump|sumur|jet pump|foot valve|klep)\b", t):
        return "pump"
    if re.search(r"\b(kempes|kempis|ban (motor |belakang |depan )?(bocor|kempes|kempis|gembos)|gembos|tambal ban|tubeless|flat (tyre|tire)|puncture|tyre|tire|nail in (the|my) (tyre|tire))\b", t):
        return "tire"
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
    if sc == "pump":
        return {"object": _L(lang, "Pompa air sumur dangkal (Shimizu)", "Shallow-well water pump (Shimizu)"), "brand_model_guess": "Shimizu PS-128", "category": "pump",
                "components": [{"id": "c1", "name": _L(lang, "Baut pancingan", "Priming plug"), "sam_phrase": "priming plug", "condition": ""},
                               {"id": "c2", "name": _L(lang, "Pipa hisap", "Suction pipe"), "sam_phrase": "suction pipe", "condition": _L(lang, "sambungan agak basah", "joint looks damp")},
                               {"id": "c3", "name": _L(lang, "Steker pompa", "Pump power plug"), "sam_phrase": "power plug", "condition": ""}],
                "visible_issues": [_L(lang, "Motor berputar tapi pipa keluar kering", "Motor spins but the outlet pipe is dry")]}
    if sc == "tire":
        return {"object": _L(lang, "Ban belakang motor skutik (tubeless)", "Scooter rear tyre (tubeless)"), "brand_model_guess": "", "category": "motor",
                "components": [{"id": "c1", "name": _L(lang, "Tapak ban", "Tyre tread"), "sam_phrase": "tyre tread", "condition": _L(lang, "ada benda logam menancap", "a metal object is stuck in it")},
                               {"id": "c2", "name": _L(lang, "Pentil (ventil)", "Valve stem"), "sam_phrase": "valve stem", "condition": ""},
                               {"id": "c3", "name": _L(lang, "Pelek", "Wheel rim"), "sam_phrase": "wheel rim", "condition": ""}],
                "visible_issues": [_L(lang, "Ban kempes dan ada paku di tapak", "Flat tyre with a nail in the tread")]}
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
    if sc == "pump":
        return {"problem_summary": _L(lang, "Pompa menyala dan berputar, tapi air tidak keluar: pompa kehilangan pancingan.", "The pump runs but no water comes out: it has lost its prime."),
                "causes": [{"title": _L(lang, "Pompa kehilangan air pancingan", "Pump lost its prime"), "confidence": 60, "evidence": [_L(lang, "Motor berputar, pipa keluar kering", "Motor spins, outlet dry")], "component_ids": ["c1"]},
                           {"title": _L(lang, "Foot valve (klep kaki) tersumbat atau bocor", "Clogged or leaking foot valve"), "confidence": 30, "evidence": [_L(lang, "Pancingan cepat habis", "Prime keeps draining")], "component_ids": ["c2"]},
                           {"title": _L(lang, "Sambungan pipa hisap bocor udara", "Air leak in the suction pipe joint"), "confidence": 10, "evidence": [_L(lang, "Sambungan terlihat basah", "Joint looks damp")], "component_ids": ["c2"]}],
                "safety_level": "amber", "safety_reason": _L(lang, "Pompa listrik 220V dekat air: selalu cabut steker dulu dan kerjakan dengan tangan kering.", "A 220V pump near water: always unplug first and work with dry hands."),
                "tools": [{"name": _L(lang, "Kunci ring 17 mm", "17 mm ring spanner"), "est_price_idr": 20000}, {"name": _L(lang, "Ember atau gayung", "Bucket or water scoop"), "est_price_idr": 10000}],
                "parts": [{"name": "Seal tape", "est_price_idr": 5000}, {"name": _L(lang, "Foot valve 1\" (cadangan)", "1\" foot valve (spare)"), "est_price_idr": 35000}],
                "difficulty": 2, "minutes_estimate": 25, "follow_up_question": ""}
    if sc == "tire":
        return {"problem_summary": _L(lang, "Ban belakang kempes pelan-pelan: ada paku menancap di tapak ban tubeless.", "The rear tyre is going flat: a nail is stuck in the tubeless tread."),
                "causes": [{"title": _L(lang, "Paku menancap di tapak ban", "Nail stuck in the tread"), "confidence": 65, "evidence": [_L(lang, "Ada benda logam di tapak ban", "A metal object sits in the tread")], "component_ids": ["c1"]},
                           {"title": _L(lang, "Pentil (ventil) bocor", "Leaking valve stem"), "confidence": 25, "evidence": [_L(lang, "Kempes pelan tanpa luka terlihat", "Slow leak with no visible wound")], "component_ids": ["c2"]},
                           {"title": _L(lang, "Pelek penyok atau bibir ban tidak rapat", "Bent rim or unseated bead"), "confidence": 10, "evidence": [], "component_ids": ["c3"]}],
                "safety_level": "amber", "safety_reason": _L(lang, "Motor harus stabil di standar tengah dan jangan ditambal di jalan ramai; tambalan cacing hanya sementara.", "Keep the bike steady on its centre stand and never fix it on a busy road; a plug is a temporary repair."),
                "tools": [{"name": _L(lang, "Set tambal ban tubeless (cacing)", "Tubeless tyre plug kit"), "est_price_idr": 25000}, {"name": _L(lang, "Tang", "Pliers"), "est_price_idr": 30000}, {"name": _L(lang, "Pompa tangan atau pompa angin", "Hand pump or air compressor"), "est_price_idr": 50000}],
                "parts": [{"name": _L(lang, "Cacing tambal cadangan", "Spare plug strips"), "est_price_idr": 10000}, {"name": _L(lang, "Air sabun dalam botol semprot", "Soapy water in a spray bottle"), "est_price_idr": 3000}],
                "difficulty": 2, "minutes_estimate": 25, "follow_up_question": ""}
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
    if sc == "tire" and cause_index >= 1:
        s = [("c3", "Naikkan motor ke standar tengah di tempat datar dan jauh dari jalan ramai.", "Put the bike on its centre stand on level ground, away from traffic.", "Motor berdiri stabil di standar tengah.", "The bike stands steady on its centre stand.", False),
             ("c2", "Semprot pentil dengan air sabun dan lihat apakah muncul gelembung.", "Spray the valve stem with soapy water and look for bubbles.", "Pentil basah berbusa dan terlihat jelas.", "The valve is wet with foam and clearly visible.", False),
             ("c2", "Kencangkan inti pentil dengan alat pembuka pentil, putar searah jarum jam sampai kencang pas.", "Tighten the valve core with a valve-core tool, clockwise until snug.", "Gelembung berhenti keluar dari pentil.", "Bubbles stop coming from the valve.", True),
             ("c2", "Pompa ban sesuai angka di stiker motor, pasang tutup pentil, lalu cek lagi dengan air sabun.", "Pump the tyre to the figure on the bike's sticker, refit the cap, then re-check with soapy water.", "Tidak ada gelembung baru di pentil.", "No new bubbles at the valve.", False)]
        done, pro, cause = (_L(lang, "Ban tetap keras setelah 30 menit.", "The tyre stays firm after 30 minutes."),
                            _L(lang, "Bila masih kempes, bawa ke tukang tambal ban untuk cek pelek dan bibir ban.", "If it still goes flat, take it to a tyre shop to check the rim and bead."),
                            _L(lang, "Pentil (ventil) bocor", "Leaking valve stem"))
    elif sc == "tire":
        s = [("c3", "Naikkan motor ke standar tengah di tempat datar dan jauh dari jalan ramai.", "Put the bike on its centre stand on level ground, away from traffic.", "Motor berdiri stabil di standar tengah.", "The bike stands steady on its centre stand.", False),
             ("c1", "Putar roda pelan sampai paku terlihat, lalu tarik paku lurus dengan tang.", "Turn the wheel slowly until the nail shows, then pull it straight out with pliers.", "Paku sudah keluar dan lubangnya terlihat.", "The nail is out and the hole is visible.", True),
             ("c1", "Lebarkan lubang dengan alat peraut dari set tambal, masukkan cacing ke jarum tusuk yang sudah diolesi lem.", "Ream the hole with the rasp from the kit, then thread a glued plug strip onto the insertion needle.", "Cacing terpasang rapi di ujung jarum.", "The plug strip sits neatly on the needle.", False),
             ("c1", "Tusuk jarum lurus ke lubang, tarik jarum cepat dan lurus, potong sisa cacing, lalu pompa ban sesuai angka di stiker motor.", "Push the needle straight in, pull it out fast and straight, trim the excess strip, then pump to the figure on the bike's sticker.", "Tidak ada gelembung saat disemprot air sabun.", "No bubbles when sprayed with soapy water.", False)]
        done, pro, cause = (_L(lang, "Ban tetap keras setelah 30 menit dan air sabun tidak berbusa.", "The tyre stays firm after 30 minutes and soapy water does not foam."),
                            _L(lang, "Tambalan cacing bersifat sementara. Bawa ke tukang tambal ban bila lukanya di dinding samping ban atau lebih dari 6 mm.", "A plug is temporary. See a tyre shop if the wound is in the sidewall or wider than 6 mm."),
                            _L(lang, "Paku menancap di tapak ban", "Nail stuck in the tread"))
    elif sc == "pump" and cause_index >= 1:
        s = [("c3", "Cabut steker pompa dari stop kontak dan pastikan tangan kering.", "Unplug the pump at the socket and make sure your hands are dry.", "Steker tercabut, pompa diam.", "The plug is out and the pump is silent.", False),
             ("c2", "Angkat pipa hisap dari sumur sampai foot valve di ujungnya terlihat.", "Pull the suction pipe up out of the well until the foot valve at its end shows.", "Foot valve di ujung pipa terlihat jelas.", "The foot valve at the pipe end is clearly visible.", False),
             ("c2", "Bersihkan saringan foot valve dari lumpur dan daun, lalu tekan kleppnya: harus membuka dan menutup lancar.", "Clean mud and leaves off the foot valve strainer, then press the flap: it must open and close freely.", "Saringan bersih dan klep bergerak lancar.", "The strainer is clean and the flap moves freely.", True),
             ("c1", "Turunkan lagi pipanya, isi air pancingan sampai meluap, pasang baut, lalu colok steker.", "Lower the pipe back, fill priming water until it overflows, refit the plug, then plug in.", "Air keluar deras dari kran.", "Water flows strongly from the tap.", False)]
        done, pro, cause = (_L(lang, "Air mengalir deras dalam 1 menit dan pancingan tidak habis lagi.", "Water flows within 1 minute and the prime holds."),
                            _L(lang, "Bila motor mendengung tapi tidak berputar, panas, atau berbau hangus, panggil teknisi pompa.", "If the motor hums without spinning, runs hot, or smells burnt, call a pump technician."),
                            _L(lang, "Foot valve (klep kaki) tersumbat atau bocor", "Clogged or leaking foot valve"))
    elif sc == "pump":
        s = [("c3", "Cabut steker pompa dari stop kontak dan pastikan tangan kering.", "Unplug the pump at the socket and make sure your hands are dry.", "Steker tercabut, pompa diam.", "The plug is out and the pump is silent.", False),
             ("c1", "Buka baut pancingan di atas pompa dengan kunci ring 17 mm, putar berlawanan jarum jam.", "Undo the priming plug on top of the pump with the 17 mm spanner, anticlockwise.", "Lubang pancingan di atas pompa terbuka.", "The priming hole on top of the pump is open.", True),
             ("c1", "Tuang air bersih pelan-pelan ke lubang pancingan sampai penuh dan meluap.", "Pour clean water slowly into the priming hole until it is full and overflowing.", "Air terlihat penuh sampai bibir lubang.", "Water is full to the rim of the hole.", False),
             ("c1", "Lilit baut dengan seal tape, pasang lagi sampai kencang, colok steker, lalu buka kran.", "Wrap the plug in seal tape, screw it back tight, plug in, then open a tap.", "Air keluar deras dari kran.", "Water flows strongly from the tap.", False)]
        done, pro, cause = (_L(lang, "Air mengalir deras dalam 1 menit.", "Water flows strongly within 1 minute."),
                            _L(lang, "Bila pancingan cepat habis lagi, cek foot valve; bila motor panas atau berbau hangus, panggil teknisi pompa.", "If the prime drains again, check the foot valve; if the motor runs hot or smells burnt, call a pump technician."),
                            _L(lang, "Pompa kehilangan air pancingan", "Pump lost its prime"))
    elif sc == "faucet" and cause_index >= 1:
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
          "priming plug": (0.44, 0.18, 0.58, 0.32), "suction pipe": (0.02, 0.50, 0.30, 0.66), "power plug": (0.72, 0.72, 0.94, 0.94),
          "cook switch": (0.40, 0.60, 0.60, 0.72), "power cord": (0.70, 0.70, 0.95, 0.95),
          "tyre tread": (0.38, 0.02, 0.62, 0.22), "valve stem": (0.62, 0.49, 0.75, 0.60), "wheel rim": (0.34, 0.34, 0.60, 0.66)}


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
    # water pump (blue motor + pump head, suction pipe left, power cord bottom right)
    im = Image.new("RGB", (1100, 900), (180, 175, 165)); d = ImageDraw.Draw(im)
    d.rectangle([0, 700, 1100, 900], fill=(120, 115, 105)); d.rounded_rectangle([300, 300, 760, 640], radius=40, fill=(30, 90, 170), outline=(15, 40, 90), width=6)
    d.ellipse([460, 160, 660, 320], fill=(200, 200, 205), outline=(90, 90, 95), width=6); d.rectangle([510, 180, 600, 260], fill=(110, 110, 115))
    d.rectangle([20, 470, 320, 570], fill=(235, 235, 235), outline=(150, 150, 150), width=4); d.rectangle([760, 400, 1080, 480], fill=(235, 235, 235), outline=(150, 150, 150), width=4)
    d.line([700, 640, 900, 760, 1000, 820], fill=(20, 20, 20), width=14); d.rectangle([960, 790, 1030, 850], fill=(40, 40, 40))
    out["pump"] = folder / "pump.jpg"; im.save(out["pump"], quality=90)
    # flat scooter tyre (tread with a nail, rim, valve stem)
    im = Image.new("RGB", (1000, 1000), (170, 168, 160)); d = ImageDraw.Draw(im)
    d.rectangle([0, 820, 1000, 1000], fill=(110, 108, 100)); d.ellipse([140, 120, 860, 840], fill=(25, 25, 27), outline=(10, 10, 10), width=8)
    d.ellipse([330, 310, 670, 650], fill=(190, 192, 196), outline=(90, 90, 95), width=6); d.ellipse([440, 420, 560, 540], fill=(120, 120, 125))
    d.rectangle([640, 520, 700, 560], fill=(60, 60, 62)); d.rectangle([488, 150, 512, 230], fill=(130, 130, 135))
    d.line([500, 135, 500, 70], fill=(230, 160, 40), width=10); d.polygon([(486, 70), (514, 70), (500, 40)], fill=(230, 160, 40)); d.ellipse([472, 130, 528, 150], fill=(240, 240, 245))
    out["tire"] = folder / "tire.jpg"; im.save(out["tire"], quality=90)
    return out
