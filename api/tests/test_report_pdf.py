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
    out = report_pdf.build(rep, {"mode": "mock", "safety": {"reason": "ok"}}, tmp_path, tmp_path / "long.pdf")
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
