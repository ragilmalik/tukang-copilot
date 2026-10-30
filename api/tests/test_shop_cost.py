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
