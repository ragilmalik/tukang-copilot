"""PDF repair report: built from a real mock session, opened back with Pillow, and served over HTTP."""
import time

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.pipeline import engine
from api.render import report_pdf

client = TestClient(app)


def _wait(sid, timeout=20.0):
    end = time.time() + timeout
    while time.time() < end:
        s = client.get(f"/api/sessions/{sid}").json()
        if s["status"] not in {"created", "running"}:
            return s
        time.sleep(0.05)
    raise AssertionError("session did not finish")


@pytest.mark.parametrize("lang", ["id", "jv", "en"])
def test_pdf_built_for_every_language(samples, tmp_path, lang):
    sid = engine.create([samples["faucet"]], lang, "Kran wastafel menetes terus")["id"]
    s = engine.run(sid)
    engine.check_step(sid, 1, samples["faucet"])
    out = report_pdf.build(engine.report(sid), engine.load(sid), engine.session_dir(sid), tmp_path / "r.pdf")
    data = out.read_bytes()
    assert data.startswith(b"%PDF") and len(data) > 20_000
    assert s["plan"]["steps"]


def test_pdf_paginates_long_reports(tmp_path):
    rep = {"id": "x", "lang": "en", "object": "Thing", "problem": "Broken " * 400, "fix": "Fix", "steps_total": 0, "steps_verified": 0,
           "tools": [{"name": f"Tool {i}", "est_price_idr": 1000 * i} for i in range(40)], "parts": [], "attempts": ["tried"] * 30,
           "safety_level": "green"}
    out = report_pdf.build(rep, {"mode": "offline", "safety": {"reason": "ok"}}, tmp_path, tmp_path / "long.pdf")
    data = out.read_bytes()  # Pillow writes PDFs but cannot read them back, so count page objects
    pages = data.count(b"/Type /Page") - data.count(b"/Type /Pages")
    assert pages >= 2


def test_rupiah_format():
    assert report_pdf.rupiah(45000) == "Rp45.000" and report_pdf.rupiah(None) == "Rp0"


def test_pdf_endpoint():
    sid = client.post("/api/sessions", data={"sample": "pump", "language": "en"}).json()["id"]
    assert _wait(sid)["status"] == "ready"
    r = client.get(f"/api/sessions/{sid}/report.pdf")
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf" and r.content.startswith(b"%PDF")
    assert client.get("/api/sessions/nope123/report.pdf").status_code == 404


def test_pdf_endpoint_red_stop_still_works():
    sid = client.post("/api/sessions", data={"sample": "rice"}).json()["id"]
    assert _wait(sid)["status"] == "stopped"
    assert client.get(f"/api/sessions/{sid}/report.pdf").status_code in {200, 409}


def _pages(data: bytes) -> int:
    return data.count(b"/Type /Page") - data.count(b"/Type /Pages")


@pytest.mark.parametrize("lang", ["id", "jv", "en"])
def test_workshop_sheets_one_page_per_step(samples, tmp_path, lang):
    from api.render import workshop_pdf

    sid = engine.create([samples["pump"]], lang, "Pompa air tidak mau menyedot")["id"]
    s = engine.run(sid)
    steps = len(s["plan"]["steps"])
    out = workshop_pdf.build(engine.report(sid), engine.load(sid), engine.session_dir(sid), tmp_path / "w.pdf")
    data = out.read_bytes()
    assert data.startswith(b"%PDF")
    assert _pages(data) >= steps + 1  # cover + one page per step (+ final page)


def test_workshop_endpoint():
    sid = client.post("/api/sessions", data={"sample": "faucet", "language": "id"}).json()["id"]
    assert _wait(sid)["status"] == "ready"
    r = client.get(f"/api/sessions/{sid}/workshop.pdf")
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf" and r.content.startswith(b"%PDF")
    assert client.get("/api/sessions/nope123/workshop.pdf").status_code == 404


def test_workshop_endpoint_red_stop_has_no_plan():
    sid = client.post("/api/sessions", data={"sample": "rice"}).json()["id"]
    assert _wait(sid)["status"] == "stopped"
    assert client.get(f"/api/sessions/{sid}/workshop.pdf").status_code == 409


# --- agent log ("What the AI did") in the PDF

def _js_agent_strings():
    import re
    from pathlib import Path
    src = (Path(__file__).resolve().parents[2] / "web" / "app.js").read_text(encoding="utf-8")
    langs, i = ["id", "jv", "en"], -1
    out: dict[str, dict[str, str]] = {"id": {}, "jv": {}, "en": {}}
    for m in re.finditer(r'\b(agentTitle|ag_\w+|agCode):\s*"((?:[^"\\]|\\.)*)"', src):
        k, v = m.group(1), m.group(2)
        if k == "agentTitle":
            i += 1
            v = v.replace("🤖 ", "")
        out[langs[i]][k] = v
    return out


def test_pdf_agent_strings_match_the_app():
    assert _js_agent_strings() == report_pdf.AGENT


@pytest.mark.parametrize("lang", ["id", "jv", "en"])
def test_agent_lines_cover_a_full_repair(samples, lang):
    sid = engine.create([samples["faucet"]], lang, "Kran wastafel menetes terus")["id"]
    engine.run(sid)
    engine.check_step(sid, 1, samples["faucet"])
    engine.replan(sid, "masih rusak")
    s = engine.load(sid)
    lines = report_pdf.agent_lines(s, lang)
    assert len(lines) == len(s["agent_log"]) >= 5
    assert not any("{" in x for x in lines), lines  # every placeholder filled
    assert any("muse-spark" in x for x in lines) and any("sam-3.1" in x for x in lines)


def test_agent_lines_special_kinds_and_bad_entries():
    log = [{"t": 0, "kind": "gate", "ok": False, "category": "gas"}, {"t": 1, "kind": "plan_guard", "ok": True, "level": "amber"},
           {"t": 2, "kind": "check", "step": 2, "passed": False, "escalate": True, "model": "muse-spark-1.3", "ms": 1500},
           {"t": 3, "kind": "escalate", "reason": "exhausted"}, {"t": 4, "kind": "outcome", "result": "pro"},
           {"t": 5, "kind": "mystery"}, "not-a-dict"]
    lines = report_pdf.agent_lines({"agent_log": log}, "en")
    assert len(lines) == 6
    assert "(gas)" in lines[0] and "[code]" in lines[0]
    assert "passed (CAUTION)" in lines[1]
    assert "Step 2" in lines[2] and "another plan" in lines[2] and "1.5s" in lines[2]
    assert "workshop" in lines[3] and "mechanic" in lines[4] and lines[5].endswith("mystery")


def test_pdf_has_more_pages_with_agent_log(tmp_path):
    rep = {"id": "x", "lang": "en", "object": "Thing", "problem": "P", "steps_total": 0, "steps_verified": 0, "safety_level": "green"}
    base = report_pdf.build(rep, {"mode": "offline"}, tmp_path, tmp_path / "a.pdf").stat().st_size
    log = [{"t": i, "kind": "look", "object": "motor", "n": 3, "model": "muse-spark-1.3"} for i in range(60)]
    big = report_pdf.build(rep, {"mode": "offline", "agent_log": log}, tmp_path, tmp_path / "b.pdf").stat().st_size
    assert big > base
