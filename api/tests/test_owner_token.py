"""Owner token, WhatsApp simulator link on the first screen, render.yaml WhatsApp settings.

Before 1.27.0, anyone holding a shared guide link could still POST an outcome (and erase the repair) even though the guide page
no longer offered it. A repair made through the web API now returns an owner token once; the owner's phone keeps it
in localStorage and sends it as X-Owner-Token. Without it the outcome and erase calls answer 403.
"""
import re
import sys
import time
from pathlib import Path
from typing import Any

import pytest
import yaml
from fastapi.testclient import TestClient

from api.main import app
from api.pipeline import engine

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"
SAMPLES = ROOT / "samples"
client = TestClient(app)


def _made(sample: str = "faucet", lang: str = "en") -> tuple[str, str]:
    j = client.post("/api/sessions", data={"sample": sample, "language": lang}).json()
    sid, tok = j["id"], j.get("owner_token", "")
    t0 = time.time()
    while time.time() - t0 < 20:
        if client.get(f"/api/sessions/{sid}").json()["status"] in ("ready", "stopped", "needs_answer", "error"):
            break
        time.sleep(0.05)
    return sid, tok


def test_create_returns_a_long_random_owner_token():
    a, ta = _made()
    b, tb = _made()
    assert len(ta) >= 20 and len(tb) >= 20 and ta != tb


def test_owner_token_never_leaves_the_server_after_creation():
    sid, tok = _made()
    for url in (f"/api/sessions/{sid}", f"/api/sessions/{sid}/report", f"/api/sessions/{sid}/handoff", f"/guide/{sid}"):
        r = client.get(url)
        assert r.status_code == 200 and tok not in r.text, url
    with client.stream("GET", f"/api/sessions/{sid}/events") as r:
        body = "".join(r.iter_text())
    assert tok not in body


@pytest.mark.parametrize("headers", [{}, {"X-Owner-Token": ""}, {"X-Owner-Token": "guess"}])
def test_shared_guide_viewer_cannot_set_the_outcome(headers):
    sid, _ = _made()
    r = client.post(f"/api/sessions/{sid}/outcome", data={"result": "fixed"}, headers=headers)
    assert r.status_code == 403 and "read-only" in r.json()["detail"]
    assert "outcome" not in client.get(f"/api/sessions/{sid}").json()


def test_owner_sets_the_outcome_with_the_token():
    sid, tok = _made()
    r = client.post(f"/api/sessions/{sid}/outcome", data={"result": "fixed"}, headers={"X-Owner-Token": tok})
    assert r.status_code == 200 and r.json()["outcome"]["result"] == "fixed"
    assert "owner_token" not in r.json()


def test_another_repairs_token_does_not_work():
    a, _ = _made()
    _, tb = _made()
    assert client.post(f"/api/sessions/{a}/outcome", data={"result": "pro"}, headers={"X-Owner-Token": tb}).status_code == 403


def test_erase_needs_the_owner_token_too():
    sid, tok = _made()
    assert client.delete(f"/api/sessions/{sid}").status_code == 403
    assert client.get(f"/api/sessions/{sid}").status_code == 200          # still there
    assert client.delete(f"/api/sessions/{sid}", headers={"X-Owner-Token": tok}).json()["deleted"] is True
    assert client.get(f"/api/sessions/{sid}").status_code == 404


def test_sessions_saved_before_the_token_existed_stay_usable():
    s = engine.create([SAMPLES / "faucet.jpg"], "en", "tap drips")
    old = engine.load(s["id"])
    old.pop("owner_token", None)
    engine.save(old)
    assert client.delete(f"/api/sessions/{s['id']}").status_code == 200


def test_whatsapp_repairs_get_a_token_that_is_never_sent():
    src = (ROOT / "api" / "channels" / "whatsapp.py").read_text(encoding="utf-8")
    assert re.search(r"engine\.create\([^\n]*owner_token=secrets\.token_urlsafe\(", src)
    assert "owner_token" not in re.sub(r"engine\.create\([^\n]*\n", "", src)  # not used anywhere else in the channel


def test_app_keeps_the_token_on_the_phone_and_sends_it():
    js = (WEB / "app.js").read_text(encoding="utf-8")
    assert "ownerSet(j.id, j.owner_token)" in js
    assert re.search(r"/outcome`, \{ method: \"POST\", body: fd, headers: ownerHeaders\(S\.id\) \}", js)
    assert js.count('method: "DELETE", headers: ownerHeaders(') == 2
    assert js.count("ownerOnly:") == 3                     # the 403 message in id, en and jv
    assert "localStorage.removeItem(OWNER_KEY)" in js       # "Clear history" forgets the tokens too


# --- WhatsApp simulator link on the first screen
def test_index_links_the_simulator_hidden_until_the_server_says_it_is_on():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    m = re.search(r'<p class="small center hidden" id="waSim"><a id="waSimLink" class="waSimLink" href="/wa" data-t="waSim">', html)
    assert m
    js = (WEB / "app.js").read_text(encoding="utf-8")
    assert 'fetch("/api/wa-sim/info")' in js and "i.enabled" in js
    assert js.count("waSim:") == 3 and "Also works in WhatsApp" in js


def test_static_build_has_no_simulator_link_or_page(tmp_path):
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_static  # type: ignore[import-not-found]

    out = tmp_path / "site"
    build_static.build(out)
    assert build_static.verify(out) == []
    html = (out / "index.html").read_text(encoding="utf-8")
    assert "waSim" not in html and 'href="/wa"' not in html
    assert not (out / "static" / "wa.html").exists()


def test_sim_info_reports_enabled_in_demo_mode():
    j: dict[str, Any] = client.get("/api/wa-sim/info").json()
    assert j["enabled"] is True and j["channel_live"] is False


# --- render.yaml
def test_render_lists_the_whatsapp_secrets_without_values():
    env = yaml.safe_load((ROOT / "render.yaml").read_text(encoding="utf-8"))["services"][0]["envVars"]
    by = {e["key"]: e for e in env}
    for k in ("WA_TOKEN", "WA_PHONE_NUMBER_ID", "WA_VERIFY_TOKEN", "WA_APP_SECRET"):
        assert by[k] == {"key": k, "sync": False}, k
