"""End-to-end pipeline runs in MOCK mode for every SPEC §8 scenario."""
import pytest
from PIL import Image

from api.pipeline import engine


def _new(samples, sc, lang="id", text=None):
    texts = {"motor": "Motor Honda Beat saya susah hidup", "pump": "Pompa air Shimizu bunyi tapi air tidak keluar", "faucet": "Kran wastafel menetes terus", "rice": "Rice cooker tidak panas", "tire": "Ban belakang motor kempes, ada paku"}
    return engine.create([samples[sc]], lang, text or texts[sc])


def test_faucet_green_full_run(samples):
    s = engine.run(_new(samples, "faucet")["id"])
    assert s["status"] == "ready"
    assert s["safety"]["level"] == "green"
    assert all(v["status"] in {"done", "skipped"} for v in s["stages"].values())
    assert len(s["plan"]["steps"]) == 4
    assert s["parts_image"] == "parts.jpg" and all(p["found"] for p in s["parts"].values())
    assert s["diagrams"]["3"]["file"] == "diagram_3.png"  # only the hidden step gets a Muse Image diagram
    assert s["cost"]["spent_usd"] == 0  # mock mode spends nothing


def test_motor_asks_follow_up_then_resumes(samples):
    sid = _new(samples, "motor")["id"]
    s = engine.run(sid)
    assert s["status"] == "needs_answer" and s["question"]
    assert s["stages"]["plan"]["status"] == "waiting"
    engine.answer(sid, "Tidak bau bensin")
    s = engine.run(sid)
    assert s["status"] == "ready" and s["safety"]["level"] == "amber"
    with pytest.raises(ValueError):
        engine.answer(sid, "again")


def test_rice_cooker_red_stop(samples):
    s = engine.run(_new(samples, "rice")["id"])
    assert s["status"] == "stopped" and s["safety"]["level"] == "red"
    assert s["plan"] is None and "servis" in s["stop_reason"]


def test_gate_stops_before_any_model_call(samples):
    s = engine.run(engine.create([samples["motor"]], "en", "there is a gas leak near the stove")["id"])
    assert s["status"] == "stopped" and s["stages"]["gate"]["status"] == "stopped"
    assert s["object_report"] is None


@pytest.mark.parametrize("text,word", [
    ("tadi saya kesetrum waktu colok pompa", "setrum"),
    ("the charger caught fire", "113"),
])
def test_shock_and_fire_stop_before_any_model_call(samples, text, word):
    lang = "id" if "setrum" in text else "en"
    s = engine.run(engine.create([samples["pump"]], lang, text)["id"])
    assert s["status"] == "stopped" and s["stages"]["gate"]["status"] == "stopped"
    assert s["object_report"] is None and word in s["stop_reason"]


@pytest.mark.parametrize("lang", ["id", "jv", "en"])
def test_languages(samples, lang):
    s = engine.run(_new(samples, "faucet", lang)["id"])
    assert s["status"] == "ready" and s["lang"] == lang


def test_step_check_pass_fail_and_escalate(samples, tmp_path):
    sid = engine.run(_new(samples, "faucet")["id"])["id"]
    dark = tmp_path / "dark.jpg"
    Image.new("RGB", (640, 480), (5, 5, 5)).save(dark)
    r1 = engine.check_step(sid, 1, dark)
    assert not r1["passed"] and r1["correction"] and not r1["escalate"]
    r2 = engine.check_step(sid, 1, dark)
    assert r2["escalate"] and r2["escalate_hint"]  # MAX_CHECK_FAILS=2 by default
    ok = engine.check_step(sid, 2, samples["faucet"])
    assert ok["passed"]
    rep = engine.report(sid)
    assert rep["steps_verified"] == 1 and rep["steps_total"] == 4


def test_step_check_errors(samples):
    sid = engine.run(_new(samples, "faucet")["id"])["id"]
    with pytest.raises(ValueError):
        engine.check_step(sid, 99, samples["faucet"])


def test_replan_moves_to_next_cause_then_exhausts(samples):
    sid = _new(samples, "motor")["id"]
    engine.run(sid); engine.answer(sid, "tidak"); engine.run(sid)
    s = engine.replan(sid, "cop sudah rapat, tetap mati")
    assert s["status"] == "ready" and s["cause_index"] == 1 and "Busi" in s["plan"]["cause_title"]
    assert s["checks"] == {}
    s = engine.replan(sid, "masih mati")
    assert s["cause_index"] == 2
    s = engine.replan(sid, "masih mati")
    assert s["status"] == "exhausted" and s["stop_reason"]
    assert len(engine.report(sid)["attempts"]) == 3


