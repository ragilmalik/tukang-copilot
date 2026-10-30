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
