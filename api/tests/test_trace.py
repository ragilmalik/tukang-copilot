"""Pipeline trace ("Under the hood"): stage -> model mapping in the session JSON and in the PDF report."""
from __future__ import annotations

import io
import time
from typing import Any

from fastapi.testclient import TestClient
from PIL import Image

from api.main import app
from api.trace import CODE_LABEL, TTS_LABEL, build_trace, meta_stage_count

MODELS = {"listen": "asr-x", "listen_javanese": "audio-jv", "look": "spark-v", "segment": "sam-3.1",
          "diagnose": "spark-r", "plan": "spark-r", "illustrate": "img-m", "verify": "spark-v"}


def _s(lang: str = "id", **over: Any) -> dict[str, Any]:
    s: dict[str, Any] = {"lang": lang, "models": dict(MODELS), "stages": {
        "listen": {"status": "done", "ms": 1200}, "gate": {"status": "done"}, "look": {"status": "done", "ms": 900},
        "segment": {"status": "skipped"}, "diagnose": {"status": "done", "ms": 2000}}}
    s.update(over)
    return s


def test_trace_order_and_kinds() -> None:
    rows = build_trace(_s())
    assert [r["stage"] for r in rows] == ["listen", "gate", "look", "segment", "diagnose", "plan", "safety", "illustrate", "narrate"]
    by = {r["stage"]: r for r in rows}
    assert by["gate"]["tool"] == CODE_LABEL and by["gate"]["kind"] == "code"
    assert by["narrate"]["tool"] == TTS_LABEL and by["narrate"]["kind"] == "tts"
    assert by["look"]["tool"] == "spark-v" and by["look"]["ms"] == 900
    assert by["plan"]["status"] == "waiting"
    assert meta_stage_count(rows) == 3  # listen, look, diagnose; segment was skipped


def test_trace_javanese_listens_with_audio_model_and_open_weights_kind() -> None:
    s = _s("jv")
    s["models"]["diagnose"] = "muse-spark-open (open weights via Baseten)"
    by = {r["stage"]: r for r in build_trace(s)}
    assert by["listen"]["tool"] == "audio-jv"
    assert by["diagnose"]["kind"] == "open" and by["plan"]["kind"] == "open"


def test_trace_survives_a_bare_session() -> None:
    rows = build_trace({})
    assert len(rows) == 9 and all(r["status"] == "waiting" for r in rows)


def _run(c: TestClient, text: str, lang: str = "id") -> dict[str, Any]:
    b = io.BytesIO()
    Image.new("RGB", (800, 600), (180, 180, 180)).save(b, "JPEG")
    r = c.post("/api/sessions", data={"text": text, "language": lang, "category": "plumbing"},
               files=[("photos", ("a.jpg", b.getvalue(), "image/jpeg"))])
    assert r.status_code == 200, r.text
    sid = r.json()["id"]
    s: dict[str, Any] = {}
    for _ in range(200):
        s = c.get(f"/api/sessions/{sid}").json()
        if s["status"] in {"ready", "error", "stopped"}:
            break
        time.sleep(0.05)
    assert s["status"] == "ready", s["status"]
    return s


def test_session_json_and_pdf_carry_the_trace() -> None:
    c = TestClient(app)
    s = _run(c, "kran wastafel menetes")
    done = [r for r in s["trace"] if r["status"] == "done"]
    assert len(done) >= 5 and {"look", "diagnose", "plan"} <= {r["stage"] for r in done}
    assert any(r["tool"] == "sam-3.1" for r in s["trace"])
    pdf = c.get(f"/api/sessions/{s['id']}/report.pdf")
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")


def test_web_has_hood_panel_in_every_language() -> None:
    from pathlib import Path
    web = Path(__file__).resolve().parents[2] / "web"
    js = (web / "app.js").read_text(encoding="utf-8")
    assert js.count('hood: "') == 3 and js.count("hs_narrate:") == 3
    for page in ("index.html", "guide.html"):
        assert 'id="hoodList"' in (web / page).read_text(encoding="utf-8")
