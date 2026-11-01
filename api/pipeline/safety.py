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
    # v1.25 red-team fixes (scripts/run_eval.py found these slipping through): Javanese "gase", gas pipes and
    # cylinders, LPG "tabung melon", 220/240 V panels, consumer units/RCDs, wall sockets, ceiling fan wiring,
    # water heater elements, car brake lines and brake failure.
    (r"\b(kompor|tabung|selang|pipa|regulator|katup) gas\w*|\bgas(e|nya|ne)? (bocor|ambu\w*|mambu|desis\w*|hiss\w*|leak\w*)\b|\b(tabung|gas) melon\b"
     r"|\bgas (pipe|cylinder|bottle|regulator|valve|cooker|stove|heater|tank)s?\b|\bregulator\b.{0,20}\b(elpiji|lpg|tabung)\b", "gas"),
    (r"\b(2[234]0) ?v(olt)?\b.{0,25}\b(panel|wiring|kabel|instalasi|socket|stop ?kontak|outlet|breaker)|\b(panel|breaker|wiring|kabel|instalasi)\b.{0,25}\b(2[234]0) ?v(olt)?\b"
     r"|\b(consumer unit|rcd|rcbo|elcb|breaker panel|electrical panel|circuit breaker|rewir\w*|house wiring|mains wiring|wall socket|wall outlet)\b"
     r"|\bstop ?kontak\b.{0,25}\b(tembok|dinding|panas|meleleh|gosong|percik\w*)\b|\bkabel\b.{0,20}\b(plafon|langit-langit|ceiling)\b"
     r"|\b(kipas (angin )?(plafon|gantung|langit-langit)|ceiling fan)\b.{0,60}\b(kabel|wir\w*|sambung\w*|pasang|install\w*|reconnect\w*|connect\w*)"
     r"|\b(kabel|wir\w*|sambung\w*|reconnect\w*)\b.{0,60}\b(kipas (angin )?(plafon|gantung)|ceiling fan|ceiling)\b"
     r"|\bwater heater\b.{0,40}\b(bongkar|buka|elemen|open|element)", "mains"),
    (r"\b(brake (line|hose|pipe)s?|selang rem|pipa rem|minyak rem\w*|rem (mobil(ku)? )?blong|brakes? (failed|failure|gone))\b", "hv"),
    # "gas" alone also means the throttle on a motorbike ("tarik gas"), so only cooking/LPG gas contexts stop
    (r"\b(elpiji|lpg|tabung gas|selang gas|regulator gas|bau gas|gas bocor|bocor gas|kompor gas|gas leak|gas smell|smell gas|gas line|gas hose)\b", "gas"),
    (r"\b(mcb|panel listrik|sekring utama|meteran pln|kwh meter|fuse box|breaker box|kabel (di )?dalam tembok|instalasi listrik|stop ?kontak (terbakar|meleleh)|korsleting|konsleting|konslet|korslet|short circuit|kabel pln|tiang listrik|tiang pln|jaringan pln|kabel listrik (putus|jatuh|menjuntai|njuntai)|power line|downed line|(trafo|travo|transformer)( \w+)? (meledak|terbakar|njeblug|mbledug|bocor|exploded)|tiga fase|3 fase|three.?phase|(380|400) ?v(olt)?)\b", "mains"),
    (r"\b(microwave|magnetron|crt|kapasitor tegangan tinggi|high voltage|airbag|minyak rem|rem hidrolik|brake fluid|brake hydraulic|bensin bocor|fuel leak|freon|refrigerant|kompresor ac|ac compressor|kompresor (kulkas|lemari es|freezer|fridge)|(tv|televisi|monitor) tabung|(bensin|pertalite|fuel|petrol|gasoline)( \w+)? (netes|menetes|merembes|ngeces|dripping|seeping|leaking)( \w+){0,4} (panas|knalpot|exhaust|muffler|hot)|(panas|knalpot|exhaust|muffler|hot)( \w+){0,4} (bensin|pertalite|fuel|petrol|gasoline)( \w+)? (netes|menetes|merembes|ngeces|dripping|seeping|leaking))\b", "hv"),
    (r"\b(kesetrum|ke setrum|tersetrum|disetrum|kena setrum|tersengat listrik|sengatan listrik|electric shock|electrocut\w*|got shocked|shocked me|nyetrum(?! ?(aki|accu|baterai|batre|hp))\w*|nyetrom\w*|kesetrom|kesengat listrik|disengat listrik|kesengat arus|dialiri listrik)\b", "shock"),
    (r"\b(kebakaran|terbakar|api menyala|keluar api|keluar asap|berasap|on fire|caught fire|catching fire|flames?|smoke coming|(baterai|batre|aki|accu|battery|lithium)( \w+){0,2} (n?g?g?embung|menggembung|kembung|mlembung|bengkak|mengembang|swollen|bloated|puffed)|swollen battery|battery swelling|percik(an)? api (dari|di|pada|ing) (stop ?kontak|kabel|colokan|listrik|mcb|saklar|kipas|setrika)|stop ?kontak\w* .{0,15}percik\w* api|ngeletik|meletik|sparks? (from|coming|flying)|sparking(?! plug)|(aki|accu|baterai|batre|kompor|tabung|trafo|travo|transformer|kabel|kapasitor|capacitor|battery|stove)( \w+){0,2} (meledak|mbledug|mbledos|njeblug|ngeblug|njeblugi|exploded|explodes|blew up|burst into flames?)|kompor( \w+)?( \w+)? (nyemprot\w*|nyembur\w*|menyembur|menyemprot)\b)", "fire"),
    (r"\b(luka|berdarah|sakit|obat|dokter|demam|pingsan|patah tulang|injury|bleeding|medicine|doctor|symptom|keracunan|diracuni|poison\w*|sesak (napas|nafas)|tidak bisa (bernapas|bernafas)|can.?t breathe)\b", "medical"),
]

