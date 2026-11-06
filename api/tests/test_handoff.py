"""Bengkel hand-off: GET /api/sessions/{id}/handoff (WhatsApp text + links, Maps search per scenario and language),
the stop report PDF for a code-level safety stop, the mechanic brief page, and the web wiring."""
import io
import time
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

import pytest
from PIL import Image

from api import handoff
from api.main import app
from api.render import report_pdf
from api.settings import settings
from api.tests.owner_auth import OwnerClient

client = OwnerClient(app)
WEB = Path(__file__).resolve().parents[2] / "web"
SAMPLES = Path(__file__).resolve().parents[2] / "samples"


WAIT_S = 60  # seconds a repair may take: generous, CI runners are slow and earlier repairs can still hold the worker pool


def _wait(sid: str) -> dict[str, Any]:
    deadline = time.monotonic() + WAIT_S
    while time.monotonic() < deadline:
        s: dict[str, Any] = client.get(f"/api/sessions/{sid}").json()
        if s["status"] not in ("created", "running"):
            return s
        time.sleep(0.05)
    raise AssertionError("timeout")


def _sample(sample: str, lang: str = "en") -> dict[str, Any]:
    return _wait(client.post("/api/sessions", data={"sample": sample, "language": lang}).json()["id"])


def _ho(sid: str) -> dict[str, Any]:
    r = client.get(f"/api/sessions/{sid}/handoff")
    assert r.status_code == 200, r.text
    j: dict[str, Any] = r.json()
    return j


@pytest.mark.parametrize("sample,query", [("pump", "servis pompa air terdekat"), ("faucet", "tukang ledeng terdekat"),
                                          ("rice", "service center rice cooker terdekat"), ("tire", "tambal ban terdekat")])
@pytest.mark.parametrize("lang", ["id", "jv", "en"])
def test_maps_query_per_scenario_and_language(sample, query, lang):
    s = _sample(sample, lang)
    h = _ho(s["id"])
    assert h["maps_query"] == query  # stays Indonesian in every UI language: the workshops are Indonesian
    q = parse_qs(urlparse(h["maps_url"]).query)
    assert h["maps_url"].startswith("https://www.google.com/maps/search/?api=1&") and q["query"] == [query]


def test_motor_after_answer_is_bengkel_motor():
    sid = client.post("/api/sessions", data={"sample": "motor", "language": "id"}).json()["id"]
    _wait(sid)
    client.post(f"/api/sessions/{sid}/answer", data={"text": "tidak"})
    s = _wait(sid)
    assert s["status"] == "ready"
    h = _ho(sid)
    assert h["maps_query"] == "bengkel motor terdekat" and h["reason"] == "requested"


@pytest.mark.parametrize("lang,hello,tried", [("id", "Halo, saya butuh bantuan", "Sudah dicoba"),
                                              ("jv", "Halo, aku butuh bantuan", "Wis dijajal"),
                                              ("en", "Hi, I need help", "Already tried")])
def test_red_stop_text(lang, hello, tried):
    s = _sample("rice", lang)
    h = _ho(s["id"])
    assert h["reason"] == "red" and h["emergency"] == "112"
    assert h["text"].startswith(hello) and "⚠️" in h["text"] and tried in h["text"]
    assert handoff.L[lang]["nothing"] in h["text"]
    assert h["title"] == handoff.L[lang]["title_red"]
    assert h["guide_url"].endswith(f"/guide/{s['id']}") and h["pdf_url"].endswith(f"/api/sessions/{s['id']}/report.pdf")
    assert h["guide_url"] in h["text"] and h["pdf_url"] in h["text"]
    assert unquote(h["whatsapp_url"].removeprefix("https://wa.me/?text=")) == h["text"]


def test_exhausted_lists_every_cause_tried():
    s = _sample("faucet", "en")
    sid = s["id"]
    for _ in s["diagnosis"]["causes"]:  # one "Still broken" per cause; the last one ends at "exhausted"
        j = client.post(f"/api/sessions/{sid}/replan", data={"report": "still dripping"}).json()
        if j["status"] == "exhausted":
            break
    assert j["status"] == "exhausted"
    # since 1.32.0 a re-plan is only taken from a plan on screen: one more is refused, and no cause is listed twice
    assert client.post(f"/api/sessions/{sid}/replan", data={"report": "still dripping"}).status_code == 409
    h = _ho(sid)
    assert h["reason"] == "exhausted" and h["title"] == "Time for a repair shop"
    for c in s["diagnosis"]["causes"]:
        assert c["title"] in h["text"].split("Already tried:")[1]


