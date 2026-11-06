"""Recorded demo: the fixture the front end replays when the server sleeps is complete, honest and current."""
import json
import re
import sys
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from api.main import app

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"
REPLAY = WEB / "replay"
DATA = json.loads((REPLAY / "demo.json").read_text(encoding="utf-8"))
c = TestClient(app)


def test_recording_is_labelled_and_has_every_language():
    assert DATA["kind"] == "recorded-demo" and DATA["source"] == "meta-api-live"
    assert "RECORDED live run" in DATA["note"] and "real Meta Model API" in DATA["note"] and DATA["recorded_at"]
    assert set(DATA["langs"]) == {"id", "jv", "en"} and DATA["sample"] == "motor"
    for lang, L in DATA["langs"].items():
        assert L["sid"] == f"replay-motor-{lang}"
        # one take, as the model answered it: the yes/no follow-up only when it was under 60% sure (record_replay.py)
        assert isinstance(L["asked"], bool)
        if L["asked"]:
            assert L["ask"]["snaps"][-1]["status"] == "needs_answer" and L["ask"]["session"]["question"]
            assert L["answer"] == {"id": "Ya", "jv": "Nggih", "en": "Yes"}[lang]
        else:
            assert L["ask"]["snaps"][-1]["status"] == "ready" and not L["ask"]["session"].get("question")
            assert L["answer"] == "" and L["ready"]["session"] == L["ask"]["session"]
            top = L["ready"]["session"]["diagnosis"]["causes"][0]["confidence"]
            assert top >= 60, top                                            # sure enough not to ask (engine threshold)
        assert len(L["ask"]["snaps"]) >= 3                                 # it streams, stage by stage
        assert L["ready"]["session"]["status"] == "ready" and L["ready"]["session"]["mode"] == "live"
        assert not L["ready"]["session"].get("fallback")                     # no stage fell back to canned answers
        assert L["ready"]["session"]["lang"] == lang


def test_every_step_of_both_plans_has_both_sample_photos_checked():
    for L in DATA["langs"].values():
        steps0 = [st["n"] for st in L["ready"]["session"]["plan"]["steps"]]
        steps1 = [st["n"] for st in L["replan"]["set"]["plan"]["steps"]]
        for key, steps in (("0", steps0), ("1", steps1)):
            assert sorted(int(n) for n in L["checks"][key]) == sorted(steps)
            for rec in L["checks"][key].values():  # real verdicts: the after-photo fits some steps, never the dark one
                assert isinstance(rec["ok"]["response"].get("passed"), bool) and rec["dark"]["response"]["passed"] is False
        assert any(rec["ok"]["response"]["passed"] for plan in L["checks"].values() for rec in plan.values())
        assert L["replan"]["set"]["cause_index"] == 1
        assert set(L["outcome"]) == {"fixed", "pro"}


def test_no_live_session_ids_or_server_paths_leak_into_the_recording():
    blob = (REPLAY / "demo.json").read_text(encoding="utf-8")
    assert "/files/" not in blob.replace("/static/replay/files/", "")
    assert not re.search(r"/api/sessions/[0-9a-f]{12}", blob) and not re.search(r"/guide/[0-9a-f]{12}", blob)


def test_every_recorded_picture_exists_and_is_served():
    for lang, L in DATA["langs"].items():
        names = set()
        for snap in L["ask"]["snaps"] + L["ready"]["snaps"]:
            assert snap["files_base"] == f"/static/replay/files/{lang}/"
        s = L["ready"]["session"]
        names |= {s["parts_image"], *s["photos"], *(p["image"] for p in s["parts"].values() if p.get("image"))}
        for plan in L["checks"].values():
            for rec in plan.values():
                for kind in ("ok", "dark"):
                    for tries in rec[kind]["delta"]["merge"].get("checks", {}).values():
                        names |= {t["photo"] for t in tries["tries"]}
        for n in names:
            assert (REPLAY / "files" / lang / n).is_file(), (lang, n)
    for url in DATA["assets"][:5] + ["/static/replay/demo.json", "/static/replay.js", "/static/replay/report-en.pdf"]:
        assert c.get(url).status_code == 200, url
    assert all(not a.endswith(".pdf") for a in DATA["assets"])          # PDFs are not pre-cached on the phone


def test_fixture_matches_what_the_app_produces_today():
    sys.path.insert(0, str(ROOT / "scripts"))
    import record_replay  # type: ignore[import-not-found, unused-ignore]

    assert record_replay.is_current(), "run: python scripts/record_replay.py"


