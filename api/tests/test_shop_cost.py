"""Typical bengkel price vs doing it yourself (shop_cost_estimate_idr, diy_saving_idr)."""
import pytest

from api.coerce import coerce
from api.pipeline import engine, mock
from api.schemas import Diagnosis


def _new(samples, sc):
    texts = {"motor": "motor tidak mau hidup", "pump": "pompa air tidak keluar air", "faucet": "kran menetes", "tire": "ban kempes ada paku"}
    return engine.create([samples[sc]], "id", texts[sc])


@pytest.mark.parametrize("sc", ["motor", "pump", "faucet", "tire"])
def test_mock_scenarios_have_shop_price(sc):
    dx = Diagnosis.model_validate(mock.diagnosis(sc, "id"))
    assert dx.shop_cost_estimate_idr > 0
    assert dx.diy_saving_idr == dx.shop_cost_estimate_idr - dx.cost_estimate_idr
    assert dx.diy_saving_idr > 0


def test_red_stop_has_no_shop_price():
    dx = Diagnosis.model_validate(mock.diagnosis("rice", "id"))
    assert dx.shop_cost_estimate_idr == 0 and dx.diy_saving_idr == 0


def test_saving_never_negative():
    d = mock.diagnosis("faucet", "en")
    d["shop_cost_estimate_idr"] = 1000
    assert Diagnosis.model_validate(d).diy_saving_idr == 0


def test_missing_field_defaults_to_unknown():
    d = mock.diagnosis("faucet", "en")
    d.pop("shop_cost_estimate_idr")
    assert Diagnosis.model_validate(d).diy_saving_idr == 0


def test_coerce_repairs_written_price():
    d = mock.diagnosis("faucet", "id")
    d["shop_cost_estimate_idr"] = "Rp 75.000"
    out = coerce(Diagnosis, d)
    assert out["shop_cost_estimate_idr"] == 75000
    d["shop_cost_estimate_idr"] = "unknown"
    assert coerce(Diagnosis, d)["shop_cost_estimate_idr"] == 0


def test_session_and_report_carry_the_numbers(samples):
    sid = _new(samples, "pump")["id"]
    s = engine.run(sid)
    assert s["diagnosis"]["shop_cost_estimate_idr"] == 150000
    assert s["diagnosis"]["diy_saving_idr"] == 150000 - s["diagnosis"]["cost_estimate_idr"] > 0
    r = engine.report(sid)
    assert r["shop_cost_estimate_idr"] == 150000 and r["diy_saving_idr"] == s["diagnosis"]["diy_saving_idr"]


@pytest.mark.parametrize("raw,want", [
    ("75k", 75000), ("75 rb", 75000), ("Rp 75 ribu", 75000), ("1,5 juta", 1500000),
    ("2jt", 2000000), (90000, 90000), ("Rp 25.000", 25000), (-5, 0), ("900000000", 0), ("gratis", 0),
])
def test_price_units_and_implausible_values(raw, want):
    d = mock.diagnosis("faucet", "id")
    d["shop_cost_estimate_idr"] = raw
    assert coerce(Diagnosis, d)["shop_cost_estimate_idr"] == want


def test_red_stop_never_keeps_a_shop_price():
    d = mock.diagnosis("faucet", "id")
    d["safety_level"] = "red"
    d["shop_cost_estimate_idr"] = 300000
    out = coerce(Diagnosis, d)
    assert out["shop_cost_estimate_idr"] == 0
    assert Diagnosis.model_validate(out).diy_saving_idr == 0


def test_part_prices_accept_k_suffix():
    d = mock.diagnosis("faucet", "id")
    d["parts"] = [{"name": "seal", "est_price_idr": "12k"}]
    assert coerce(Diagnosis, d)["parts"][0]["est_price_idr"] == 12000
