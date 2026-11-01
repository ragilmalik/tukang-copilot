"""Privacy controls: erase one repair now, periodic purge on a long-running server."""
import asyncio
import os
import threading
import time
from typing import Any

from fastapi.testclient import TestClient

from api import main
from api.main import app
from api.pipeline import engine
from api.settings import settings
from api.tests.owner_auth import owner

client = TestClient(app)


def _wait(sid: str, until: tuple[str, ...] = ("ready", "stopped", "needs_answer", "error", "exhausted")) -> dict[str, Any]:
    t0 = time.time()
    while time.time() - t0 < 20:
        s: dict[str, Any] = client.get(f"/api/sessions/{sid}").json()
        if s["status"] in until:
            return s
        time.sleep(0.05)
    raise AssertionError("timeout")


def test_delete_erases_files_and_session():
    sid = client.post("/api/sessions", data={"sample": "faucet", "language": "en"}).json()["id"]
    _wait(sid)
    folder = settings.data_dir / "sessions" / sid
    assert folder.exists() and any(folder.iterdir())
    own = owner(sid)
    r = client.delete(f"/api/sessions/{sid}", headers=own)
    assert r.status_code == 200 and r.json() == {"id": sid, "deleted": True}
    assert not folder.exists()
    assert client.get(f"/api/sessions/{sid}").status_code == 404
    assert client.delete(f"/api/sessions/{sid}", headers=own).status_code == 404  # already gone
    assert client.get(f"/api/sessions/{sid}/report.pdf").status_code == 404


def test_delete_unknown_or_bad_id_is_404():
    assert client.delete("/api/sessions/doesnotexist").status_code == 404
    assert client.delete("/api/sessions/bad..id").status_code == 404


def test_delete_while_worker_running_does_not_resurrect_folder():
    sid = client.post("/api/sessions", data={"sample": "motor", "language": "id"}).json()["id"]
    assert client.delete(f"/api/sessions/{sid}", headers=owner(sid)).status_code in (200, 404)
    time.sleep(1.0)  # let the worker thread finish its remaining saves
    for t in threading.enumerate():
        if t.name.startswith("session-"):
            t.join(20)
    assert not (settings.data_dir / "sessions" / sid).exists()


def test_janitor_purges_expired_sessions_repeatedly(monkeypatch):
    sid = client.post("/api/sessions", data={"sample": "faucet"}).json()["id"]
    _wait(sid)
    f = settings.data_dir / "sessions" / sid / "session.json"
    old = time.time() - 3600 * (settings.retention_hours + 1)
    os.utime(f, (old, old))

    async def run() -> None:
        task = asyncio.create_task(main._janitor(0.05))
        await asyncio.sleep(0.4)
        task.cancel()

    asyncio.run(run())
    assert not f.exists()


def test_janitor_survives_a_failing_cleanup(monkeypatch):
    calls = {"n": 0}

    def boom(*_a: object) -> int:
        calls["n"] += 1
        raise RuntimeError("disk gone")

    monkeypatch.setattr(engine, "cleanup", boom)

    async def run() -> None:
        task = asyncio.create_task(main._janitor(0.05))
        await asyncio.sleep(0.4)
        assert not task.done()
        task.cancel()

    asyncio.run(run())
    assert calls["n"] >= 2


def test_ui_has_erase_button_and_strings():
    html = (main.WEB / "index.html").read_text(encoding="utf-8")
    js = (main.WEB / "app.js").read_text(encoding="utf-8")
    assert 'id="eraseBtn"' in html and 'method: "DELETE"' in js
    for key in ("erase:", "eraseAsk:", "erased:"):
        assert js.count(key) == 3  # id, en, jv
