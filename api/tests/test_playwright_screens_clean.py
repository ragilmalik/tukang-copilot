"""Every main screen in real Chromium with no console error and no page error (1.32.0 audit), the owner's
actions working through the owner token, a repair a restart interrupted coming back with Try again, and a
progress screen that stays honest on a slow (throttled) connection. Skips cleanly without Chromium."""
import os
import shutil
import socket
import threading
import time
from pathlib import Path
from typing import Any

import pytest

pw = pytest.importorskip("playwright.sync_api")
FIX = Path(__file__).parent / "fixtures"


def _chromium_path() -> str | None:
    for p in (os.environ.get("PLAYWRIGHT_CHROMIUM"), shutil.which("chromium"), shutil.which("chromium-browser"), shutil.which("google-chrome")):
        if p and Path(p).exists():
            return p
    return None


@pytest.fixture
def server() -> Any:
    import uvicorn

    from api.main import app

    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    srv = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    t = threading.Thread(target=srv.run, daemon=True)
    t.start()
    for _ in range(100):
        if srv.started:
            break
        time.sleep(0.05)
    os.environ["NO_PROXY"] = "127.0.0.1,localhost"
    yield f"http://127.0.0.1:{port}"
    srv.should_exit = True
    t.join(5)


@pytest.fixture
def browser() -> Any:
    with pw.sync_playwright() as p:
        try:
            b = p.chromium.launch(executable_path=_chromium_path(), args=["--no-proxy-server"])
        except Exception as e:
            pytest.skip(f"Chromium not available: {str(e).splitlines()[0]}")
        yield b
        b.close()


def _phone(browser: Any, problems: list[str]) -> Any:
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, locale="id-ID")
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: problems.append(f"pageerror: {e}"))
    # a 403/404/409 the app expects shows up as a console "Failed to load resource" line; anything else is a bug
    pg.on("console", lambda m: problems.append(f"console: {m.text}") if m.type == "error" and "Failed to load resource" not in m.text else None)
    pg.on("response", lambda r: problems.append(f"{r.status} {r.url}") if r.status >= 500 or r.status == 403 else None)
    return pg


def test_every_main_screen_has_no_console_error(server: str, browser: Any) -> None:
    problems: list[str] = []
    pg = _phone(browser, problems)
    pg.goto(server + "/")
    pg.wait_for_selector("#modeBadge:not(.hidden)")
    pg.click('button.sample[data-sample="motor"]')                       # progress -> question
    pg.wait_for_selector("#question:not(.hidden)", timeout=20000)
    pg.fill("#answerText", "tidak")
    pg.click("#answerBtn")                                                # answer (owner token)
    pg.wait_for_selector("#result:not(.hidden)", timeout=20000)
    pg.set_input_files("#stepPhoto", str(FIX / "sample_faucet_hose_clamp.jpg"))  # step check (owner token)
    pg.wait_for_selector("#checkResult:not(.hidden)")
    pg.wait_for_function("() => !document.querySelector('#checkResult').textContent.includes('…')", timeout=15000)
    sid = pg.evaluate("() => S.id")
    pg.fill("#stuckText", "masih mati")
    pg.click("#stuckBtn")                                                 # still broken (owner token)
    pg.wait_for_function("() => S && Number(S.cause_index) === 1", timeout=20000)
    pg.goto(server + "/")
    pg.click('button.sample[data-sample="rice"]')                        # red stop
    pg.wait_for_selector("#stopBox:not(.hidden)", timeout=20000)
    viewer = _phone(browser, problems)                                    # someone the owner shared the guide with
    viewer.goto(f"{server}/guide/{sid}")
    viewer.wait_for_selector("#result:not(.hidden)", timeout=20000)
    viewer.goto(f"{server}/guide/aaaaaaaaaaaa")                           # an expired link
    assert "Panduan ini sudah tidak ada" in viewer.content()
    viewer.goto(server + "/wa")
    viewer.wait_for_load_state("load")
    assert not problems, problems


def test_a_repair_a_restart_interrupted_comes_back_with_try_again(server: str, browser: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    from api.pipeline import engine, mock
    from api.settings import settings

    problems: list[str] = []
    pg = _phone(browser, problems)
    pg.goto(server + "/")
    sid = engine.create([mock.make_sample_photos(settings.data_dir / "s")["faucet"]], "id", "Kran netes terus", owner_token="tok")["id"]
    s = engine.load(sid)
    s["status"], s["stages"]["look"] = "running", {"status": "running", "note": ""}
    engine.save(s)
    monkeypatch.setattr(engine, "STARTED_AT", time.time() + 5)
    assert engine.recover_interrupted() == 1                              # what the server does when it starts
    pg.evaluate("([id, tok]) => { localStorage.setItem('tc_owner', JSON.stringify({[id]: tok})); }", [sid, "tok"])
    pg.goto(f"{server}/#{sid}")
    pg.wait_for_selector("#retryBtn:not(.hidden)", timeout=15000)
    assert "dimulai ulang" in pg.inner_text("#progress")
    pg.click("#retryBtn")
    pg.wait_for_selector("#result:not(.hidden)", timeout=20000)
    assert not problems, problems


def test_progress_stays_honest_on_a_slow_connection(server: str, browser: Any) -> None:
    problems: list[str] = []
    pg = _phone(browser, problems)
    pg.goto(server + "/")
    cdp = pg.context.new_cdp_session(pg)
    cdp.send("Network.enable")
    cdp.send("Network.emulateNetworkConditions", {"offline": False, "latency": 400, "downloadThroughput": 50_000, "uploadThroughput": 25_000})
    pg.click('button.sample[data-sample="faucet"]')
    pg.wait_for_selector("#progress:not(.hidden)", timeout=10000)
    assert pg.is_visible("#progTitle")                                    # "Checking..." at once, before any answer
    pg.wait_for_function("() => document.querySelector('#elapsed').textContent.trim() !== ''", timeout=5000)  # a clock the phone counts
    pg.wait_for_function("() => document.querySelectorAll('#stageList li').length > 0", timeout=30000)  # then the real stages
    pg.wait_for_selector("#result:not(.hidden)", timeout=40000)
    cdp.send("Network.emulateNetworkConditions", {"offline": True, "latency": 0, "downloadThroughput": -1, "uploadThroughput": -1})
    pg.evaluate("() => window.dispatchEvent(new Event('offline'))")
    pg.wait_for_selector("#offlineBar:not(.hidden)", timeout=5000)        # the phone says it is offline
    assert not problems, problems
