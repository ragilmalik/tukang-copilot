"""Browser smoke test of the main phone flow (mock backend, mobile viewport).

Skips cleanly when Playwright or a Chromium binary is missing. Chromium is found via
PLAYWRIGHT_CHROMIUM (path), Playwright's own download (`python -m playwright install chromium`),
or a system /usr/bin/chromium. Run alone: python -m pytest api/tests/test_playwright_smoke.py -q
"""
import os
import shutil
import socket
import threading
import time
from pathlib import Path

import pytest

pw = pytest.importorskip("playwright.sync_api")
FIX = Path(__file__).parent / "fixtures"


def _chromium_path():
    for p in (os.environ.get("PLAYWRIGHT_CHROMIUM"), shutil.which("chromium"), shutil.which("chromium-browser"), shutil.which("google-chrome")):
        if p and Path(p).exists():
            return p
    return None  # let Playwright try its own bundled browser


@pytest.fixture
def server():
    import uvicorn

    from api.main import app

    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    srv = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    t = threading.Thread(target=srv.run, daemon=True); t.start()
    for _ in range(100):
        if srv.started:
            break
        time.sleep(0.05)
    os.environ["NO_PROXY"] = "127.0.0.1,localhost"
    yield f"http://127.0.0.1:{port}"
    srv.should_exit = True; t.join(5)


@pytest.fixture
def page(server):
    with pw.sync_playwright() as p:
        try:
            browser = p.chromium.launch(executable_path=_chromium_path(), args=["--no-proxy-server"])
        except Exception as e:  # no browser available in this environment
            pytest.skip(f"Chromium not available: {str(e).splitlines()[0]}")
        ctx = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, locale="id-ID")
        pg = ctx.new_page()
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.base = server
        yield pg
        browser.close()
        assert not errors, errors  # no JavaScript errors anywhere in the flow


def test_main_flow_faucet_check_step(page):
    page.goto(page.base + "/")
    page.wait_for_selector("#modeBadge:not(.hidden)")              # demo mode badge shown
    page.click('button.sample[data-sample="faucet"]')
    page.wait_for_selector("#result:not(.hidden)", timeout=20000)
    assert page.is_visible("#partsImg") and page.is_visible("#stepCard")
    assert page.locator("#dxCauses li, #dxCauses > *").count() >= 1
    page.set_input_files("#stepPhoto", str(FIX / "standin_faucet_hose_clamp.jpg"))
    page.wait_for_selector("#checkResult:not(.hidden)")
    page.wait_for_function("!document.querySelector('#checkResult').textContent.includes('…')", timeout=15000)
    assert page.text_content("#checkResult").strip()


def test_motor_follow_up_question(page):
    page.goto(page.base + "/")
    page.click('button.sample[data-sample="motor"]')
    page.wait_for_selector("#question:not(.hidden)", timeout=20000)
    page.fill("#answerText", "tidak bau bensin")
    page.click("#answerBtn")
    page.wait_for_selector("#result:not(.hidden)", timeout=20000)
    assert page.is_visible("#stepCard")


def test_rice_cooker_red_stop(page):
    page.goto(page.base + "/")
    page.click('button.sample[data-sample="rice"]')
    page.wait_for_selector("#stopBox:not(.hidden)", timeout=20000)
    assert "⛔" in page.text_content("#stopBox")


def test_pwa_manifest_linked(page):
    page.goto(page.base + "/")
    href = page.get_attribute('link[rel="manifest"]', "href")
    assert href and page.request.get(page.base + href).ok
