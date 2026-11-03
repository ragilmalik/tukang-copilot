"""Bugs I found in 1.26.0 by playing every flow end to end.

1. Brake failure on the owner's own motorbike ("rem motorku blong", "rem ora makan", "my brakes don't work")
   slipped past the safety gate; only "rem mobil blong" was caught. Now a red stop with a brake-specific message.
2. In the 1-tap demo the follow-up answer changed nothing (55% before, 55% after). The demo diagnosis now
   moves with the answer, so the "asked one question instead of guessing" step visibly matters.
3. The share card said "Every step camera-checked" for a plan with 0 checked steps. Now a real count.
"""
import time
from typing import Any

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.pipeline import mock, safety
from api.render import share_card
from api.tests.owner_auth import owner

client = TestClient(app)


@pytest.mark.parametrize("text,lang", [
    ("Rem motorku blong, kampas rem arep tak ganti dhewe", "jv"),
    ("remku blong pas mudhun", "jv"),
    ("rem ora makan babar blas", "jv"),
    ("rem motor blong", "id"),
    ("rem belakang tidak makan", "id"),
    ("rem motor nggak pakem sama sekali", "id"),
    ("rem cakram blong", "id"),
    ("my brakes don't work", "en"),
    ("my bike has no brakes", "en"),
    ("brakes feel spongy", "en"),
    ("the brake pedal goes to the floor", "en"),
    ("my scooter brakes are weak", "en"),
])
def test_brake_failure_is_a_red_stop(text, lang):
    g = safety.check_text(text, lang)
    assert not g.allowed and g.category == "brake"
    assert g.reason == safety._MSG["brake"][lang]


@pytest.mark.parametrize("text", [
    "kampas rem habis bunyi cit cit", "lampu rem mati", "brake light bulb is out", "no brake light",
    "rem tangan kendor sedikit", "remote TV mati", "remote AC ora jalan", "tarik gas motor berat", "rem cakram bunyi",
])
def test_brake_words_that_are_not_failures_pass(text):
    assert safety.check_text(text, "id").allowed


def test_brake_messages_in_every_language():
    m = safety._MSG["brake"]
    assert set(m) == {"id", "jv", "en"} and all(len(v) > 40 for v in m.values())
    assert "bengkel" in m["id"] and "bengkel" in m["jv"] and "mechanic" in m["en"]


def test_brake_stop_over_http_is_red():
    sid = client.post("/api/sessions", data={"text": "rem motorku blong", "language": "jv"},
                      files=[("photos", ("a.jpg", _jpg(), "image/jpeg"))]).json()["id"]
    s = _wait(sid)
    assert s["status"] == "stopped" and s["safety"]["level"] == "red"
    gate = [e for e in s["agent_log"] if e["kind"] == "gate"]
    assert gate and gate[0]["ok"] is False and gate[0]["category"] == "brake"


def _jpg():
    import io

    from PIL import Image
    b = io.BytesIO(); Image.new("RGB", (640, 480), (120, 120, 120)).save(b, "JPEG"); b.seek(0)
    return b


def _wait(sid, until=("ready", "stopped", "needs_answer", "error", "exhausted")):
    for _ in range(200):
        s = client.get(f"/api/sessions/{sid}").json()
        if s["status"] in until:
            return s
        time.sleep(0.05)
    raise AssertionError("timeout")


@pytest.mark.parametrize("answer,lang,top", [("Yes", "en", 70), ("Ya", "id", 70), ("Iya", "jv", 70),
                                             ("No", "en", 58), ("Tidak tahu", "id", 58), ("Ora", "jv", 58)])
def test_demo_follow_up_answer_changes_the_diagnosis(answer, lang, top):
    before = mock.diagnosis("motor", lang)
    after = mock.diagnosis("motor", lang, answer)
    assert before["causes"][0]["confidence"] == 55 and before["follow_up_question"]
    assert after["causes"][0]["confidence"] == top and after["follow_up_question"] == ""
    assert sum(c["confidence"] for c in after["causes"]) == 100
    assert len(after["causes"][0]["evidence"]) == len(before["causes"][0]["evidence"]) + 1


def test_follow_up_answer_moves_the_confidence_over_http():
    sid = client.post("/api/sessions", data={"sample": "motor", "language": "en"}).json()["id"]
    assert _wait(sid)["status"] == "needs_answer"
    assert client.post(f"/api/sessions/{sid}/answer", data={"text": "Yes"}).json()["ok"]
    s = _wait(sid, ("ready",))
    assert s["diagnosis"]["causes"][0]["confidence"] == 70
    confs = [e["conf"] for e in s["agent_log"] if e["kind"] == "diagnose"]
    assert confs == [55, 70]  # the agent log shows the answer mattered


