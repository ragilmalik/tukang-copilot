"""The labelled sample after-photo is checked on the step it shows, not on whatever step is open.

samples/check_motor.jpg is a close-up of the spark plug cap pushed onto the plug. Checked against "turn the key off"
a correct model says "not quite", so the 1-tap demo looked broken. api/sample_step.py picks the step whose expected
state is what the photo shows; these tests pin that pick on the live recording and on every offline plan.
"""
import json
from pathlib import Path

import pytest

from api import sample_step
from api.main import app
from api.pipeline import mock
from api.tests.owner_auth import OwnerClient

ROOT = Path(__file__).resolve().parents[2]
DEMO = json.loads((ROOT / "web" / "replay" / "demo.json").read_text(encoding="utf-8"))


def _steps(*expected):
    return [{"n": i, "expected_state": e} for i, e in enumerate(expected, 1)]


def test_cap_pushed_on_beats_cap_pulled_off_and_unrelated_steps():
    steps = _steps("the key is out, bike on the centre stand", "the black plug cap is off, plug top visible",
                   "the plug hole is open", "the plug cap is pushed fully onto the spark plug, no gap", "the engine runs")
    assert sample_step.pick("motor", steps) == {"n": 4, "shows": True}


@pytest.mark.parametrize("text", ["cop busi menutupi busi penuh tanpa celah", "cop busi nancep rapet nutupi busi, ora ana celah"])
def test_indonesian_and_javanese_wording(text):
    steps = _steps("kunci kontak OFF", "cop busi terlepas, busi terlihat", text, "mesin menyala")
    assert sample_step.pick("motor", steps) == {"n": 3, "shows": True}


def test_no_matching_step_falls_back_to_the_last_step_and_says_so():
    assert sample_step.pick("motor", _steps("the key is off", "the engine runs")) == {"n": 2, "shows": False}
    assert sample_step.pick("rice", _steps("unplugged", "the light is on")) == {"n": 2, "shows": False}
    assert sample_step.pick("motor", []) is None


def test_whole_words_only():
    # "cap" must not match "capacitor", "off" must not match "offset"
    steps = _steps("the capacitor is seated fully", "the plug cap is seated fully, offset 2 mm")
    assert sample_step.pick("motor", steps) == {"n": 2, "shows": True}


def test_a_dry_spout_with_no_drips_counts_as_done():
    steps = _steps("No water when the faucet is opened.", "The spindle is visible.", "The spout is dry, no drips.")
    assert sample_step.pick("faucet", steps) == {"n": 3, "shows": True}


@pytest.mark.parametrize("lang", ["id", "jv", "en"])
def test_live_recording_plans_pick_the_cap_seated_step(lang):
    L = DEMO["langs"][lang]
    for steps in (L["ready"]["session"]["plan"]["steps"], L["replan"]["set"]["plan"]["steps"]):
        got = sample_step.pick("motor", steps)
        assert got and got["shows"]
        text = next(st for st in steps if st["n"] == got["n"])["expected_state"].lower()
        assert "cap" in text or "cop" in text


# the step each offline plan's sample photo shows (cause 0, cause 1): mock.plan wording in api/pipeline/mock.py
OFFLINE = {"motor": (3, 4), "pump": (2, None), "tire": (2, None), "faucet": (4, 4)}


@pytest.mark.parametrize("sample", sorted(OFFLINE))
@pytest.mark.parametrize("lang", ["id", "en"])
def test_offline_plans(sample, lang):
    for cause, want in enumerate(OFFLINE[sample]):
        got = sample_step.pick(sample, mock.plan(sample, lang, cause)["steps"])
        if want is None:  # plan 2 has no step showing what the photo shows: last step, not claimed
            assert got is not None and got["n"] == len(mock.plan(sample, lang, cause)["steps"])
        else:
            assert got == {"n": want, "shows": True}, (sample, lang, cause, got)


def test_session_exposes_the_sample_step_and_the_check_passes_there():
    c = OwnerClient(app)
    sid = c.post("/api/sessions", data={"sample": "motor", "language": "en", "text": "won't start"}).json()["id"]
    with c.stream("GET", f"/api/sessions/{sid}/events") as r:
        "".join(r.iter_text())
    s = c.get(f"/api/sessions/{sid}").json()
    if s["status"] == "needs_answer":
        c.post(f"/api/sessions/{sid}/answer", data={"text": "no"})
        with c.stream("GET", f"/api/sessions/{sid}/events") as r:
            "".join(r.iter_text())
        s = c.get(f"/api/sessions/{sid}").json()
    assert s["status"] == "ready"
    ss = s["sample_step"]
    assert ss == sample_step.pick("motor", s["plan"]["steps"]) and ss["shows"]
    photo = c.get("/api/demo/check-photo/ok?sample=motor").content
    r = c.post(f"/api/sessions/{sid}/steps/{ss['n']}/check", files={"photo": ("sample-ok.jpg", photo, "image/jpeg")})
    assert r.status_code == 200 and r.json()["passed"] is True


def test_own_photo_session_has_no_sample_step():
    assert sample_step.for_session({"sample": "", "plan": {"steps": _steps("x")}}) is None
    assert sample_step.for_session({"sample": "motor"}) is None