def test_requested_counts_current_cause_and_checks():
    s = _sample("pump", "id")
    buf = io.BytesIO()
    Image.open(SAMPLES / "pump.jpg").save(buf, "JPEG")
    client.post(f"/api/sessions/{s['id']}/steps/1/check", files={"photo": ("c.jpg", buf.getvalue(), "image/jpeg")})
    h = _ho(s["id"])
    assert h["reason"] == "requested" and h["emergency"] is None
    assert f"Sudah dicoba: {s['diagnosis']['causes'][0]['title']}" in h["text"]
    assert f"Langkah dicek kamera: 1/{len(s['plan']['steps'])}" in h["text"]
    assert "Shimizu" in h["text"] and h["text"].count("Shimizu") <= 2


def test_public_base_url_is_used(monkeypatch):
    monkeypatch.setattr(settings, "public_base_url", "https://tukang.example")
    s = _sample("faucet")
    h = _ho(s["id"])
    assert h["guide_url"] == f"https://tukang.example/guide/{s['id']}"


def test_unknown_session():
    assert client.get("/api/sessions/nope/handoff").status_code == 404


def test_maps_query_rules():
    assert handoff.maps_query({"text": "bau gas dari kompor"}) == "service kompor gas terdekat"
    assert handoff.maps_query({"object_report": {"object": "Honda Vario", "category": "motor"}, "text": "gasnya macet"}) == "bengkel motor terdekat"
    assert handoff.maps_query({"object_report": {"object": "Kipas angin Miyako", "category": "appliance"}}) == "servis kipas angin terdekat"
    assert handoff.maps_query({"object_report": {"object": "Blender", "category": "appliance"}}) == "service center elektronik terdekat"
    assert handoff.maps_query({}) == "tukang servis terdekat"


def test_gate_stop_gets_a_stop_report_pdf():
    """A code-level safety stop happens before any diagnosis: the PDF must still build (useful for the hand-off)."""
    sid = client.post("/api/sessions", data={"language": "en", "text": "strong gas leak smell from the stove hose"},
                      files={"photos": ("a.jpg", (SAMPLES / "rice.jpg").read_bytes(), "image/jpeg")}).json()["id"]
    s = _wait(sid)
    assert s["status"] == "stopped" and not s.get("diagnosis")
    r = client.get(f"/api/sessions/{sid}/report.pdf")
    assert r.status_code == 200 and r.content.startswith(b"%PDF")
    h = _ho(sid)
    assert h["pdf_url"] and h["maps_query"] == "service kompor gas terdekat" and h["reason"] == "red"


def test_report_pdf_still_409_while_running():
    from api.pipeline import engine

    s = _sample("faucet")
    sess = engine.load(s["id"])
    sess["diagnosis"], sess["status"] = None, "running"
    engine.save(sess)
    assert client.get(f"/api/sessions/{s['id']}/report.pdf").status_code == 409


@pytest.mark.parametrize("lang", ["id", "jv", "en"])
def test_mechanic_brief_lines(lang):
    from api.pipeline import engine

    s = _sample("pump", lang)
    sid = s["id"]
    dark = io.BytesIO()
    Image.new("RGB", (300, 200), (5, 5, 5)).save(dark, "JPEG")
    client.post(f"/api/sessions/{sid}/steps/1/check", files={"photo": ("d.jpg", dark.getvalue(), "image/jpeg")})
    sess = engine.load(sid)
    rows = report_pdf.brief_lines(sess, lang)
    B = report_pdf.BRIEF[lang]
    heads = [t for k, t in rows if k == "h"]
    assert heads == [B["status"], B["found"], B["tried"], B["checks"]]
    text = "\n".join(t for _, t in rows)
    assert s["diagnosis"]["causes"][0]["title"] in text and f"[{B['fail']}]" in text
    pics = report_pdf.brief_photos(sess, engine.session_dir(sid), lang)
    assert pics[0][1] == f"{B['photo']} 1" and any(B["check"] in c for _, c in pics)
    pdf = client.get(f"/api/sessions/{sid}/report.pdf").content
    assert pdf.count(b"/Type /Page") - pdf.count(b"/Type /Pages") >= 2


def test_brief_for_red_stop_says_nothing_tried():
    s = _sample("rice", "en")
    from api.pipeline import engine

    text = "\n".join(t for _, t in report_pdf.brief_lines(engine.load(s["id"]), "en"))
    assert "Safety STOP" in text and report_pdf.BRIEF["en"]["nothing"] in text


def test_web_handoff_wiring():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    js = (WEB / "app.js").read_text(encoding="utf-8")
    assert 'id="mechBtn"' in html and 'id="handoff"' in html
    assert "/handoff`" in js and "showHandoff(\"stopHandoff\")" in js and 'if (result === "pro") showHandoff' in js
    jv = js[js.index("T.jv = Object.assign"):]
    assert "Celuk mekanik" in jv