def test_share_card_never_claims_unchecked_steps_were_checked():
    s: dict[str, Any] = {"plan": {"steps": [{"n": 1}, {"n": 2}, {"n": 3}, {"n": 4}]}, "checks": {}}
    for lang in ("id", "jv", "en"):
        line, passed = share_card.check_line(s, lang)
        assert not passed and "✓" not in line and line
    assert share_card.check_line(s, "en")[0] == "The camera checks each step"
    s["checks"] = {"1": {"passed": True}, "2": {"passed": False}, "3": {"passed": True}}
    assert share_card.check_line(s, "en") == ("✓ 2 of 4 steps passed a camera check", True)
    assert share_card.check_line(s, "id")[0] == "✓ 2 dari 4 langkah lolos cek kamera"
    assert share_card.check_line({"plan": {}}, "en") == ("", False)


def test_share_card_png_still_renders_after_checks():
    sid = client.post("/api/sessions", data={"sample": "faucet", "language": "en"}).json()["id"]
    assert _wait(sid)["status"] == "ready"
    r = client.get(f"/api/sessions/{sid}/card.png")
    assert r.status_code == 200 and r.content[:8] == b"\x89PNG\r\n\x1a\n"


# --- more fixes from the same pass
def _ready(sample="faucet", lang="en"):
    sid = client.post("/api/sessions", data={"sample": sample, "language": lang}).json()["id"]
    assert _wait(sid)["status"] == "ready"
    return sid


@pytest.mark.parametrize("lang,fixed,asked", [
    ("en", "Owner says it works again", "Owner asked for a mechanic"),
    ("id", "Pemilik bilang sudah jalan lagi", "Pemilik minta bantuan mekanik"),
    ("jv", "Sing duwe kandha wis urip maneh", "Sing duwe njaluk bantuan mekanik"),
])
def test_mechanic_brief_status_follows_it_works_now(lang, fixed, asked):
    from api.pipeline import engine
    from api.render import report_pdf

    sid = _ready("faucet", lang)
    before = [t for _, t in report_pdf.brief_lines(engine.load(sid), lang)]
    assert asked in before and fixed not in before
    assert client.post(f"/api/sessions/{sid}/outcome", data={"result": "fixed"}, headers=owner(sid)).status_code == 200
    after = [t for _, t in report_pdf.brief_lines(engine.load(sid), lang)]
    assert fixed in after and asked not in after
    assert client.get(f"/api/sessions/{sid}/report.pdf").status_code == 200


def test_mechanic_brief_after_took_it_to_a_mechanic_still_says_asked():
    from api.pipeline import engine
    from api.render import report_pdf

    sid = _ready("faucet", "en")
    client.post(f"/api/sessions/{sid}/outcome", data={"result": "pro"}, headers=owner(sid))
    rows = [t for _, t in report_pdf.brief_lines(engine.load(sid), "en")]
    assert "Owner asked for a mechanic" in rows


def _pdf_pages(data: bytes) -> int:
    return data.count(b"/Type /Page") - data.count(b"/Type /Pages")


@pytest.mark.parametrize("sample", ["faucet", "pump", "tire"])
@pytest.mark.parametrize("lang", ["id", "jv", "en"])
def test_workshop_sheet_has_no_near_empty_done_page(sample, lang, tmp_path):
    """"Done when" closes the last step page instead of sitting alone on its own page."""
    from api.pipeline import engine
    from api.render import workshop_pdf

    sid = _ready(sample, lang)
    s = engine.load(sid)
    out = workshop_pdf.build(engine.report(sid), s, engine.session_dir(sid), tmp_path / "w.pdf")
    assert _pdf_pages(out.read_bytes()) == len(s["plan"]["steps"]) + 1  # cover + one page per step


def test_workshop_done_block_gets_its_own_page_only_when_it_does_not_fit(tmp_path):
    from api.render import workshop_pdf
    from api.render.report_pdf import _Doc

    doc = _Doc("f", "p")
    doc.y = 300
    assert workshop_pdf.done_fits(doc, "No drips for 2 minutes.", "Light repairs only.")
    doc.y = workshop_pdf.TICK_Y - 100
    assert not workshop_pdf.done_fits(doc, "No drips for 2 minutes.", "Light repairs only.")
    plan = {"steps": [{"n": 1, "instruction": "x " * 1000}], "done_check": "It holds air for a day."}  # condensed type fits more per line
    out = workshop_pdf.build({"lang": "en"}, {"plan": plan}, tmp_path, tmp_path / "w.pdf")
    assert _pdf_pages(out.read_bytes()) >= 3  # a full step page pushes "Done when" to a page of its own


def test_share_fallback_label_is_translated():
    from pathlib import Path
    js = (Path(__file__).resolve().parents[2] / "web" / "app.js").read_text(encoding="utf-8")
    assert 'prompt("Link"' not in js and 'prompt(t("linkLabel"), url)' in js
    for word in ('linkLabel: "Tautan"', 'linkLabel: "Link"', 'linkLabel: "Pranala"'):
        assert word in js


def test_shared_guide_cannot_send_an_outcome():
    from pathlib import Path
    js = (Path(__file__).resolve().parents[2] / "web" / "app.js").read_text(encoding="utf-8")
    assert "if (!S || !S.id || sharedView()) return;" in js
    for key in ("ocFixed", "ocPro"):
        assert js.count(key + ":") == 3
