"""The WhatsApp simulator page (/wa) in real Chromium: labelled as a simulator, runs a repair through the same
handler in id/jv/en, buttons work, red stop shows no steps, no JS errors."""
import pytest

pytest.importorskip("playwright.sync_api")
import playwright.sync_api as pw  # noqa: E402

from api.channels import whatsapp as wa  # noqa: E402
from api.tests.test_playwright_smoke import _chromium_path  # noqa: E402

pytestmark = pytest.mark.slow


@pytest.fixture
def server():
    import os
    import socket
    import threading
    import time

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


def _page(p, server, lang):
    try:
        b = p.chromium.launch(executable_path=_chromium_path(), args=["--no-proxy-server"])
    except Exception as e:
        pytest.skip(f"Chromium not available: {str(e).splitlines()[0]}")
    pg = b.new_page(viewport={"width": 390, "height": 844})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(f"{server}/wa?lang={lang}")
    pg.wait_for_selector("#chips button")
    return b, pg, errs


@pytest.mark.parametrize("lang,label,first,done", [
    ("id", "Simulator, menjalankan mesin yang sama dalam mode demo", "Langkah 1 dari 4", "Selesai"),
    ("jv", "Simulator, nglakokake mesin sing padha ing mode demo", "Langkah 1 saka 4", "Rampung"),
    ("en", "Simulator, runs the same engine on offline sample answers", "Step 1 of 4", "Done"),
])
def test_simulator_repair_flow(server, lang, label, first, done):
    with pw.sync_playwright() as p:
        b, pg, errs = _page(p, server, lang)
        assert pg.inner_text("#simLabel") == label
        assert "Simulator, runs the same engine on offline sample answers" in pg.inner_text(".sim")
        pg.locator("#chips button").nth(0).click()  # sample: dripping tap
        pg.wait_for_selector(".btns button", timeout=30000)
        assert first in pg.inner_text("#log")
        assert pg.locator(".btns button").first.inner_text() == done
        assert pg.locator("#log img").count() >= 2  # the owner's photo and the SAM-marked photo
        pg.locator(".btns button").first.click()
        pg.wait_for_function("() => document.querySelectorAll('.btns').length >= 2", timeout=30000)
        assert first.replace("1", "2", 1) in pg.inner_text("#log")
        b.close()
    assert wa.wait_idle(20)
    assert errs == []


def test_simulator_red_stop_shows_no_steps(server):
    with pw.sync_playwright() as p:
        b, pg, errs = _page(p, server, "jv")
        pg.evaluate("sessionStorage.clear()")
        pg.reload()
        pg.wait_for_selector("#chips button")
        pg.locator("#chips button").nth(3).click()  # gas smell, text only
        pg.wait_for_function("() => document.querySelectorAll('.row:not(.me)').length >= 1", timeout=30000)
        pg.wait_for_timeout(1500)
        text = pg.inner_text("#log")
        assert "keslametan" in text and "Google Maps" in text and "Langkah" not in text
        assert pg.locator(".btns").count() == 0
        b.close()
    assert wa.wait_idle(20)
    assert errs == []
