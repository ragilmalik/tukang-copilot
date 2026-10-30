"""Safety gate (see docs/SAFETY.md). Three layers:

1. `check_text`: a fast keyword gate on the user's own words. Runs before any paid call, works offline.
2. The model's `safety_level` in the Diagnosis (red ends guidance).
3. `check_plan`: scans every generated plan for hard-stop actions, forcing red even if the model said green.

Hard stops: gas lines, house/mains wiring and panels, opening mains-powered internals, high voltage
(microwave, CRT, capacitors), brake hydraulics, fuel leaks near heat, airbags, and anything about the
human body (no medical advice, ever).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_MSG = {
    "gas": {
        "id": "Masalah gas berbahaya. Matikan kompor, buka jendela, jangan nyalakan saklar, dan hubungi teknisi resmi.",
        "jv": "Masalah gas mbebayani. Pateni kompor, bukak jendela, aja nguripke saklar, lan hubungi teknisi resmi.",
        "en": "Gas problems are dangerous. Turn off the stove, open windows, don't touch switches, and call a certified technician."},
    "mains": {
        "id": "Instalasi listrik rumah dan bagian dalam alat bertegangan 220V harus ditangani teknisi atau servis resmi.",
        "jv": "Instalasi listrik omah lan jeroan piranti 220V kudu ditangani teknisi utawa servis resmi.",
        "en": "House wiring and the inside of mains-powered appliances need a licensed electrician or service centre."},
    "hv": {
        "id": "Bagian ini menyimpan energi berbahaya (tegangan tinggi, rem hidrolik, bahan bakar, atau airbag). Bawa ke servis resmi.",
        "jv": "Bagean iki nyimpen energi mbebayani (tegangan dhuwur, rem hidrolik, bensin, utawa airbag). Gawanen menyang servis resmi.",
        "en": "This part stores dangerous energy (high voltage, brake hydraulics, fuel, or an airbag). Take it to a service centre."},
    "fire": {
        "id": "Ada api, asap, atau baterai menggembung. Jauhi barangnya, matikan listrik dari sumbernya bila aman, dan hubungi pemadam kebakaran (113).",
        "jv": "Ana geni, kukus, utawa baterai mlembung. Adohana barange, pateni listrik saka sumbere yen aman, lan hubungi pemadam kebakaran (113).",
        "en": "Fire, smoke or a swollen battery. Keep away from it, cut power at the source only if it is safe, and call the fire service (113)."},
    "shock": {
        "id": "Kena setrum itu serius. Jangan sentuh alatnya, matikan MCB bila aman, dan hubungi tenaga medis (119) bila pusing, nyeri dada, atau luka bakar.",
        "jv": "Kena setrum iku serius. Aja nyenthuh piranti, pateni MCB yen aman, lan hubungi tenaga medis (119) yen mumet, nyeri dhadha, utawa kobong.",
        "en": "An electric shock is serious. Don't touch the device, switch off the breaker if it is safe, and call a medical professional (119) if you feel dizzy, have chest pain or burns."},
    "medical": {
        "id": "Tukang Copilot hanya untuk memperbaiki barang, bukan kesehatan. Untuk luka atau sakit, hubungi tenaga medis (119).",
        "jv": "Tukang Copilot mung kanggo ndandani barang, dudu kesehatan. Yen tatu utawa lara, hubungi tenaga medis (119).",
        "en": "Tukang Copilot repairs things, not people. For injuries or illness, contact a medical professional."},
}

_TEXT_RULES: list[tuple[str, str]] = [
    # "gas" alone also means the throttle on a motorbike ("tarik gas"), so only cooking/LPG gas contexts stop
    (r"\b(elpiji|lpg|tabung gas|selang gas|regulator gas|bau gas|gas bocor|bocor gas|kompor gas|gas leak|gas smell|smell gas|gas line|gas hose)\b", "gas"),
    (r"\b(mcb|panel listrik|sekring utama|meteran pln|kwh meter|fuse box|breaker box|kabel (di )?dalam tembok|instalasi listrik|stop ?kontak (terbakar|meleleh)|korsleting|konsleting|konslet|korslet|short circuit)\b", "mains"),
    (r"\b(microwave|magnetron|crt|kapasitor tegangan tinggi|high voltage|airbag|minyak rem|rem hidrolik|brake fluid|brake hydraulic|bensin bocor|fuel leak|freon|refrigerant|kompresor ac|ac compressor)\b", "hv"),
    (r"\b(kesetrum|ke setrum|tersetrum|disetrum|kena setrum|tersengat listrik|sengatan listrik|electric shock|electrocut\w*|got shocked|shocked me)\b", "shock"),
    (r"\b(kebakaran|terbakar|api menyala|keluar api|keluar asap|berasap|on fire|caught fire|catching fire|flames?|smoke coming|baterai( \w+)? (menggembung|kembung|mlembung)|swollen battery|battery swelling)\b", "fire"),
    (r"\b(luka|berdarah|sakit|obat|dokter|demam|pingsan|patah tulang|injury|bleeding|medicine|doctor|symptom)\b", "medical"),
]

# actions a plan must never ask for (checked on instruction text, any language)
_PLAN_RULES: list[tuple[str, str]] = [
    (r"(buka|bongkar|open|remove).{0,30}(casing|cover|tutup|housing|body).{0,40}(220|mains|listrik|power board|pcb|elemen pemanas|heating element)", "mains"),
    (r"(buka|bongkar|open|disassemble).{0,40}(rice cooker|magic ?com|microwave|kulkas|fridge|ac |air conditioner|dispenser)", "mains"),
    (r"(lepas|buka|bleed|kuras).{0,30}(minyak rem|selang rem|brake (fluid|line|caliper piston))", "hv"),
    (r"(sambung|ganti|tap|splice).{0,30}(kabel|wire).{0,30}(tembok|wall|panel|mcb|pln)", "mains"),
    (r"(selang gas|regulator gas|gas hose|gas line)", "gas"),
]


@dataclass
class Gate:
    allowed: bool
    category: str = ""
    reason: str = ""


def _msg(cat: str, lang: str) -> str:
    return _MSG[cat].get(lang, _MSG[cat]["en"])


def check_text(text: str, lang: str = "id") -> Gate:
    """Hard-stop words in what the user said or typed."""
    t = (text or "").lower()
    for pat, cat in _TEXT_RULES:
        if re.search(pat, t):
            return Gate(False, cat, _msg(cat, lang))
    return Gate(True)


def check_plan(instructions: list[str], lang: str = "id") -> Gate:
    """Hard-stop actions in a generated plan."""
    t = " \n".join(instructions).lower()
    for pat, cat in _PLAN_RULES:
        if re.search(pat, t):
            return Gate(False, cat, _msg(cat, lang))
    return Gate(True)


BASE_RULES = {
    "id": ["Cabut steker / matikan mesin dan tunggu dingin sebelum mulai.", "Pakai sarung tangan dan kacamata bila ada serpihan, bensin, atau cairan."],
    "jv": ["Copot steker / pateni mesin lan enteni adhem sadurunge miwiti.", "Nganggo sarung tangan lan kacamata yen ana pecahan, bensin, utawa cairan."],
    "en": ["Unplug it / switch the engine off and let it cool before you start.", "Wear gloves and eye protection around shards, fuel or liquids."],
}

RED_MESSAGE = {
    "id": "Perbaikan ini berisiko tinggi. Demi keselamatan, bawa ke servis resmi atau panggil teknisi.",
    "jv": "Ndandani iki risikone dhuwur. Supaya slamet, gawanen menyang servis resmi utawa undangen teknisi.",
    "en": "This repair is high-risk. For your safety, take it to a service centre or call a professional.",
}

DISCLAIMER = {
    "id": "Panduan ini dibuat AI dan bisa salah. Kamu bertanggung jawab atas keselamatanmu. Berhenti bila ragu.",
    "jv": "Pandhuan iki digawe AI lan bisa luput. Kowe tanggung jawab marang keslametanmu. Mandheg yen mangu.",
    "en": "This guide is AI-generated and can be wrong. You are responsible for your safety. Stop if unsure.",
}
