"""v1.24 recorded demo (J5): the fixture the front end replays when the server sleeps is complete, honest and current."""
import json
import re
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"
REPLAY = WEB / "replay"
DATA = json.loads((REPLAY / "demo.json").read_text(encoding="utf-8"))
c = TestClient(app)


def test_recording_is_labelled_and_has_every_language():
    assert DATA["kind"] == "recorded-demo" and "RECORDED" in DATA["note"] and "Not a live" in DATA["note"]
    assert set(DATA["langs"]) == {"id", "jv", "en"} and DATA["sample"] == "motor"
    for lang, L in DATA["langs"].items():
        assert L["sid"] == f"replay-motor-{lang}"
        assert L["ask"]["snaps"][-1]["status"] == "needs_answer" and L["ask"]["session"]["question"]
        assert len(L["ask"]["snaps"]) >= 3                                 # it streams, stage by stage
        assert L["ready"]["session"]["status"] == "ready" and L["ready"]["session"]["mode"] == "mock"
        assert L["ready"]["session"]["lang"] == lang


def test_every_step_of_both_plans_has_a_pass_and_a_fail():
    for L in DATA["langs"].values():
        steps0 = [st["n"] for st in L["ready"]["session"]["plan"]["steps"]]
        steps1 = [st["n"] for st in L["replan"]["set"]["plan"]["steps"]]
        for key, steps in (("0", steps0), ("1", steps1)):
            assert sorted(int(n) for n in L["checks"][key]) == sorted(steps)
            for rec in L["checks"][key].values():
                assert rec["ok"]["response"]["passed"] is True and rec["dark"]["response"]["passed"] is False
        assert L["replan"]["set"]["cause_index"] == 1
        assert set(L["outcome"]) == {"fixed", "pro"}


def test_no_live_session_ids_or_server_paths_leak_into_the_recording():
    blob = (REPLAY / "demo.json").read_text(encoding="utf-8")
    assert "/files/" not in blob.replace("/static/replay/files/", "")
    assert not re.search(r"/api/sessions/[0-9a-f]{12}", blob) and not re.search(r"/guide/[0-9a-f]{12}", blob)


def test_every_recorded_picture_exists_and_is_served():
    names = set()
    for L in DATA["langs"].values():
        for snap in L["ask"]["snaps"] + L["ready"]["snaps"]:
            assert snap["files_base"] == "/static/replay/files/"
        s = L["ready"]["session"]
        names |= {s["parts_image"], *s["photos"], *(p["image"] for p in s["parts"].values() if p.get("image"))}
        for plan in L["checks"].values():
            for rec in plan.values():
                for kind in ("ok", "dark"):
                    for tries in rec[kind]["delta"]["merge"].get("checks", {}).values():
                        names |= {t["photo"] for t in tries["tries"]}
    for n in names:
        assert (REPLAY / "files" / n).is_file(), n
    for url in DATA["assets"][:5] + ["/static/replay/demo.json", "/static/replay.js", "/static/replay/report-en.pdf"]:
        assert c.get(url).status_code == 200, url
    assert all(not a.endswith(".pdf") for a in DATA["assets"])          # PDFs are not pre-cached on the phone


def test_fixture_matches_what_the_app_produces_today():
    sys.path.insert(0, str(ROOT / "scripts"))
    import record_replay  # type: ignore[import-not-found]

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
