"""A repair whose worker died without saving its end state (a full disk, a crash inside the worker) must not spin.

Up to 1.33.0 a full disk during a repair made every save fail, the last one included, so session.json kept
"running" with no worker left. The phone showed the progress screen until its 7.5 min stream ran out, and only a
server restart (engine.recover_interrupted) turned it into an error with Try again. Each worker now registers
itself; a "running" repair with no worker in this process and no save for STALL_GRACE_S is shown as an error
the owner can retry, and saved that way as soon as the disk takes writes again."""
import asyncio
import errno
import threading
import time
from typing import Any

import pytest

from api import main
from api.main import app
from api.pipeline import engine, mock
from api.settings import settings
from api.tests.owner_auth import OwnerClient

client = OwnerClient(app)


def _wait(sid: str, until: tuple[str, ...] = ("ready", "stopped", "needs_answer", "error", "exhausted")) -> dict[str, Any]:
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        s: dict[str, Any] = engine.load(sid)
        if s["status"] in until:
            return s
        time.sleep(0.02)
    raise AssertionError("timeout")


def _new_repair() -> str:
    """A repair made the way the web API makes it, but with no worker started yet (and no owner token)."""
    photo = mock.make_sample_photos(settings.data_dir / "s")["faucet"]
    return str(engine.create([photo], "en", "my kitchen tap drips")["id"])


def _full_disk_after(monkeypatch: pytest.MonkeyPatch, n_ok: int) -> dict[str, bool]:
    """engine.save works n_ok times, then fails like a full disk until state["full"] is set to False."""
    real = engine.save
    state = {"full": True}
    calls = {"n": 0}

    def save(s: dict[str, Any]) -> None:
        calls["n"] += 1
        if state["full"] and calls["n"] > n_ok:
            raise OSError(errno.ENOSPC, "No space left on device")
        real(s)

    monkeypatch.setattr(engine, "save", save)
    return state


def _died_mid_repair(monkeypatch: pytest.MonkeyPatch) -> tuple[str, dict[str, bool]]:
    sid = _new_repair()
    state = _full_disk_after(monkeypatch, n_ok=3)  # "running" reaches the disk, then the disk is full
    t = threading.Thread(target=engine.run, args=(sid,), name="test-worker")
    t.start()
    t.join(30)
    assert not t.is_alive()
    assert engine.load(sid)["status"] == "running"  # what the disk says: where the old bug left the owner
    monkeypatch.setattr(engine, "STALL_GRACE_S", 0.0, raising=False)
    return sid, state


def test_a_repair_whose_worker_died_on_a_full_disk_is_shown_as_retryable(monkeypatch: pytest.MonkeyPatch) -> None:
    sid, state = _died_mid_repair(monkeypatch)
    view = client.get(f"/api/sessions/{sid}").json()  # the disk is still full: the view says so anyway
    assert view["status"] == "error" and view["error_kind"] == "stalled" and "Try again" in view["error"]
    assert engine.load(sid)["status"] == "running"
    state["full"] = False
    view = client.get(f"/api/sessions/{sid}").json()
    assert view["status"] == "error"
    assert engine.load(sid)["status"] == "error"  # saved once the disk takes writes again
    r = client.post(f"/api/sessions/{sid}/retry")
    assert r.status_code == 200, r.text
    assert _wait(sid)["status"] == "ready"


def test_the_progress_stream_ends_on_a_stalled_repair(monkeypatch: pytest.MonkeyPatch) -> None:
    sid, state = _died_mid_repair(monkeypatch)
    state["full"] = False

    async def drive() -> list[str]:
        resp = await main.events(sid)
        return [c if isinstance(c, str) else bytes(c).decode() async for c in resp.body_iterator]

    chunks = asyncio.run(asyncio.wait_for(drive(), 10))
    assert len(chunks) == 1 and '"status": "error"' in chunks[0] and '"stalled"' in chunks[0]


def test_the_janitor_marks_a_stalled_repair(monkeypatch: pytest.MonkeyPatch) -> None:
    sid, state = _died_mid_repair(monkeypatch)
    state["full"] = False
    engine.cleanup()
    s = engine.load(sid)
    assert s["status"] == "error" and s["error_kind"] == "stalled"
    assert s["stages"]["look"]["status"] != "running"  # Try again restarts the stage that was cut off


def test_a_running_repair_with_its_worker_alive_is_left_alone(monkeypatch: pytest.MonkeyPatch) -> None:
    sid = _new_repair()
    monkeypatch.setattr(engine, "STALL_GRACE_S", 0.0, raising=False)
    gate, entered = threading.Event(), threading.Event()
    real = engine.stage_look

    def slow_look(s: dict[str, Any]) -> Any:
        entered.set()
        assert gate.wait(30)
        return real(s)

    monkeypatch.setattr(engine, "stage_look", slow_look)
    t = threading.Thread(target=engine.run, args=(sid,), name="session-test")
    t.start()
    try:
        assert entered.wait(30)
        assert client.get(f"/api/sessions/{sid}").json()["status"] == "running"
        engine.cleanup()
        assert engine.load(sid)["status"] == "running"
    finally:
        gate.set()
        t.join(30)
    assert engine.load(sid)["status"] in {"ready", "needs_answer"}


def test_a_fresh_running_repair_is_not_stalled_inside_the_grace_time() -> None:
    sid = _new_repair()
    s = engine.load(sid)
    s["status"] = "running"  # what answer() and retry() leave for the worker that start() is about to run
    engine.save(s)
    assert client.get(f"/api/sessions/{sid}").json()["status"] == "running"
    engine.cleanup()
    assert engine.load(sid)["status"] == "running"


def test_retry_on_a_full_disk_answers_503_not_500(monkeypatch: pytest.MonkeyPatch) -> None:
    sid, state = _died_mid_repair(monkeypatch)
    state["full"] = False
    assert client.get(f"/api/sessions/{sid}").json()["status"] == "error"
    state["full"] = True
    r = client.post(f"/api/sessions/{sid}/retry")
    assert r.status_code == 503 and r.headers.get("retry-after")
