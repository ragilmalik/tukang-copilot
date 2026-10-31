"""Real-browser check of the live camera guide: Chromium's fake camera feeds getUserMedia, the page sends
frames to /track and draws the SAM highlight on the canvas over the video; "Check now" reuses check-step.
Skips cleanly without Playwright or Chromium (same discovery as test_playwright_smoke.py)."""
import os
import socket
import threading
import time

import pytest

from api.tests.test_playwright_smoke import _chromium_path

pw = pytest.importorskip("playwright.sync_api")


@pytest.fixture
def base():
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


def test_live_guide_draws_highlight_over_fake_camera(base):
    with pw.sync_playwright() as p:
        try:
            browser = p.chromium.launch(executable_path=_chromium_path(), args=[
                "--no-proxy-server", "--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream"])
        except Exception as e:
            pytest.skip(f"Chromium not available: {str(e).splitlines()[0]}")
        ctx = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, locale="en-US")
        ctx.grant_permissions(["camera"], origin=base)
        pg = ctx.new_page()
        errors: list[str] = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        tracked: list[int] = []
        pg.on("response", lambda r: tracked.append(r.status) if "/track" in r.url else None)
        pg.add_init_script("localStorage.setItem('tc_lang','en')")
        pg.goto(base + "/")
        pg.click('button.sample[data-sample="pump"]')
        pg.wait_for_selector("#result:not(.hidden)", timeout=20000)
        for box in pg.locator("#preList input").all():
            box.check()
        pg.click("#liveBtn")
        pg.wait_for_selector("#live:not(.hidden)")
        pg.wait_for_function("document.querySelector('#liveState').textContent.startsWith('🎯 Found')", timeout=15000)
        assert 200 in tracked
        lit = pg.evaluate("""() => { const c = document.querySelector('#liveCanvas'); const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
                                     let n = 0; for (let i = 3; i < d.length; i += 4) if (d[i] > 0) n++; return n; }""")
        assert lit > 500, lit  # the orange outline/box is really drawn over the video
        assert pg.evaluate("document.querySelector('#liveVideo').videoWidth") > 0
        pg.click("#liveCheck")
        pg.wait_for_function("(() => { const t = document.querySelector('#checkResult').textContent; return t && !t.includes('…'); })()", timeout=15000)
        assert pg.text_content("#checkResult").strip()
        pg.click("#liveClose")
        assert pg.is_hidden("#live")
        browser.close()
        assert not errors, errors
