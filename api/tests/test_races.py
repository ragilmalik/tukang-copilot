"""Races between the requests that change one repair (1.32.0 audit, after the lost-answer race CI found on 6 Nov).

Every test is deterministic: it holds the session lock, or blocks the (mock) model call on an Event, or meets two
threads at a Barrier, instead of sleeping and hoping the timing lines up. Each one checks a behaviour that was wrong
on 1.31.1; the double re-plan, the check on a red stop and the erased spend were confirmed by running the same steps
on 5d9dd75 (the 1.31.1 head)."""
import asyncio
import io
import json
import math
import threading
import time
from typing import Any

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from api import guard
from api.main import app
from api.pipeline import engine, mock, track
from api.settings import settings
from api.tests.owner_auth import OwnerClient, owner

client = OwnerClient(app)
WAIT_S = 60


def _wait(sid: str, until: tuple[str, ...] = ("ready", "stopped", "needs_answer", "error", "exhausted")) -> dict[str, Any]:
    deadline = time.monotonic() + WAIT_S
    while time.monotonic() < deadline:
        s: dict[str, Any] = engine.load(sid)
        if s["status"] in until:
            return s
        time.sleep(0.02)
    raise AssertionError("timeout")


def _ready(sample: str = "faucet") -> str:
    sid: str = client.post("/api/sessions", data={"sample": sample, "language": "en"}).json()["id"]
    assert _wait(sid)["status"] == "ready"
    return sid


def _jpg() -> io.BytesIO:
    b = io.BytesIO()
    Image.new("RGB", (640, 480), (190, 190, 190)).save(b, "JPEG")
    b.seek(0)
    return b


def _photo(tmp_path: Any, name: str = "after.jpg") -> Any:
    p = tmp_path / name
    Image.new("RGB", (640, 480), (190, 190, 190)).save(p, "JPEG")
    return p


class Blocker:
    """Wraps a function so its first call waits until release(); later calls run straight through."""

    def __init__(self, fn: Any) -> None:
        self.fn, self.entered, self.go, self.calls = fn, threading.Event(), threading.Event(), 0

    def __call__(self, *a: Any, **kw: Any) -> Any:
        self.calls += 1
        if self.calls == 1:
            self.entered.set()
            assert self.go.wait(20), "test never released the blocked call"
        return self.fn(*a, **kw)


def _in_thread(fn: Any, *a: Any) -> tuple[threading.Thread, dict[str, Any]]:
    box: dict[str, Any] = {}

    def go() -> None:
        try:
            box["value"] = fn(*a)
        except BaseException as e:  # noqa: BLE001 (handed back to the test)
            box["error"] = e

    t = threading.Thread(target=go, daemon=True)
    t.start()
    return t, box


# --- A1: two "Still broken" at once
def test_a_second_replan_while_one_is_planning_is_busy(monkeypatch: pytest.MonkeyPatch) -> None:
    sid = _ready()
    slow = Blocker(engine.stage_plan)
    monkeypatch.setattr(engine, "stage_plan", slow)
    t, box = _in_thread(engine.replan, sid, "still drips")
    assert slow.entered.wait(10)
    try:
        with pytest.raises(engine.Busy):
            engine.replan(sid, "still drips")
        r = client.post(f"/api/sessions/{sid}/replan", data={"report": "still drips"})
        assert r.status_code == 409 and r.headers.get("retry-after")
    finally:
        slow.go.set()
    t.join(20)
    assert "error" not in box, box
    s = engine.load(sid)
    assert s["cause_index"] == 1 and len(s["history"]) == 1 and len(s["attempts"]) == 1


