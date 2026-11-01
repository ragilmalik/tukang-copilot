"""Closing the loop: "it works now" / "a mechanic took over", the saving it counts, the PDF line, the web wiring."""
import time
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.tests.owner_auth import owner

client = TestClient(app)
WEB = Path(__file__).resolve().parents[2] / "web"


def _ready(sample: str, lang: str = "en") -> dict[str, Any]:
    sid = client.post("/api/sessions", data={"sample": sample, "language": lang}).json()["id"]
    t0 = time.time()
    while time.time() - t0 < 20:
        s: dict[str, Any] = client.get(f"/api/sessions/{sid}").json()
        if s["status"] in ("ready", "stopped", "needs_answer", "error"):
            return s
        time.sleep(0.05)
    raise AssertionError("timeout")


def test_fixed_counts_the_saving():
    s = _ready("pump")
    r = client.post(f"/api/sessions/{s['id']}/outcome", data={"result": "fixed"}, headers=owner(s['id']))
    assert r.status_code == 200
    oc = r.json()["outcome"]
    assert oc["result"] == "fixed" and oc["saved_idr"] == s["diagnosis"]["diy_saving_idr"] > 0
    assert client.get(f"/api/sessions/{s['id']}").json()["outcome"]["result"] == "fixed"
    assert client.get(f"/api/sessions/{s['id']}/report").json()["outcome"]["result"] == "fixed"


def test_pro_counts_no_saving():
    s = _ready("faucet")
    oc = client.post(f"/api/sessions/{s['id']}/outcome", data={"result": " PRO "}, headers=owner(s['id'])).json()["outcome"]
    assert oc["result"] == "pro" and oc["saved_idr"] == 0


@pytest.mark.parametrize("bad", ["", "maybe", "fixed; drop", "x" * 400])
def test_unknown_result_is_rejected(bad):
    s = _ready("faucet")
    assert client.post(f"/api/sessions/{s['id']}/outcome", data={"result": bad}, headers=owner(s['id'])).status_code == 422
    assert "outcome" not in client.get(f"/api/sessions/{s['id']}").json()


def test_unknown_session_and_red_stop():
    assert client.post("/api/sessions/nope/outcome", data={"result": "fixed"}).status_code == 404
    s = _ready("rice")  # red stop: there is no plan to mark as fixed
    assert s["status"] == "stopped"
    assert client.post(f"/api/sessions/{s['id']}/outcome", data={"result": "fixed"}, headers=owner(s['id'])).status_code == 409


def test_replan_clears_outcome():
    s = _ready("pump")
    client.post(f"/api/sessions/{s['id']}/outcome", data={"result": "fixed"}, headers=owner(s['id']))
    j = client.post(f"/api/sessions/{s['id']}/replan", data={"report": "still broken"}).json()
    assert j["status"] == "ready" and "outcome" not in j


@pytest.mark.parametrize("lang", ["id", "jv", "en"])
def test_pdf_has_result_line(lang, monkeypatch):
    from api.render import report_pdf

    seen: list[str] = []
    orig = report_pdf._Doc.text

    def spy(self, txt, *a, **k):
        seen.append(str(txt))
        return orig(self, txt, *a, **k)

    monkeypatch.setattr(report_pdf._Doc, "text", spy)
    s = _ready("pump", lang)
    client.post(f"/api/sessions/{s['id']}/outcome", data={"result": "fixed"}, headers=owner(s['id']))
    r = client.get(f"/api/sessions/{s['id']}/report.pdf")
    assert r.status_code == 200 and r.content.startswith(b"%PDF")
    label = report_pdf.LABELS[lang]
    assert any(t.startswith(label["outcome"] + ":") and label["o_fixed"] in t for t in seen), seen


def test_web_has_outcome_wiring_in_every_language():
    js = (WEB / "app.js").read_text()
    for key in ("outcomeAsk", "fixedBtn", "proBtn", "fixedThanks", "proThanks", "savedTotal"):
        assert js.count(f"{key}:") == 3, key
    for page in ("index.html", "guide.html"):
        html = (WEB / page).read_text()
        assert 'id="fixedBtn"' in html and 'id="proBtn"' in html and 'id="outcomeMsg"' in html
    assert 'id="garageSaved"' in (WEB / "index.html").read_text()
