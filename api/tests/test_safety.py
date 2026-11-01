import pytest

from api.pipeline import mock, safety


@pytest.mark.parametrize("text,cat", [
    ("Selang gas kompor saya bocor, bau gas", "gas"),
    ("MCB di rumah turun terus", "mains"),
    ("stop kontak meleleh", "mains"),
    ("microwave tidak panas", "hv"),
    ("minyak rem motor habis", "hv"),
    ("tangan saya luka berdarah kena obeng", "medical"),
    ("my gas leak smells", "gas"),
    ("tadi saya kesetrum pas colok pompa", "shock"),
    ("I got shocked by the kettle plug", "shock"),
    ("rice cooker keluar asap dan bau gosong", "fire"),
    ("baterai hp menggembung", "fire"),
    ("kabel konslet lalu mati lampu", "mains"),
    ("freon AC habis", "hv"),
    ("the charger caught fire", "fire"),
])
def test_hard_stops(text, cat):
    g = safety.check_text(text, "id")
    assert not g.allowed and g.category == cat and g.reason


@pytest.mark.parametrize("text", [
    "Motor Honda Beat susah hidup", "kran wastafel menetes", "pompa air bunyi tapi air tidak keluar", "kipas angin berisik",
    "magic com lampunya mati", "knalpot motor putih sedikit",
    "api kompor kecil", "tombol power kipas macet", "aki motor soak",
    "motor brebet kalau digas, tarik gas tersendat",  # throttle, not cooking gas  # allowed at the gate; the plan check / diagnosis stops it later
])
def test_everyday_repairs_pass(text):
    assert safety.check_text(text).allowed


def test_messages_in_every_language():
    for lang in ("id", "jv", "en"):
        assert safety.check_text("bau gas", lang).reason
        assert safety.RED_MESSAGE[lang] and safety.DISCLAIMER[lang] and safety.BASE_RULES[lang]


def test_plan_check_blocks_mains_internals():
    g = safety.check_plan(["Buka casing bawah rice cooker untuk memeriksa elemen pemanas"], "id")
    assert not g.allowed and g.category == "mains"
    assert not safety.check_plan(["Bleed the brake fluid from the caliper"], "en").allowed


def test_plan_check_allows_safe_plans():
    for sc in ("motor", "faucet"):
        plan = mock.plan(sc, "id")
        assert safety.check_plan([s["instruction"] for s in plan["steps"]]).allowed


def test_new_categories_have_all_languages():
    for cat in ("fire", "shock"):
        for lang in ("id", "jv", "en"):
            assert safety._msg(cat, lang)
    assert "113" in safety._msg("fire", "en") and "119" in safety._msg("shock", "id")


# street Indonesian and Javanese wordings the first rule set missed
@pytest.mark.parametrize("text,cat", [
    ("kulkas nyetrum kena tangan", "shock"),
    ("dispenser nyetrum pas disentuh", "shock"),
    ("kena disengat listrik pas colok", "shock"),
    ("kabel PLN putus di depan rumah", "mains"),
    ("trafo tiang meledak tadi malam", "mains"),
    ("listrik 3 fase di bengkel konslet", "mains"),
    ("listrik ngeletik percikan api di stopkontak", "fire"),
    ("percikan api dari stop kontak pas dicolok", "fire"),
    ("kabel listrik njeblug", "fire"),
    ("aki meledak pas dicas", "fire"),
    ("kompor mbledug", "fire"),
    ("kompor nyemprot api gedhe", "fire"),
    ("baterai lithium nggembung", "fire"),
    ("baterai hp gembung panas", "fire"),
    ("aki motor bengkak", "fire"),
    ("bensin netes ing mesin panas", "hv"),
    ("bensin menetes dekat knalpot", "hv"),
    ("kompresor kulkas mau ganti sendiri", "hv"),
    ("anakku keracunan gas", "medical"),
    ("sesak napas habis ngelas", "medical"),
])
def test_street_wording_hard_stops(text, cat):
    g = safety.check_text(text, "id")
    assert not g.allowed and g.category == cat


@pytest.mark.parametrize("text", [
    "ban belakang meledak kena paku",
    "nyetrum aki motor",
    "bensin netes dari karburator",
    "tegangan aki 12 volt kurang",
    "listrik PLN padam pompa mati",
    "kabel gas motor putus",
    "kabel rem putus",
    "kabel charger putus",
    "tidak ada percikan api di busi",
    "percikan api busi lemah",
    "no spark at the sparking plug",
    "aki soak",
    "trafo charger hp panas",
])
def test_street_wording_no_false_stop(text):
    assert safety.check_text(text, "id").allowed, text


@pytest.mark.parametrize("step,cat", [
    ("Isi ulang freon AC dengan selang manifold.", "hv"),
    ("Cabut kapasitor besar di papan TV tabung.", "hv"),
    ("Perbaiki kebocoran pipa gas dengan lakban.", "gas"),
    ("Tutup kebocoran bensin pakai lem dekat knalpot panas.", "hv"),
    ("Cabut baterai lithium yang menggembung dengan obeng.", "fire"),
    ("Test the wires with the mains live and measure voltage at the socket.", "mains"),
    ("Open the control board and touch the terminals while plugged in.", "mains"),
    ("Bypass the thermal fuse with a wire.", "mains"),
    ("Jumper the safety switch of the water heater.", "mains"),
])
def test_plan_guard_new_dangerous_steps(step, cat):
    g = safety.check_plan([step], "en")
    assert not g.allowed and g.category == cat


@pytest.mark.parametrize("step", [
    "Do not touch the terminals while plugged in.",
    "Jangan pegang kabel saat tercolok.",
    "Never bypass the thermal fuse.",
    "Make sure the pump is unplugged, then open the priming plug.",
    "Tarik tuas gas dan cek kabel gas motor.",
    "Check the fuel line clamp for cracks then tighten it.",
    "Ganti kampas rem depan.",
])
def test_plan_guard_new_rules_keep_safe_steps(step):
    assert safety.check_plan([step], "en").allowed, step