def test_replan_report_goes_through_gate(samples):
    sid = engine.run(_new(samples, "faucet")["id"])["id"]
    s = engine.replan(sid, "sekarang tangan saya berdarah")
    assert s["status"] == "stopped"


def test_audio_is_deleted_after_listen(samples, tmp_path, monkeypatch):
    import subprocess
    wav = tmp_path / "v.wav"
    from api.pipeline import media
    subprocess.run([media.ffmpeg_exe(), "-loglevel", "error", "-f", "lavfi", "-i", "sine=frequency=440:duration=1", str(wav)], check=True)
    s = engine.create([samples["motor"]], "id", "", wav)
    d = engine.session_dir(s["id"])
    assert (d / "voice.wav").exists()
    s = engine.run(s["id"])
    assert s["transcript"] and not (d / "voice.wav").exists()


def test_bad_session_ids_rejected():
    for bad in ["../etc", "a/b", "", "x" * 40]:
        with pytest.raises(ValueError):
            engine.session_dir(bad)


def test_cleanup_removes_old_sessions(samples):
    sid = engine.run(_new(samples, "faucet")["id"])["id"]
    assert engine.cleanup(max_age_hours=1) == 0
    assert engine.cleanup(max_age_hours=-1) == 1
    with pytest.raises(FileNotFoundError):
        engine.load(sid)


def test_budget_guard(samples, monkeypatch):
    from api import cost
    m = cost.Meter(0.01)
    m.charge("x", 0.009)
    with pytest.raises(cost.BudgetExceeded):
        m.check(0.01)


def test_pump_amber_full_run_and_replan_to_foot_valve(samples):
    s = engine.run(_new(samples, "pump")["id"])
    assert s["status"] == "ready" and s["safety"]["level"] == "amber"
    assert s["object_report"]["category"] == "pump" and all(p["found"] for p in s["parts"].values())
    assert "pancingan" in s["plan"]["cause_title"].lower()
    assert s["plan"]["steps"][0]["component_id"] == "c3"  # unplug first, always
    assert s["diagrams"]["2"]["file"] == "diagram_2.png"
    s = engine.replan(s["id"], "sudah dipancing, airnya habis lagi")
    assert s["status"] == "ready" and "foot valve" in s["plan"]["cause_title"].lower()


@pytest.mark.parametrize("text,cat,want", [
    ("Pompa air nggak keluar airnya", "", "pump"), ("my water pump runs dry", "", "pump"), ("airnya mati", "pump", "pump"),
    ("filter udara kotor, air filter", "", "motor"), ("kran netes", "", "faucet"), ("magic com mati", "", "rice"),
    ("ledeng di dapur bocor", "", "faucet"), ("the kitchen sink leaks", "", "faucet"), ("ban belakang kempes", "motor", "tire"), ("my tyre has a puncture", "", "tire"), ("tambal ban tubeless", "", "tire"), ("motor mogok busi", "motor", "motor"),
])
def test_scenario_routing(text, cat, want):
    from api.pipeline import mock

    assert mock.scenario(text, cat) == want


def test_tire_amber_full_run_and_replan(samples):
    s = engine.run(_new(samples, "tire")["id"])
    assert s["status"] == "ready" and s["safety"]["level"] == "amber"
    assert len(s["plan"]["steps"]) == 4 and "paku" in s["plan"]["cause_title"].lower()
    assert [c["name"] for c in s["object_report"]["components"]][0].lower().startswith("tapak")
    assert all(p["found"] for p in s["parts"].values())  # every tyre part gets a SAM mask in the demo
    s = engine.replan(s["id"], "sudah ditambal tapi masih kempes pelan")
    assert s["status"] == "ready" and "pentil" in s["plan"]["cause_title"].lower()
    assert len(s["plan"]["steps"]) == 4


def test_tire_english_plan_is_english(samples):
    s = engine.run(engine.create([samples["tire"]], "en", "Flat tyre with a nail")["id"])
    assert s["plan"]["steps"][0]["instruction"].startswith("Put the bike")
    assert s["plan"]["when_to_call_pro"].startswith("A plug is temporary")