# actions a plan must never ask for (checked on instruction text, any language)
_PLAN_RULES: list[tuple[str, str]] = [
    (r"(buka|bongkar|open|remove).{0,30}(casing|cover|tutup|housing|body).{0,40}(220|mains|listrik|power board|pcb|elemen pemanas|heating element)", "mains"),
    (r"(buka|bongkar|open|disassemble).{0,40}(rice cooker|magic ?com|microwave|kulkas|fridge|ac |air conditioner|dispenser)", "mains"),
    (r"(lepas|buka|bleed|kuras).{0,30}(minyak rem|selang rem|brake (fluid|line|caliper piston))", "hv"),
    (r"(sambung|ganti|tap|splice).{0,30}(kabel|wire).{0,30}(tembok|wall|panel|mcb|pln)", "mains"),
    (r"(selang gas|regulator gas|gas hose|gas line)", "gas"),
    # v1.25 red-team: plans that touch LPG regulators, house panels, ceiling wiring or car brake lines
    (r"regulator.{0,40}(tabung|elpiji|lpg|gas cylinder|cylinder)|(elpiji|lpg|tabung gas|gas cylinder).{0,40}regulator", "gas"),
    (r"(buka|bongkar|ganti|open|replace|swap|rewire).{0,30}(panel listrik|mcb|consumer unit|breaker|rcd|fuse box)", "mains"),
    (r"(sambung|splice|connect|reconnect|join).{0,40}(kabel|wire|wiring).{0,40}(plafon|ceiling|langit-langit)", "mains"),
    (r"(lepas|ganti|buka|remove|replace|disconnect).{0,30}(brake (line|hose|pipe)|selang rem|pipa rem)", "hv"),
    # v1.25.4 audit 10: refrigerant, CRT, gas pipes, tank patching, swollen cells, live testing, bypassed safeties
    (r"(isi|tambah|refill|recharge|charge|ganti|bocor).{0,25}(freon|refrigerant)|\bmanifold (gauge|set)\b|\b(flyback|crt|tv tabung|anode cap)\b", "hv"),
    (r"(buang muatan|discharge|cabut|lepas|remove).{0,30}(kapasitor|capacitor).{0,30}(besar|tv|crt|microwave|tabung|high|large)", "hv"),
    (r"(perbaiki|tambal|tutup|sambung|las|repair|patch|seal|fix|lakban|tape).{0,30}(pipa gas|gas pipe|kebocoran gas|gas leak)|(pipa gas|gas pipe)", "gas"),
    (r"(tutup|tambal|lem|las|solder|weld|seal|patch|glue).{0,30}(tangki|tank|bensin|fuel).{0,40}(bocor|leak|retak|crack)|(tutup|tambal|lem|las|solder|weld|seal|patch|glue).{0,20}(kebocoran|leak\\w*).{0,15}(bensin|fuel|tangki|tank)", "hv"),
    (r"(cabut|bongkar|tusuk|bedah|buka|pierce|puncture|open|disassemble|cut).{0,30}(baterai|battery|lithium|sel).{0,30}(gembung|menggembung|swollen|bengkak|bloated)", "fire"),
    (r"(?<!not )(?<!n't )(?<!never )(?<!jangan )(?<!tidak )(?<!dilarang )(touch|sentuh|pegang|measure|ukur|test|tes|probe|bridge|jumper|bongkar|buka|open)\b.{0,40}(while|saat|ketika|selagi|sambil).{0,20}(plugged in|tercolok|powered on|energi[sz]ed|live|dialiri listrik)", "mains"),
    (r"\b(mains live|live mains|live (wire|terminal)s?|kabel (yang )?(hidup|bertegangan))\b", "mains"),
    (r"(?<!not )(?<!n't )(?<!never )(?<!jangan )(?<!tidak )(?<!dilarang )(bypass|jumper|short|bridge|lewati|jembatani|lepas)\b.{0,25}(thermal fuse|thermostat|termostat|sekring termal|safety (switch|cutoff|valve)|pengaman|saklar pengaman)", "mains"),
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
