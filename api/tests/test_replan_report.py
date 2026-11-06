"""After "Still broken": the PDF report and the mechanic brief say what was tried in the owner's language, and the
link preview card and the guide page description follow the plan being tried, not the first guess."""
import time

import pytest

from api import handoff
from api.main import app
from api.pipeline import engine
from api.render import brand, report_pdf, share_card
from api.tests.owner_auth import OwnerClient

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


def _replanned(lang, report):
    sid = client.post("/api/sessions", data={"sample": "motor", "language": lang}).json()["id"]
    if _wait(sid)["status"] == "needs_answer":
        assert client.post(f"/api/sessions/{sid}/answer", data={"text": "ya"}).json()["ok"]
        _wait(sid, ("ready",))
    first = engine.load(sid)["diagnosis"]["causes"][0]["title"]
    s2 = client.post(f"/api/sessions/{sid}/replan", data={"report": report}).json()
    assert s2["cause_index"] == 1 and s2["status"] == "ready"
    return sid, first


@pytest.mark.parametrize("lang,report,want", [
    ("jv", "isih mati", "Dijajal: {c}. Asile: isih mati"),
    ("id", "tetap mati", "Dicoba: {c}. Hasilnya: tetap mati"),
    ("en", "still dead", "Tried: {c}. Result: still dead"),
])
def test_attempts_read_in_the_owners_language(lang, report, want):
    sid, first = _replanned(lang, report)
    line = want.format(c=first)
    assert client.get(f"/api/sessions/{sid}/report").json()["attempts"] == [line]
    brief = "\n".join(t for _, t in report_pdf.brief_lines(engine.load(sid), lang))
    assert line in brief
    if lang != "en":
        assert "Tried '" not in brief and "result:" not in brief
    # the model still gets the earlier attempt, in English, like before
    assert engine.load(sid)["history"] == [f"Tried '{first}', result: {report}"]


def test_empty_report_says_still_broken_in_basa_jawa():
    sid, first = _replanned("jv", "")
    assert client.get(f"/api/sessions/{sid}/report").json()["attempts"] == [f"Dijajal: {first}. Asile: isih rusak"]


def test_old_session_without_attempts_keeps_its_history_line():
    s = {"lang": "jv", "history": ["Tried 'X', result: still bad"]}
    assert handoff.attempt_lines(s, "jv") == ["Tried 'X', result: still bad"]


def test_attempts_stay_off_the_wire():
    sid, _ = _replanned("jv", "OWNER WORDS HERE")
    r = client.get(f"/api/sessions/{sid}")
    assert "OWNER WORDS HERE" not in r.text and "attempts" not in r.json()


def test_failed_replan_rolls_the_attempt_back(monkeypatch):
    sid, _ = _replanned("id", "tetap mati")
    monkeypatch.setattr(engine, "stage_plan", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("model down")))
    with pytest.raises(RuntimeError):
        engine.replan(sid, "masih mati juga")
    s = engine.load(sid)
    assert len(s["attempts"]) == 1 and len(s["history"]) == 1 and s["cause_index"] == 1


def _card_words(monkeypatch, s, tmp_path):
    seen: list[str] = []
    real = brand.draw

    def spy(d, xy, text, *a, **k):
        seen.append(str(text))
        return real(d, xy, text, *a, **k)
    monkeypatch.setattr(brand, "draw", spy)
    share_card.build(s, engine.session_dir(s["id"]), tmp_path / "c.png")
    return seen


@pytest.mark.parametrize("lang,label,likely", [("jv", "Rencana 2 saka 3, dijajal saiki", "Sing paling mungkin"),
                                               ("id", "Rencana 2 dari 3, dicoba sekarang", "Paling mungkin"),
                                               ("en", "Plan 2 of 3, being tried now", "Most likely")])
def test_share_card_names_the_plan_after_a_replan(monkeypatch, tmp_path, lang, label, likely):
    sid, _ = _replanned(lang, "")
    s = engine.load(sid)
    words = _card_words(monkeypatch, s, tmp_path)
    assert label in words and likely not in words
    assert s["diagnosis"]["causes"][1]["title"] in " ".join(words)
    before = _card_words(monkeypatch, dict(s, cause_index=0), tmp_path)
    assert likely in before and label not in before


def test_guide_preview_text_follows_the_current_plan():
    sid, first = _replanned("id", "")
    now = engine.load(sid)["diagnosis"]["causes"][1]["title"]
    page = client.get(f"/guide/{sid}").text
    desc = page[page.index('property="og:description"'):][:300]
    assert now in desc and first not in desc