def test_page_loads_replay_before_app_and_worker_keeps_it_offline():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    assert html.index("/static/replay.js") < html.index("/static/app.js") and 'id="wakeNote"' in html
    sw = (WEB / "sw.js").read_text(encoding="utf-8")
    shell = sw.split("const SHELL")[1].split(";")[0]
    assert "/static/replay.js" in shell and "/static/replay/demo.json" in shell and "/api/" not in shell
    assert "SHELL_WAIT_MS" in sw and "d.assets" in sw


def test_replay_never_fakes_a_check_of_the_visitors_own_photo():
    js = (WEB / "replay.js").read_text(encoding="utf-8")
    assert 'return nope("rpOwnPhoto")' in js and "sample-(ok|dark)" in js
    app_js = (WEB / "app.js").read_text(encoding="utf-8")
    assert "sample-${kind}.jpg" in app_js                                  # the only names the replay accepts


def test_replay_strings_in_all_three_languages():
    js = (WEB / "app.js").read_text(encoding="utf-8")
    block = js[js.index("/* I18N_REPLAY:start"):js.index("/* I18N_REPLAY:end */")]
    keys = {}
    for k in ("id", "jv", "en"):
        rest = block[block.index(f"  {k}: {{"):]
        keys[k] = dict(re.findall(r"(\w+): \"([^\"]*)\"", rest[:rest.index("},\n")]))
    assert set(keys["id"]) == set(keys["jv"]) == set(keys["en"]) and len(keys["id"]) >= 6
    rjs = (WEB / "replay.js").read_text(encoding="utf-8")
    for key in set(re.findall(r'nope\("(\w+)"\)', rjs)):
        assert key in keys["en"], key
    assert all(keys["jv"][k] != keys["id"][k] for k in keys["id"])
    assert "Recorded demo" in keys["en"]["rpBadge"] and "rekaman" in keys["id"]["rpBadge"]
    day = DATA["recorded_at"][:10]  # the badge names the day the recording was made
    from datetime import date
    label = f"{date.fromisoformat(day).day} Nov {day[:4]}"
    assert all(label in keys[lang]["rpBadge"] for lang in ("id", "jv", "en")), label


def test_recording_ships_no_duplicate_pictures() -> None:
    """The service worker downloads every recorded picture on install, on mobile data. The step-check photos used to be
    copied once per step and plan (70 identical files, about 5 MB); one copy per kind and language is enough."""
    import hashlib

    data = json.loads((REPLAY / "demo.json").read_text(encoding="utf-8"))
    files = [REPLAY / u.split("/static/replay/", 1)[1] for u in data["assets"]]
    digests = [hashlib.md5(f.read_bytes()).hexdigest() for f in files]
    dupes = len(digests) - len(set(digests))
    assert dupes <= 6, f"{dupes} duplicate pictures in web/replay"  # check_ok/check_dark: one per language, plus the top-level pair
    assert sum(f.stat().st_size for f in files) < 4_500_000


def test_sample_photo_is_checked_on_the_step_it_shows_and_passes_there() -> None:
    """The 1-tap demo's 'Sample photo: plug cap on' is checked on the step it shows (sample_step, stored per plan),
    and the live model passed it there: the demo never shows a fail on its own 'good' photo."""
    for lang, L in DATA["langs"].items():
        assert L["ready"]["session"]["sample_step"] == L["sample_step"]["0"]
        assert L["replan"]["set"]["sample_step"] == L["sample_step"]["1"]
        for plan, ss in L["sample_step"].items():
            assert L["checks"][plan][str(ss["n"])]["ok"]["response"]["passed"] is True, (lang, plan, ss)


def test_shape_check_allows_a_recording_without_the_follow_up_question():
    """The live model asks only when unsure; the offline run asks. The ask part and the log's ask/answer lines are then
    left out of the comparison, and any other difference still counts."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import record_replay  # type: ignore[import-not-found, unused-ignore]

    def lang(asked: bool, extra: bool = False) -> dict[str, Any]:
        log = [{"t": 0, "kind": "gate", "ok": True}] + ([{"t": 1, "kind": "ask", "conf": 55, "threshold": 60}] if asked else [])
        sess = {"status": "ready", "agent_log": log, **({"new_field": 1} if extra else {})}
        ask = {"snaps": [{"status": "needs_answer" if asked else "ready", "question": "q" if asked else None}],
               "session": {"status": "needs_answer", "question": "q"} if asked else sess}
        return {"asked": asked, "ask": ask, "ready": {"snaps": [sess], "session": sess}}

    offline = {"langs": {"id": lang(True)}}
    assert record_replay.shape_diff({"langs": {"id": lang(False)}}, offline) == []
    assert record_replay.shape_diff({"langs": {"id": lang(False, extra=True)}}, offline)  # a real change is still caught
    assert record_replay.shape_diff({"langs": {"id": lang(True)}}, offline) == []
