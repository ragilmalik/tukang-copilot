"""Mechanic brief on a repair that is still going: the cause being tried now is not listed as already tried,
and the status does not say the owner asked for a mechanic when they have not chosen anything yet."""
import time

import pytest

from api import handoff
from api.main import app
from api.pipeline import engine
from api.render import report_pdf
from api.tests.owner_auth import OwnerClient, owner

client = OwnerClient(app)


WAIT_S = 60  # seconds a repair may take: generous, CI runners are slow and earlier repairs can still hold the worker pool


def _wait(sid, want=("ready", "needs_answer", "stopped", "error")):
    deadline = time.monotonic() + WAIT_S
    while time.monotonic() < deadline:
        s = client.get(f"/api/sessions/{sid}").json()
        if s["status"] in want:
            return s
        time.sleep(0.05)
    raise AssertionError("timeout")


def _motor(lang):
    sid = client.post("/api/sessions", data={"sample": "motor", "language": lang}).json()["id"]
    if _wait(sid)["status"] == "needs_answer":
        client.post(f"/api/sessions/{sid}/answer", data={"text": "ya"})
        _wait(sid, ("ready",))
    return sid


def _brief(sid, lang):
    return report_pdf.brief_lines(engine.load(sid), lang)


@pytest.mark.parametrize("lang", ["jv", "id", "en"])
def test_after_a_replan_the_current_cause_is_being_tried_not_tried(lang):
    sid = _motor(lang)
    causes = engine.load(sid)["diagnosis"]["causes"]
    client.post(f"/api/sessions/{sid}/replan", data={"report": "isih mati"})
    B = report_pdf.BRIEF[lang]
    rows = _brief(sid, lang)
    tried_at = rows.index(("h", B["tried"]))
    block = [t for _, t in rows[tried_at + 1:tried_at + 4]]
    assert f"- {causes[0]['title']}" in block                       # plan 1 really was tried
    assert f"- {B['now']}: {causes[1]['title']}" in block          # plan 2 is the one on the bench
    assert f"- {causes[1]['title']}" not in block


@pytest.mark.parametrize("lang", ["jv", "id", "en"])
def test_status_is_open_until_the_owner_chooses(lang):
    sid = _motor(lang)
    B = report_pdf.BRIEF[lang]
    texts = [t for _, t in _brief(sid, lang)]
    assert B["open"] in texts and B["requested"] not in texts and B["fixed"] not in texts
    assert f"- {B['now']}: {engine.load(sid)['diagnosis']['causes'][0]['title']}" in texts


def test_took_it_to_a_mechanic_counts_the_current_cause_as_tried():
    sid = _motor("en")
    client.post(f"/api/sessions/{sid}/outcome", data={"result": "pro"}, headers=owner(sid))
    B = report_pdf.BRIEF["en"]
    texts = [t for _, t in _brief(sid, "en")]
    first = engine.load(sid)["diagnosis"]["causes"][0]["title"]
    assert B["requested"] in texts and f"- {first}" in texts and not any(t.startswith(f"- {B['now']}") for t in texts)


def test_progress_helper():
    s = {"plan": {"steps": []}, "cause_index": 1, "diagnosis": {"causes": [{"title": "A"}, {"title": "B"}, {"title": "C"}]}}
    assert handoff.progress(s, "requested") == (["A"], "B")
    assert handoff.progress(s, "exhausted") == (["A", "B"], "")
    assert handoff.progress({**s, "outcome": {"result": "fixed"}}, "requested") == (["A", "B"], "")
    assert handoff.progress(s, "red") == ([], "")


def test_whatsapp_message_is_unchanged_by_the_brief_split():
    # the WhatsApp summary is sent when the owner hands over, so the current cause still counts as tried there
    sid = _motor("en")
    first = engine.load(sid)["diagnosis"]["causes"][0]["title"]
    assert first in client.get(f"/api/sessions/{sid}/handoff").json()["text"].split("Already tried")[-1]
