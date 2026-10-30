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
])
def test_hard_stops(text, cat):
    g = safety.check_text(text, "id")
    assert not g.allowed and g.category == cat and g.reason


@pytest.mark.parametrize("text", [
    "Motor Honda Beat susah hidup", "kran wastafel menetes", "pompa air bunyi tapi air tidak keluar", "kipas angin berisik",
    "magic com lampunya mati",
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