# --- A2: a step check that finishes after a re-plan
def test_a_check_that_finishes_after_a_replan_is_not_put_on_the_new_plan(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
    sid = _ready()
    slow = Blocker(mock.step_check)
    monkeypatch.setattr(mock, "step_check", slow)
    t, box = _in_thread(engine.check_step, sid, 1, _photo(tmp_path))
    assert slow.entered.wait(10)
    try:
        engine.replan(sid, "still drips")  # the check holds no lock while the model looks
    finally:
        slow.go.set()
    t.join(20)
    assert box["value"]["stale"] is True
    s = engine.load(sid)
    assert s["cause_index"] == 1 and s["checks"] == {}, "the old plan's check must not tick a step of the new plan"
    assert s["checks_used"] == 1, "the check still counts against the cap"
    assert not any(e["kind"] == "check" for e in s["agent_log"])


# --- A3 and A4: parallel checks
def test_parallel_checks_cannot_get_past_the_photo_check_cap(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
    sid = _ready()
    monkeypatch.setattr(settings, "max_step_checks", 1)
    slow = Blocker(mock.step_check)
    monkeypatch.setattr(mock, "step_check", slow)
    t, box = _in_thread(engine.check_step, sid, 1, _photo(tmp_path, "a.jpg"))
    assert slow.entered.wait(10)
    try:
        with pytest.raises(engine.LimitReached):
            engine.check_step(sid, 1, _photo(tmp_path, "b.jpg"))
    finally:
        slow.go.set()
    t.join(20)
    assert "value" in box and engine.load(sid)["checks_used"] == 1


def test_two_checks_on_one_step_keep_both_photos(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
    sid = _ready()
    slow = Blocker(mock.step_check)
    monkeypatch.setattr(mock, "step_check", slow)
    t, box = _in_thread(engine.check_step, sid, 1, _photo(tmp_path, "a.jpg"))
    assert slow.entered.wait(10)
    try:
        engine.check_step(sid, 1, _photo(tmp_path, "b.jpg"))
    finally:
        slow.go.set()
    t.join(20)
    tries = engine.load(sid)["checks"]["1"]["tries"]
    names = [x["photo"] for x in tries]
    assert len(names) == 2 and len(set(names)) == 2, names
    assert all((engine.session_dir(sid) / n).exists() for n in names)


def test_a_failed_check_gives_its_count_back(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
    sid = _ready()

    def boom(*_a: Any, **_k: Any) -> Any:
        raise RuntimeError("503 from model")

    monkeypatch.setattr(mock, "step_check", boom)
    with pytest.raises(RuntimeError):
        engine.check_step(sid, 1, _photo(tmp_path))
    assert int(engine.load(sid).get("checks_used", 0)) == 0


# --- A5: actions on the wrong status
@pytest.mark.parametrize("status", ["stopped", "running", "needs_answer", "error"])
def test_steps_and_live_guide_are_refused_off_the_steps(status: str, tmp_path: Any) -> None:
    sid = _ready()
    s = engine.load(sid)
    s["status"] = status
    engine.save(s)
    with pytest.raises(ValueError):
        engine.check_step(sid, 1, _photo(tmp_path))
    with pytest.raises(ValueError):
        track.track_step(sid, 1, _photo(tmp_path))
    assert client.post(f"/api/sessions/{sid}/steps/1/check", files={"photo": ("a.jpg", _jpg(), "image/jpeg")}).status_code == 409


@pytest.mark.parametrize("status", ["running", "needs_answer", "stopped", "exhausted"])
def test_replan_only_from_a_plan_on_screen(status: str) -> None:
    sid = _ready()
    s = engine.load(sid)
    s["status"] = status
    engine.save(s)
    with pytest.raises(ValueError):
        engine.replan(sid, "")
    s = engine.load(sid)
    assert s["cause_index"] == 0 and s["history"] == []


# --- A6: a second start
def test_a_second_start_does_not_run_a_finished_repair_again(monkeypatch: pytest.MonkeyPatch) -> None:
    sid = _ready()
    before = engine.load(sid)
    calls: list[str] = []
    real = engine.stage_plan
    def counted(*a: Any, **k: Any) -> Any:
        calls.append("plan")
        return real(*a, **k)

    monkeypatch.setattr(engine, "stage_plan", counted)
    out = engine.run(sid)
    assert calls == [] and out["status"] == "ready"
    after = engine.load(sid)
    assert after["plan"] == before["plan"] and after["agent_log"] == before["agent_log"]


# --- A7: two quick retries
def test_two_quick_retries_make_one(monkeypatch: pytest.MonkeyPatch) -> None:
    sid = _ready()
    s = engine.load(sid)
    s["status"], s["error_kind"] = "error", "busy"
    engine.save(s)
    meet = threading.Barrier(2)
    real_load = engine.load

    def load(x: str) -> dict[str, Any]:
        try:  # both retries reach load() at the same moment on code without the lock
            meet.wait(timeout=0.5)
        except threading.BrokenBarrierError:
            pass
        return real_load(x)

    monkeypatch.setattr(engine, "load", load)
    a, ra = _in_thread(engine.retry, sid)
    b, rb = _in_thread(engine.retry, sid)
    a.join(10)
    b.join(10)
    ok = [r for r in (ra, rb) if "value" in r]
    assert len(ok) == 1, (ra, rb)
    assert isinstance((rb if "value" in ra else ra)["error"], ValueError)
    monkeypatch.setattr(engine, "load", real_load)
    assert real_load(sid)["retries"] == 1


# --- A8: short writers during a re-plan
def test_live_guide_frame_during_a_replan_waits_its_turn(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
    sid = _ready("pump")
    monkeypatch.setattr(settings, "track_min_interval_s", 0.0)
    track._last.clear()
    lock = engine.session_lock(sid)
    lock.acquire()  # stand in for a re-plan in progress
    try:
        with pytest.raises(track.TooFast):
            track.track_step(sid, 1, _photo(tmp_path))
    finally:
        lock.release()
    assert int((engine.load(sid).get("track") or {}).get("frames", 0)) == 0
    assert track.track_step(sid, 1, _photo(tmp_path))["frames_used"] == 1


def test_it_works_now_during_a_replan_is_busy(monkeypatch: pytest.MonkeyPatch) -> None:
    sid = _ready()
    monkeypatch.setattr(engine, "OUTCOME_WAIT_S", 0.05)
    lock = engine.session_lock(sid)
    lock.acquire()
    try:
        with pytest.raises(engine.Busy):
            engine.set_outcome(sid, "fixed")
        r = client.post(f"/api/sessions/{sid}/outcome", data={"result": "fixed"}, headers=owner(sid))
        assert r.status_code == 409
    finally:
        lock.release()
    assert engine.set_outcome(sid, "fixed")["outcome"]["result"] == "fixed"


def test_step_check_runs_off_the_event_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    # A live check takes seconds; on the event loop it froze every other request (polling, other phones).
    sid = _ready()
    seen: list[bool] = []
    real = engine.check_step

    def spy(*a: Any) -> Any:
        try:
            asyncio.get_running_loop()
            seen.append(True)
        except RuntimeError:
            seen.append(False)
        return real(*a)

    monkeypatch.setattr(engine, "check_step", spy)
    assert client.post(f"/api/sessions/{sid}/steps/1/check", files={"photo": ("a.jpg", _jpg(), "image/jpeg")}).status_code == 200
    assert seen == [False]


# --- A9: bookkeeping that used to grow forever
def test_erase_and_janitor_drop_the_lock_and_erase_marks() -> None:
    sid = _ready()
    assert sid in engine._locks
    assert engine.delete(sid)
    assert sid not in engine._locks and sid in engine._deleted
    engine._deleted[sid] = time.time() - engine.DELETED_KEEP_S - 1
    engine.cleanup()
    assert sid not in engine._deleted


def test_janitor_drops_locks_of_expired_sessions() -> None:
    sid = _ready()
    p = engine.session_dir(sid) / "session.json"
    old = time.time() - 3600 * (settings.retention_hours + 1)
    import os

    os.utime(p, (old, old))
    assert engine.cleanup() == 1
    assert sid not in engine._locks


# --- A10: a restart mid-repair
def test_a_repair_left_running_by_a_restart_becomes_retryable(monkeypatch: pytest.MonkeyPatch) -> None:
    sid = engine.create([mock.make_sample_photos(settings.data_dir / "s")["motor"]], "en", "rusak")["id"]
    s = engine.load(sid)
    s["status"] = "running"
    s["stages"]["listen"] = {"status": "done", "note": ""}
    s["stages"]["look"] = {"status": "running", "note": ""}
    engine.save(s)
    monkeypatch.setattr(engine, "STARTED_AT", time.time() + 5)  # as if this process started after that save
    assert engine.recover_interrupted() == 1
    s = engine.load(sid)
    assert s["status"] == "error" and s["error_kind"] == "interrupted" and "restarted" in s["error"]
    assert s["stages"]["look"]["status"] == "error" and s["stages"]["listen"]["status"] == "done"
    r = client.post(f"/api/sessions/{sid}/retry")
    assert r.status_code == 200, r.text
    assert _wait(sid)["status"] in {"ready", "needs_answer"}


def test_recovery_leaves_a_session_its_own_worker_holds(monkeypatch: pytest.MonkeyPatch) -> None:
    sid = engine.create([mock.make_sample_photos(settings.data_dir / "s")["faucet"]], "en", "netes")["id"]
    monkeypatch.setattr(engine, "STARTED_AT", time.time() + 5)
    lock = engine.session_lock(sid)
    lock.acquire()
    try:
        assert engine.recover_interrupted() == 0
    finally:
        lock.release()
    monkeypatch.setattr(engine, "STARTED_AT", 0.0)  # saved after this process started: a worker may still come
    assert engine.recover_interrupted() == 0
    assert engine.load(sid)["status"] == "created"


def test_server_start_runs_the_recovery(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []
    def counted() -> int:
        calls.append(1)
        return 0

    monkeypatch.setattr(engine, "recover_interrupted", counted)
    with TestClient(app) as c:
        assert c.get("/health").status_code == 200
    assert calls == [1]


# --- A11: erase while the progress stream is open
def test_progress_stream_ends_cleanly_when_the_repair_is_erased() -> None:
    # The stream reads the session every half second; an erase in between used to raise FileNotFoundError inside
    # the generator (a server error in the log, the stream cut without a clean end). Driven by hand, no client.
    from api import main

    sid = engine.create([mock.make_sample_photos(settings.data_dir / "s")["faucet"]], "en", "netes")["id"]  # no worker

    async def drive() -> list[str]:
        resp = await main.events(sid)
        it = resp.body_iterator.__aiter__()
        got = [await it.__anext__()]
        assert engine.delete(sid)
        async for chunk in it:  # must end by itself, without an exception
            got.append(chunk)
        return [c if isinstance(c, str) else bytes(c).decode() for c in got]

    chunks = asyncio.run(asyncio.wait_for(drive(), 10))
    assert len(chunks) == 1 and chunks[0].startswith("data: ")


# --- A12: what the janitor used to leave behind
def test_janitor_removes_half_made_folders_and_stale_tmp_files() -> None:
    import os

    root = settings.data_dir / "sessions"
    half = root / "abc123def456"
    half.mkdir(parents=True)
    (half / "photo1.jpg").write_bytes(b"x")
    old = time.time() - 3600 * (settings.retention_hours + 1)
    os.utime(half, (old, old))
    sid = _ready()
    tmp = engine.session_dir(sid) / "session.999.tmp"
    tmp.write_text("{}")
    os.utime(tmp, (time.time() - engine.STALE_TMP_S - 5,) * 2)
    fresh = engine.session_dir(sid) / "session.998.tmp"
    fresh.write_text("{}")
    engine.cleanup()
    assert not half.exists() and not tmp.exists() and fresh.exists() and engine.load(sid)["status"] == "ready"


# --- A13: erasing must not reset the daily spend cap
def test_erasing_a_repair_keeps_its_spend_in_the_daily_cap() -> None:
    sid = _ready()
    s = engine.load(sid)
    s["cost"] = {"spent_usd": 1.25, "budget_usd": 0.5, "by_model": {}}
    engine.save(s)
    now = time.time()
    assert guard.spent_last_24h(now) == pytest.approx(1.25)
    assert engine.delete(sid)
    assert guard.spent_last_24h(now) == pytest.approx(1.25)
    assert guard.spent_last_24h(now + 86400 + 60) == pytest.approx(0.0)
    guard.prune_spend_ledger(now + 86400 + 60)
    assert (settings.data_dir / guard.LEDGER).read_text() == ""


def test_an_erase_counts_in_the_cap_at_once() -> None:
    """The ledger time is rounded down: with round() a spend recorded at x.06 s was stored as x.1 s, after a
    "now" of x.07 s, and the daily sum asked right after the erase left it out (seen on a CI runner)."""
    at = math.floor(time.time()) - 10 + 0.06
    before = guard.spent_last_24h(at + 0.01)
    guard.record_erased_spend(1.0, at)
    assert guard.spent_last_24h(at + 0.01) - before == pytest.approx(1.0)


def test_ledger_lines_hold_numbers_only() -> None:
    guard.record_erased_spend(0.5, time.time())
    rec = json.loads((settings.data_dir / guard.LEDGER).read_text().splitlines()[0])
    assert set(rec) == {"t", "usd"}
